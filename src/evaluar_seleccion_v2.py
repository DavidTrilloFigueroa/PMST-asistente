"""Ejecuta una vez los cuatro casos acordados para selección por objetivos v2."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from src.ollama_local import ErrorLocal, OllamaLocal, URL_LOCAL, json_estricto
from src.prueba_qwen_local import (consultar_ps_cli, extraer_resultado, guardar,
                                   metricas)
from src.seleccion_objetivos import (INSTRUCCIONES, INSTRUCCIONES_VERSION,
                                     preparar_peticion, validar_catalogo)


RAIZ = Path(__file__).resolve().parents[1]
CASOS = (
    ("A", "Quiero reducir el uso del vehículo privado individual en los desplazamientos al trabajo dentro de mi empresa"),
    ("B", "Queremos que menos personas vengan solas en coche al trabajo"),
    ("C", "Queremos mejorar la movilidad de nuestra empresa"),
    ("D", "Quiero reducir el consumo de agua de los aseos de mi empresa"),
)

# Criterios de esta evaluación, no usados por el selector ni enviados al modelo.
MINIMOS_DIRECTOS_AB = {
    "MED-002", "MED-003", "MED-004", "MED-005", "MED-015",
    "MED-023", "MED-024", "MED-025", "MED-026", "MED-030",
}
NO_DIRECTA_AB = "MED-029"


def verificar_entorno(cliente, modelo, digest, contexto):
    entorno = cliente.inspeccionar(modelo, digest)
    info = entorno["detalle"].get("model_info") or {}
    maximos = [valor for clave, valor in info.items()
               if clave.endswith(".context_length") and isinstance(valor, int)]
    if not maximos or contexto > min(maximos):
        raise ErrorLocal("contexto_insuficiente",
                         "No se puede confirmar que el modelo admita el contexto solicitado.")
    if info.get("tokenizer.ggml.model") != "gpt2":
        raise ErrorLocal("tokenizador_no_verificado",
                         "La cota requiere un tokenizador BPE de bytes verificado.")
    if "completion" not in (entorno["detalle"].get("capabilities") or []):
        raise ErrorLocal("capacidad_ausente", "El modelo no declara capacidad de generación.")
    return entorno


def evaluar_criterios(casos):
    evaluacion = {}
    for clave in ("A", "B"):
        respuesta = casos[clave]["respuesta"]
        directas = {m["id"] for m in respuesta["medidas"]
                    if m["tipo_coincidencia"] == "directa"}
        condicionadas = {m["id"] for m in respuesta["medidas"]
                         if m["tipo_coincidencia"] == "condicionada"}
        evaluacion[clave] = {
            "minimos_directos_presentes": sorted(MINIMOS_DIRECTOS_AB & directas),
            "minimos_directos_omitidos": sorted(MINIMOS_DIRECTOS_AB - directas),
            "directas_adicionales": sorted(directas - MINIMOS_DIRECTOS_AB),
            "condicionadas": sorted(condicionadas),
            "med_029_no_es_directa": NO_DIRECTA_AB not in directas,
            "cumple_minimo_provisional": MINIMOS_DIRECTOS_AB <= directas,
        }
    evaluacion["C"] = {
        "esperado": "necesita_aclaracion",
        "obtenido": casos["C"]["respuesta"]["estado"],
        "cumple": casos["C"]["respuesta"]["estado"] == "necesita_aclaracion",
    }
    evaluacion["D"] = {
        "esperado": "sin_coincidencias",
        "obtenido": casos["D"]["respuesta"]["estado"],
        "cumple": casos["D"]["respuesta"]["estado"] == "sin_coincidencias",
    }
    directas_a = {m["id"] for m in casos["A"]["respuesta"]["medidas"]
                  if m["tipo_coincidencia"] == "directa"}
    directas_b = {m["id"] for m in casos["B"]["respuesta"]["medidas"]
                  if m["tipo_coincidencia"] == "directa"}
    evaluacion["comparacion_A_B"] = {
        "directas_comunes": sorted(directas_a & directas_b),
        "solo_A": sorted(directas_a - directas_b),
        "solo_B": sorted(directas_b - directas_a),
        "no_exige_justificaciones_identicas": True,
    }
    evaluacion["resumen"] = {
        "comprobaciones_superadas": sum((evaluacion["A"]["cumple_minimo_provisional"],
                                          evaluacion["A"]["med_029_no_es_directa"],
                                          evaluacion["B"]["cumple_minimo_provisional"],
                                          evaluacion["B"]["med_029_no_es_directa"],
                                          evaluacion["C"]["cumple"], evaluacion["D"]["cumple"])),
        "comprobaciones_totales": 6,
        "calidad_general": "no_validada; requiere revisión humana",
    }
    return evaluacion


def ejecutar(args, cliente=None):
    cliente = cliente or OllamaLocal()
    salida = RAIZ / "data/procesados/evaluacion_seleccion_v2.json"
    referencia = RAIZ / "data/procesados/prueba_qwen_local.json"
    referencia_antes = hashlib.sha256(referencia.read_bytes()).hexdigest()
    informe = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "url": URL_LOCAL,
        "estado": "en_curso",
        "instrucciones": {
            "version": INSTRUCCIONES_VERSION,
            "sha256": hashlib.sha256(INSTRUCCIONES.encode("utf-8")).hexdigest(),
        },
        "configuracion": {"modelo": args.modelo, "contexto": args.contexto,
                          "generacion": args.generacion, "espera_s": args.espera,
                          "think": False, "temperatura": 0, "seed": 42,
                          "una_peticion_por_caso": True},
        "referencia_original": {"archivo": referencia.name, "sha256_antes": referencia_antes},
        "casos": {},
        "errores": [],
        "calidad_general": "pendiente_de_revision_humana",
    }
    try:
        entorno = verificar_entorno(cliente, args.modelo, args.digest, args.contexto)
        informe["entorno_inicial"] = entorno
        informe["ollama_ps_inicial"] = consultar_ps_cli()
        digest = entorno["modelo"]["digest"]
        archivo_catalogo = RAIZ / "data/procesados/objetivos_busqueda.json"
        bruto_catalogo = archivo_catalogo.read_bytes()
        catalogo = json_estricto(bruto_catalogo)
        validar_catalogo(catalogo)
        informe["catalogo"] = {
            "archivo": archivo_catalogo.name,
            "sha256": hashlib.sha256(bruto_catalogo).hexdigest(),
            "registros": len(catalogo),
            "campos": ["id", "objetivo"],
            "completo": True,
        }
        guardar(salida, informe)
        for clave, peticion in CASOS:
            actual = verificar_entorno(cliente, args.modelo, digest, args.contexto)
            cuerpo, cota = preparar_peticion(args.modelo, catalogo, peticion,
                                             args.contexto, args.generacion)
            caso = {
                "peticion": peticion,
                "validacion": "pendiente",
                "cota_conservadora_tokens_entrada": cota,
                "solicitud_sha256": hashlib.sha256(
                    json.dumps(cuerpo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
                "cargados_antes": actual["cargados"],
            }
            informe["casos"][clave] = caso
            guardar(salida, informe)
            print(f"Caso {clave}/D iniciado (máximo {args.espera:g} s).", flush=True)
            inicio = time.perf_counter()
            try:
                bruto = cliente.solicitar("/api/chat", cuerpo, args.espera)
                caso["metricas"] = metricas(bruto, time.perf_counter() - inicio)
                caso["respuesta"] = extraer_resultado(
                    bruto, catalogo, args.generacion, args.contexto)
                caso["validacion"] = "correcta"
                caso["cargados_despues"] = cliente.solicitar("/api/ps")
                del bruto
                guardar(salida, informe)
                print(f"Caso {clave}: respuesta válida en "
                      f"{caso['metricas']['tiempo_cliente_s']:.2f} s.", flush=True)
            except ErrorLocal:
                caso["validacion"] = "error"
                caso["tiempo_hasta_error_s"] = time.perf_counter() - inicio
                raise

        # Los nombres se consultan solo después de validar todas las selecciones.
        fichas = json.loads((RAIZ / "data/procesados/medidas.json").read_text(encoding="utf-8"))
        nombres = {m["id"]: m.get("nombre") for m in fichas}
        for caso in informe["casos"].values():
            caso["nombres_para_presentacion"] = {
                m["id"]: nombres.get(m["id"]) or "No consta en la documentación"
                for m in caso["respuesta"]["medidas"]
            }
        informe["evaluacion_automatica"] = evaluar_criterios(informe["casos"])
        informe["ollama_ps_final"] = consultar_ps_cli()
        informe["estado"] = "completado"
    except (ErrorLocal, OSError, ValueError, KeyError) as exc:
        informe["estado"] = "error"
        informe["errores"].append({
            "codigo": getattr(exc, "codigo", "archivo_o_dato_invalido"),
            "mensaje": str(exc),
        })
        print(f"ERROR: {exc}", flush=True)
    finally:
        referencia_despues = hashlib.sha256(referencia.read_bytes()).hexdigest()
        informe["referencia_original"]["sha256_despues"] = referencia_despues
        informe["referencia_original"]["sin_cambios"] = referencia_antes == referencia_despues
        guardar(salida, informe)
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="qwen3.6:latest")
    parser.add_argument("--contexto", type=int, default=16384)
    parser.add_argument("--generacion", type=int, default=3072)
    parser.add_argument("--espera", type=float, default=300)
    parser.add_argument("--digest", help="Digest esperado del modelo ya instalado.")
    informe = ejecutar(parser.parse_args())
    print("Resultado privado: data/procesados/evaluacion_seleccion_v2.json")
    return 0 if informe["estado"] == "completado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
