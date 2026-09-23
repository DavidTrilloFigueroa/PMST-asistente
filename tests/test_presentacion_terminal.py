"""Pruebas pequeñas de la lógica local de presentación, sin Ollama."""

import unittest

from src.presentacion_terminal import (
    SIN_DOCUMENTACION, descripcion_breve, filtrar_relaciones,
    validar_ids_seleccion,
)


class PresentacionTerminalTests(unittest.TestCase):
    def test_descripcion_breve_usa_primer_parrafo_y_recorta(self):
        self.assertEqual(descripcion_breve(None), SIN_DOCUMENTACION)
        self.assertEqual(
            descripcion_breve("\n\nPrimer párrafo.\n\nSegundo párrafo."),
            "Primer párrafo.")
        resultado = descripcion_breve("A" * 351)
        self.assertEqual(len(resultado), 350)
        self.assertTrue(resultado.endswith("…"))

    def test_validacion_ids_ignora_espacios_caja_y_duplicados(self):
        validos, invalidos = validar_ids_seleccion(
            " med-003, MED-024, MED-003, no-mostrada ",
            ["MED-003", "MED-024", "MED-025"])
        self.assertEqual(validos, ["MED-003", "MED-024"])
        self.assertEqual(invalidos, ["no-mostrada"])
        self.assertEqual(validar_ids_seleccion("desconocida", ["MED-003"])[0], [])

    def test_filtrado_relaciones_exige_ambos_extremos_y_no_infiere(self):
        tipos = [
            {"tipo": "COMPLEMENTA", "direccion": "Simétrica", "significado": "Ambas"},
            {"tipo": "POTENCIA", "direccion": "A → B", "significado": "A mejora B"},
        ]
        relaciones = [
            {"origen": "MED-A", "tipo": "COMPLEMENTA", "destino": "MED-B"},
            {"origen": "MED-B", "tipo": "POTENCIA", "destino": "MED-C"},
            {"origen": "MED-C", "tipo": "POTENCIA", "destino": "MED-D"},
        ]
        resultado = filtrar_relaciones(relaciones, tipos, ["MED-B", "MED-A", "MED-C"])
        self.assertEqual(
            [(r["origen"], r["tipo"], r["destino"]) for r in resultado],
            [("MED-A", "COMPLEMENTA", "MED-B"),
             ("MED-B", "POTENCIA", "MED-C")])
        self.assertEqual(resultado[0]["direccion"], "Simétrica")
        self.assertEqual(resultado[1]["direccion"], "A → B")


if __name__ == "__main__":
    unittest.main()
