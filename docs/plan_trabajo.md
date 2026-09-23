# Plan de trabajo

Estado: importador y catálogos completados. MVP local con interpretación, aclaración y comparación v5 exhaustiva: una única consulta de todos los objetivos elegibles, excluyendo MED-036 del envío sin eliminarla documentalmente. Implementación completada y 59 pruebas automáticas superadas sin inferencia real. El siguiente paso acordado es la primera evaluación semántica real A–E de v5. Calidad semántica no validada. Interfaz gráfica y acceso por internet fuera del alcance actual.

## Flujo final acordado

1. El usuario plantea su necesidad.
2. El modelo la reformula como objetivo y pregunta solo si hay una ambigüedad relevante.
3. Compara exclusivamente con los objetivos documentados y selecciona las medidas con coincidencia alta o parcial.
4. La futura presentación muestra una ficha por candidata con nombre e identificador, descripción breve documentada, objetivo documentado, relaciones relevantes y KPIs del archivo de asociaciones.
5. El usuario selecciona una o varias medidas.
6. Cada medida elegida tendrá un desplegable propio con actores implicados, presupuesto y fases en su orden original.

La información ausente se muestra como «No consta en la documentación». En esta etapa están implementados los tres primeros pasos mediante terminal. Las fichas, la selección visual y los desplegables son las siguientes tareas.

## 1. Preparación

Completada. Estructura y repositorio local preparados. Entorno `.venv` con Python 3.13 y openpyxl, dependencias fijadas en `requirements.txt`. Comandos de PowerShell documentados en README; no se cambia la política de ejecución.

## 2. Revisión documental

Completada para la versión actual de los tres Excel revisados manualmente. Se han inspeccionado encabezados, hojas, formato de asociaciones y leyenda de relaciones simétricas y dirigidas. No se realiza conciliación automática de IDs. Se comprueba la integridad de los originales mediante huellas SHA-256.

## 3. Catálogo estructurado

Completada. El comando `.\.venv\Scripts\python.exe -m src.importar_catalogo` genera los seis catálogos y el informe en `data/procesados/`. Conserva textos, fases como texto original, identificadores y procedencia. `objetivos_busqueda.json` contiene solo `id` y `objetivo`. El texto de KPIs de la ficha permanece separado de las asociaciones del Excel específico.

## 4. Búsqueda por objetivos

Implementada la comparación v5 con `qwen3.6:latest`. Una única consulta recibe exclusivamente el objetivo interpretado y todos los objetos elegibles `id`/`objetivo` (actualmente 37; MED-036 excluida en memoria). Qwen devuelve `estado` y `evaluaciones`, una por ID, con `decision` alta/parcial/descartar, justificación y condición. Alta requiere justificación y condición null; parcial exige ambos textos y un límite expresamente documentado; descartar exige ambos null. Sin coincidencias exige todas descartadas. El código rechaza cobertura incompleta, IDs duplicados/no enviados/excluidos y estados o campos incoherentes. Deriva tres grupos y presenta solo altas y parciales, por ID dentro de cada grupo, recuperando nombres y objetivos localmente después de validar. No hay lotes ni reintentos.

Reproducibilidad: temperatura 0 y semilla 42 para ambas etapas, sin pensamiento. Se conservan los límites configurables de contexto, generación y espera. La respuesta exhaustiva puede necesitar más generación; no se cambia automáticamente y un truncamiento invalida toda la selección. El evaluador conserva el nombre `src/evaluar_seleccion_v4.py`, pero guardará la primera evaluación exhaustiva en `evaluacion_seleccion_v5.json` y rechazará sobrescribirla.

Siguiente paso: ejecutar una sola pasada real A–E con el catálogo vigente y `qwen3.6:latest`. Antes se comprobarán modelo, digest, metadatos y ausencia del informe v5. Se registrarán respuestas brutas, salidas procesadas, tiempos, cobertura de los 37 IDs, exclusión de MED-036 e integridad de archivos. Después habrá revisión humana separada de altas, parciales, condiciones y descartes. No se modificará el prompt ni se repetirá la batería tras observar el resultado.

La evaluación v4 se ejecutó una sola vez y quedó en `data/procesados/evaluacion_seleccion_v4.json`. Las cinco comparaciones incluyeron el catálogo completo, terminaron sin errores ni truncamientos y preservaron los originales, objetivos e informes previos. C pidió e integró la aclaración; E no pidió la aclaración esperada. Qwen devolvió `sin_coincidencias` en todos los casos. El resultado automático fue seis de nueve, pero cuatro comprobaciones se superan porque una lista vacía excluye MED-018 y evita marcar MED-029 como alta. A y B omitieron todas las medidas esperadas, incluida MED-005, MED-024 y MED-030. La calidad semántica no está validada y no se repetirá ni ajustará la misma pasada para forzar el resultado.

La evaluación v3 y sus lotes quedan como referencia histórica en `data/procesados/evaluacion_seleccion_v3.json`. No forman parte del flujo vigente.

## 5. Presentación

Pendiente. Para cada candidata validada, crear una ficha con nombre e ID, descripción breve documentada, objetivo que justifica la coincidencia, relaciones relevantes y KPIs del archivo de asociaciones. Indicar «No consta en la documentación» ante datos ausentes. Permitir consultar relaciones simétricas desde ambos extremos; conservar origen y destino de las dirigidas, sin inferir inversas ni transitivas.

## 6. Selección e implementación por medida

Pendiente. Permitir seleccionar visualmente una o varias medidas. Cada elegida tendrá un desplegable propio con actores implicados, presupuesto y fases documentadas en el orden original. No incluye seguimiento operativo, asignación de tareas ni control de ejecución.

## 7. Conversación

Implementada por terminal. Conserva petición y aclaraciones, formula una pregunta cada vez y realiza una sola comparación exhaustiva cuando el objetivo queda listo. Pendiente validar v5 mediante su primera evaluación semántica real; después, convertir el flujo en una experiencia visual y enlazar las candidatas con fichas y selección posterior.

## 8. Validación

Completada para el importador: pruebas sintéticas aisladas con unittest, importación real, contraste de recuentos revisados, referencias y nombres, duplicados con simetría, separación estricta de objetivos, integridad de originales y conservación del catálogo anterior ante errores. Resultados privados en `docs/validacion_importacion.md` y `data/procesados/informe_validacion.json`, excluidos de Git.

Completada la validación automática de v5 con 59 pruebas: consulta única, 37 elegibles derivados dinámicamente, MED-036 excluida sin alterar el catálogo, cobertura exacta, rechazo de omitidos/duplicados/desconocidos, decisiones y estados coherentes, separación estricta de campos, orden estable, recuperación documental posterior y ausencia de reintentos. La comprobación del cuerpo confirmó temperatura 0, semilla 42 y envío exclusivo de `id`/`objetivo`.

Las evaluaciones v4 quedan como historial: la inicial produjo listas vacías y las revisiones posteriores recuperaron candidatas con errores semánticos. La primera evaluación real v5 aún no se ha ejecutado. Después de ella, y solo si la calidad es suficiente, quedarán las fichas documentales, la selección visual y los desplegables por medida. No incluir datos sintéticos de pruebas en el catálogo real.
