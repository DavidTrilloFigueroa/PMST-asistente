"""Entrada por terminal para la consulta guiada local de PMST Asistente."""

import argparse
from pathlib import Path

from src.consulta_guiada import ConsultaGuiadaLocal
from src.ollama_local import ErrorLocal
from src.presentacion_terminal import (
    cargar_datos_presentacion, construir_tarjetas, filtrar_relaciones,
    mostrar_detalles, mostrar_relaciones, mostrar_tarjetas, pedir_seleccion,
    RESPUESTAS_SALIDA,
)


RAIZ = Path(__file__).resolve().parents[1]


def mostrar_candidatas(resultado, datos=None):
    if resultado["estado"] == "sin_coincidencias":
        print("\nNo se encontraron objetivos documentados que respondan a la necesidad.")
        return 0
    if datos:
        tarjetas = construir_tarjetas(resultado["candidatas"], datos)
    else:
        tarjetas = [{**candidata,
                     "descripcion_breve": candidata.get(
                         "descripcion_breve", "No consta en la documentación"),
                     "kpis": candidata.get("kpis", [])}
                    for candidata in resultado["candidatas"]]
    mostrar_tarjetas(tarjetas)
    return tarjetas


def _es_salida(texto):
    return texto.strip().casefold() in RESPUESTAS_SALIDA


def ejecutar_terminal(args):
    consulta = ConsultaGuiadaLocal(
        RAIZ, modelo=args.modelo, contexto=args.contexto,
        generacion=args.generacion, espera=args.espera, digest=args.digest)
    try:
        consulta.inicializar()
        peticion = args.peticion or input("Describe el problema de movilidad de tu empresa: ").strip()
        if _es_salida(peticion):
            print("\nConsulta finalizada.")
            return 0
        if not peticion:
            raise ErrorLocal("consulta_invalida", "La petición no puede estar vacía.")
        aclaraciones = []
        while True:
            interpretacion = consulta.interpretar(peticion, aclaraciones)["respuesta"]
            print(f"\nObjetivo interpretado: {interpretacion['objetivo_interpretado']}")
            if interpretacion["estado"] == "listo_para_buscar":
                break
            pregunta = interpretacion["pregunta_aclaracion"]
            respuesta = input(f"{pregunta}\nTu respuesta: ").strip()
            if _es_salida(respuesta):
                print("\nConsulta finalizada.")
                return 0
            if not respuesta:
                raise ErrorLocal("consulta_incompleta", "La aclaración no puede estar vacía.")
            aclaraciones.append({"pregunta": pregunta, "respuesta": respuesta})
        print("\nComparando el objetivo con el catálogo completo en una sola consulta...")
        resultado = consulta.comparar(interpretacion["objetivo_interpretado"])
        if resultado["estado"] == "sin_coincidencias":
            mostrar_candidatas(resultado)
            return 0
        datos = cargar_datos_presentacion(RAIZ)
        tarjetas = mostrar_candidatas(resultado, datos)
        seleccion = pedir_seleccion([tarjeta["id"] for tarjeta in tarjetas])
        if seleccion is None:
            print("\nConsulta finalizada sin seleccionar medidas.")
            return 0
        mostrar_detalles(seleccion, datos)
        relaciones = filtrar_relaciones(
            datos["relaciones"], datos["tipos_relacion"], seleccion)
        mostrar_relaciones(relaciones)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nConsulta cancelada.")
        return 0
    except (ErrorLocal, OSError, ValueError) as exc:
        print(f"\nERROR: {exc}")
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--peticion", help="Petición inicial; si se omite, se solicita por terminal.")
    parser.add_argument("--modelo", default="qwen3.6:latest")
    parser.add_argument("--contexto", type=int, default=16384)
    parser.add_argument("--generacion", type=int, default=3072)
    parser.add_argument("--espera", type=float, default=300)
    parser.add_argument("--digest", help="Digest esperado del modelo local ya instalado.")
    return ejecutar_terminal(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
