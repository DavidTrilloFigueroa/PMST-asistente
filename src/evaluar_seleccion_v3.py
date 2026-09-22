"""Referencia histórica de la evaluación v3 por lotes; no ejecuta nuevas inferencias."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

from src.consulta_guiada import ConsultaGuiadaLocal
from src.ollama_local import ErrorLocal, URL_LOCAL


RAIZ = Path(__file__).resolve().parents[1]
CASOS = {
    "A": {"peticion": "Quiero reducir el uso del vehículo privado individual en los desplazamientos al trabajo dentro de mi empresa"},
    "B": {"peticion": "Queremos que menos personas vengan solas en coche al trabajo"},
    "C": {
        "peticion": "Queremos mejorar la movilidad de nuestra empresa",
        "aclaracion_automatica": "Queremos reducir los desplazamientos al trabajo en coche individual",
    },
    "D": {"peticion": "Quiero reducir el consumo de agua de los aseos de mi empresa"},
    "E": {"peticion": "Tenemos problemas con el aparcamiento"},
}

# Criterios provisionales exclusivos de esta evaluación; nunca se envían al modelo.
ALTAS_ESPERADAS_AB = {
    "MED-002", "MED-003", "MED-004", "MED-005", "MED-015",
    "MED-023", "MED-024", "MED-025", "MED-026", "MED-030",
}
POSIBLES_PARCIALES_AB = {"MED-020", "MED-027", "MED-031"}
NO_ALTA_AB = "MED-029"
NO_CANDIDATA_AB = "MED-018"


def guardar_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent,
                                     delete=False) as archivo:
        temporal = Path(archivo.name)
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    try:
        os.replace(temporal, ruta)
    finally:
        temporal.unlink(missing_ok=True)


def sha256_si_existe(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest() if ruta.exists() else None


def clasificaciones(comparacion):
    if not comparacion or comparacion.get("estado") == "evaluacion_incompleta":
        return {}
    resultado = {}
    for etiqueta, clave in (("alta", "altas"), ("parcial", "parciales"),
                            ("insuficiente", "insuficientes")):
        for evaluacion in comparacion[clave]:
            resultado[evaluacion["id"]] = etiqueta
    return resultado


def evaluar_criterios(casos):
    evaluacion = {}
    comprobaciones = []
    for clave in ("A", "B"):
        comparacion = casos[clave].get("comparacion")
        etiquetas = clasificaciones(comparacion)
        completa = bool(comparacion and comparacion.get("cobertura", {}).get("completa"))
        altas = {identificador for identificador, etiqueta in etiquetas.items()
                 if etiqueta == "alta"}
        parciales = {identificador for identificador, etiqueta in etiquetas.items()
                     if etiqueta == "parcial"}
        candidatas = altas | parciales
        resultado = {
            "evaluacion_completa": completa,
            "altas_esperadas_presentes": sorted(ALTAS_ESPERADAS_AB & altas),
            "altas_esperadas_omitidas": sorted(ALTAS_ESPERADAS_AB - altas),
            "altas_adicionales": sorted(altas - ALTAS_ESPERADAS_AB),
            "parciales": sorted(parciales),
            "posibles_parciales_observadas": {
                identificador: etiquetas.get(identificador, "ausente")
                for identificador in sorted(POSIBLES_PARCIALES_AB)
            },
            "med_029_no_es_alta": completa and etiquetas.get(NO_ALTA_AB) != "alta",
            "med_018_no_es_candidata": completa and NO_CANDIDATA_AB not in candidatas,
            "cumple_minimo_altas": completa and ALTAS_ESPERADAS_AB <= altas,
        }
        evaluacion[clave] = resultado
        comprobaciones.extend((resultado["cumple_minimo_altas"],
                               resultado["med_029_no_es_alta"],
                               resultado["med_018_no_es_candidata"]))

    caso_c = casos["C"]
    c_pidio = bool(caso_c["interpretaciones"]
                   and caso_c["interpretaciones"][0]["respuesta"]["estado"] == "necesita_aclaracion")
    c_integro = bool(len(caso_c["interpretaciones"]) == 2
                     and caso_c["interpretaciones"][-1]["respuesta"]["estado"] == "listo_para_buscar")
    evaluacion["C"] = {"pidio_aclaracion": c_pidio,
                       "integro_aclaracion_y_quedo_listo": c_integro}
    comprobaciones.append(c_pidio)

    comparacion_d = casos["D"].get("comparacion")
    d_sin = bool(comparacion_d and comparacion_d.get("estado") == "sin_coincidencias"
                 and comparacion_d.get("cobertura", {}).get("completa"))
    evaluacion["D"] = {"sin_coincidencias_con_cobertura_completa": d_sin}
    comprobaciones.append(d_sin)

    caso_e = casos["E"]
    e_pidio = bool(caso_e["interpretaciones"]
                   and caso_e["interpretaciones"][0]["respuesta"]["estado"] == "necesita_aclaracion")
    e_sin_seleccion = "comparacion" not in caso_e
    evaluacion["E"] = {"pidio_aclaracion": e_pidio,
                       "no_selecciono_antes_de_aclarar": e_sin_seleccion}
    comprobaciones.append(e_pidio and e_sin_seleccion)
    evaluacion["resumen"] = {
        "comprobaciones_superadas": sum(comprobaciones),
        "comprobaciones_totales": len(comprobaciones),
        "calidad_general": "no_validada; requiere revisión humana",
    }
    return evaluacion


def ejecutar(args, cliente=None):
    salida = RAIZ / "data/procesados/evaluacion_seleccion_v3.json"
    referencias = [RAIZ / "data/procesados/prueba_qwen_local.json",
                   RAIZ / "data/procesados/evaluacion_seleccion_v2.json"]
    huellas_antes = {ruta.name: sha256_si_existe(ruta) for ruta in referencias}
    informe = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "url": URL_LOCAL,
        "estado": "en_curso",
        "configuracion": {},
        "referencias_anteriores": {nombre: {"sha256_antes": huella}
                                    for nombre, huella in huellas_antes.items()},
        "casos": {},
        "errores": [],
        "calidad_general": "pendiente_de_revision_humana",
    }
    consulta = ConsultaGuiadaLocal(
        RAIZ, modelo=args.modelo, contexto=args.contexto,
        generacion=args.generacion, espera=args.espera,
        tamano_lote=args.tamano_lote, digest=args.digest, cliente=cliente)
    try:
        entorno = consulta.inicializar()
        informe["configuracion"] = consulta.metadatos()
        informe["modelo_instalado"] = entorno["modelo"]
        informe["detalle_modelo"] = entorno["detalle"]
        guardar_json(salida, informe)

        for clave, definicion in CASOS.items():
            print(f"Caso {clave}: interpretación inicial.", flush=True)
            caso = {"peticion": definicion["peticion"], "aclaraciones": [],
                    "interpretaciones": [], "estado": "en_curso"}
            informe["casos"][clave] = caso
            interpretacion = consulta.interpretar(caso["peticion"], caso["aclaraciones"])
            caso["interpretaciones"].append(interpretacion)
            guardar_json(salida, informe)

            if (clave == "C"
                    and interpretacion["respuesta"]["estado"] == "necesita_aclaracion"):
                turno = {"pregunta": interpretacion["respuesta"]["pregunta_aclaracion"],
                         "respuesta": definicion["aclaracion_automatica"]}
                caso["aclaraciones"].append(turno)
                print("Caso C: incorporando la aclaración acordada.", flush=True)
                interpretacion = consulta.interpretar(caso["peticion"], caso["aclaraciones"])
                caso["interpretaciones"].append(interpretacion)
                guardar_json(salida, informe)

            respuesta = interpretacion["respuesta"]
            if respuesta["estado"] == "listo_para_buscar":
                print(f"Caso {clave}: comparación completa por lotes.", flush=True)

                def progreso(evento, datos, caso_clave=clave):
                    if evento == "inicio_lote":
                        print(f"Caso {caso_clave}: lote {datos['numero']}/{datos['total']}.",
                              flush=True)

                caso["comparacion"] = consulta.comparar(
                    respuesta["objetivo_interpretado"], progreso=progreso)
                caso["estado"] = ("completado" if caso["comparacion"]["estado"]
                                  != "evaluacion_incompleta" else "incompleto")
            else:
                caso["estado"] = "pendiente_de_aclaracion"
            guardar_json(salida, informe)

        informe["evaluacion_automatica"] = evaluar_criterios(informe["casos"])
        informe["estado"] = "completado"
    except (ErrorLocal, OSError, ValueError, KeyError) as exc:
        informe["estado"] = "error"
        informe["errores"].append({"codigo": getattr(exc, "codigo", "error_local"),
                                   "mensaje": str(exc)})
        print(f"ERROR: {exc}", flush=True)
    finally:
        for ruta in referencias:
            registro = informe["referencias_anteriores"][ruta.name]
            registro["sha256_despues"] = sha256_si_existe(ruta)
            registro["sin_cambios"] = registro["sha256_antes"] == registro["sha256_despues"]
        guardar_json(salida, informe)
    print("Resultado privado: data/procesados/evaluacion_seleccion_v3.json")
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recalcular-sin-inferencia", action="store_true",
                        help="Recalcula solo los criterios del informe existente.")
    parser.add_argument("--modelo", default="qwen3.6:latest")
    parser.add_argument("--contexto", type=int, default=16384)
    parser.add_argument("--generacion", type=int, default=3072)
    parser.add_argument("--espera", type=float, default=300)
    parser.add_argument("--tamano-lote", type=int, default=8)
    parser.add_argument("--digest", help="Digest esperado del modelo local instalado.")
    args = parser.parse_args()
    if args.recalcular_sin_inferencia:
        ruta = RAIZ / "data/procesados/evaluacion_seleccion_v3.json"
        informe = json.loads(ruta.read_text(encoding="utf-8"))
        informe["evaluacion_automatica"] = evaluar_criterios(informe["casos"])
        guardar_json(ruta, informe)
        print("Criterios recalculados sin realizar inferencias.")
        return 0
    print("La evaluación v3 es histórica y no admite nuevas inferencias. Usa src.evaluar_seleccion_v4.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
