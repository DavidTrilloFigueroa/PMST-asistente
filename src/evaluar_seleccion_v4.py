"""Evaluador del flujo vigente; conserva el nombre histórico del módulo v4."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

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
    "MED-003", "MED-004", "MED-015", "MED-023", "MED-025", "MED-026",
}
POSIBLES_PARCIALES_AB = {"MED-005", "MED-024", "MED-030"}
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
    if not comparacion or comparacion.get("estado") not in ("resultados", "sin_coincidencias"):
        return {}
    return {candidata["id"]: candidata["coincidencia"]
            for candidata in comparacion.get("candidatas", [])}


def comparacion_completa(comparacion):
    catalogo = (comparacion or {}).get("catalogo", {})
    return bool(
        comparacion
        and comparacion.get("modo") == "consulta_unica_catalogo_completo"
        and comparacion.get("consultas_modelo") == 1
        and catalogo.get("completo_enviado") is True
        and catalogo.get("registros_enviados", 0) > 0
        and catalogo.get("campos_enviados") == ["id", "objetivo"]
    )


def evaluar_criterios(casos):
    evaluacion = {}
    comprobaciones = []
    for clave in ("A", "B"):
        comparacion = casos[clave].get("comparacion")
        etiquetas = clasificaciones(comparacion)
        completa = comparacion_completa(comparacion)
        altas = {identificador for identificador, etiqueta in etiquetas.items()
                 if etiqueta == "alta"}
        parciales = {identificador for identificador, etiqueta in etiquetas.items()
                     if etiqueta == "parcial"}
        candidatas = altas | parciales
        no_vacia = completa and comparacion.get("estado") == "resultados" and bool(candidatas)
        resultado = {
            "consulta_unica_catalogo_completo": completa,
            "altas_esperadas_presentes": sorted(ALTAS_ESPERADAS_AB & altas),
            "altas_esperadas_omitidas": sorted(ALTAS_ESPERADAS_AB - altas),
            "altas_adicionales": sorted(altas - ALTAS_ESPERADAS_AB),
            "parciales": sorted(parciales),
            "posibles_parciales_observadas": {
                identificador: etiquetas.get(identificador, "ausente")
                for identificador in sorted(POSIBLES_PARCIALES_AB)
            },
            "med_029_no_es_alta": no_vacia and etiquetas.get(NO_ALTA_AB) != "alta",
            "med_018_no_es_candidata": no_vacia and NO_CANDIDATA_AB not in candidatas,
            "med_019_no_es_candidata": no_vacia and "MED-019" not in candidatas,
            "cumple_minimo_altas": no_vacia and bool(ALTAS_ESPERADAS_AB & altas),
            "candidatas_no_vacias": no_vacia,
            "posibles_parciales_omitidas_revision_humana": sorted(POSIBLES_PARCIALES_AB - candidatas),
            "respaldo_documental_parciales": "pendiente_de_revision_humana; presencia no acredita respaldo y ausencia no acredita irrelevancia",
        }
        evaluacion[clave] = resultado
        comprobaciones.extend((resultado["cumple_minimo_altas"],
                               resultado["med_029_no_es_alta"],
                               resultado["med_018_no_es_candidata"],
                               resultado["med_019_no_es_candidata"]))

    caso_c = casos["C"]
    c_pidio = bool(caso_c.get("interpretaciones")
                   and caso_c["interpretaciones"][0]["respuesta"]["estado"]
                   == "necesita_aclaracion")
    c_integro = bool(len(caso_c.get("interpretaciones", [])) == 2
                     and caso_c["interpretaciones"][-1]["respuesta"]["estado"]
                     == "listo_para_buscar")
    comparacion_c = caso_c.get("comparacion") or {}
    c_resultados = bool(comparacion_completa(comparacion_c)
                        and comparacion_c.get("estado") == "resultados"
                        and comparacion_c.get("candidatas"))
    evaluacion["C"] = {"pidio_aclaracion": c_pidio,
                       "integro_aclaracion_y_quedo_listo": c_integro,
                       "candidatas_tras_aclaracion": c_pidio and c_integro and c_resultados}
    comprobaciones.append(c_pidio and c_integro and c_resultados)

    comparacion_d = casos["D"].get("comparacion")
    d_sin = bool(comparacion_d and comparacion_d.get("estado") == "sin_coincidencias"
                 and comparacion_completa(comparacion_d))
    evaluacion["D"] = {"sin_coincidencias_con_catalogo_completo": d_sin}
    comprobaciones.append(d_sin)

    caso_e = casos["E"]
    e_pidio = bool(caso_e.get("interpretaciones")
                   and caso_e["interpretaciones"][0]["respuesta"]["estado"]
                   == "necesita_aclaracion")
    e_sin_seleccion = "comparacion" not in caso_e
    evaluacion["E"] = {"pidio_aclaracion": e_pidio,
                       "no_selecciono_antes_de_aclarar": e_sin_seleccion}
    comprobaciones.append(e_pidio and e_sin_seleccion)
    evaluacion["resumen"] = {
        "minimos_automaticos_cumplidos": all(comprobaciones),
        "comprobaciones_superadas": sum(comprobaciones),
        "comprobaciones_totales": len(comprobaciones),
        "calidad_general": "no_validada; requiere revisión humana",
    }
    return evaluacion


def ejecutar(args, cliente=None):
    salida = RAIZ / "data/procesados/evaluacion_seleccion_v5.json"
    if salida.exists():
        raise FileExistsError("Ya existe la evaluación v5; no se sobrescribe ni se repite automáticamente.")
    referencias = [
        RAIZ / "data/procesados/prueba_qwen_local.json",
        RAIZ / "data/procesados/evaluacion_seleccion_v2.json",
        RAIZ / "data/procesados/evaluacion_seleccion_v3.json",
    ]
    originales = [
        RAIZ / "data/originales/MEDIDAS.xlsx",
        RAIZ / "data/originales/Relaciones medidas-medidas.xlsx",
        RAIZ / "data/originales/Relaciones medidas-KPIs.xlsx",
        RAIZ / "data/procesados/objetivos_busqueda.json",
    ]
    huellas_antes = {str(ruta.relative_to(RAIZ)): sha256_si_existe(ruta)
                     for ruta in referencias + originales}
    informe = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "url": URL_LOCAL,
        "estado": "en_curso",
        "configuracion": {},
        "integridad_archivos": {
            nombre: {"sha256_antes": huella} for nombre, huella in huellas_antes.items()
        },
        "casos": {},
        "errores": [],
        "calidad_general": "pendiente_de_revision_humana",
    }
    consulta = ConsultaGuiadaLocal(
        RAIZ, modelo=args.modelo, contexto=args.contexto,
        generacion=args.generacion, espera=args.espera,
        digest=args.digest, cliente=cliente)
    try:
        entorno = consulta.inicializar()
        informe["configuracion"] = consulta.metadatos()
        informe["modelo_instalado"] = entorno["modelo"]
        informe["detalle_modelo"] = entorno["detalle"]
        guardar_json(salida, informe)

        for clave, definicion in CASOS.items():
            inicio_caso = time.perf_counter()
            print(f"Caso {clave}: interpretación inicial.", flush=True)
            caso = {"peticion": definicion["peticion"], "aclaraciones": [],
                    "interpretaciones": [], "estado": "en_curso"}
            informe["casos"][clave] = caso
            try:
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
                    print(f"Caso {clave}: consulta única al catálogo completo.", flush=True)
                    caso["comparacion"] = consulta.comparar(respuesta["objetivo_interpretado"])
                    caso["estado"] = "completado"
                else:
                    caso["estado"] = "pendiente_de_aclaracion"
            except (ErrorLocal, OSError, ValueError, KeyError) as exc:
                caso["estado"] = "error"
                error = {"caso": clave, "codigo": getattr(exc, "codigo", "error_local"),
                         "mensaje": str(exc)}
                caso["error"] = error
                informe["errores"].append(error)
                print(f"Caso {clave}: ERROR: {exc}", flush=True)
            finally:
                caso["tiempo_total_cliente_s"] = time.perf_counter() - inicio_caso
                guardar_json(salida, informe)

        informe["evaluacion_automatica"] = evaluar_criterios(informe["casos"])
        informe["estado"] = "completado" if not informe["errores"] else "completado_con_errores"
    except (ErrorLocal, OSError, ValueError, KeyError) as exc:
        informe["estado"] = "error"
        informe["errores"].append({"codigo": getattr(exc, "codigo", "error_local"),
                                   "mensaje": str(exc)})
        print(f"ERROR: {exc}", flush=True)
    finally:
        for ruta in referencias + originales:
            nombre = str(ruta.relative_to(RAIZ))
            registro = informe["integridad_archivos"][nombre]
            registro["sha256_despues"] = sha256_si_existe(ruta)
            registro["sin_cambios"] = registro["sha256_antes"] == registro["sha256_despues"]
        guardar_json(salida, informe)
    print("Resultado privado: data/procesados/evaluacion_seleccion_v5.json")
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="qwen3.6:latest")
    parser.add_argument("--contexto", type=int, default=16384)
    parser.add_argument("--generacion", type=int, default=3072)
    parser.add_argument("--espera", type=float, default=300)
    parser.add_argument("--digest", help="Digest esperado del modelo local instalado.")
    args = parser.parse_args()
    try:
        informe = ejecutar(args)
    except FileExistsError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0 if informe["estado"] == "completado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
