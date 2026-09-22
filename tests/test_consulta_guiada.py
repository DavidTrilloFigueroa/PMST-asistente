"""Pruebas sintéticas del flujo guiado, sin Ollama ni datos privados."""

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from src.consulta_guiada import (
    COMPARACION_VERSION, ESQUEMA_COMPARACION, INSTRUCCIONES_COMPARACION,
    INSTRUCCIONES_INTERPRETACION, INTERPRETACION_VERSION,
    ConsultaGuiadaLocal, preparar_comparacion, preparar_interpretacion,
    validar_comparacion, validar_interpretacion,
    objetivos_elegibles,
)
from src.consulta_terminal import mostrar_candidatas
from src.evaluar_seleccion_v4 import evaluar_criterios
from src.ollama_local import ErrorLocal


CATALOGO = [
    {"id": "PRUEBA-A", "objetivo": "Reducir viajes individuales al trabajo."},
    {"id": "PRUEBA-B", "objetivo": "Mejorar una parte del desplazamiento bajo ciertas condiciones."},
    {"id": "PRUEBA-C", "objetivo": "Objetivo temático sin efecto documentado."},
]


def candidata(identificador, coincidencia="alta", condicion=None):
    return {
        "id": identificador,
        "coincidencia": coincidencia,
        "justificacion": "Justificación sintética.",
        "condicion_o_limite": condicion,
    }


def respuesta_bruta(contenido):
    return {
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 100,
        "eval_count": 30,
        "message": {"content": json.dumps(contenido)},
    }


def evaluacion(identificador, decision="alta", condicion=None):
    return {"id": identificador, "decision": decision,
            "justificacion": None if decision == "descartar" else "Justificación sintética.",
            "condicion_o_limite": condicion}


def todas_descartadas(catalogo=CATALOGO):
    return {"estado": "sin_coincidencias", "evaluaciones": [
        evaluacion(r["id"], "descartar") for r in catalogo if r["id"] != "MED-036"]}


