# Plan de trabajo

Estado actualizado el 28 de septiembre de 2026: importador, catálogos, comparación v5, presentación en terminal y primera interfaz web local completados. La evaluación real v5 confirmó la mecánica exhaustiva y reveló sobreselección semántica. El próximo paso inmediato es validar manualmente el flujo web completo; después se abordará la precisión con casos nuevos.

## Flujo funcional vigente

1. El usuario plantea una necesidad en terminal o Streamlit.
2. Qwen reformula el objetivo y pide una aclaración cuando existe una ambigüedad relevante.
3. Una única consulta compara el objetivo interpretado con todos los objetivos elegibles, usando exclusivamente `id` y `objetivo`.
4. El programa valida la cobertura completa y recupera localmente la documentación de las candidatas.
5. Se muestran primero coincidencias altas y después parciales, con descripción breve, objetivo y KPIs.
6. El usuario selecciona una o varias medidas.
7. Se muestran actores, presupuesto y fases de cada medida por separado.
8. Se muestran exclusivamente las relaciones documentadas entre las medidas seleccionadas, respetando dirección y simetría.

La información ausente se muestra como «No consta en la documentación». No se deducen relaciones inversas dirigidas, transitivas ni nuevas candidatas por relación.

## 1. Preparación

Completada. Entorno `.venv` con Python 3.13, openpyxl y Streamlit 1.64.0. Dependencias fijadas en `requirements.txt`. El proyecto permanece completamente local.

## 2. Revisión documental

Completada para los tres Excel actuales. Se preservan identificadores, textos, orden de fases, procedencia y huellas SHA-256. No se realiza conciliación automática de IDs.

## 3. Catálogo estructurado

Completada. `src/importar_catalogo.py` genera y valida medidas, objetivos de búsqueda, relaciones, tipos de relación, KPIs, asociaciones e informe. `objetivos_busqueda.json` contiene exclusivamente `id` y `objetivo`.

## 4. Selección por objetivos

Implementada mediante interpretación v1 y comparación v5 exhaustiva en `src/consulta_guiada.py`:

- Una consulta con todos los objetivos elegibles; actualmente 37 de 38.
- MED-036 filtrada en memoria sin eliminarla del catálogo documental.
- Temperatura 0, semilla 42 y pensamiento desactivado.
- Decisiones `alta`, `parcial` o `descartar` para cada ID.
- Rechazo de cobertura incompleta, duplicados, IDs desconocidos o excluidos, truncamientos y formatos incoherentes.
- Sin lotes ni reintentos automáticos.
- Recuperación de datos documentales solo después de validar la respuesta.

La evaluación real A–E se ejecutó el 23 de septiembre de 2026 y se conserva en `evaluacion_seleccion_v5_real_01.json`, con informe y anexo en `docs/`. Técnicamente cubrió los 37 IDs y excluyó MED-036. Semánticamente recuperó las medidas directas esperadas, pero generó demasiadas candidatas al inferir reducciones del coche desde mecanismos como modos alternativos, teletrabajo o movilidad compartida.

No repetir la batería A–E ni ajustar el prompt para mejorar artificialmente ese resultado. La siguiente intervención semántica deberá evaluarse con casos nuevos y centrarse en la diferencia entre efecto expresamente documentado y efecto inferido.

## 5. Presentación local

Completada en `src/presentacion_terminal.py` y reutilizada por terminal y web:

- Descripción breve desde el primer párrafo documental, limitada a 350 caracteres.
- Objetivo documental y KPIs procedentes de catálogos locales.
- Justificación y condición visibles para coincidencias parciales.
- Actores, presupuesto y fases por medida seleccionada.
- Relaciones filtradas a los dos extremos seleccionados, con dirección documental.

## 6. Terminal

Completada en `src/consulta_terminal.py`. Admite petición interactiva o `--peticion`, aclaraciones, tarjetas, selección múltiple por IDs, salida limpia, detalles y relaciones. Cuatro pruebas locales afectadas pasaron sin Ollama.

## 7. Interfaz web

Primera versión completada en `src/app_web.py` con Streamlit:

- Barra lateral, `Nueva consulta` y estado local de sesión.
- Conversación con mensajes diferenciados e historial visible durante la sesión.
- Caja de chat inferior e indicador de procesamiento.
- Tarjetas separadas para altas y parciales.
- Selección mediante casillas y resumen de cantidad.
- Detalles y relaciones de las medidas seleccionadas.
- Estética institucional en azul marino, cian, naranja, blanco y gris claro.

La aplicación importa y arranca técnicamente en modo headless sin consultar Qwen. Falta una validación manual completa en navegador con Ollama local. No existe persistencia entre reinicios, autenticación, base de datos, exportación ni acceso público.

## 8. Validación

- Última suite completa documentada: 59 pruebas superadas el 22 de septiembre de 2026, sin inferencia real.
- Presentación local: 4 pruebas afectadas superadas el 23 de septiembre de 2026.
- Evaluación v5 real: técnicamente válida; calidad semántica insuficiente por sobreselección.
- Streamlit: importación y arranque headless correctos; importación repetida correctamente después de los ajustes visuales y de historial.
- La suite completa no se ha repetido después de incorporar presentación y web.

## Próximos pasos

1. Ejecutar una prueba manual de Streamlit con consulta directa y otra que requiera aclaración.
2. Verificar historial, tarjetas, selección múltiple, persistencia durante reruns, detalles, relaciones y reinicio.
3. Registrar cualquier fallo funcional de interfaz sin modificar la selección semántica durante esa prueba.
4. Diseñar después el cambio semántico mínimo para impedir altas basadas solo en mecanismos y parciales sin condición documental suficiente.
5. Evaluar ese cambio con casos nuevos, manteniendo A–E como referencia histórica cerrada.

El seguimiento operativo de la implantación, la publicación en internet, las cuentas y la persistencia continúan fuera del alcance.
