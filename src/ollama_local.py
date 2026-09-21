"""Cliente limitado a Ollama en loopback. Solo biblioteca estándar."""

import http.client
import json
import socket
import time

URL_LOCAL = "http://127.0.0.1:11434"


class ErrorLocal(Exception):
    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo


def json_estricto(texto):
    def pares(items):
        resultado = {}
        for clave, valor in items:
            if clave in resultado:
                raise ValueError("Clave JSON duplicada")
            resultado[clave] = valor
        return resultado

    def constante(_):
        raise ValueError("Constante JSON no válida")

    try:
        return json.loads(texto, object_pairs_hook=pares, parse_constant=constante)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ErrorLocal("respuesta_invalida", "No se recibió JSON estricto válido.") from exc


def clasificar_error(estado, texto):
    texto = texto.lower()
    if any(x in texto for x in ("out of memory", "insufficient memory", "not enough", "requires more", "unable to allocate", "cuda malloc", "failed to allocate")):
        return ErrorLocal("memoria_insuficiente", "Ollama informa de memoria insuficiente. Prueba detenida.")
    if estado == 404:
        return ErrorLocal("modelo_ausente", "El modelo o el recurso solicitado no está disponible localmente.")
    return ErrorLocal("error_ollama", f"Ollama devolvió un error HTTP {estado}; no equivale a ausencia de coincidencias.")


class OllamaLocal:
    def solicitar(self, ruta, datos=None, espera=10):
        if ruta not in ("/api/version", "/api/tags", "/api/show", "/api/ps", "/api/chat"):
            raise ErrorLocal("ruta_no_permitida", "Endpoint no permitido.")
        if not isinstance(espera, (int, float)) or not 0 < espera <= 1800:
            raise ErrorLocal("configuracion_invalida", "La espera debe estar entre 0 y 1800 segundos.")
        conexion = http.client.HTTPConnection("127.0.0.1", 11434, timeout=espera)
        limite = time.monotonic() + espera
        try:
            # Sin proxy, redirecciones, credenciales ni URL configurable.
            conexion.connect()
            canal = conexion.sock
            def restante():
                segundos = limite - time.monotonic()
                if segundos <= 0:
                    raise TimeoutError()
                canal.settimeout(segundos)
            restante()
            cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8") if datos is not None else None
            conexion.request("POST" if datos is not None else "GET", ruta, cuerpo,
                             {"Content-Type": "application/json"})
            restante()
            respuesta = conexion.getresponse()
            partes, longitud = [], 0
            while True:
                restante()
                bloque = respuesta.read1(65536)
                if not bloque:
                    break
                longitud += len(bloque)
                if longitud > 8 * 1024 * 1024:
                    raise ErrorLocal("respuesta_invalida", "Respuesta local excesivamente grande.")
                partes.append(bloque)
            bruto = b"".join(partes)
            if respuesta.status != 200:
                raise clasificar_error(respuesta.status, bruto.decode("utf-8", errors="replace"))
            resultado = json_estricto(bruto)
            if not isinstance(resultado, dict):
                raise ErrorLocal("respuesta_invalida", "La API no devolvió un objeto JSON.")
            if "error" in resultado:
                raise clasificar_error(500, str(resultado["error"]))
            return resultado
        except (TimeoutError, socket.timeout) as exc:
            raise ErrorLocal("tiempo_agotado", "Tiempo máximo agotado. No se reintentará ni se cambiará de modelo.") from exc
        except (OSError, http.client.HTTPException) as exc:
            raise ErrorLocal("servicio_no_disponible", "No se pudo completar la conexión con Ollama en 127.0.0.1:11434. Comprueba que Ollama esté abierto.") from exc
        finally:
            conexion.close()

    def inspeccionar(self, modelo, digest_esperado=None):
        version = self.solicitar("/api/version")
        instalados = self.solicitar("/api/tags").get("models", [])
        if not isinstance(instalados, list) or any(not isinstance(m, dict) for m in instalados):
            raise ErrorLocal("respuesta_invalida", "Lista de modelos inválida en la API local.")
        coincidencias = [m for m in instalados if m.get("name") == modelo]
        if len(coincidencias) != 1:
            raise ErrorLocal("modelo_ausente", "La etiqueta solicitada no figura en los modelos instalados. No se descargará nada.")
        registro = coincidencias[0]
        detalle = self.solicitar("/api/show", {"model": modelo})
        if (not isinstance(registro.get("details"), dict) or not isinstance(detalle.get("details"), dict)
                or not isinstance(registro.get("size"), int)):
            raise ErrorLocal("respuesta_invalida", "Metadatos locales incompletos o inválidos.")
        if (registro.get("remote_host") or registro.get("remote_model") or detalle.get("remote_host")
                or detalle.get("remote_model") or registro.get("details", {}).get("format") != "gguf"
                or detalle.get("details", {}).get("format") != "gguf"
                or not registro.get("size", 0) > 0 or not registro.get("digest")):
            raise ErrorLocal("modelo_no_local", "No se ha podido confirmar un modelo GGUF local sin referencia cloud.")
        if digest_esperado and registro["digest"] != digest_esperado:
            raise ErrorLocal("modelo_cambiado", "El digest instalado no coincide con el solicitado. No se ejecutará otro modelo.")
        return {"version_ollama": version, "instalados": instalados, "modelo": registro,
                "detalle": {k: detalle.get(k) for k in ("details", "capabilities", "model_info", "parameters", "remote_host", "remote_model")},
                "cargados": self.solicitar("/api/ps")}
