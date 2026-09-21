# PMST Asistente

Herramienta para elegir y consultar medidas de planes de movilidad sostenible al trabajo a partir de documentación aportada por el usuario.

## Estado actual

MVP completamente local. El importador de Excel está comprobado y existe una conexión reutilizable con Ollama para probar selección por objetivos. Los catálogos JSON se generan localmente después de validar los datos. La primera versión cubrirá selección y consulta, sin seguimiento operativo. Todavía no hay interfaz web ni acceso por internet.

La búsqueda inicial recibirá exclusivamente identificadores y objetivos. Solo después de validar las candidatas se consultarán sus detalles. Las fases de las medidas seleccionadas se presentarán por separado y en su orden original.

## Estructura

- `data/originales/`: los tres Excel revisados, intactos y excluidos de Git.
- `data/procesados/`: catálogos JSON, informe y huellas de integridad, excluidos de Git.
- `docs/`: documentación local privada, excluida salvo `plan_trabajo.md`.
- `src/importar_catalogo.py`: lectura, validación y generación de los catálogos.
- `tests/test_importar_catalogo.py`: pruebas sintéticas sin datos privados.
- `src/ollama_local.py`: cliente de la API local con tiempo máximo y errores diferenciados.
- `src/prueba_qwen_local.py`: prueba de selección y repetición, con validación de evidencias e IDs.
- `tests/test_ollama_local.py`: respuestas simuladas, sin requerir Ollama.
- `requirements.txt`: versiones utilizadas de openpyxl y et-xmlfile.
- `AGENTS.md`: instrucciones para Codex.

## Regenerar el catálogo en PowerShell

1. Abrir la terminal de VS Code en la carpeta raíz del proyecto.
2. Comprobar que `data/originales/` contiene `MEDIDAS.xlsx`, `Relaciones medidas-medidas.xlsx` y `Relaciones medidas-KPIs.xlsx`.
3. Ejecutar con el entorno ya creado:

```powershell
.\.venv\Scripts\python.exe -m src.importar_catalogo
```

El comando imprime recuentos y advertencias. Si devuelve un error, abrir `data/procesados/informe_validacion.json`: incluye archivo, hoja y fila de las incidencias documentales. Los errores impiden publicar los nuevos catálogos; los anteriores permanecen disponibles y el informe describe el intento fallido. Las advertencias no bloquean la importación. El código de salida es 0 cuando termina correctamente y 1 ante errores.

Para ejecutar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Probar Qwen localmente

Abrir Ollama y ejecutar desde la raíz del proyecto, con el catálogo ya generado:

```powershell
.\.venv\Scripts\python.exe -m src.prueba_qwen_local
```

El comando usa `qwen3.6:latest`, contexto de 16.384 tokens, máximo de 3.072 tokens de salida y 300 segundos por petición. Envía una primera petición y la repite una sola vez si obtiene una respuesta técnicamente válida. No cambia de modelo ni descarga nada. Puede consumir una parte importante de la RAM; no se detienen otras aplicaciones automáticamente.

Para configurar explícitamente los límites:

```powershell
.\.venv\Scripts\python.exe -m src.prueba_qwen_local --modelo qwen3.6:latest --contexto 16384 --generacion 3072 --espera 300
```

Para repetir verificando el mismo modelo de una ejecución anterior, antes de sobrescribir el informe:

```powershell
$digestPrueba = (Get-Content .\data\procesados\prueba_qwen_local.json -Raw -Encoding UTF8 | ConvertFrom-Json).entorno_inicial.modelo.digest
.\.venv\Scripts\python.exe -m src.prueba_qwen_local --digest $digestPrueba
```

El digest identifica el contenido instalado. Si la etiqueta apunta a otro digest, el programa se detiene; no restaura ni descarga el modelo anterior. Temperatura 0 y semilla fija ayudan a comparar, pero no garantizan resultados idénticos entre versiones de Ollama o hardware.

La conexión está limitada a `http://127.0.0.1:11434`, sin proxies ni redirecciones. Se comprueba que el modelo sea GGUF local y no declare referencia remota. No se cambia la dirección de escucha de Ollama. La implementación usa exclusivamente la biblioteca estándar de Python y no añade dependencias.

El único catálogo enviado contiene `id` y `objetivo`. Se guarda su huella y se verifica que no tenga otros campos. Los nombres se recuperan con código después de validar la respuesta y no se envían en la repetición. La petición y los objetivos se separan de las instrucciones y se tratan como datos.

