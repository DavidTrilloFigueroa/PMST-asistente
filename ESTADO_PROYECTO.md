# Estado de PMST Asistente

Actualizado el 28 de septiembre de 2026. Este archivo permite retomar el proyecto sin depender del historial de conversación.

## Cómo reanudar el trabajo

Leer, en este orden:

1. `AGENTS.md`: reglas obligatorias, separación de datos y alcance.
2. Este archivo: estado técnico, resultados y trabajo pendiente.
3. `README.md`: instalación, comandos y estructura.
4. `docs/plan_trabajo.md`: etapas y próximos pasos.

Inspeccionar después solo el código afectado. No repetir evaluaciones históricas, regenerar catálogos ni modificar los Excel sin una petición expresa.

## Objetivo y límites

PMST Asistente selecciona y consulta medidas de movilidad sostenible al trabajo a partir de documentación local. La selección inicial utiliza exclusivamente el objetivo interpretado y los pares `id`/`objetivo`. Los nombres, descripciones, KPIs, relaciones, actores, presupuestos y fases se recuperan localmente después de validar las candidatas.

El MVP funciona en local con Ollama en `http://127.0.0.1:11434`, `qwen3.6:latest`, terminal y una interfaz web Streamlit. No usa inferencia externa, cuentas, base de datos, historial persistente, exportación ni seguimiento operativo de la implantación.

## Estado funcional

- Importación, validación, trazabilidad y catálogos JSON de los tres Excel: completados.
- Catálogo actual: 38 medidas; MED-036 se conserva documentalmente y se excluye de la búsqueda. Actualmente se envían 37 objetivos elegibles, sin fijar ese recuento como límite.
- Interpretación y aclaraciones acumuladas: implementadas.
- Comparación v5 exhaustiva: una consulta, temperatura 0, semilla 42, pensamiento desactivado y una decisión por cada objetivo elegible.
- Presentación local: implementada en terminal y Streamlit.
- Tarjetas: altas antes que parciales, descripción documental breve, objetivo y KPIs asociados.
- Selección: uno o varios IDs en terminal y casillas persistentes durante la sesión web.
- Detalle: actores, presupuesto y fases documentales por medida, respetando el orden original.
- Relaciones: solo entre medidas seleccionadas, respetando dirección y simetría documental, sin inversas dirigidas ni transitividad.
- Ausencias: `No consta en la documentación`.
- Interfaz web: conversación con historial de sesión, aclaraciones, tarjetas, selección, detalles, relaciones y reinicio mediante `Nueva consulta`.

## Implementación vigente

- `src/consulta_guiada.py`: núcleo de interpretación v1 y comparación `comparacion_objetivos_v5_exhaustiva`.
- `src/ollama_local.py`: cliente restringido a Ollama local y errores diferenciados.
- `src/consulta_terminal.py`: flujo interactivo completo por terminal.
- `src/presentacion_terminal.py`: lógica local reutilizable de descripción breve, catálogos de presentación, selección y relaciones.
- `src/app_web.py`: frontend local Streamlit; reutiliza el núcleo y la presentación local, conserva el historial durante la sesión y no inicializa Ollama hasta el primer mensaje.
- `src/importar_catalogo.py`: importador y validación documental.
- `src/evaluar_seleccion_v4.py`: nombre histórico del evaluador usado para el flujo vigente.
- `tests/test_consulta_guiada.py` y `tests/test_presentacion_terminal.py`: pruebas sintéticas sin Ollama.

Los módulos de selección y evaluación v2/v3 se conservan como referencia histórica y no forman parte del flujo vigente.

## Reglas de la comparación v5

La comparación recibe el objetivo interpretado y todos los objetivos elegibles de `objetivos_busqueda.json`, exclusivamente como `id` y `objetivo`. Qwen devuelve `estado` y `evaluaciones`, con una entrada por ID enviado y los campos `id`, `decision`, `justificacion` y `condicion_o_limite`.

- `alta`: justificación no vacía y condición `null`.
- `parcial`: justificación y condición o límite no vacíos.
- `descartar`: justificación y condición `null`.
- `resultados`: al menos una alta o parcial.
- `sin_coincidencias`: todas las evaluaciones son descartes.

