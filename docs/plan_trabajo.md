# Plan de trabajo

Estado: importador y catálogos completados. MVP local con interpretación, aclaración y comparación v5 exhaustiva: una única consulta de todos los objetivos elegibles, excluyendo MED-036 del envío sin eliminarla documentalmente. Implementación y pruebas simuladas; evaluación real A–E pendiente de autorización. Calidad semántica no validada. Interfaz gráfica y acceso por internet fuera del alcance actual.

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

Reproducibilidad: temperatura 0 y semilla 42 para ambas etapas, sin pensamiento. Se conservan los límites configurables de contexto, generación y espera. La respuesta exhaustiva puede necesitar más generación; no se cambia automáticamente y un truncamiento invalida toda la selección. Falta evaluar la calidad semántica y la suficiencia de límites con Qwen cuando se autorice. El evaluador conserva el nombre `src/evaluar_seleccion_v4.py`, pero guarda la futura evaluación en un archivo v5 nuevo y rechaza sobrescribirlo.

La evaluación v4 se ejecutó una sola vez y quedó en `data/procesados/evaluacion_seleccion_v4.json`. Las cinco comparaciones incluyeron el catálogo completo, terminaron sin errores ni truncamientos y preservaron los originales, objetivos e informes previos. C pidió e integró la aclaración; E no pidió la aclaración esperada. Qwen devolvió `sin_coincidencias` en todos los casos. El resultado automático fue seis de nueve, pero cuatro comprobaciones se superan porque una lista vacía excluye MED-018 y evita marcar MED-029 como alta. A y B omitieron todas las medidas esperadas, incluida MED-005, MED-024 y MED-030. La calidad semántica no está validada y no se repetirá ni ajustará la misma pasada para forzar el resultado.

La evaluación v3 y sus lotes quedan como referencia histórica en `data/procesados/evaluacion_seleccion_v3.json`. No forman parte del flujo vigente.

## 5. Presentación

Pendiente. Para cada candidata validada, crear una ficha con nombre e ID, descripción breve documentada, objetivo que justifica la coincidencia, relaciones relevantes y KPIs del archivo de asociaciones. Indicar «No consta en la documentación» ante datos ausentes. Permitir consultar relaciones simétricas desde ambos extremos; conservar origen y destino de las dirigidas, sin inferir inversas ni transitivas.

## 6. Selección e implementación por medida

Pendiente. Permitir seleccionar visualmente una o varias medidas. Cada elegida tendrá un desplegable propio con actores implicados, presupuesto y fases documentadas en el orden original. No incluye seguimiento operativo, asignación de tareas ni control de ejecución.

## 7. Conversación

Implementada por terminal. Conserva petición y aclaraciones, formula una pregunta cada vez y realiza una sola comparación completa cuando el objetivo queda listo. Pendiente corregir de forma general la selección semántica vacía observada en v4, convertir el flujo en una experiencia visual y enlazar las candidatas con fichas y selección posterior.

## 8. Validación

Completada para el importador: pruebas sintéticas aisladas con unittest, importación real, contraste de recuentos revisados, referencias y nombres, duplicados con simetría, separación estricta de objetivos, integridad de originales y conservación del catálogo anterior ante errores. Resultados privados en `docs/validacion_importacion.md` y `data/procesados/informe_validacion.json`, excluidos de Git.

Completada la validación técnica del flujo v4 con 50 pruebas: catálogo completo en una sola llamada, separación estricta de campos, IDs inexistentes o duplicados, formatos inválidos, condiciones incoherentes, estados sin resultados, conservación de aclaraciones, orden estable, recuperación documental posterior y ausencia de reintentos. La evaluación real confirma que los fallos técnicos se distinguen de `sin_coincidencias` y que el nuevo formato evita los errores de evidencia de v3.

El tiempo agregado de los cinco casos bajó de unos 1.079 segundos en v3 a 102 segundos en v4; las comparaciones bajaron de unos 1.018 a 45 segundos. Pendiente: investigar con criterios generales por qué Qwen devolvió listas vacías para necesidades claramente relacionadas, mejorar la aclaración de aparcamiento, validar con casos independientes, construir fichas documentales, selección visual y desplegables por medida. No incluir datos sintéticos de las pruebas en el catálogo real.
