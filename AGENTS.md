# Instrucciones para trabajar en PMST Asistente

## Colaboración y alcance

- El usuario es principiante: explicar en español qué se hace y cualquier acción necesaria mediante pasos concretos.
- Trabajar dentro de la carpeta del proyecto abierta en VS Code.
- Inspeccionar antes de editar y no sobrescribir archivos existentes sin revisar su contenido.
- Conservar intactos los documentos originales.
- No incluir documentación propia o privada ni credenciales en el control de versiones. Guardar documentos fuente en `data/originales/`, derivados en `data/procesados/` y documentación privada de trabajo en `docs/`, excluida salvo `docs/plan_trabajo.md`. README, estas instrucciones y el plan son documentación general versionable y no deben contener datos privados.
- No crear repositorios remotos ni publicar archivos sin instrucción expresa del usuario.
- La primera versión se centrará en selección y consulta; no incluirá seguimiento operativo de la implementación.
- Etapa actual autorizada: entorno Python 3.13, importación y validación de los tres Excel mediante openpyxl, y generación del catálogo JSON. No implementar el chatbot ni llamar a un LLM todavía.
- Ejecutar comandos con `.venv/Scripts/python.exe`, sin cambiar la política de ejecución de PowerShell. Registrar dependencias en `requirements.txt` y usar `unittest`.
- Se permiten datos sintéticos únicamente en pruebas aisladas; nunca incorporarlos al catálogo real.

## Fuentes y fidelidad documental

- Fuentes actuales: `data/originales/MEDIDAS.xlsx` (Hoja1), `Relaciones medidas-medidas.xlsx` (Relaciones candidatas y Leyenda relaciones) y `Relaciones medidas-KPIs.xlsx` (FICHA_MEDIDA_KPI).
- La documentación se ha corregido y revisado manualmente. No realizar conciliación automática de identificadores. Los saltos en su numeración son válidos. No imponer recuentos permanentes: el catálogo puede ampliarse.
- No inventar medidas, objetivos, relaciones, indicadores, fases ni resultados.
- Ante información ausente, indicar exactamente: «No consta en la documentación».
- Mantener una referencia a la fuente de cada dato importado, con el localizador que permita encontrarlo en el documento o en la hoja y fila/celda correspondiente.
- Respetar los identificadores existentes y la dirección de cada relación.
- Las relaciones simétricas según la leyenda se podrán consultar desde ambos extremos, conservando una única relación original. Las dirigidas conservan origen y destino: no deducir su inversa. No deducir relaciones transitivas.
- Leer campos por encabezados. Ignorar filas completamente vacías y columnas vacías sin encabezado. Una fila con contenido sin identificador genera un error con archivo, hoja y fila.
- Conservar textos completos y saltos de línea; las fases se guardan como texto original en esta etapa. Representar celdas vacías como `null`. Normalizar espacios y mayúsculas únicamente al comparar nombres, nunca al guardar datos ni identificadores.
- Conservar las referencias de todas las apariciones de cada KPI y los nombres originales correspondientes.
- Las asociaciones de KPIs proceden exclusivamente del Excel específico. El campo KPI's Éxito/Eficacia de la ficha se conserva como `kpis_texto_ficha`, sin convertirlo automáticamente en asociaciones. Tipo y subtipo son propiedades de cada asociación, no propiedades universales del KPI.
- `objetivos_busqueda.json` contiene exclusivamente `id` y `objetivo`. Su procedencia se consulta por ID en `medidas.json`; no añadir fuentes ni nombres al archivo de búsqueda.
- Validar todos los datos antes de publicar salidas. Ante errores, escribir el informe y terminar con código de error sin sustituir los catálogos anteriores. Las fases, actores y KPIs asociados ausentes generan advertencias, no bloqueos.
- No modificar Excel ni usar IA o servicios externos para importar los datos. Verificar las huellas SHA-256 de los originales antes y después de importar.

## Flujo y separación obligatoria de datos

1. El usuario explica su problema en un chat.
2. El LLM identifica el objetivo y pide aclaraciones si son necesarias.
3. La búsqueda inicial utiliza exclusivamente los objetivos documentados: solo puede recibir identificadores y objetivos de las medidas. No puede recibir descripciones, presupuestos, actores, relaciones, KPIs ni fases como criterios de selección.
4. Validar los identificadores devueltos por el LLM contra el catálogo permitido antes de consultar datos. No consultar datos de identificadores inválidos ni sustituirlos por otros inventados.
5. Consultar el resto de los campos solo después de identificar las candidatas. Recuperar su descripción, objetivos, relaciones documentadas y KPIs asociados.
6. Las medidas relacionadas no pasan automáticamente a ser candidatas por objetivo.
7. El usuario puede seleccionar una o varias medidas.
8. Mostrar las fases documentadas de cada medida seleccionada por separado y en su orden original. No fusionar, reordenar ni completar fases mediante inferencias.

## Validación futura

Comprobar la separación entre la búsqueda por objetivos y la consulta posterior, la validación de identificadores, la trazabilidad de cada dato, el tratamiento de ausencias, la dirección y simetría de relaciones y la conservación del orden y separación de fases. Validar identidades, referencias, nombres, duplicados y coherencia de los IDs de asociación. Usar datos sintéticos en pruebas aisladas y ejecutar la importación con la documentación real autorizada; no reproducir datos privados en archivos versionables.
