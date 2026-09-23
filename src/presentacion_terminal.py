"""Presentación y selección local de medidas para la entrada por terminal."""

import json
import re


SIN_DOCUMENTACION = "No consta en la documentación"
SIN_RELACIONES = "No constan relaciones documentadas entre las medidas seleccionadas."

RESPUESTAS_SALIDA = {"salir", "cancelar", "fin", "q", "quit", "exit"}
RESPUESTAS_AFIRMATIVAS = {"s", "si", "sí"}

VERBOS_RELACION = {
    "COMPLEMENTA": "complementa",
    "POTENCIA": "potencia",
    "PRERREQUISITO_DE": "es prerrequisito de",
    "ALTERNATIVA_A": "es alternativa a",
    "SOLAPA_CON": "se solapa con",
    "PUEDE_ENTRAR_EN_CONFLICTO_CON": "puede entrar en conflicto con",
    "ES_COMPONENTE_DE": "es componente de",
}


def descripcion_breve(descripcion, limite=350):
    """Devuelve el primer párrafo no vacío sin superar el límite indicado."""
    if not isinstance(descripcion, str) or not descripcion.strip():
        return SIN_DOCUMENTACION
    parrafos = re.split(r"(?:\r?\n)\s*(?:\r?\n)+", descripcion)
    primero = next((" ".join(p.split()) for p in parrafos if p.strip()), "")
    if not primero:
        return SIN_DOCUMENTACION
    if len(primero) <= limite:
        return primero
    return primero[:limite - 1].rstrip() + "…"


def validar_ids_seleccion(texto, ids_candidatos):
    """Separa IDs válidos e inválidos, ignorando espacios, caja y duplicados."""
    permitidos = {identificador.casefold(): identificador for identificador in ids_candidatos}
    validos = []
    invalidos = []
    vistos_validos = set()
    vistos_invalidos = set()
    for fragmento in texto.split(","):
        recibido = fragmento.strip()
        if not recibido:
            continue
        canonico = permitidos.get(recibido.casefold())
        if canonico is None:
            if recibido.casefold() not in vistos_invalidos:
                invalidos.append(recibido)
                vistos_invalidos.add(recibido.casefold())
        elif canonico not in vistos_validos:
            validos.append(canonico)
            vistos_validos.add(canonico)
    return validos, invalidos


def filtrar_relaciones(relaciones, tipos_relacion, ids_seleccionados):
    """Conserva solo relaciones documentadas cuyos dos extremos están seleccionados."""
    seleccionados = set(ids_seleccionados)
    tipos = {registro["tipo"]: registro for registro in tipos_relacion}
    resultado = []
    for relacion in relaciones:
        if relacion["origen"] not in seleccionados or relacion["destino"] not in seleccionados:
            continue
        tipo = tipos.get(relacion["tipo"])
        if tipo is None:
            raise ValueError(f"Tipo de relación desconocido: {relacion['tipo']}")
        resultado.append({**relacion,
                          "direccion": tipo["direccion"],
                          "significado": tipo["significado"]})
    return resultado


def _leer_lista(ruta):
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError(f"El archivo {ruta.name} no contiene una lista.")
    return datos


def _indexar(registros, campo, nombre):
    indice = {}
    for registro in registros:
        clave = registro.get(campo)
        if not isinstance(clave, str) or not clave or clave in indice:
            raise ValueError(f"{nombre} contiene identificadores vacíos o duplicados.")
        indice[clave] = registro
    return indice


def cargar_datos_presentacion(raiz):
    """Carga exclusivamente los catálogos locales usados en la presentación."""
    base = raiz / "data/procesados"
    medidas = _leer_lista(base / "medidas.json")
    kpis = _leer_lista(base / "kpis.json")
    asociaciones = _leer_lista(base / "asociaciones_medida_kpi.json")
    relaciones = _leer_lista(base / "relaciones_medidas.json")
    tipos = _leer_lista(base / "tipos_relacion.json")
    return {
        "medidas": medidas,
        "medidas_por_id": _indexar(medidas, "id", "medidas.json"),
        "kpis": kpis,
        "kpis_por_id": _indexar(kpis, "id", "kpis.json"),
        "asociaciones": asociaciones,
        "relaciones": relaciones,
        "tipos_relacion": tipos,
    }


