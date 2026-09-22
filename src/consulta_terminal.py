"""Entrada por terminal para la consulta guiada local de PMST Asistente."""

import argparse
from pathlib import Path

from src.consulta_guiada import ConsultaGuiadaLocal
from src.ollama_local import ErrorLocal


RAIZ = Path(__file__).resolve().parents[1]


def mostrar_candidatas(resultado):
    if resultado["estado"] == "sin_coincidencias":
        print("\nNo se encontraron objetivos documentados que respondan a la necesidad.")
        return 0
    print("\nCandidatas (coincidencia alta primero y parcial después):")
    for candidata in resultado["candidatas"]:
        print(f"\n{candidata['id']} — {candidata['nombre']}")
        print(f"Coincidencia: {candidata['coincidencia']}")
        print(f"Justificación: {candidata['justificacion']}")
        print(f"Objetivo documentado: {candidata['objetivo_documentado']}")
        condicion = candidata["condicion_o_limite"] or "No aplica"
        print(f"Condición o límite: {condicion}")
    return 0


def ejecutar_terminal(args):
    consulta = ConsultaGuiadaLocal(
        RAIZ, modelo=args.modelo, contexto=args.contexto,
        generacion=args.generacion, espera=args.espera, digest=args.digest)
    try:
        consulta.inicializar()
        peticion = args.peticion or input("Describe el problema de movilidad de tu empresa: ").strip()
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
            if not respuesta:
                raise ErrorLocal("consulta_incompleta", "La aclaración no puede estar vacía.")
            aclaraciones.append({"pregunta": pregunta, "respuesta": respuesta})
        print("\nComparando el objetivo con el catálogo completo en una sola consulta...")
        resultado = consulta.comparar(interpretacion["objetivo_interpretado"])
        return mostrar_candidatas(resultado)
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
