# PMST Asistente

Herramienta para elegir y consultar medidas de planes de movilidad sostenible al trabajo a partir de documentación aportada por el usuario.

## Estado actual

MVP completamente local. La consulta guiada interpreta la petición, solicita aclaraciones y exige una evaluación explícita de cada objetivo elegible en una sola selección v5. El catálogo actual tiene 38 medidas: MED-036 se conserva documentalmente y se excluye del envío, dejando 37 objetivos elegibles. Usa Ollama y `qwen3.6:latest`, con entrada por terminal y una primera interfaz web Streamlit. No incluye acceso público, persistencia ni seguimiento operativo.

La evaluación real v5 completó correctamente la cobertura técnica y mejoró la recuperación de medidas directas, pero confirmó sobreselección semántica por inferir efectos no declarados desde mecanismos. La búsqueda inicial sigue recibiendo exclusivamente identificadores y objetivos. Solo después de validar las candidatas se consultan tarjetas, KPIs, detalles y relaciones locales.

## Estructura

- `data/originales/`: los tres Excel revisados, intactos y excluidos de Git.
- `data/procesados/`: catálogos JSON, informe y huellas de integridad, excluidos de Git.
- `docs/`: documentación local privada, excluida salvo `plan_trabajo.md`.
- `src/importar_catalogo.py`: lectura, validación y generación de los catálogos.
- `tests/test_importar_catalogo.py`: pruebas sintéticas sin datos privados.
- `src/ollama_local.py`: cliente de la API local con tiempo máximo y errores diferenciados.
- `src/prueba_qwen_local.py`: prueba de selección y repetición, con validación de evidencias e IDs.
- `src/seleccion_objetivos.py`: instrucciones v2 versionadas, esquema JSON y validación de la selección.
- `src/evaluar_seleccion_v2.py`: batería reproducible de cuatro casos, una inferencia por caso.
- `src/consulta_guiada.py`: interpretación, validación y consulta única al catálogo completo del flujo vigente.
- `src/consulta_terminal.py`: entrada interactiva completa por terminal.
- `src/presentacion_terminal.py`: presentación documental, selección y filtrado de relaciones reutilizables.
- `src/app_web.py`: frontend local Streamlit con conversación, tarjetas, selección, detalles y relaciones.
- `src/evaluar_seleccion_v3.py`: evaluación histórica del flujo anterior por lotes.
- `src/evaluar_seleccion_v4.py`: evaluación vigente de la consulta única con cinco casos.
- `tests/test_consulta_guiada.py`: pruebas sintéticas de aclaraciones, consulta única y validación de candidatas.
- `tests/test_presentacion_terminal.py`: pruebas locales de descripción breve, selección y relaciones.
- `tests/test_ollama_local.py`: respuestas simuladas, sin requerir Ollama.
- `requirements.txt`: dependencias fijadas, incluidas openpyxl y Streamlit.
- `AGENTS.md`: instrucciones para Codex.
- `ESTADO_PROYECTO.md`: resumen para reanudar el trabajo en otro chat.

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

## Iniciar una consulta guiada por terminal

1. Abrir Ollama.
2. Abrir una terminal de PowerShell en la raíz del proyecto.
3. Ejecutar:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal
```

La terminal solicita la necesidad. Si hay una ambigüedad relevante, muestra una sola pregunta y conserva la petición original al incorporar la respuesta. Cuando el objetivo está claro, filtra MED-036 en memoria y envía todos los objetivos elegibles en una única consulta, exclusivamente con `id` y `objetivo`. No modifica el catálogo documental ni fija un recuento permanente.

También se puede aportar la primera petición en el comando:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal --peticion "Quiero reducir los viajes al trabajo en coche individual"
```

Qwen devuelve `estado` y `evaluaciones`: exactamente una por cada ID enviado. Cada evaluación contiene `id`, `decision` (`alta`, `parcial` o `descartar`), `justificacion` y `condicion_o_limite`. Alta y parcial exigen justificación; solo parcial admite y exige condición, expresamente respaldada por el objetivo. Descartar exige ambos textos null. `resultados` exige alguna alta o parcial; `sin_coincidencias` exige todas descartadas. No devuelve candidatas separadas ni copia objetivos o evidencias literales. Se rechazan omisiones, IDs repetidos/no enviados, MED-036 y estados o condiciones incoherentes, sin mostrar resultados ni reintentar.

