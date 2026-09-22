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
- `src/evaluar_seleccion_v4.py`: conserva el nombre histórico; la siguiente salida será `evaluacion_seleccion_v5.json` y se rechaza sobrescribirla. No ejecutar todavía A–E.
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

## Verificación e historial

Ejecutar las pruebas automáticas sin inferencia real con:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La primera y única pasada real v4 se guardó en `data/procesados/evaluacion_seleccion_v4.json`. Terminó sin errores técnicos ni truncamientos. Cada comparación fue una sola llamada con los 38 pares `id`/`objetivo`. Los Excel, `objetivos_busqueda.json` y los informes v2 y v3 conservaron sus huellas SHA-256.

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

La mecánica v4 está validada técnicamente. La calidad semántica no está validada.

## Trabajo pendiente recomendado

1. Revisar el resultado de las pruebas automáticas de v5. Esta implementación no ejecuta ninguna evaluación real A–E.
2. Cuando se autorice, evaluar cobertura, truncamiento, calidad de descartes, categorías y respaldo de condiciones. Las revisiones v4 posteriores recuperaron candidatas, pero conservaron omisiones y errores semánticos; sus informes privados se mantienen intactos. No repetir ni retocar la misma batería para forzar resultados.
3. Cuando la selección tenga calidad suficiente, construir las fichas documentales sin mezclar sus datos con el selector.
4. Después, añadir selección visual y un desplegable independiente por medida con actores, presupuesto y fases en orden original.

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
