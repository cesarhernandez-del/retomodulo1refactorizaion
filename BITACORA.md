# Bitácora de refactorización

**Nombre:** César Jesús Hernández Torres
**Matrícula:** cesar.hernandez@energeticosnieto.com
**Fecha:** 2026-10-07

Registra aquí cada refactorización realizada con Claude Code: el prompt tal cual se escribió, el cambio aplicado al código y la justificación de por qué mejora la calidad. Después de cada cambio se ejecutó `pytest` y se anotó el resultado.

---

## Fase 0: Preparación y configuración del proyecto

Pasos previos a las refactorizaciones (no cuentan dentro de las 5 requeridas).

| # | Prompt usado | Cambio realizado | Justificación | Tests OK |
| :--- | :--- | :--- | :--- | :--- |
| 0.1 | *(manual, sin IA)* | Se configuró el entorno con uv y se guardaron las líneas base: `docs/linea_base_tests.txt` (20 tests pasando) y `docs/linea_base_linter.txt` (20 errores de ruff). Commit `8ac03e8`. | Tener un punto de comparación para verificar que ninguna refactorización altere el comportamiento y medir el avance del linter. | ✅ 20/20 |
| 0.2 | `/init` — "Please analyze this codebase and create a CLAUDE.md file…" | Claude analizó `src/`, `tests/`, `pyproject.toml` y el README, y generó CLAUDE.md con: comandos (`uv run pytest`, `uv run ruff check src`, cómo correr un solo test), reglas del reto (no tocar `tests/` ni `pyproject.toml`, conservar `agregarProducto`/`buscarProducto`), arquitectura (estado global en `gestor.py`), reglas de negocio (descuentos, VIP, IVA 16 %, stock bajo < 5) y *code smells* conocidos. | Dar a Claude el contexto y las restricciones del proyecto desde el inicio para que sus propuestas respeten las reglas del reto. | ✅ 20/20 |
| 0.3 | "genera una copia del archivo CLAUDE.md en /tmp/claude_md_init.txt" | Se guardó una copia de la versión inicial de CLAUDE.md generada por `/init`. | Conservar la versión original para comparar contra los ajustes posteriores. | N/A |
| 0.4 | "ajuste mi rama, ya que esta mal nombrada, tiene que ir de refactorizacion a main y yo estoy en preparación, realiza los ajustes" | No existía la rama `main`. Se creó desde la línea base (`8ac03e8`), se renombró `preparacion` → `refactorizacion`, se subieron ambas a GitHub, se configuró `main` como rama por defecto y se eliminó `preparacion` del remoto. | El reto pide entregar mediante PR de `refactorizacion` → `main`. | N/A |
| 0.5 | "Mueve mi archivo de bitacora que esta en la carpeta docs hacia la raíz y actualiza la referencia en el archivo CLAUDE.md. Tambien genera el archivo .claudeignore" | `docs/bitacora.md` → `BITACORA.md` (con `git mv`, conservando el historial); se actualizó la ruta en CLAUDE.md; se creó `.claudeignore` excluyendo `.venv/`, cachés, `.DS_Store` y `src/datos_ejemplo.json`. | El README pide `BITACORA.md` en la raíz. El `.claudeignore` evita que Claude lea archivos irrelevantes o generados. | N/A |
| 0.6 | "Remueve el archivo uv.lock del claudeignore y crea el archivo .claude/settings.json…" | Se quitó `uv.lock` de `.claudeignore` y se creó `.claude/settings.json` con reglas deny de lectura para `.env`, `.env.*`, `.venv/**`, `__pycache__/**`, `.pytest_cache/**` y `.ruff_cache/**`. | `uv.lock` describe el entorno y conviene que sea legible. `settings.json` refuerza con permisos lo que Claude no debe leer. | N/A |

---

## Fase 1: Exploración y planificación

Antes de escribir código se usó el **modo plan** de Claude Code, que impide modificar archivos y solo permite leer y analizar.

### Prompt de inventario