El código deriva altas, parciales y descartadas. Solo muestra altas primero y parciales después, ambas por ID. Tras validar toda la cobertura, recupera los datos documentales y presenta descripción breve, objetivo y KPIs. Después de la selección muestra actores, presupuesto, fases y exclusivamente las relaciones documentadas cuyos dos extremos estén seleccionados.

Interpretación y selección usan temperatura 0, semilla 42 y `think: false`. Ya estaban configuradas así; ahora también se registran temperatura y semilla en los metadatos. Ayudan a reproducir, pero no garantizan salidas idénticas entre versiones o hardware. Contexto 16.384, generación 3.072 y espera 300 s permanecen configurables. La respuesta exhaustiva es más larga: su suficiencia y calidad están pendientes de evaluación real. Un truncamiento se rechaza, sin recortar el catálogo ni reintentar. La validación estructural no demuestra que una condición esté semánticamente respaldada por el documento.

Configuración explícita equivalente a la actual:

```powershell
.\.venv\Scripts\python.exe -m src.consulta_terminal --modelo qwen3.6:latest --contexto 16384 --generacion 3072 --espera 300
```

## Iniciar la interfaz web local

1. Abrir Ollama y comprobar que `qwen3.6:latest` está disponible.
2. Ejecutar desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/app_web.py
```

3. Abrir `http://localhost:8501`.

La interfaz conserva durante la sesión actual la petición, aclaraciones, mensajes, candidatas y selección. `Nueva consulta` limpia ese estado. Ollama no se inicializa hasta que se envía el primer mensaje. No existe historial persistente entre reinicios.

## Prueba histórica de Qwen

Abrir Ollama y ejecutar desde la raíz del proyecto, con el catálogo ya generado:

```powershell
.\.venv\Scripts\python.exe -m src.prueba_qwen_local
```

El comando usa `qwen3.6:latest`, contexto de 16.384 tokens, máximo de 3.072 tokens de salida y 300 segundos por petición. Envía una primera petición y la repite una sola vez si obtiene una respuesta técnicamente válida. Guarda las nuevas ejecuciones en `data/procesados/prueba_qwen_local_actual.json` para no sobrescribir la referencia original. No cambia de modelo ni descarga nada. Puede consumir una parte importante de la RAM; no se detienen otras aplicaciones automáticamente.

Para configurar explícitamente los límites:

```powershell
.\.venv\Scripts\python.exe -m src.prueba_qwen_local --modelo qwen3.6:latest --contexto 16384 --generacion 3072 --espera 300
```

Para repetir verificando el mismo modelo de una ejecución anterior, antes de sobrescribir el informe:

```powershell
$digestPrueba = (Get-Content .\data\procesados\prueba_qwen_local_actual.json -Raw -Encoding UTF8 | ConvertFrom-Json).entorno_inicial.modelo.digest
.\.venv\Scripts\python.exe -m src.prueba_qwen_local --digest $digestPrueba
```

El digest identifica el contenido instalado. Si la etiqueta apunta a otro digest, el programa se detiene; no restaura ni descarga el modelo anterior. Temperatura 0 y semilla fija ayudan a comparar, pero no garantizan resultados idénticos entre versiones de Ollama o hardware.

La conexión está limitada a `http://127.0.0.1:11434`, sin proxies ni redirecciones. Se comprueba que el modelo sea GGUF local y no declare referencia remota. No se cambia la dirección de escucha de Ollama. El cliente de Ollama usa la biblioteca estándar; la interfaz web añade Streamlit como dependencia local.

El único catálogo enviado contiene `id` y `objetivo`. Se guarda su huella y se verifica que no tenga otros campos. Los nombres se recuperan con código después de validar la respuesta y no se envían en la repetición. La petición y los objetivos se separan de las instrucciones y se tratan como datos.