La respuesta se solicita mediante el esquema JSON del parámetro `format` de la [API local de chat de Ollama](https://docs.ollama.com/api/chat). Contiene `estado`, `objetivo_interpretado`, `pregunta_aclaracion` y `medidas`; cada selección tiene `id`, `justificacion` y `evidencia_objetivo`. Se validan estructura y tipos, IDs únicos existentes, evidencia literal del objetivo de cada ID y coherencia entre estado, aclaración y lista. No se solicita ni guarda razonamiento interno.

El contexto se comprueba con una cota conservadora basada en bytes UTF-8, válida para el tokenizador BPE de bytes verificado en los metadatos, más margen de plantilla y reserva de generación. No es una tokenización exacta y puede rechazar contextos que en realidad cabrían. Nunca elimina objetivos para ajustarlos. No se utiliza automáticamente el contexto máximo del modelo.

`data/procesados/prueba_qwen_local.json` contiene metadatos y digest, modelos cargados, configuración, huella del catálogo, resultados validados y métricas que proporciona Ollama. Los tiempos de carga y generación se convierten de nanosegundos a segundos. La medición de hardware adjunta conserva su fecha: al repetir, no debe interpretarse como memoria libre actual. El informe se reemplaza en cada ejecución; copiarlo dentro de `data/procesados/` si se quieren conservar comparaciones.

Errores de servicio, modelo ausente, memoria insuficiente, tiempo agotado, contexto insuficiente, truncamiento y respuesta inválida son fallos explícitos (salida 1), nunca «sin coincidencias». Tras agotar el tiempo se cierra la conexión y no se repite la inferencia; la liberación de recursos depende de Ollama y no se fuerza la detención de procesos. La permanencia solicitada del modelo en memoria es de cinco minutos.

La validación técnica no acredita la pertinencia, exhaustividad ni utilidad de la selección. Las recomendaciones deben revisarse con el usuario antes de dar por validada su calidad.

## Preparar el entorno si falta

Comprobado con Python 3.13.15 y openpyxl 3.1.5. Con Python Install Manager instalado, ejecutar desde la raíz:

```powershell
py -3.13 --version
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si PowerShell no reconoce `py`, cerrar y volver a abrir VS Code para actualizar la ruta de comandos. En este equipo el lanzador también puede ejecutarse por su ubicación:

```powershell
& "$env:LOCALAPPDATA\Microsoft\WindowsApps\py.exe" -3.13 --version
& "$env:LOCALAPPDATA\Microsoft\WindowsApps\py.exe" -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell. Si Python 3.13 falta, instalarlo mediante Python Install Manager antes de continuar. No recrear `.venv` si el entorno existente funciona.

## Archivos generados y procedencia

Todos se guardan en `data/procesados/`, en UTF-8:

| Archivo | Contenido |
| --- | --- |
| `medidas.json` | Todos los campos de las fichas, con nombres definidos en `CAMPOS_MEDIDA` y fuente por registro. |
| `objetivos_busqueda.json` | Lista con solo `id` y `objetivo`, sin nombres, detalles ni fuentes adicionales. |
| `relaciones_medidas.json` | Origen, destino, tipo y nombres originales, con procedencia. |
| `tipos_relacion.json` | Tipo, significado y dirección originales de la leyenda. |
| `kpis.json` | ID, primer nombre documentado y todas las referencias, con el nombre original de cada aparición. |
| `asociaciones_medida_kpi.json` | ID de asociación, medida, KPI, nombres, tipo y subtipo, con procedencia. |
| `informe_validacion.json` | Estado, recuentos, errores, advertencias, datos ausentes y huellas SHA-256 de los originales. |

`fuente` conserva archivo, hoja, fila y columnas de cada campo. En el archivo de búsqueda se omite deliberadamente la procedencia: puede recuperarse por ID desde `medidas.json`. En el catálogo de KPIs, `fuentes` conserva todas sus apariciones. No se reescriben textos ni saltos de línea. Las fases siguen siendo texto original separado por medida. Las celdas vacías se guardan como `null`; la futura interfaz mostrará «No consta en la documentación». Las expresiones de ausencia escritas en las fichas se conservan literalmente.

Los indicadores asociados se recuperan únicamente de `Relaciones medidas-KPIs.xlsx`. El texto de KPI's Éxito/Eficacia de `MEDIDAS.xlsx` se conserva en `kpis_texto_ficha` y no genera asociaciones. El tipo y subtipo pertenecen a la asociación concreta.

Las relaciones simétricas se reconocen por la dirección `Simétrica` de la leyenda. Se conserva el registro original y la futura consulta podrá acceder a él desde ambos extremos. Las relaciones `A → B` conservan su dirección. No se crean relaciones inversas dirigidas ni transitivas, ni se amplía automáticamente la lista de candidatas.

## Validaciones y límites

Se comprueban IDs únicos, referencias existentes, correspondencia entre IDs y nombres (solo al comparar se normalizan espacios y mayúsculas), IDs de asociación con formato `REL__<ID_MEDIDA>__<ID_KPI>`, parejas medida–KPI duplicadas, nombres contradictorios de KPI, tipos definidos en la leyenda, relaciones duplicadas según su simetría y presencia de objetivos y descripciones.

La lectura usa encabezados, permite columnas reordenadas e ignora filas y columnas sin contenido. Se rechazan filas con contenido sin ID, encabezados requeridos ausentes o repetidos, contenido sin encabezado, columnas adicionales no revisadas, fórmulas y errores Excel. Una dirección de leyenda desconocida requiere revisión explícita. No se calculan fórmulas ni se inventa su resultado.

Los recuentos revisados se han contrastado localmente; no son límites del programa. Los resultados documentales detallados permanecen fuera de Git en `data/procesados/` y `docs/validacion_importacion.md`.

Se valida y serializa todo antes de reemplazar salidas. Ante errores de escritura se intenta restaurar los archivos anteriores. Cada reemplazo es atómico, pero el conjunto no es una transacción frente a un corte eléctrico: ejecutar una sola importación cada vez.

No guardar credenciales ni documentación privada en el control de versiones. `.env.example`, si se crea, contendrá únicamente ejemplos sin secretos. No se han creado remotos ni publicado archivos.

Consultar las etapas en [docs/plan_trabajo.md](docs/plan_trabajo.md).
