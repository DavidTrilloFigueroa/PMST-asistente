# PMST Asistente

Herramienta para elegir y consultar medidas de planes de movilidad sostenible al trabajo a partir de documentación aportada por el usuario.

## Estado actual

Entorno Python 3.13 e importador de los tres Excel implementados y comprobados. Los catálogos JSON se generan localmente después de validar los datos. Todavía no hay chatbot ni llamadas a un LLM. La primera versión cubrirá selección y consulta, sin seguimiento operativo de la implementación.

La búsqueda inicial recibirá exclusivamente identificadores y objetivos. Solo después de validar las candidatas se consultarán sus detalles. Las fases de las medidas seleccionadas se presentarán por separado y en su orden original.

## Estructura

- `data/originales/`: los tres Excel revisados, intactos y excluidos de Git.
- `data/procesados/`: catálogos JSON, informe y huellas de integridad, excluidos de Git.
- `docs/`: documentación local privada, excluida salvo `plan_trabajo.md`.
- `src/importar_catalogo.py`: lectura, validación y generación de los catálogos.
- `tests/test_importar_catalogo.py`: pruebas sintéticas sin datos privados.
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