```
Objetivo: refactorizar este proyecto para mejorar legibilidad y mantenibilidad,
sin cambiar el comportamiento observable descrito en CLAUDE.md.

Contexto: el CLAUDE.md ya lista los code smells conocidos. No los repitas.
Lo que necesito ahora es lo que ahí no está.

Entrégame:
1. Inventario completo con ubicación, en dos grupos: los que ruff detecta
   (agrupados por código de regla) y los que no detecta ninguna herramienta.
2. Mapa de acoplamiento: almacen.py y reportes.py leen y escriben el estado
   de gestor.py directamente. Dime exactamente qué toca qué.
3. Cobertura de los tests: qué verifican los 20 tests y qué comportamiento
   NO verifica ninguno.
4. Zonas de riesgo: dónde una refactorización razonable rompería la semántica
   que CLAUDE.md exige conservar.

No modifiques ningún archivo. Solo repórtame.
```

Los puntos 2 y 4 se agregaron tras leer la salida de `/init`, que reveló que `almacen.py` y `reportes.py` manipulan directamente el estado global de `gestor.py` y que `cargar_datos` muta las listas in situ con `clear()` en lugar de reasignarlas. Sin ese mapa, una refactorización estructural habría roto comportamiento a media ejecución. El punto 3 cumplió doble función: señaló dónde se podía refactorizar sin red y produjo la lista de casos límite para los tests de caracterización.

### Medición empírica de las zonas de riesgo

Al pedirle las zonas de riesgo, Claude no emitió una opinión: escribió un script que recorrió ~83,000 combinaciones de precio y cantidad comparando cuatro reescrituras plausibles del cálculo de IVA y descuentos contra la implementación original, contando en cuántos casos divergía el resultado por aritmética de punto flotante.

| Reescritura evaluada | Casos con diferencia |
| :--- | :--- |
| Factorizar `base + base*0.16` como `base * 1.16` | ~0.2 % |
| Sumar desde campos ya redondeados | ~16.6 % |

Ambas quedaron prohibidas explícitamente en el PLAN.md, con el dato de respaldo. Es el origen de las restricciones del Paso 6.

### PLAN.md

| # | Prompt usado | Cambio realizado | Justificación |
| :--- | :--- | :--- | :--- |
| 1.1 | "Con base en el inventario que ya hiciste, propón el orden de refactorización en al menos 6 pasos, de menor a mayor riesgo de romper comportamiento. Para cada paso: qué cambia, qué archivos toca, por qué mejora el código, el criterio de aceptación verificable, y si involucra alguna de las zonas de riesgo que identificaste. […] Escribe el resultado en PLAN.md." | Se generó `PLAN.md` con la secuencia de refactorización, criterios de aceptación verificables por paso y una tabla de trayectoria esperada del linter. Commit `3aa53b9`. | Corregir un plan cuesta una frase; corregir código ya escrito cuesta reverts. Los criterios verificables (greps, conteos de ruff, textos exactos) permitieron validar cada paso con evidencia en lugar de con impresiones. |
| 1.2 | *(corrección al plan propuesto, antes de aprobarlo)* | Se rechazó el primer plan y se pidieron tres ajustes: **(a)** partir el Paso 1, que mezclaba `ruff --fix` con eliminación manual de código muerto, en dos pasos independientes; **(b)** declarar explícitamente que la convención de agregar type hints y docstrings a toda función tocada es una decisión deliberada, porque contradice la regla "un cambio por tarea" del CLAUDE.md; **(c)** agregar una precondición verificable antes del paso del estado compartido: comprobar con `grep` que ningún test referenciara `contadorVentas`. | El diff automático de ruff conviene revisarlo aislado del borrado manual. La convención transversal necesitaba quedar justificada para que un revisor no la lea como descontrol. La precondición se verificó: sin coincidencias, el renombrado era seguro. |

### Tabla de trayectoria del linter

Predicha en el plan, cumplida en la ejecución con una sola desviación (documentada en el Paso 6).

| Después de | Hallazgos | Commit |
| :--- | :--- | :--- |
| Línea base | 20 | — |
| Paso 1 | 13 | `93dfa80` |
| Paso 2 | 11 | `af90aeb` |
| Paso 3 | 7 | `78bfedc` |
| Paso 4 | 7 | `033bf84` |
| Paso 5 | 6 | `eb9245e` |
| Paso 6 | 1 | `c601190` |
| Paso 7 | 1 | `18e5c28` |
| Paso 8 | **0** | `98772ce` |

