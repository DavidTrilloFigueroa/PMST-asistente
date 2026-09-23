"""Frontend web local de PMST Asistente mediante Streamlit."""

from pathlib import Path

import streamlit as st

from src.consulta_guiada import ConsultaGuiadaLocal
from src.ollama_local import ErrorLocal
from src.presentacion_terminal import (
    SIN_DOCUMENTACION,
    SIN_RELACIONES,
    cargar_datos_presentacion,
    construir_tarjetas,
    filtrar_relaciones,
    formatear_relacion,
)


RAIZ = Path(__file__).resolve().parents[1]

CLAVES_CONSULTA = (
    "mensajes",
    "peticion_original",
    "aclaraciones",
    "pregunta_actual",
    "esperando_aclaracion",
    "consulta_completada",
    "tarjetas",
    "seleccionadas",
    "mostrar_detalle",
)


def aplicar_estilos():
    st.markdown(
        """
        <style>
        :root {
            --pmst-navy: #102A43;
            --pmst-bg: #F6F8FB;
            --pmst-card: #FFFFFF;
            --pmst-border: #E5EAF0;
            --pmst-cyan: #14A6C8;
            --pmst-orange: #E98A2E;
        }
        .stApp { background: var(--pmst-bg); color: var(--pmst-navy); }
        header[data-testid="stHeader"] {
            background: var(--pmst-navy);
            color: #FFFFFF;
        }
        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] [data-testid="stToolbar"],
        header[data-testid="stHeader"] [data-testid="stToolbarActions"] {
            color: #FFFFFF;
        }
        header[data-testid="stHeader"] svg {
            fill: currentColor;
            color: #FFFFFF;
        }
        [data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 2px solid #B8C7D9;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 { color: var(--pmst-navy); }
        [data-testid="stChatMessage"] {
            background: #FFFFFF;
            border: 1px solid var(--pmst-border);
            border-radius: 14px;
            margin-bottom: .75rem;
            padding: .25rem .75rem;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: rgba(20, 166, 200, .09);
            border-color: rgba(20, 166, 200, .38);
            border-right: 4px solid var(--pmst-cyan);
            margin-left: 2.5rem;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background: #FFFFFF;
            border-left: 4px solid var(--pmst-navy);
            margin-right: 2.5rem;
        }
        [data-testid="stChatMessage"] p { color: var(--pmst-navy); }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--pmst-card);
            border-color: var(--pmst-border);
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(16, 42, 67, .04);
        }
        .pmst-alta, .pmst-parcial {
            display: inline-block;
            border-radius: 999px;
            font-size: .82rem;
            font-weight: 700;
            padding: .25rem .7rem;
            margin: .15rem 0 .8rem;
        }
        .pmst-alta { background: rgba(20, 166, 200, .13); color: #087D98; }
        .pmst-parcial { background: rgba(233, 138, 46, .14); color: #A95A0B; }
        .pmst-resumen {
            background: #FFFFFF;
            border: 1px solid var(--pmst-border);
            border-left: 5px solid var(--pmst-cyan);
            border-radius: 10px;
            color: var(--pmst-navy);
            font-weight: 700;
            padding: .85rem 1rem;
            margin: 1rem 0;
        }
        h1, h2, h3 { color: var(--pmst-navy); }
        .stButton > button[kind="primary"] {
            background: var(--pmst-cyan);
            border-color: var(--pmst-cyan);
        }
        .pmst-local { color: #6B7C8F; font-size: .85rem; margin-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inicializar_estado():
    valores = {
        "mensajes": [],
        "peticion_original": None,
        "aclaraciones": [],
        "pregunta_actual": None,
        "esperando_aclaracion": False,
        "consulta_completada": False,
        "tarjetas": [],
        "seleccionadas": [],
        "mostrar_detalle": False,
    }
    for clave, valor in valores.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor
    # Migra sesiones abiertas con la forma anterior y conserva una sola lista canónica.
    st.session_state.mensajes = [
        {
            "role": mensaje.get("role", mensaje.get("rol")),
            "content": mensaje.get("content", mensaje.get("contenido")),
        }
        for mensaje in st.session_state.mensajes
        if mensaje.get("role", mensaje.get("rol")) in {"user", "assistant"}
        and isinstance(mensaje.get("content", mensaje.get("contenido")), str)
    ]


def nueva_consulta():
    for clave in CLAVES_CONSULTA:
        st.session_state.pop(clave, None)
    for clave in list(st.session_state):
        if clave.startswith("seleccionar_"):
            del st.session_state[clave]
    inicializar_estado()


@st.cache_resource
def datos_presentacion():
    return cargar_datos_presentacion(RAIZ)


def obtener_nucleo():
    """Inicializa Ollama solo al recibir el primer mensaje del usuario."""
    if "nucleo_consulta" not in st.session_state:
        nucleo = ConsultaGuiadaLocal(RAIZ)
        nucleo.inicializar()
        st.session_state.nucleo_consulta = nucleo
    return st.session_state.nucleo_consulta


def agregar_mensaje(role, content):
    st.session_state.mensajes.append({"role": role, "content": content})


def procesar_mensaje(texto):
    if st.session_state.peticion_original is None:
        st.session_state.peticion_original = texto
    elif st.session_state.esperando_aclaracion:
        st.session_state.aclaraciones.append({
            "pregunta": st.session_state.pregunta_actual,
            "respuesta": texto,
        })

    nucleo = obtener_nucleo()
    interpretacion = nucleo.interpretar(
        st.session_state.peticion_original,
        st.session_state.aclaraciones,
    )["respuesta"]
    objetivo = interpretacion["objetivo_interpretado"]

    if interpretacion["estado"] == "necesita_aclaracion":
        pregunta = interpretacion["pregunta_aclaracion"]
        st.session_state.pregunta_actual = pregunta
        st.session_state.esperando_aclaracion = True
        agregar_mensaje("assistant", pregunta)
        return

    st.session_state.esperando_aclaracion = False
    st.session_state.pregunta_actual = None
    resultado = nucleo.comparar(objetivo)
    st.session_state.consulta_completada = True

    if resultado["estado"] == "sin_coincidencias":
        agregar_mensaje(
            "assistant",
            f"He interpretado tu objetivo como: **{objetivo}**\n\n"
            "No se encontraron objetivos documentados que respondan a la necesidad.",
        )
        return

    st.session_state.tarjetas = construir_tarjetas(
        resultado["candidatas"], datos_presentacion())
    agregar_mensaje(
        "assistant",
        f"He interpretado tu objetivo como: **{objetivo}**\n\n"
        "Estas son las medidas candidatas documentadas. Puedes seleccionar una o varias.",
    )


def mostrar_conversacion():
    if not st.session_state.mensajes:
        st.info(
            "Describe una necesidad de movilidad de tu empresa. "
            "El asistente podrá pedirte una aclaración antes de buscar medidas."
        )
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])


def mostrar_kpis(kpis):
    st.markdown("**KPIs asociados**")
    if not kpis:
        st.write(SIN_DOCUMENTACION)
        return
    for kpi in kpis:
        st.markdown(f"- **{kpi['id']}** — {kpi['nombre']}")


def mostrar_tarjeta(tarjeta):
    identificador = tarjeta["id"]
    with st.container(border=True):
        st.subheader(f"{tarjeta['nombre']} · {identificador}")
        clase = "pmst-alta" if tarjeta["coincidencia"] == "alta" else "pmst-parcial"
        etiqueta = "Coincidencia alta" if tarjeta["coincidencia"] == "alta" else "Coincidencia parcial"
        st.markdown(f'<span class="{clase}">{etiqueta}</span>', unsafe_allow_html=True)
        st.markdown("**Descripción breve**")
        st.write(tarjeta["descripcion_breve"])
        st.markdown("**Objetivo documentado**")
        st.write(tarjeta["objetivo_documentado"])
        mostrar_kpis(tarjeta["kpis"])
        if tarjeta["coincidencia"] == "parcial":
            st.markdown("**Justificación**")
            st.write(tarjeta["justificacion"])
            st.markdown("**Condición o límite**")
            st.write(tarjeta["condicion_o_limite"])
        st.checkbox("Seleccionar esta medida", key=f"seleccionar_{identificador}")


def mostrar_candidatas():
    tarjetas = st.session_state.tarjetas
    if not tarjetas:
        return
    altas = [tarjeta for tarjeta in tarjetas if tarjeta["coincidencia"] == "alta"]
    parciales = [tarjeta for tarjeta in tarjetas if tarjeta["coincidencia"] == "parcial"]

    if altas:
        st.header("Coincidencias altas")
        for tarjeta in altas:
            mostrar_tarjeta(tarjeta)
    if parciales:
        st.header("Coincidencias parciales")
        for tarjeta in parciales:
            mostrar_tarjeta(tarjeta)

    seleccionadas = [
        tarjeta["id"] for tarjeta in tarjetas
        if st.session_state.get(f"seleccionar_{tarjeta['id']}", False)
    ]
    st.session_state.seleccionadas = seleccionadas
    if not seleccionadas:
        st.session_state.mostrar_detalle = False

    cantidad = len(seleccionadas)
    st.markdown(
        f'<div class="pmst-resumen">{cantidad} medidas seleccionadas</div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "Ver detalle y relaciones",
        type="primary",
        disabled=not seleccionadas,
        use_container_width=True,
    ):
        st.session_state.mostrar_detalle = True


def valor_documental(valor):
    return valor if isinstance(valor, str) and valor.strip() else SIN_DOCUMENTACION


def mostrar_detalles_y_relaciones():
    if not st.session_state.mostrar_detalle or not st.session_state.seleccionadas:
        return
    datos = datos_presentacion()
    st.header("Detalle de las medidas seleccionadas")
    for identificador in st.session_state.seleccionadas:
        medida = datos["medidas_por_id"][identificador]
        with st.container(border=True):
            st.subheader(f"{medida.get('nombre') or SIN_DOCUMENTACION} · {identificador}")
            st.markdown("**Actores implicados**")
            st.write(valor_documental(medida.get("actores_implicados")))
            st.markdown("**Presupuesto**")
            st.write(valor_documental(medida.get("presupuesto")))
            st.markdown("**Fases de implementación**")
            st.text(valor_documental(medida.get("fases_implementacion")))

    st.header("Relaciones entre las medidas seleccionadas")
    relaciones = filtrar_relaciones(
        datos["relaciones"],
        datos["tipos_relacion"],
        st.session_state.seleccionadas,
    )
    if not relaciones:
        st.write(SIN_RELACIONES)
        return
    for relacion in relaciones:
        with st.container(border=True):
            st.markdown(f"**{formatear_relacion(relacion)}**")
            st.caption(f"{relacion['significado']} · {relacion['direccion']}")


def main():
    st.set_page_config(
        page_title="PMST Asistente",
        page_icon="🚲",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    aplicar_estilos()
    inicializar_estado()

    with st.sidebar:
        st.title("PMST Asistente")
        st.write("Elección y gestión de medidas de movilidad sostenible al trabajo")
        st.button("Nueva consulta", on_click=nueva_consulta, use_container_width=True)
        st.markdown('<p class="pmst-local">Aplicación local</p>', unsafe_allow_html=True)

    st.title("Consulta de medidas de movilidad")
    bloqueada = st.session_state.consulta_completada
    indicacion = (
        "Inicia una nueva consulta desde la barra lateral"
        if bloqueada else
        "Escribe tu necesidad o responde a la aclaración"
    )
    mensaje = st.chat_input(indicacion, disabled=bloqueada)

    if mensaje:
        # Se registra antes de procesar para que el bocadillo aparezca durante la espera.
        agregar_mensaje("user", mensaje)

    mostrar_conversacion()
    mostrar_candidatas()
    mostrar_detalles_y_relaciones()

    if mensaje:
        try:
            with st.chat_message("assistant"):
                with st.spinner("Procesando la consulta localmente…"):
                    procesar_mensaje(mensaje)
        except (ErrorLocal, OSError, ValueError) as exc:
            agregar_mensaje("assistant", f"No se pudo completar la consulta: {exc}")
        st.rerun()


if __name__ == "__main__":
    main()