class FuncionesGuiadasTests(unittest.TestCase):
    def test_instrucciones_generales_sin_ids_de_evaluacion(self):
        self.assertEqual(INTERPRETACION_VERSION, "interpretacion_necesidad_v1")
        self.assertEqual(COMPARACION_VERSION, "comparacion_objetivos_v5_exhaustiva")
        self.assertNotIn("MED-", INSTRUCCIONES_INTERPRETACION + INSTRUCCIONES_COMPARACION)
        self.assertIn("TODOS", INSTRUCCIONES_COMPARACION)
        self.assertIn("parcial", INSTRUCCIONES_COMPARACION)
        propiedades = ESQUEMA_COMPARACION["properties"]["evaluaciones"]["items"]["properties"]
        self.assertNotIn("evidencia_objetivo", propiedades)
        self.assertNotIn("objetivo_documentado", propiedades)

    def test_interpretacion_lista_y_aclaracion_coherentes(self):
        lista = {"estado": "listo_para_buscar", "objetivo_interpretado": "Reducir viajes",
                 "pregunta_aclaracion": None}
        self.assertEqual(validar_interpretacion(lista, []), lista)
        aclarar = {"estado": "necesita_aclaracion", "objetivo_interpretado": "Mejorar movilidad",
                   "pregunta_aclaracion": "¿Qué problema quieres resolver?"}
        self.assertEqual(validar_interpretacion(aclarar, []), aclarar)
        with self.assertRaises(ErrorLocal):
            validar_interpretacion({**lista, "pregunta_aclaracion": "Pregunta"}, [])

    def test_aclaracion_conserva_peticion_y_no_repite_pregunta(self):
        aclaraciones = [{"pregunta": "¿Qué problema quieres resolver?",
                         "respuesta": "Reducir viajes en coche"}]
        cuerpo, _ = preparar_interpretacion(
            "modelo-local", "Mejorar la movilidad", aclaraciones, 8192, 1024)
        datos = json.loads(cuerpo["messages"][1]["content"])
        self.assertEqual(datos["peticion_original"], "Mejorar la movilidad")
        self.assertEqual(datos["aclaraciones_previas"], aclaraciones)
        repetida = {"estado": "necesita_aclaracion", "objetivo_interpretado": "Movilidad",
                    "pregunta_aclaracion": " ¿Qué problema quieres resolver? "}
        with self.assertRaisesRegex(ErrorLocal, "repitió"):
            validar_interpretacion(repetida, aclaraciones)

    def test_peticion_unica_contiene_catalogo_completo_y_solo_campos_permitidos(self):
        cuerpo, _ = preparar_comparacion(
            "modelo-local", "Reducir viajes", CATALOGO, 8192, 1024)
        datos = json.loads(cuerpo["messages"][1]["content"])
        self.assertEqual(set(datos), {"objetivo_interpretado", "catalogo_objetivos"})
        self.assertEqual(datos["catalogo_objetivos"], CATALOGO)
        self.assertTrue(all(set(registro) == {"id", "objetivo"}
                            for registro in datos["catalogo_objetivos"]))
        serializado = json.dumps(cuerpo).casefold()
        for campo_prohibido in ("nombre", "descripcion", "relaciones", "kpis", "presupuesto"):
            self.assertNotIn(f'"{campo_prohibido}"', serializado)

    def test_validacion_acepta_resultados_y_sin_coincidencias(self):
        resultados = {"estado": "resultados", "evaluaciones": [
            evaluacion("PRUEBA-A"),
            evaluacion("PRUEBA-B", "parcial", "Solo si se cumple la condición."),
            evaluacion("PRUEBA-C", "descartar"),
        ]}
        self.assertEqual(validar_comparacion(resultados, CATALOGO), resultados)
        sin_coincidencias = todas_descartadas()
        self.assertEqual(validar_comparacion(sin_coincidencias, CATALOGO), sin_coincidencias)

    def test_validacion_rechaza_ids_inexistentes_o_duplicados(self):
        inexistente = todas_descartadas()
        inexistente["evaluaciones"][0]["id"] = "NO-EXISTE"
        duplicado = todas_descartadas()
        duplicado["evaluaciones"][1]["id"] = "PRUEBA-A"
        for respuesta in (inexistente, duplicado):
            with self.subTest(respuesta=respuesta), self.assertRaises(ErrorLocal):
                validar_comparacion(respuesta, CATALOGO)

    def test_validacion_rechaza_formato_y_condiciones_incoherentes(self):
        invalidas = [
            evaluacion("PRUEBA-A", condicion="No permitida"),
            evaluacion("PRUEBA-A", "parcial"),
            evaluacion("PRUEBA-A", "parcial", "   "),
            evaluacion("PRUEBA-A", "insuficiente"),
            {**evaluacion("PRUEBA-A"), "evidencia_objetivo": "No debe devolverse"},
            {**evaluacion("PRUEBA-A"), "justificacion": None},
            {**evaluacion("PRUEBA-A"), "justificacion": "  "},
            {**evaluacion("PRUEBA-A", "parcial", "Límite"), "justificacion": None},
            {**evaluacion("PRUEBA-A", "descartar"), "justificacion": "No permitida"},
            {**evaluacion("PRUEBA-A", "descartar"), "justificacion": ""},
            evaluacion("PRUEBA-A", "descartar", "No permitida"),
        ]
        for invalida in invalidas:
            respuesta = todas_descartadas()
            respuesta["estado"] = "resultados"
            respuesta["evaluaciones"][0] = invalida
            with self.subTest(invalida=invalida), self.assertRaises(ErrorLocal):
                validar_comparacion(respuesta, CATALOGO)

    def test_estado_coherente_con_todas_las_decisiones(self):
        for respuesta in (
            {**todas_descartadas(), "estado": "resultados"},
            {"estado": "sin_coincidencias", "evaluaciones": []},
            {"estado": "sin_coincidencias", "candidatas": []},
            {"evaluaciones": todas_descartadas()["evaluaciones"]},
        ):
            with self.subTest(respuesta=respuesta), self.assertRaises(ErrorLocal):
                validar_comparacion(respuesta, CATALOGO)
        for decision in ("alta", "parcial"):
            respuesta = todas_descartadas()
            respuesta["evaluaciones"][0] = evaluacion(
                "PRUEBA-A", decision, "Límite" if decision == "parcial" else None)
            with self.subTest(decision=decision), self.assertRaises(ErrorLocal):
                validar_comparacion(respuesta, CATALOGO)

    def test_cobertura_exacta_37_elegibles_y_exclusion_sin_mutar(self):
        catalogo = [{"id": f"SINTETICO-{i:03}", "objetivo": "Objetivo sintético."}
                    for i in range(37)] + [{"id": "MED-036", "objetivo": "Texto excluido sintético."}]
        original = deepcopy(catalogo)
        cuerpo, _ = preparar_comparacion("local", "Necesidad", catalogo, 16384, 3072)
        enviados = json.loads(cuerpo["messages"][1]["content"])["catalogo_objetivos"]
        self.assertEqual(len(enviados), 37)
        self.assertEqual(len({x["id"] for x in enviados}), 37)
        self.assertNotIn("MED-036", json.dumps(cuerpo))
        self.assertTrue(all(set(x) == {"id", "objetivo"} for x in enviados))
        self.assertEqual(catalogo, original)
        esquema = cuerpo["format"]["properties"]["evaluaciones"]
        self.assertEqual(esquema["minItems"], 37)
        self.assertEqual(esquema["maxItems"], 37)
        respuesta = todas_descartadas(catalogo)
        self.assertEqual(validar_comparacion(respuesta, catalogo), respuesta)
        positiva = deepcopy(respuesta)
        positiva["estado"] = "resultados"
        positiva["evaluaciones"][0] = evaluacion(enviados[0]["id"])
        positiva["evaluaciones"][1] = evaluacion(enviados[1]["id"], "parcial", "Límite sintético")
        self.assertEqual(validar_comparacion(positiva, enviados), positiva)
        for cambio in ("omitido", "duplicado", "desconocido", "excluido"):
            invalida = deepcopy(respuesta)
            if cambio == "omitido":
                invalida["evaluaciones"].pop()
            else:
                invalida["evaluaciones"][-1]["id"] = {
                    "duplicado": enviados[0]["id"], "desconocido": "NO-ENVIADO",
                    "excluido": "MED-036"}[cambio]
            with self.subTest(cambio=cambio), self.assertRaises(ErrorLocal):
                validar_comparacion(invalida, catalogo)
        # El tamaño se calcula, no se fija permanentemente en 37.
        ampliado = catalogo + [{"id": "SINTETICO-NUEVO", "objetivo": "Objetivo nuevo."}]
        self.assertEqual(len(objetivos_elegibles(ampliado)), 38)
        self.assertEqual(validar_comparacion(todas_descartadas(ampliado), ampliado),
                         todas_descartadas(ampliado))

    def test_catalogo_sin_elegibles_no_se_envia(self):
        with self.assertRaisesRegex(ErrorLocal, "No hay objetivos elegibles"):
            preparar_comparacion("local", "Necesidad",
                                 [{"id": "MED-036", "objetivo": "Excluida"}], 8192, 1024)

    def test_reproducibilidad_en_ambas_etapas(self):
        cuerpos = [preparar_interpretacion("local", "Necesidad", [], 8192, 1024)[0],
                   preparar_comparacion("local", "Necesidad", CATALOGO, 8192, 1024)[0]]
        for cuerpo in cuerpos:
            self.assertEqual(cuerpo["options"]["temperature"], 0)
            self.assertEqual(cuerpo["options"]["seed"], 42)
            self.assertIs(cuerpo["think"], False)

    def test_contexto_insuficiente_no_recorta_catalogo(self):
        with self.assertRaisesRegex(ErrorLocal, "No se recortan datos"):
            preparar_comparacion("local", "Necesidad", CATALOGO, 1000, 900)