---

## Fase 2: Tests de caracterización

| # | Prompt usado | Cambio realizado | Justificación | Tests OK |
| :--- | :--- | :--- | :--- | :--- |
| 2.1 | "Ejecuta el Paso 9 del PLAN.md: los tests de caracterización en tests/test_caracterizacion.py. Restricciones: no modifiques ningún archivo existente en tests/, ni conftest.py, ni pyproject.toml, ni nada en src/. Solo API pública. Los tests fijan el comportamiento ACTUAL, bugs incluidos. Si un test falla, el test está mal escrito, no el código." | Se crearon 91 tests nuevos (42 funciones, varias parametrizadas) fijando el comportamiento del código original: texto exacto del ticket y de ambos reportes, todos los mensajes de `ultimo_error` incluida la diferencia entre `registrar_venta("")` y `cotizar("")`, los límites de descuento (499.99 / 500 / 999.99 / 1000) y de VIP (200 / 200.01), el tipo `int` del descuento cero, el orden de empates en `mas_vendidos`, el formato del JSON y los cuatro defectos N6, N15, N19 y N20. Commit `c3aefcb`. | Garantizar que el comportamiento observable y la API pública permanezcan intactos durante cada refactorización. La suite sube de 20 a 111 tests. | ✅ 111/111 |

**Método empleado por el agente.** En lugar de deducir los valores esperados leyendo el código, ejecutó el programa original desde una carpeta temporal y registró lo que producía. Los nombres de los tests se revisaron para que declaren qué afirman (`test_descuento_cero_es_entero`, `test_stock_bajo_es_estrictamente_menor_a_cinco`, `test_ultimo_error_no_se_limpia_tras_un_exito`), y los que fijan defectos lo hacen explícito para que nadie los lea como validación de comportamiento correcto.

**Decisión sobre la ubicación.** El README indica "no modificar `tests/`". Se resolvió distinguiendo entre *modificar* los tests existentes, que está prohibido, y *agregar* un archivo nuevo, que no lo está. La alternativa —una carpeta `caracterizacion/` fuera de `tests/`— se descartó porque no correría con un `pytest` normal y dejaría el trabajo invisible para quien evalúe.

---

## Fase 3: Refactorizaciones

