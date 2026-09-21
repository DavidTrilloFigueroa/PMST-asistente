# Plan de trabajo

Estado: preparación, revisión estructural, catálogo JSON y validación del importador completados. MVP completamente local con Ollama. Conexión reutilizable y prueba inicial de selección completadas con dos respuestas técnicamente válidas. Calidad pendiente de revisión humana; interfaz web y acceso por internet fuera del alcance actual.

## 1. Preparación

Completada. Estructura y repositorio local preparados. Entorno `.venv` con Python 3.13 y openpyxl, dependencias fijadas en `requirements.txt`. Comandos de PowerShell documentados en README; no se cambia la política de ejecución.

## 2. Revisión documental

Completada para la versión actual de los tres Excel revisados manualmente. Se han inspeccionado encabezados, hojas, formato de asociaciones y leyenda de relaciones simétricas y dirigidas. No se realiza conciliación automática de IDs. Se comprueba la integridad de los originales mediante huellas SHA-256.

## 3. Catálogo estructurado

Completada. El comando `.\.venv\Scripts\python.exe -m src.importar_catalogo` genera los seis catálogos y el informe en `data/procesados/`. Conserva textos, fases como texto original, identificadores y procedencia. `objetivos_busqueda.json` contiene solo `id` y `objetivo`. El texto de KPIs de la ficha permanece separado de las asociaciones del Excel específico.

## 4. Búsqueda por objetivos

Prueba inicial completada con `qwen3.6:latest` instalado localmente. Se envía exclusivamente el catálogo completo de identificadores y objetivos. Hay esquema JSON, validación de IDs, evidencias literales y coherencia de estado, aclaración y medidas. Contexto, generación y espera acotados y configurables; sin descargas, cambio automático de modelo ni recorte silencioso. Resultados y métricas privados en `data/procesados/prueba_qwen_local.json`. Pendiente revisar con el usuario la pertinencia y exhaustividad de la selección.

## 5. Presentación

Pendiente. Una vez identificadas y validadas las candidatas, recuperar y mostrar sus descripciones, objetivos, relaciones documentadas y KPIs asociados, con referencias a las fuentes. Indicar «No consta en la documentación» ante datos ausentes. Permitir consultar relaciones simétricas desde ambos extremos según la leyenda; conservar origen y destino de las dirigidas, sin inferir inversas ni relaciones transitivas.

## 6. Selección e implementación por medida

Pendiente. Permitir seleccionar una o varias medidas. Mostrar las fases documentadas de cada medida por separado y en el orden original. Esta etapa consiste en consultar las instrucciones de implementación; no incluye seguimiento operativo, asignación de tareas ni control de ejecución.

## 7. Conversación

Pendiente. Integrar el flujo de chat local: recoger el problema, identificar el objetivo, solicitar aclaraciones cuando hagan falta y facilitar la selección. Mantener la separación entre búsqueda por objetivos y consulta de detalles durante toda la conversación. Ya existe una prueba aislada con el LLM local; no hay interfaz web ni conversación de varios turnos.

## 8. Validación

Completada para el importador: pruebas sintéticas aisladas con unittest, importación real, contraste de recuentos revisados, referencias y nombres, duplicados con simetría, separación estricta de objetivos, integridad de originales y conservación del catálogo anterior ante errores. Resultados privados en `docs/validacion_importacion.md` y `data/procesados/informe_validacion.json`, excluidos de Git.

Completada la validación técnica de la prueba local: respuestas simuladas sin Ollama y dos peticiones reales, con comprobación de esquema, IDs, citas literales, coherencia y métricas. Se comprueba que una respuesta inválida no consulte fichas ni active una repetición y que los nombres nunca pasen a la petición del modelo.

Pendiente para la aplicación futura: revisión humana de recomendaciones, integración de la validación en la conversación, presentación de ausencias y consulta de relaciones y fases por medida. No incluir datos sintéticos de las pruebas en el catálogo real.