class ClienteSimulado:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.cuerpos = []

    def inspeccionar(self, modelo, digest=None):
        return {
            "modelo": {"digest": "digest-sintetico"},
            "detalle": {"model_info": {"prueba.context_length": 32768,
                                        "tokenizer.ggml.model": "gpt2"},
                        "capabilities": ["completion"]},
            "cargados": {"models": []},
        }

    def solicitar(self, ruta, cuerpo=None, espera=10):
        self.cuerpos.append(deepcopy(cuerpo))
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


class FlujoConsultaUnicaTests(unittest.TestCase):
    def crear_consulta(self, respuestas, incluir_fichas=True, catalogo=CATALOGO):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        raiz = Path(temporal.name)
        procesados = raiz / "data/procesados"
        procesados.mkdir(parents=True)
        (procesados / "objetivos_busqueda.json").write_text(
            json.dumps(catalogo), encoding="utf-8")
        if incluir_fichas:
            (procesados / "medidas.json").write_text(json.dumps([
                {"id": registro["id"], "nombre": f"Nombre {registro['id']}"}
                for registro in catalogo]), encoding="utf-8")
        cliente = ClienteSimulado(respuestas)
        consulta = ConsultaGuiadaLocal(
            raiz, modelo="modelo-local", contexto=8192, generacion=1024,
            espera=10, cliente=cliente)
        consulta.inicializar()
        return consulta, cliente

    def test_una_sola_llamada_envia_todo_y_recupera_datos_locales(self):
        modelo = {"estado": "resultados", "evaluaciones": [
            evaluacion("PRUEBA-B", "parcial", "Solo en el supuesto indicado."),
            evaluacion("PRUEBA-C", "descartar"),
            evaluacion("PRUEBA-A"),
        ]}
        consulta, cliente = self.crear_consulta([respuesta_bruta(modelo)])
        resultado = consulta.comparar("Reducir viajes")
        self.assertEqual(len(cliente.cuerpos), 1)
        datos = json.loads(cliente.cuerpos[0]["messages"][1]["content"])
        self.assertEqual(datos["catalogo_objetivos"], CATALOGO)
        self.assertEqual(resultado["modo"], "consulta_unica_catalogo_completo")
        self.assertEqual(resultado["consultas_modelo"], 1)
        self.assertTrue(resultado["catalogo"]["completo_enviado"])
        self.assertEqual([c["id"] for c in resultado["candidatas"]],
                         ["PRUEBA-A", "PRUEBA-B"])
        self.assertEqual(resultado["candidatas"][0]["nombre"], "Nombre PRUEBA-A")
        self.assertEqual(resultado["candidatas"][0]["objetivo_documentado"],
                         CATALOGO[0]["objetivo"])
        self.assertNotIn("Nombre PRUEBA-A", json.dumps(cliente.cuerpos))
        self.assertNotIn("objetivo_documentado", json.dumps(resultado["respuesta_modelo"]))
        self.assertEqual([c["id"] for c in resultado["altas"]], ["PRUEBA-A"])
        self.assertEqual([c["id"] for c in resultado["parciales"]], ["PRUEBA-B"])
        self.assertEqual([c["id"] for c in resultado["descartadas"]], ["PRUEBA-C"])
        salida = StringIO()
        with redirect_stdout(salida):
            mostrar_candidatas(resultado)
        self.assertNotIn("PRUEBA-C", salida.getvalue())
        self.assertLess(salida.getvalue().index("PRUEBA-A"), salida.getvalue().index("PRUEBA-B"))

    def test_sin_coincidencias_no_consulta_medidas(self):
        modelo = todas_descartadas()
        consulta, cliente = self.crear_consulta([respuesta_bruta(modelo)], incluir_fichas=False)
        resultado = consulta.comparar("Reducir consumo de agua")
        self.assertEqual(resultado["estado"], "sin_coincidencias")
        self.assertEqual(resultado["candidatas"], [])
        self.assertEqual(len(cliente.cuerpos), 1)

    def test_fallo_no_se_reintenta_ni_presenta_resultados(self):
        consulta, cliente = self.crear_consulta([
            ErrorLocal("tiempo_agotado", "Tiempo agotado"),
            respuesta_bruta(todas_descartadas()),
        ])
        with self.assertRaisesRegex(ErrorLocal, "Tiempo agotado"):
            consulta.comparar("Reducir viajes")
        self.assertEqual(len(cliente.cuerpos), 1)

    def test_respuesta_invalida_no_lee_fichas_ni_reintenta(self):
        invalida = todas_descartadas()
        invalida["evaluaciones"][0]["id"] = "NO-EXISTE"
        consulta, cliente = self.crear_consulta([respuesta_bruta(invalida)], incluir_fichas=False)
        with self.assertRaises(ErrorLocal):
            consulta.comparar("Reducir viajes")
        self.assertEqual(len(cliente.cuerpos), 1)

    def test_cobertura_incompleta_no_lee_fichas_ni_reintenta(self):
        invalida = todas_descartadas()
        invalida["estado"] = "resultados"
        invalida["evaluaciones"][0] = evaluacion("PRUEBA-A")
        invalida["evaluaciones"].pop()
        consulta, cliente = self.crear_consulta([respuesta_bruta(invalida)], incluir_fichas=False)
        with self.assertRaisesRegex(ErrorLocal, "Faltan evaluaciones"):
            consulta.comparar("Reducir viajes")
        self.assertEqual(len(cliente.cuerpos), 1)

    def test_excluida_permanece_documental_pero_no_se_envia(self):
        catalogo = CATALOGO + [{"id": "MED-036", "objetivo": "Excluida sintética"}]
        consulta, cliente = self.crear_consulta([respuesta_bruta(todas_descartadas())], catalogo=catalogo)
        resultado = consulta.comparar("Necesidad")
        self.assertEqual(consulta.catalogo, catalogo)
        self.assertEqual(resultado["catalogo"]["registros_enviados"], 3)
        self.assertEqual(resultado["catalogo"]["ids_excluidos"], ["MED-036"])
        self.assertNotIn("MED-036", json.dumps(cliente.cuerpos))

    def test_orden_por_id_dentro_de_cada_grupo(self):
        catalogo = [{"id": i, "objetivo": "Objetivo sintético."} for i in ("Z", "Y", "B", "A")]
        modelo = {"estado": "resultados", "evaluaciones": [
            evaluacion("Z", "parcial", "Límite"), evaluacion("Y"),
            evaluacion("B"), evaluacion("A", "parcial", "Límite")]}
        consulta, _ = self.crear_consulta([respuesta_bruta(modelo)], catalogo=catalogo)
        self.assertEqual([c["id"] for c in consulta.comparar("Necesidad")["candidatas"]],
                         ["B", "Y", "A", "Z"])