| # | Prompt usado | Cambio realizado | Justificación | Tests OK |
| :--- | :--- | :--- | :--- | :--- |
| 1 | "Ejecuta el Paso 1 del PLAN.md: correcciones automáticas de ruff. Restricciones: Solo `ruff check src --fix`. Nada manual, nada de código muerto, eso es el Paso 2. No toques tests/, pyproject.toml ni PLAN.md. Un cambio por tarea: nada de mejoras de paso. Al terminar corre `uv run pytest` y `uv run ruff check src`, y muéstrame ambas salidas." | Eliminación de 4 cabeceras `coding: utf-8` (UP009), del modo `"r"` explícito en `open()` (UP015), corrección del orden de imports en `main.py` (I001) y eliminación del `import os` sin uso en `reportes.py` (F401). 4 archivos, 2 inserciones, 7 borrados. Commit `93dfa80`. | Eliminar advertencias de estándares de Python moderno sin alterar lógica. El agente **no** aplicó `--unsafe-fixes`, que habría cerrado 5 hallazgos más: ruff los marca inseguros porque pueden cambiar comportamiento, y en este reto deben pasar por refactorización manual con los tests corriendo. Ruff 20 → 13. | ✅ 111/111 |
| 2 | "Ejecuta el Paso 2 del PLAN.md: eliminación de código muerto. Verifica previamente con grep que los elementos a eliminar no posean referencias activas." | Eliminación de `calcular_descuento_viejo`, el bloque comentado de `exportar_txt` y `MODO_DEBUG` en `gestor.py`; `reporteViejoCSV` en `reportes.py`. 29 líneas borradas, cero agregadas. Commit `af90aeb`. | Reducir la carga cognitiva eliminando componentes en desuso que arrastraban advertencias (N802, SIM115). El agente verificó con `grep -rn` que cada nombre apareciera solo en su propia definición, borró, y volvió a correr el grep para confirmar que no quedaran referencias. Ruff 13 → 11. | ✅ 111/111 |
| 3 | "Ejecuta el Paso 3 del PLAN.md: persistencia con `with` en almacen.py. Conserva tal cual lo que el plan marca como N15: el `except Exception` sin restringir, el `clear()` antes de leer, el `d.get(\"contador\", 0)` y la mutación in situ. El diccionario de guardado mantiene el mismo orden de llaves." | Sustitución de `open()` manual por `with open(...)` en `guardar_datos` y `cargar_datos`; `hayArchivo` → `hay_archivo` con `os.path.exists()` directo; diccionario de guardado como literal. Commit `78bfedc`. | Garantizar el cierre del descriptor ante cualquier excepción. El criterio del plan ("JSON idéntico byte a byte") se verificó generando el archivo con el código anterior y el nuevo fuera del repositorio y comparándolos con `cmp`: idénticos, 1034 bytes, usando fecha fija y nombres con acentos para ejercitar `ensure_ascii=False`. Ruff 11 → 7; `almacen.py` sin hallazgos. | ✅ 111/111 |
| 4 | "Ejecuta el Paso 4 del PLAN.md: limpieza de reportes.py. `mas_vendidos` usa `sorted(..., reverse=True)`. NO uses `sorted(...)[::-1]`: invierte el orden de los empates. Los reportes siguen imprimiendo Y regresando el texto. El texto exacto no cambia, incluido el doble espacio en `\"  <-- STOCK BAJO\"` y el formato `$20.0`." | `hacer_cosa` → `formatear_dinero`; constante compartida `STOCK_MINIMO = 5`; `mas_vendidos` con `dict.get` y ordenamiento estable; `resumen_ventas` reutiliza `total_vendido()`; nombres descriptivos en lugar de `s`, `t`, `aux`, `temp`, `temp2`, `k`, `v`, `p`. Commit `033bf84`. | Eliminar duplicación del umbral y de la suma. **Se conservó deliberadamente el bucle acumulador en lugar de `sum()`**: desde Python 3.12 `sum()` aplica compensación de Neumaier, comprobado con `sum([0.1]*10) == 1.0` frente a `0.9999999999999999` del bucle. Verificación cruzada sobre 3,000 estados aleatorios, incluidos empates y `n = 0, 1, 3, 10`: equivalencia exacta. Ruff se mantiene en 7, como preveía el plan. | ✅ 111/111 |
| 5 | "Ejecuta el Paso 5 del PLAN.md: dividir `menu()` en main.py. Conserva tal cual N6, N19 y N20. Todos los textos de `print` e `input` idénticos, carácter por carácter. Solo main.py." | Descomposición en una función por opción, despachadas mediante el diccionario `OPCIONES`, más `mostrar_opciones` y `cargar_datos_iniciales`. Complejidad ciclomática de `menu()` de 17 a 4. Commit `eb9245e`. | Eliminar el bloque imperativo con condicionales anidados. Validación sobre 4,500 sesiones simuladas con entradas aleatorias (opciones inválidas, `nan`, `inf`, `2.7`, códigos inexistentes, VIP) por tres escenarios de arranque —sin archivo, con archivo corrupto y con datos válidos— comparando salida impresa, textos solicitados, errores, JSON y `ultimo_error`: sin discrepancias. Conteo de las 30 llamadas a `print`/`input` verificado contra el commit anterior. Ruff 7 → 6, cerrando el C901 de `menu`. | ✅ 111/111 |
| 6 | "Ejecuta el Paso 6 del PLAN.md: extraer descuentos e IVA con constantes. Restricciones críticas, verifícalas una por una antes de terminar: `impuesto = base * TASA_IVA` y `total = round(base + impuesto, 2)` en ese orden, NUNCA `base * 1.16` ni sumar desde campos redondeados. Umbrales con `>=`. VIP con `>` sobre `subtotal - descuento`. El extra VIP sobre el subtotal bruto. Cuando no hay descuento, `descuento` es el entero `0`. `cotizar` no aplica VIP. […] Compara contra el commit anterior en una rejilla amplia de precios y cantidades." | 8 constantes con nombre y dos funciones puras (`descuento_por_volumen`, `descuento_vip`). Las 19 líneas de descuentos e IVA de `registrar_venta` quedaron en 5. Commit `c601190`. | Desacoplar las reglas fiscales y comerciales, centralizándolas en funciones puras y probables. **Verificación con control negativo:** 480,408 casos en `registrar_venta` y 60,038 en `cotizar`, comparando tipo y valor exacto de cada campo e incluyendo el texto del ticket: cero diferencias. Para comprobar que el comparador no estuviera roto, se corrió contra una copia con el error inyectado (`base * 1.16`): detectó 286 diferencias en ventas y 50 en cotizar. Ruff 6 → 1. | ✅ 111/111 |
| 7 | "Ejecuta el Paso 7 del PLAN.md: dividir `registrar_venta`. El orden de validación no cambia: código vacío → producto no existe → cantidad inválida → stock insuficiente. `cotizar` conserva su propia validación (N2). La línea \"Descuento\" depende del descuento SIN redondear. El diccionario de venta conserva el mismo orden de llaves. Agrega aquí los type hints." | Extracción de `validar_venta(codigo, cantidad)` con salidas tempranas y `armar_ticket(venta, descuento)`. Type hints completos. Commit `18e5c28`. | Aislar validación, cálculo y formateo. **Hallazgo crítico:** al invertir las condiciones para las salidas tempranas, la inversión intuitiva `cantidad <= 0` habría dejado pasar `NaN` como válido, porque toda comparación con `NaN` es `False`. Se escribió `not cantidad > 0` (y `not stock >= cantidad`), que sí conserva la semántica. Control negativo con `cantidad <= 0`: 4 diferencias, justo los casos con `NaN`. Verificación sobre 190,715 ventas válidas, 128 combinaciones de validación y 24 de `cotizar`: cero diferencias. Ruff se mantiene en 1. | ✅ 111/111 |
| 8 | "Ejecuta el Paso 8 del PLAN.md: el estado compartido de gestor.py. `contadorVentas` pasa a `contador_ventas`; la llave del JSON sigue siendo `\"contador\"`. Conserva `agregarProducto`, `buscarProducto`, `INVENTARIO`, `VENTAS`, `ultimo_error`, la mutación in situ y el acceso como `gestor.X`. […] Verifica que `grep -rn contadorVentas src` no devuelva nada y que el folio continúe tras recargar." | Renombrado de `contadorVentas` a `contador_ventas` en `gestor.py` y `almacen.py`; `aux` → `nuevo_stock` en `actualizar_stock`; `buscarProducto` como list comprehension sobre `.values()`; producto como literal con orden `codigo`, `nombre`, `precio`, `stock`. Commit `98772ce`. | Alinear el estado global a PEP 8 sin romper el contrato de persistencia ni las funciones públicas. Se conservó `texto.lower()` dentro del filtro de `buscarProducto` en lugar de calcularlo una vez: sacarlo habría hecho que `buscarProducto(None)` con inventario vacío lanzara excepción en lugar de regresar `[]`. Las 11 verificaciones solicitadas pasaron, y se repitieron las 4,500 sesiones del Paso 5 contra el commit anterior sin diferencias. **Ruff: `All checks passed!`** | ✅ 111/111 |

