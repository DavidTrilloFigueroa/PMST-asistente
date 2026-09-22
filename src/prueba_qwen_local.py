"""Prueba local de selección por objetivos: una petición y una repetición válida."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from src.ollama_local import ErrorLocal, OllamaLocal, URL_LOCAL, json_estricto
from src.seleccion_objetivos import (INSTRUCCIONES_VERSION, preparar_peticion,
                                     validar_respuesta)

RAIZ = Path(__file__).resolve().parents[1]
PETICION = "Quiero reducir el uso del vehículo privado individual en los desplazamientos al trabajo dentro de mi empresa"
def extraer_resultado(bruto, catalogo, generacion, contexto):
    if bruto.get("done") is not True or bruto.get("done_reason") != "stop":
        raise ErrorLocal("respuesta_truncada", "La generación no terminó normalmente; no se acepta como selección.")
    if isinstance(bruto.get("eval_count"), int) and bruto["eval_count"] >= generacion:
        raise ErrorLocal("respuesta_truncada", "Se alcanzó el límite de generación.")
    entrada, salida = bruto.get("prompt_eval_count"), bruto.get("eval_count")
    if isinstance(entrada, int) and isinstance(salida, int) and entrada + salida >= contexto:
        raise ErrorLocal("contexto_insuficiente", "Se alcanzó el contexto; no se acepta una posible selección incompleta.")
    mensaje = bruto.get("message")
    if not isinstance(mensaje, dict) or not isinstance(mensaje.get("content"), str):
        raise ErrorLocal("respuesta_invalida", "Falta el contenido textual de la respuesta.")
    # Nunca serializar message.thinking ni la respuesta bruta de Ollama.
    if mensaje.get("thinking") or "<think>" in mensaje["content"] or "</think>" in mensaje["content"]:
        raise ErrorLocal("razonamiento_no_solicitado", "El modelo devolvió razonamiento no solicitado; se descarta sin guardarlo.")
    return validar_respuesta(json_estricto(mensaje["content"]), catalogo)


def metricas(bruto, segundos):
    claves = ("total_duration", "load_duration", "prompt_eval_count", "prompt_eval_cached_count",
              "prompt_eval_duration", "eval_count", "eval_duration", "done_reason")
    resultado = {k: bruto.get(k) for k in claves}
    resultado["tiempo_cliente_s"] = segundos
    for clave in ("total_duration", "load_duration", "prompt_eval_duration", "eval_duration"):
        valor = bruto.get(clave)
        resultado[clave + "_s"] = valor / 1e9 if isinstance(valor, (int, float)) else None
    duracion, tokens = bruto.get("eval_duration"), bruto.get("eval_count")
    resultado["tokens_s"] = tokens / (duracion / 1e9) if isinstance(tokens, int) and isinstance(duracion, int) and duracion > 0 else None
    return resultado


def guardar(ruta, informe):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent, delete=False) as archivo:
        temporal = Path(archivo.name)
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    try:
        os.replace(temporal, ruta)
    finally:
        temporal.unlink(missing_ok=True)


def consultar_ps_cli():
    """Consulta solicitada a la CLI, forzando también su servidor a loopback."""
    ejecutable = shutil.which("ollama")
    if not ejecutable and os.name == "nt":
        candidato = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Ollama/ollama.exe"
        if candidato.is_file():
            ejecutable = str(candidato)
    if not ejecutable:
        return {"disponible": False, "motivo": "CLI no localizada; consultar cargados_despues de la API."}
    try:
        resultado = subprocess.run([ejecutable, "ps"], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=10,
                                   env={**os.environ, "OLLAMA_HOST": URL_LOCAL},
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        return {"disponible": resultado.returncode == 0, "salida": resultado.stdout.strip()}
    except (OSError, subprocess.TimeoutExpired):
        return {"disponible": False, "motivo": "No se pudo consultar la CLI."}


def ejecutar(args, cliente=None):
    cliente = cliente or OllamaLocal()
    # La referencia original se conserva; las nuevas ejecuciones usan otro archivo.
    ruta = RAIZ / "data/procesados/prueba_qwen_local_actual.json"
    informe = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "url": URL_LOCAL,
               "estado": "en_curso", "modelo_ejecutable": None, "respuesta_tecnicamente_valida": False,
               "calidad_seleccion": "pendiente_de_revision_humana", "peticion": args.peticion,
               "instrucciones_version": INSTRUCCIONES_VERSION,
               "configuracion": {"modelo": args.modelo, "contexto": args.contexto, "generacion": args.generacion,
                                 "espera_s": args.espera, "think": False, "temperatura": 0, "seed": 42},
               "peticiones": [], "errores": []}
    try:
        hardware = RAIZ / "data/procesados/hardware_ollama_local.json"
        if hardware.exists():
            informe["hardware_previo_con_fecha"] = json.loads(hardware.read_text(encoding="utf-8-sig"))
        entorno = cliente.inspeccionar(args.modelo, args.digest)
        informe["entorno_inicial"] = entorno
        informe["ollama_ps_inicial"] = consultar_ps_cli()
        digest = entorno["modelo"]["digest"]
        info = entorno["detalle"]["model_info"] or {}
        maximos = [v for k, v in info.items() if k.endswith(".context_length") and isinstance(v, int)]
        if not maximos or args.contexto > min(maximos):
            raise ErrorLocal("contexto_insuficiente", "No se puede confirmar que el modelo admita el contexto solicitado.")
        if info.get("tokenizer.ggml.model") != "gpt2":
            raise ErrorLocal("tokenizador_no_verificado", "La cota de contexto requiere verificar un tokenizador BPE de bytes; no se presupone por la etiqueta.")
        if "completion" not in (entorno["detalle"]["capabilities"] or []):
            raise ErrorLocal("capacidad_ausente", "El modelo no declara capacidad de generación.")
        archivo = RAIZ / "data/procesados/objetivos_busqueda.json"
        datos = archivo.read_bytes()
        catalogo = json_estricto(datos)
        cuerpo, cota = preparar_peticion(args.modelo, catalogo, args.peticion, args.contexto, args.generacion)
        informe["catalogo"] = {"archivo": archivo.name, "sha256": hashlib.sha256(datos).hexdigest(),
                               "medidas": len(catalogo), "campos": ["id", "objetivo"],
                               "cota_conservadora_tokens_entrada": cota, "catalogo_completo": True}
        informe["solicitud_sha256"] = hashlib.sha256(json.dumps(cuerpo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        guardar(ruta, informe)
        for numero in (1, 2):
            # Verificar la identidad justo antes de cada inferencia, sin cambiar etiquetas.
            actual = cliente.inspeccionar(args.modelo, digest)
            corrida = {"numero": numero, "cargados_antes": actual["cargados"], "validacion": "pendiente"}
            informe["peticiones"].append(corrida)
            guardar(ruta, informe)
            print(f"Petición {numero}/2 iniciada (máximo {args.espera:g} s).", flush=True)
            inicio = time.perf_counter()
            try:
                bruto = cliente.solicitar("/api/chat", cuerpo, args.espera)
                corrida["metricas"] = metricas(bruto, time.perf_counter() - inicio)
                informe["modelo_ejecutable"] = True
                respuesta = extraer_resultado(bruto, catalogo, args.generacion, args.contexto)
                corrida["respuesta"] = respuesta
                corrida["validacion"] = "correcta"
                informe["respuesta_tecnicamente_valida"] = True
                del bruto
                posterior = cliente.inspeccionar(args.modelo, digest)
                corrida["cargados_despues"] = posterior["cargados"]
                corrida["ollama_ps"] = consultar_ps_cli()
                # Recuperación local posterior: jamás se incluye en cuerpo ni en la siguiente petición.
                fichas = json.loads((RAIZ / "data/procesados/medidas.json").read_text(encoding="utf-8"))
                nombres = {m["id"]: m.get("nombre") for m in fichas}
                corrida["nombres_para_presentacion"] = {m["id"]: nombres.get(m["id"]) or "No consta en la documentación" for m in respuesta["medidas"]}
                guardar(ruta, informe)
                print(f"Petición {numero}: respuesta válida, {corrida['metricas']['tiempo_cliente_s']:.2f} s.", flush=True)
            except ErrorLocal:
                corrida["tiempo_hasta_error_s"] = time.perf_counter() - inicio
                corrida["validacion"] = "error"
                raise
        informe["estado"] = "completado"
    except (ErrorLocal, OSError, ValueError) as exc:
        informe["estado"] = "error"
        informe["errores"].append({"codigo": getattr(exc, "codigo", "archivo_o_dato_invalido"), "mensaje": str(exc)})
        try:
            informe["cargados_tras_error"] = cliente.solicitar("/api/ps")
        except ErrorLocal:
            informe["cargados_tras_error"] = None
        print(f"ERROR: {exc}", flush=True)
    guardar(ruta, informe)
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="qwen3.6:latest")
    parser.add_argument("--contexto", type=int, default=16384)
    parser.add_argument("--generacion", type=int, default=3072)
    parser.add_argument("--espera", type=float, default=300)
    parser.add_argument("--digest", help="Digest esperado; impide ejecutar una etiqueta cuyo contenido haya cambiado.")
    parser.add_argument("--peticion", default=PETICION)
    informe = ejecutar(parser.parse_args())
    print("Resultado privado: data/procesados/prueba_qwen_local_actual.json")
    return 0 if informe["estado"] == "completado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