def construir_tarjetas(candidatas, datos):
    """Completa candidatas ya validadas con textos y KPIs exclusivamente locales."""
    tarjetas = []
    for candidata in candidatas:
        identificador = candidata["id"]
        medida = datos["medidas_por_id"].get(identificador)
        if medida is None:
            raise ValueError(f"Falta {identificador} en medidas.json.")
        kpis = []
        vistos = set()
        for asociacion in datos["asociaciones"]:
            if asociacion.get("medida") != identificador:
                continue
            kpi_id = asociacion.get("kpi")
            if kpi_id in vistos:
                continue
            kpi = datos["kpis_por_id"].get(kpi_id)
            if kpi is None:
                raise ValueError(f"Falta {kpi_id} en kpis.json.")
            kpis.append({"id": kpi_id, "nombre": kpi.get("nombre") or SIN_DOCUMENTACION})
            vistos.add(kpi_id)
        tarjetas.append({
            **candidata,
            "nombre": medida.get("nombre") or SIN_DOCUMENTACION,
            "descripcion_breve": descripcion_breve(medida.get("descripcion")),
            "objetivo_documentado": medida.get("objetivo") or SIN_DOCUMENTACION,
            "kpis": kpis,
        })
    return tarjetas


def mostrar_tarjetas(tarjetas):
    print("\nMedidas candidatas:")
    for tarjeta in tarjetas:
        print("\n" + "=" * 78)
        print(f"{tarjeta['id']} — {tarjeta['nombre']}")
        etiqueta = "Coincidencia alta" if tarjeta["coincidencia"] == "alta" else "Coincidencia parcial"
        print(etiqueta)
        print(f"\nDescripción breve: {tarjeta['descripcion_breve']}")
        print(f"Objetivo documentado: {tarjeta['objetivo_documentado']}")
        print("KPIs asociados:")
        if tarjeta["kpis"]:
            for kpi in tarjeta["kpis"]:
                print(f"  - {kpi['id']} — {kpi['nombre']}")
        else:
            print(f"  {SIN_DOCUMENTACION}")
        if tarjeta["coincidencia"] == "parcial":
            print(f"Justificación: {tarjeta['justificacion']}")
            print(f"Condición o límite: {tarjeta['condicion_o_limite']}")
    print("\n" + "=" * 78)


def _es_salida(texto):
    return texto.strip().casefold() in RESPUESTAS_SALIDA


def pedir_seleccion(ids_candidatos, entrada=input):
    """Solicita una selección válida; None significa terminar sin seleccionar."""
    while True:
        texto = entrada(
            "\nEscribe uno o varios IDs separados por comas "
            "(o 'salir' para terminar):\n> ").strip()
        if _es_salida(texto):
            return None
        if not texto:
            confirmar = entrada(
                "No has seleccionado medidas. ¿Deseas terminar la consulta sin seleccionar? [s/N]: "
            ).strip()
            if confirmar.casefold() in RESPUESTAS_AFIRMATIVAS or _es_salida(confirmar):
                return None
            continue
        validos, invalidos = validar_ids_seleccion(texto, ids_candidatos)
        if invalidos:
            print("IDs no válidos para esta consulta: " + ", ".join(invalidos))
        if validos:
            return validos
        print("No queda ninguna medida válida. Introduce al menos un ID mostrado.")


def _valor_documental(valor):
    return valor if isinstance(valor, str) and valor.strip() else SIN_DOCUMENTACION


def mostrar_detalles(ids_seleccionados, datos):
    print("\nDetalle de las medidas seleccionadas:")
    for identificador in ids_seleccionados:
        medida = datos["medidas_por_id"][identificador]
        print("\n" + "-" * 78)
        print(f"{identificador} — {medida.get('nombre') or SIN_DOCUMENTACION}")
        print(f"\nActores implicados:\n{_valor_documental(medida.get('actores_implicados'))}")
        print(f"\nPresupuesto:\n{_valor_documental(medida.get('presupuesto'))}")
        print(f"\nFases de implementación:\n{_valor_documental(medida.get('fases_implementacion'))}")
    print("\n" + "-" * 78)


def formatear_relacion(relacion):
    verbo = VERBOS_RELACION.get(
        relacion["tipo"], relacion["tipo"].casefold().replace("_", " "))
    return f"{relacion['origen']} {verbo} {relacion['destino']}"


def mostrar_relaciones(relaciones):
    print("\nRelaciones documentadas entre las medidas seleccionadas:")
    if not relaciones:
        print(SIN_RELACIONES)
        return
    for relacion in relaciones:
        print(f"- {formatear_relacion(relacion)}")