El programa rechaza omitidos, duplicados, IDs desconocidos, MED-036, truncamientos y estados o campos incoherentes. No reintenta la comparación ni convierte errores en `sin_coincidencias`. Las candidatas se ordenan por ID dentro de altas y parciales; después se recupera la documentación local.

## Evaluación semántica real v5

La primera evaluación real exhaustiva se ejecutó el 23 de septiembre de 2026 en una única pasada A–E, sin reintentos ni cambios posteriores del prompt. El primer intento con Ollama apagado se conserva como antecedente. La ejecución válida se guardó sin sobrescribirlo en:

- `data/procesados/evaluacion_seleccion_v5_real_01.json`.
- `docs/informe_evaluacion_v5_real_01.md`.
- `docs/anexo_evaluacion_v5_real_01.md`.

Resultado técnico:

- A–D cubrieron exactamente los 37 IDs elegibles y excluyeron MED-036.
- Todas las comparaciones fueron técnicamente válidas, terminaron normalmente y usaron una sola consulta.
- D produjo `sin_coincidencias` con 37 descartes.
- E pidió una aclaración concreta y no comparó antes de recibirla.
- C pidió aclaración, integró la respuesta exacta y comparó después.

Resultado semántico:

- Mejoró la cobertura: A, B y C recuperaron las medidas directas esperadas MED-003, MED-004, MED-015, MED-023, MED-025, MED-026 y MED-030 como altas; MED-005 no se omitió y MED-024 apareció como parcial.
- MED-028 se descartó correctamente.
- Persistió una sobreselección importante. Qwen convirtió mecanismos plausibles en efectos documentados y clasificó como altas o parciales varias medidas cuyo objetivo no declara reducir específicamente el coche individual.
- Entre los errores confirmados figuran altas indebidas de MED-001, MED-013, MED-020, MED-021, MED-022, MED-031 y, en algunos casos, MED-040; también parciales no respaldadas o insuficientemente limitadas de teletrabajo y movilidad compartida.
- A produjo 20 candidatas; B y C, 29 cada una. La revisión exhaustiva hizo visible el criterio y redujo omisiones, pero no resolvió la precisión.

Conclusión: v5 es técnicamente trazable y útil para revisión, pero todavía no es un selector semántico fiable con revisión humana ligera. La barrera concreta es la inferencia de efectos no declarados a partir del mecanismo de una medida.

## Verificación disponible

- La última suite completa documentada contiene 59 pruebas superadas el 22 de septiembre de 2026, sin inferencia real.
- El 23 de septiembre se ejecutaron 4 pruebas afectadas por la presentación local: descripción breve, validación de selección, filtrado de relaciones y compatibilidad con el flujo guiado. Las cuatro pasaron.
- Streamlit 1.64.0 se instaló en `.venv` y se añadió a `requirements.txt`.
- `src/app_web.py` importó correctamente y Streamlit arrancó en modo headless en `http://localhost:8501`, sin consultar Qwen. Tras los últimos ajustes visuales y de historial, la importación volvió a completarse correctamente.
- No se ha vuelto a ejecutar la suite completa después de añadir la presentación y la interfaz web.

## Siguiente paso recomendado

1. Probar manualmente el flujo web completo con Ollama local: consulta directa, aclaración, historial visible, tarjetas, selección múltiple, detalles, relaciones y `Nueva consulta`.
2. No repetir la batería A–E ni ajustar el prompt para perseguir sus resultados.
3. Después de validar la interfaz, diseñar y evaluar con casos nuevos una intervención mínima sobre la frontera entre efecto documentado y efecto inferido, especialmente para `alta` y para las condiciones de `parcial`.
4. Mantener fuera de alcance el seguimiento operativo, la publicación en internet y la persistencia de usuarios o conversaciones.

## Comandos habituales

Terminal:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal
```

Web local:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/app_web.py
```

Abrir `http://localhost:8501`. Ollama y `qwen3.6:latest` deben estar disponibles cuando se envíe el primer mensaje.

No se ha realizado ningún commit durante esta actualización.