class EvaluacionV4Tests(unittest.TestCase):
    def test_vacios_no_acreditan_seleccion_semantica_en_abc(self):
        comparacion = {
            "estado": "resultados",
            "modo": "consulta_unica_catalogo_completo",
            "consultas_modelo": 1,
            "catalogo": {"completo_enviado": True, "registros_enviados": 38,
                         "campos_enviados": ["id", "objetivo"]},
            "candidatas": [],
        }
        casos = {
            "A": {"comparacion": deepcopy(comparacion)},
            "B": {"comparacion": deepcopy(comparacion)},
            "C": {"interpretaciones": [{"respuesta": {"estado": "necesita_aclaracion"}},
                                          {"respuesta": {"estado": "listo_para_buscar"}}]},
            "D": {"comparacion": {**deepcopy(comparacion), "estado": "sin_coincidencias"}},
            "E": {"interpretaciones": [{"respuesta": {"estado": "necesita_aclaracion"}}]},
        }
        evaluacion = evaluar_criterios(casos)
        for clave in ("A", "B"):
            self.assertFalse(evaluacion[clave]["cumple_minimo_altas"])
            self.assertFalse(evaluacion[clave]["candidatas_no_vacias"])
        self.assertFalse(evaluacion["C"]["candidatas_tras_aclaracion"])

        # Una muestra de alta basta; no se exige una lista cerrada de medidas.
        for clave in ("A", "B", "C"):
            casos[clave]["comparacion"] = {
                **deepcopy(comparacion),
                "candidatas": [candidata("MED-003")] + [
                    candidata(i, "parcial", "Condición sintética pendiente de revisión.")
                    for i in ("MED-005", "MED-024", "MED-030")],
            }
        positiva = evaluar_criterios(casos)
        self.assertTrue(positiva["resumen"]["minimos_automaticos_cumplidos"])
        for clave in ("A", "B"):
            self.assertEqual(positiva[clave]["posibles_parciales_omitidas_revision_humana"], [])
            casos[clave]["comparacion"]["candidatas"].extend([
                candidata("MED-018"), candidata("MED-019")])
        negativa = evaluar_criterios(casos)
        for clave in ("A", "B"):
            self.assertFalse(negativa[clave]["med_018_no_es_candidata"])
            self.assertFalse(negativa[clave]["med_019_no_es_candidata"])
        self.assertFalse(negativa["resumen"]["minimos_automaticos_cumplidos"])
        self.assertTrue(evaluacion["D"]["sin_coincidencias_con_catalogo_completo"])
        self.assertTrue(evaluacion["E"]["pidio_aclaracion"])
        self.assertFalse(evaluacion["resumen"]["minimos_automaticos_cumplidos"])
        self.assertEqual(evaluacion["resumen"]["comprobaciones_superadas"], 2)
        # También rechaza el vacío técnicamente válido en los tres casos positivos.
        for clave in ("A", "B", "C"):
            casos[clave]["comparacion"] = {**deepcopy(comparacion), "estado": "sin_coincidencias"}
        evaluacion = evaluar_criterios(casos)
        self.assertFalse(evaluacion["A"]["cumple_minimo_altas"])
        self.assertFalse(evaluacion["B"]["cumple_minimo_altas"])
        self.assertFalse(evaluacion["C"]["candidatas_tras_aclaracion"])


if __name__ == "__main__":
    unittest.main()