---

## Iteraciones del CLAUDE.md

El archivo no se escribió una sola vez: se ajustó tres veces durante el reto, cada una a partir de un problema real y no de una lista anticipada. De hecho se dejó deliberadamente incompleto al inicio —sin reglas sobre docstrings ni estilo de nombres— para agregarlas solo si el comportamiento del agente las hacía necesarias.

| # | Qué lo provocó | Qué se agregó | Commit |
| :--- | :--- | :--- | :--- |
| 1 | Durante la exploración, el modo plan se desactivó sin aviso y el agente modificó `BITACORA.md` por iniciativa propia. Se detectó porque `git status` mostró el archivo modificado cuando en modo plan no debía haber ningún cambio. | `NO escribir en BITACORA.md ni en PLAN.md sin que yo lo pida explícitamente. La bitácora la redacto yo.` | `adb7fb1` |
| 2 | La línea base del linter salió vacía: se había corrido `ruff` contra el Python 3.9 del sistema, donde no estaba instalado. El proyecto tenía dos intérpretes compitiendo (`pip3` instalaba en el del sistema, `uv` trabajaba sobre un `.venv` con 3.12). | Sección de entorno: Python 3.12 en `.venv` gestionado con uv; todo comando pasa por `uv run`, nunca `pip` ni `python` del sistema. | `1be9306` |
| 3 | Al cerrar el Paso 8, el agente señaló que el archivo había quedado desactualizado en tres puntos: mencionaba `contadorVentas`, listaba code smells ya resueltos y decía que la suite tenía 20 tests. Además la regla de tests nunca reflejó la decisión tomada en la Fase 2. | Nombres actualizados, lista de smells retirada, conteo corregido a 111, y la regla precisada: *los 20 tests originales son el contrato y NO se modifican; sí se permite agregar archivos nuevos de tests propios*. Se conservó intacta la línea de la línea base (`20 passed`), que registra el estado de partida. | `6532666` |

