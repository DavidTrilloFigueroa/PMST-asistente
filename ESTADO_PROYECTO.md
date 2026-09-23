# Estado de PMST Asistente

Actualizado el 22 de septiembre de 2026. Este archivo permite retomar el proyecto en otro chat sin depender del historial de conversación.

## Cómo reanudar el trabajo

Leer, en este orden:

1. `AGENTS.md`: reglas obligatorias, separación de datos y alcance.
2. Este archivo: estado técnico, resultados y trabajo pendiente.
3. `README.md`: comandos y estructura del proyecto.
4. `docs/plan_trabajo.md`: etapas y flujo funcional acordado.

Después, inspeccionar el código afectado antes de editar. No volver a ejecutar evaluaciones históricas ni modificar los Excel o `objetivos_busqueda.json` sin una petición expresa.

## Objetivo y límites

PMST Asistente ayuda a elegir medidas de planes de movilidad sostenible al trabajo a partir de documentación local. La selección inicial solo puede usar el objetivo interpretado del usuario y los campos `id` y `objetivo` del catálogo. Los nombres y otros datos se consultan después de validar las candidatas.

El MVP usa exclusivamente Ollama en `http://127.0.0.1:11434` con `qwen3.6:latest`. No usa servicios externos, no descarga modelos y no tiene todavía interfaz gráfica. Tampoco incluye seguimiento operativo de la implementación.

## Estado funcional

- Importación de los tres Excel, validación documental, trazabilidad y catálogos JSON: completadas.
- Catálogo actual: 38 medidas. El programa no impone ese número como límite permanente.
- Interpretación de la necesidad y aclaraciones acumuladas: implementadas en terminal.
- Selección v5 exhaustiva: una única consulta con todos los objetivos elegibles. MED-036 permanece en el catálogo documental y se excluye del envío; actualmente 37 elegibles de 38 registros, sin límite permanente.
- Presentación actual: nombre, ID, coincidencia, justificación, condición y objetivo documental.
- Fichas completas con descripción, relaciones y KPIs: pendientes.
- Selección visual y desplegables de actores, presupuesto y fases: pendientes.

El flujo aprobado completo permanece en `AGENTS.md` y `docs/plan_trabajo.md`.

## Implementación vigente

- `src/consulta_guiada.py`: interpretación v1 y comparación `comparacion_objetivos_v5_exhaustiva`; cobertura exacta, validación y recuperación local posterior.
- `src/consulta_terminal.py`: conversación interactiva en PowerShell.
- `src/evaluar_seleccion_v4.py`: conserva el nombre histórico; la primera evaluación real exhaustiva escribirá `evaluacion_seleccion_v5.json` y rechazará sobrescribirla.
- `tests/test_consulta_guiada.py`: pruebas sintéticas de cobertura completa, exclusión, grupos, presentación, validación y consulta única.
- `src/ollama_local.py`: cliente restringido a Ollama local y errores diferenciados.
- `src/importar_catalogo.py`: importador y validación documental.

`src/seleccion_objetivos.py`, `src/prueba_qwen_local.py`, `src/evaluar_seleccion_v2.py` y `src/evaluar_seleccion_v3.py` documentan flujos anteriores. Sus informes se conservan y no se deben sobrescribir.

## Reglas de la comparación v5

La única solicitud de comparación contiene:

- El objetivo interpretado.
- Todos los registros elegibles de `objetivos_busqueda.json`, excluyendo MED-036 en memoria, con solo `id` y `objetivo`.

Qwen devuelve `estado` y `evaluaciones`, con exactamente una entrada por ID elegible. Campos: `id`, `decision`, `justificacion` y `condicion_o_limite`. Alta exige justificación y condición null; parcial exige justificación y condición expresamente documentada; descartar exige ambos textos null. `resultados` exige alguna alta o parcial; `sin_coincidencias` exige todas descartadas. No se permite lista de candidatas separada en la respuesta del modelo.

Qwen no copia objetivos ni evidencias literales. El programa rechaza omitidos, duplicados, IDs no enviados y MED-036, deriva altas/parciales/descartadas y solo recupera nombre y objetivo local para altas y parciales. La presentación existente conserva `coincidencia` mediante adaptación por código. Se ordenan altas por ID y después parciales por ID. Una respuesta inválida, truncada o fallida no genera resultados ni se reintenta.

Temperatura 0 y semilla 42 en interpretación y selección; pensamiento desactivado. Contexto 16.384, generación 3.072 y espera 300 s permanecen configurables y acotados. Falta comprobar en una evaluación autorizada si la salida exhaustiva cabe en el presupuesto de generación; no se aumenta automáticamente ni se recorta el catálogo. La cobertura verificable no acredita pertinencia ni límites semánticos: esto sigue requiriendo revisión humana.