La respuesta se solicita mediante el esquema JSON del parámetro `format` de la [API local de chat de Ollama](https://docs.ollama.com/api/chat). Contiene `estado`, `objetivo_interpretado`, `pregunta_aclaracion` y `medidas`; cada selección tiene `id`, `justificacion`, `evidencia_objetivo`, `tipo_coincidencia` y `condicion`. Se validan estructura y tipos, IDs únicos existentes, evidencia literal del objetivo de cada ID, coherencia entre estado, aclaración y lista, y coherencia entre tipo y condición. No se solicita ni guarda razonamiento interno.

Las instrucciones `seleccion_objetivos_v2` comparan el significado de la petición con todos los objetivos. No exigen coincidencia literal, un objetivo principal único ni un máximo de resultados. Una candidata es `directa` si su objetivo respalda la necesidad y `condicionada` si requiere una condición que no figura en la petición ni en ese objetivo. Una coincidencia condicionada no representa una relación entre medidas. Las coincidencias temáticas se excluyen y los efectos no se completan con conocimiento externo.

## Evaluar la selección v2

La batería acordada ejecuta una sola vez cuatro peticiones: dos formulaciones sobre reducción del coche individual, una petición de movilidad demasiado amplia y una petición ajena a movilidad. Usa la misma configuración local comprobada y no envía al modelo los resultados esperados ni los criterios de evaluación.

```powershell
.\.venv\Scripts\python.exe -m src.evaluar_seleccion_v2
```

Para exigir exactamente el modelo empleado en la evaluación registrada:

```powershell
.\.venv\Scripts\python.exe -m src.evaluar_seleccion_v2 --digest 07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522
```

El resultado queda en `data/procesados/evaluacion_seleccion_v2.json`, excluido de Git. Incluye versión y huella de instrucciones, configuración, métricas, respuestas validadas y comparación automática. También comprueba mediante SHA-256 que `prueba_qwen_local.json` no cambia.

La primera evaluación v2 completó las cuatro inferencias sin errores técnicos ni truncamiento, pero solo superó tres de seis comprobaciones funcionales. Conservó las siete coincidencias ya aceptadas y excluyó correctamente como directa la medida que solo reduce emisiones; siguió omitiendo las tres coincidencias semánticas identificadas en la revisión, no utilizó la categoría condicionada y respondió con resultados ante una petición que requería aclaración. El caso ajeno a movilidad devolvió correctamente `sin_coincidencias`. Este resultado no valida la calidad general ni justifica ajustar reiteradamente el prompt contra esta batería.

## Referencia histórica del flujo v3

La evaluación v3 ejecutó cinco casos con lotes de ocho medidas. Se conserva como referencia del enfoque anterior y no debe repetirse ni sobrescribirse.

El informe privado se guarda en `data/procesados/evaluacion_seleccion_v3.json`. Registra todas las evaluaciones por medida, cobertura, intentos, tiempos, configuración, versiones de instrucciones, modelo y digest.

La primera pasada v3 superó dos de nueve comprobaciones funcionales. C pidió aclaración y la integró correctamente; D cubrió los 38 IDs y terminó sin coincidencias. A y B agotaron el reintento en dos lotes, y C en uno, porque Qwen devolvió evidencias que no eran fragmentos literales del objetivo correspondiente. Esos tres casos quedaron incompletos y no generan listas definitivas. E no pidió la aclaración esperada antes de seleccionar. No se repitió la evaluación ni se relajó la validación para mejorar artificialmente el resultado.

## Evaluación exhaustiva v5 y referencia histórica v4

El módulo `src.evaluar_seleccion_v4` conserva su nombre histórico. El primer intento v5, realizado con Ollama apagado, se conserva en `data/procesados/evaluacion_seleccion_v5.json`. La primera ejecución real válida A–E se guardó sin sobrescribirlo en `data/procesados/evaluacion_seleccion_v5_real_01.json`, con informe y anexo en `docs/`.

La ejecución real cubrió exactamente los 37 objetivos elegibles en A–D, excluyó MED-036, no tuvo truncamientos ni reintentos y pidió las aclaraciones esperadas en C y E. D devolvió correctamente `sin_coincidencias`. A, B y C recuperaron las medidas directas principales, MED-005 y MED-024, pero produjeron entre 20 y 29 candidatas. La revisión humana confirmó falsas altas y parciales basadas en efectos inferidos. V5 mejora cobertura y trazabilidad, pero su precisión semántica todavía no permite una revisión humana ligera. No repetir A–E ni ajustar el prompt para perseguir esa batería; cualquier cambio posterior debe evaluarse con casos nuevos.

Los párrafos siguientes describen la primera evaluación histórica v4. Su contrato era solo de candidatas y ya no es el contrato vigente.

El evaluador v4 usa una sola consulta completa por necesidad, conserva los informes previos y registra entradas, salidas validadas, candidatas, configuración, modelo, digest, tiempos e integridad de los archivos.

```powershell
.\.venv\Scripts\python.exe -m src.evaluar_seleccion_v4 --digest 07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522
```

La pasada aprobada ya se ejecutó una vez y quedó en `data/procesados/evaluacion_seleccion_v4.json`. Las cinco comparaciones fueron técnicamente válidas, incluyeron los 38 pares `id`/`objetivo` y no tuvieron errores ni truncamientos. C pidió e integró una aclaración; E no pidió la aclaración esperada. Qwen devolvió `sin_coincidencias` en A, B, C, D y E. Por tanto, A y B no produjeron candidatas altas ni parciales y no recuperaron MED-005, MED-024 o MED-030. El resultado automático fue seis de nueve comprobaciones, debido principalmente a que la lista vacía también cumple las exclusiones de MED-018 y MED-029; no representa una calidad semántica aceptable.

La suma de tiempos de los cinco casos bajó de aproximadamente 1.079 segundos en v3 a 102 segundos en v4. La comparación propiamente dicha pasó de unos 1.018 segundos a 45 segundos. Esta mejora de rendimiento no valida la selección semántica.

El contexto se comprueba con una cota conservadora basada en bytes UTF-8, válida para el tokenizador BPE de bytes verificado en los metadatos, más margen de plantilla y reserva de generación. No es una tokenización exacta y puede rechazar contextos que en realidad cabrían. Nunca elimina objetivos para ajustarlos. No se utiliza automáticamente el contexto máximo del modelo.

`data/procesados/prueba_qwen_local.json` se conserva como referencia original. `evaluacion_seleccion_v2.json` contiene la evaluación posterior. Ambos registran metadatos, digest, configuración, huella del catálogo, resultados validados y métricas proporcionadas por Ollama. Los tiempos de carga y generación se convierten de nanosegundos a segundos. La medición de hardware adjunta conserva su fecha y no representa la memoria libre actual.

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

`fuente` conserva archivo, hoja, fila y columnas de cada campo. En el archivo de búsqueda se omite deliberadamente la procedencia: puede recuperarse por ID desde `medidas.json`. En el catálogo de KPIs, `fuentes` conserva todas sus apariciones. No se reescriben textos ni saltos de línea. Las fases siguen siendo texto original separado por medida. Las celdas vacías se guardan como `null`; las interfaces muestran «No consta en la documentación». Las expresiones de ausencia escritas en las fichas se conservan literalmente.

Los indicadores asociados se recuperan únicamente de `Relaciones medidas-KPIs.xlsx`. El texto de KPI's Éxito/Eficacia de `MEDIDAS.xlsx` se conserva en `kpis_texto_ficha` y no genera asociaciones. El tipo y subtipo pertenecen a la asociación concreta.

Las relaciones simétricas se reconocen por la dirección `Simétrica` de la leyenda y se consultan desde cualquiera de los extremos. Las relaciones `A → B` conservan su dirección. No se crean relaciones inversas dirigidas ni transitivas, ni se amplía automáticamente la lista de candidatas.

## Validaciones y límites

Se comprueban IDs únicos, referencias existentes, correspondencia entre IDs y nombres (solo al comparar se normalizan espacios y mayúsculas), IDs de asociación con formato `REL__<ID_MEDIDA>__<ID_KPI>`, parejas medida–KPI duplicadas, nombres contradictorios de KPI, tipos definidos en la leyenda, relaciones duplicadas según su simetría y presencia de objetivos y descripciones.

La lectura usa encabezados, permite columnas reordenadas e ignora filas y columnas sin contenido. Se rechazan filas con contenido sin ID, encabezados requeridos ausentes o repetidos, contenido sin encabezado, columnas adicionales no revisadas, fórmulas y errores Excel. Una dirección de leyenda desconocida requiere revisión explícita. No se calculan fórmulas ni se inventa su resultado.

Los recuentos revisados se han contrastado localmente; no son límites del programa. Los resultados documentales detallados permanecen fuera de Git en `data/procesados/` y `docs/validacion_importacion.md`.

Se valida y serializa todo antes de reemplazar salidas. Ante errores de escritura se intenta restaurar los archivos anteriores. Cada reemplazo es atómico, pero el conjunto no es una transacción frente a un corte eléctrico: ejecutar una sola importación cada vez.

No guardar credenciales ni documentación privada en el control de versiones. `.env.example`, si se crea, contendrá únicamente ejemplos sin secretos. Este trabajo no modifica repositorios remotos ni publica archivos.

Consultar las etapas en [docs/plan_trabajo.md](docs/plan_trabajo.md).