---

## Intentos que no funcionaron

| Qué falló | Cómo se detectó | Cómo se resolvió |
| :--- | :--- | :--- |
| La captura inicial del linter quedó vacía. | El archivo `linea_base_linter.txt` salió sin contenido, aunque ruff imprime resumen incluso sin hallazgos. | Se había ejecutado contra el Python 3.9 del sistema y el error se fue a stderr. Se corrigió redirigiendo ambos flujos (`2>&1`) y ejecutando con `uv run`. Originó la iteración 2 del CLAUDE.md. |
| El modo plan se desactivó sin aviso. | `git status` mostró `BITACORA.md` modificado durante una fase que no debía escribir nada. | `git restore BITACORA.md` y regla nueva en el CLAUDE.md. Originó la iteración 1. |
| Mi instrucción sobre los tests de caracterización era lógicamente incorrecta. | Pedí incluirlos "al final como paso separado". El agente objetó: escritos al final solo certificarían que el código refactorizado se comporta como el código refactorizado, y además las zonas sin cobertura quedarían desprotegidas durante toda la refactorización. | Se adoptó su propuesta: listarlos al final del plan pero **ejecutarlos primero**, contra el código original. |
| El PLAN.md afirmaba algo falso. | Al escribir los tests, el agente descubrió que un JSON sin la llave `"ventas"` no deja el inventario vacío: lo reemplaza con el del archivo y lo que se vacía son las ventas. El inventario solo queda vacío si falta `"inventario"`. Lo detectó ejecutando, no leyendo. | Dos líneas corregidas en el plan. Commit `80bc8e4`. |
| Comando incorrecto para la plataforma. | Pedí verificar espacios con `cat -A`, que es de GNU; macOS trae la versión BSD. | El agente usó `cat -e` y además señaló que el patrón de grep que yo había dado no habría mostrado el doble espacio, porque está *antes* del `<--`; lo revisó aparte. |
| El script de verificación del Paso 5 falló en el primer intento. | El propio agente lo reportó: error suyo al leer el archivo corrupto, no del código bajo prueba. | Lo corrigió y volvió a ejecutarlo. Documentarlo importa porque un script de verificación roto puede dar falsos positivos tan fácilmente como falsos negativos. |
| Autorreporte en lugar del diff. | En el Paso 4, al pedir el diff, el agente entregó su propia revisión resumida afirmando que todo estaba correcto. | Se pidieron verificaciones puntuales con `grep` y `cat -e` sobre los cuatro puntos críticos del paso. Aceptar sistemáticamente el autorreporte es como se mueve el umbral de auto-aceptación sin decidirlo conscientemente. |

**Sobre las confirmaciones de permisos.** A lo largo del reto se mantuvo la aprobación manual de cada comando, rechazando tres veces la opción de *auto mode*. En dos ocasiones el cliente pidió confirmación de permisos para comandos compuestos que combinaban `cd` con rutas relativas, advirtiendo que existía una regla `Read()` de deny que podía aplicar. Es evidencia de que la configuración estaba activa y no era decorativa.

---

## Notas y observaciones