## Verificación automática vigente

El 22 de septiembre de 2026 pasaron 59 pruebas automáticas, sin inferencia real, con:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La verificación preparó el cuerpo de selección sin enviarlo a Ollama y confirmó:

- 38 registros documentales y 37 objetivos elegibles.
- MED-036 no aparece en el mensaje destinado a Qwen.
- Cada objeto enviado contiene exclusivamente `id` y `objetivo`.
- Temperatura 0, semilla 42 y pensamiento desactivado.
- Cobertura exacta exigida por esquema y por validación posterior.
- Rechazo de omitidos, duplicados, IDs desconocidos, MED-036 y estados o campos incoherentes.
- Derivación de altas, parciales y descartadas; presentación únicamente de altas y parciales, ordenadas por ID dentro de cada grupo.
- Recuperación local posterior de nombre y objetivo documental.
- Sin cambios en Excel, JSON generados, importador o presentación por terminal.

La validación automática acredita el contrato y la mecánica, no la calidad semántica de las decisiones de Qwen.

## Historial de evaluaciones anteriores

La primera pasada histórica v4 se guardó en `data/procesados/evaluacion_seleccion_v4.json`. Terminó sin errores técnicos ni truncamientos. Cada comparación fue una sola llamada con los 38 pares `id`/`objetivo`. Los Excel, `objetivos_busqueda.json` y los informes v2 y v3 conservaron sus huellas SHA-256.

Resultados de la pasada:

- A y B pasaron directamente a búsqueda, pero devolvieron `sin_coincidencias`.
- C pidió una aclaración concreta, incorporó la respuesta y devolvió `sin_coincidencias`.
- D, ajeno a movilidad, devolvió correctamente `sin_coincidencias`.
- E no pidió la aclaración esperada sobre el problema de aparcamiento y devolvió `sin_coincidencias`.
- A y B no produjeron candidatas altas o parciales. MED-005, MED-024 y MED-030 no se recuperaron.
- La evaluación automática marcó 6 de 9 comprobaciones. Ese dato no acredita calidad: cuatro aciertos proceden de exclusiones que también satisface una lista vacía.

Tiempos agregados:

- v3 por lotes: aproximadamente 1.079 segundos para los cinco casos; 1.018 segundos correspondieron a comparaciones.
- v4 en consulta única: aproximadamente 102 segundos para los cinco casos; 45 segundos correspondieron a comparaciones.

Después se realizaron revisiones v4 conservadas en `evaluacion_seleccion_v4_revision_semantica.json` y `evaluacion_seleccion_v4_catalogo_actualizado.json`. Recuperaron candidatas, pero documentaron omisiones, categorías demasiado amplias y condiciones no respaldadas. Esos resultados motivaron el contrato exhaustivo v5 y no validan su calidad.

## Siguiente paso acordado

1. Ejecutar la primera evaluación semántica real de v5 con `qwen3.6:latest` sobre los casos A–E ya definidos. Debe ser una única pasada, sin lotes ni reintentos, y guardar un informe nuevo en `data/procesados/evaluacion_seleccion_v5.json`.
2. Antes de inferir, comprobar modelo, digest, metadatos, catálogo actual y ausencia previa del archivo de salida. Durante la ejecución, registrar respuestas brutas, salidas procesadas, métricas y huellas, sin guardar razonamientos internos.
3. Revisar por separado el resultado técnico y el semántico: cobertura de los 37 IDs, MED-036 excluida, ausencia de truncamiento, categorías, condiciones documentadas y descartes. La cobertura exhaustiva no equivale a calidad.
4. No cambiar el prompt ni repetir A–E después de observar el resultado. Si aparecen problemas, informar y decidir una intervención posterior con casos independientes.
5. Solo cuando la selección tenga calidad suficiente, construir las fichas documentales; después, la selección visual y los desplegables por medida.

La primera evaluación real v5 no se ha ejecutado en esta sesión de actualización documental.

## Comandos habituales

Consulta por terminal:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal
```

Consulta con petición inicial:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal --peticion "Quiero reducir los viajes al trabajo en coche individual"
```

Regenerar catálogos, únicamente cuando corresponda revisar los Excel:

```powershell
.\.venv\Scripts\python.exe -m src.importar_catalogo
```

Los datos e informes privados están excluidos de Git. No publicar, crear repositorios remotos ni guardar credenciales.