**Sobre `.claudeignore`.** El reto lo pide y se incluye. No aparece en la documentación oficial de Claude Code —donde el mecanismo documentado para excluir archivos sensibles es `permissions.deny` en `.claude/settings.json`— y existe una solicitud de funcionalidad abierta en el repositorio del proyecto pidiendo que se implemente. Por eso se trata como señal de intención y no como garantía: la exclusión efectiva la hacen las reglas deny, que el cliente aplica independientemente de lo que decida el modelo. Ambos archivos se entregan y se mantienen sincronizados.

**Preservación estricta de bugs conocidos (N6, N15, N19, N20).** Durante el diagnóstico se detectaron cuatro defectos reales: el menú imprime "Datos cargados" aunque la carga falle, un JSON válido al que le falta una llave (`"ventas"` o `"inventario"`) lanza `KeyError` y deja el estado a medias, `pedir_numero` acepta `nan`, y la ruta del archivo depende del directorio de ejecución. Se decidió **no corregirlos**: el README exige comportamiento observable idéntico y corregir un bug cambia el comportamiento, aunque sea para bien. Son dos trabajos distintos y mezclarlos rompe el alcance. Quedaron fijados con tests de caracterización que los documentan explícitamente, de modo que están registrados, protegidos contra alteración accidental y disponibles para un alcance posterior.

**Manejo de flotantes en Python 3.12.** Se descartó reemplazar los bucles acumuladores por `sum()` en los reportes: desde 3.12 `sum()` implementa suma compensada de Neumaier, lo que genera diferencias de precisión frente a la suma imperativa original en casos de borde.

**Desviación respecto al plan.** El hallazgo C901 de `registrar_venta` desapareció en el Paso 6 en lugar del Paso 7. El plan lo contemplaba como posible. La consecuencia es que la justificación del Paso 7 pasó a ser puramente de diseño —separar validación, cálculo y presentación— y no de cierre de hallazgos del linter.

---

## Reflexión final

Claude Code resultó eficiente para el análisis estructural, las refactorizaciones sistemáticas y, sobre todo, para generar scripts de verificación masiva: ahí estuvo el mayor ahorro de tiempo. Pero el patrón que explica los buenos resultados no fue la capacidad del modelo, sino la forma de dirigirlo.

Cinco veces el agente dejó de inferir y midió: la divergencia de redondeos en ~83,000 combinaciones, la comparación byte a byte del JSON con `cmp`, los 3,000 reportes, las 4,500 sesiones de menú y los 480,000 casos de ventas. En dos de ellas inyectó deliberadamente un error en una copia para comprobar que su propio comparador lo detectara antes de confiar en un resultado de cero diferencias. Validar el instrumento antes que el resultado es metodología de pruebas, no de refactorización, y no apareció por casualidad: apareció porque el PLAN.md exigía criterios de aceptación verificables en cada paso.

Las decisiones de mayor valor fueron las de **no** cambiar algo. Conservar el bucle acumulador en vez de `sum()`, escribir `not cantidad > 0` en vez de `cantidad <= 0` para no dejar pasar `NaN`, dejar `texto.lower()` dentro del filtro para no alterar el retorno con inventario vacío. Ninguna de esas tres la habría señalado un linter, y las tres habrían producido un refactor "más limpio" con comportamiento distinto.

En cuanto al reparto de trabajo: delegaría sin reservas las correcciones mecánicas de linter, la eliminación de código muerto verificada con grep, la extracción de funciones, la generación de tests de caracterización y la escritura de scripts de verificación. No delegaría la decisión de qué constituye comportamiento observable, la de no corregir los bugs encontrados, la revisión de los diffs en zonas de riesgo, ni esta bitácora. El momento en que ese límite estuvo más cerca de moverse solo fue cuando el agente ofreció su propio resumen del diff en lugar del diff: era cómodo, probablemente correcto, y aceptarlo sistemáticamente habría vaciado de contenido la supervisión.

La refactorización asistida por IA no consiste en delegar la reescritura, sino en diseñar restricciones explícitas y fijar de antemano un arnés de pruebas que funcione como frontera infranqueable. La combinación de verificación masiva automatizada y revisión humana de los diffs en los puntos de riesgo es lo que permitió llegar a cero hallazgos de linter sin una sola diferencia de comportamiento en todos los casos comparados.
