# Plan de refactorización

Orden de menor a mayor riesgo de romper comportamiento. Un commit por paso.
Después de CADA paso: `uv run pytest` (20 tests originales + caracterización)
y `uv run ruff check src`.

> **Orden de ejecución:** el Paso 9 (tests de caracterización) se ejecuta
> **primero**, contra el código original (commit `adb7fb1`), y después se
> corre en cada paso. Se lista al final porque no es una refactorización.

## Decisión deliberada: type hints y docstrings junto con cada paso

Las funciones que un paso toque reciben, en ese mismo commit, type hints y
docstring (en lugar de comentarios), sin cambiar firmas ni nombres públicos
usados por los tests.

Esto se aparta de la regla de un solo tipo de cambio por tarea/commit. Se
acepta a propósito para **no tocar la misma función dos veces**: un paso final
"agregar type hints" volvería a abrir todas las funciones ya refactorizadas,
duplicaría el diff a revisar y mezclaría de nuevo código ya validado. El
cambio es aditivo (no altera comportamiento) y lo cubren los mismos tests.
Excepción: los Pasos 1 y 2 no agregan hints (son un diff automático y una
eliminación pura).

## Trayectoria esperada de ruff

| Después de | Hallazgos |
|------------|-----------|
| Línea base | 20 |
| Paso 1     | 13 |
| Paso 2     | 11 |
| Paso 3     | 7  |
| Paso 4     | 7  |
| Paso 5     | 6  |
| Paso 6     | 1–2 (el C901 de `registrar_venta` puede desaparecer aquí) |
| Paso 7     | 1  |
| Paso 8     | 0  |

---

## Paso 1 — Correcciones automáticas de ruff

- **Qué cambia:** solo `uv run ruff check src --fix`: UP009 ×4 (cabeceras
  `coding`), UP015 (modo `"r"`), I001 (orden de imports en `main.py`), F401
  (`import os` en `reportes.py`). Ningún cambio manual.
- **Archivos:** `src/gestor.py`, `src/almacen.py`, `src/reportes.py`, `src/main.py`.
- **Por qué mejora:** quita ruido sintáctico; commit aislado para revisar el
  diff automático por separado.
- **Criterio de aceptación:** `git diff` contiene solo esas 7 correcciones;
  ruff 20 → 13; pytest verde.
- **Zonas de riesgo:** ninguna.

## Paso 2 — Eliminar código muerto

- **Qué cambia:** se borran `calcular_descuento_viejo`, el bloque comentado
  `exportar_txt` y `MODO_DEBUG` (`gestor.py`), y `reporteViejoCSV`
  (`reportes.py`, que arrastra un N802 y un SIM115).
- **Archivos:** `src/gestor.py`, `src/reportes.py`.
- **Por qué mejora:** el código que queda es el que se ejecuta; menos superficie que mantener.
- **Criterio de aceptación:**
  - Antes de borrar: `grep -rn "calcular_descuento_viejo\|reporteViejoCSV\|exportar_txt\|MODO_DEBUG" src tests`
    solo encuentra las definiciones.
  - Después: el mismo `grep` → sin resultados. ruff 13 → 11. pytest verde.
- **Zonas de riesgo:** ninguna.

## Paso 3 — Persistencia con `with` en `almacen.py`

- **Qué cambia:** `open()` → `with open(...)` en `guardar_datos` y
  `cargar_datos`; `hayArchivo` → `hay_archivo` con `return os.path.exists(ruta)`;
  se actualiza la llamada en `main.py`. Diccionario de guardado como literal
  con el mismo orden de llaves (`inventario`, `ventas`, `contador`).
- **Se conserva a propósito (N15):** `except Exception` (no se restringe), el
  `clear()` antes de leer `d["inventario"]`/`d["ventas"]`, `d.get("contador", 0)`,
  y la mutación in situ de `INVENTARIO`/`VENTAS`.
- **Archivos:** `src/almacen.py`, `src/main.py`.
- **Por qué mejora:** el archivo siempre se cierra, aun con excepción; nombres PEP 8.
- **Criterio de aceptación:** ruff 11 → 7 (SIM115 ×2, N802, SIM103). Caracterización:
  archivo corrupto y binario → `False` + `"archivo corrupto"`; JSON sin
  `"ventas"` sigue lanzando `KeyError` con el inventario vaciado; JSON
  guardado idéntico byte a byte.
- **Zonas de riesgo:** **sí** — mutación in situ de `cargar_datos` y alcance del `except`.

## Paso 4 — Limpieza de `reportes.py`

- **Qué cambia:** `hacer_cosa` → `formatear_dinero` (misma salida
  `"$" + str(round(v, 2))`); constante `STOCK_MINIMO = 5` usada por
  `productos_stock_bajo` y `reporte_inventario`; `mas_vendidos` con
  `dict.get` y `sorted(..., key=..., reverse=True)` (estable, igual que la
  burbuja); `resumen_ventas` reutiliza `total_vendido()`; recorrer con
  `.values()`; nombres descriptivos en lugar de `aux`/`temp`/`temp2`/`s`/`t`.
- **Se conserva:** los reportes siguen imprimiendo **y** regresando el texto (N4).
- **Archivos:** `src/reportes.py`.
- **Por qué mejora:** sin duplicación del umbral ni de la suma; algoritmo O(n log n) legible.
- **Criterio de aceptación:** ruff sin cambios (7). Caracterización: texto exacto
  de `reporte_inventario` y `resumen_ventas`; empates en `mas_vendidos`
  conservan el orden de primera venta; `mas_vendidos()` sin argumento regresa 3.
- **Zonas de riesgo:** **sí** — formato de reportes (`$20.0`, doble espacio en
  `"  <-- STOCK BAJO"`) y orden de empates (no usar `sorted(...)[::-1]`).

## Paso 5 — Dividir `menu()` en `main.py`

- **Qué cambia:** una función por opción (`opcion_agregar_producto`,
  `opcion_registrar_venta`, …) y un diccionario de despacho
  `{"1": ..., "8": ...}`; la opción 8 indica salir. Nombres descriptivos en
  lugar de `c`, `n`, `p`, `s`, `v`, `t`, `cant`, `cli`.
- **Se conserva a propósito:** N6 (imprime "Datos cargados" aunque la carga
  falle), N19 (`int(pedir_numero(...))`, acepta `nan`/`inf`), N20 (`ARCHIVO`
  relativo al cwd). Todos los textos de `print`/`input` idénticos.
- **Archivos:** `src/main.py`.
- **Por qué mejora:** `menu` pasa de complejidad 17 a un bucle simple; cada opción se lee aislada.
- **Criterio de aceptación:** ruff 7 → 6 (C901 de `menu`). Caracterización:
  sesión completa del menú (entradas simuladas) produce la misma salida exacta.
- **Zonas de riesgo:** salida de consola (sin cobertura en los tests originales;
  la cubre solo la caracterización).

## Paso 6 — Extraer descuentos e IVA con constantes (`gestor.py`)

- **Qué cambia:** constantes con nombre (`UMBRAL_VOLUMEN_ALTO = 1000`,
  `TASA_VOLUMEN_ALTO = 0.10`, `UMBRAL_VOLUMEN_MEDIO = 500`,
  `TASA_VOLUMEN_MEDIO = 0.05`, `PREFIJO_VIP = "VIP"`, `MONTO_MINIMO_VIP = 200`,
  `TASA_VIP = 0.02`, `TASA_IVA = 0.16`) y funciones puras
  `descuento_por_volumen(subtotal)` y `descuento_vip(subtotal, descuento, cliente)`.
  `registrar_venta` usa ambas; `cotizar` solo la de volumen.
- **Reglas exactas a conservar:** umbrales de volumen con `>=`; VIP con `>`
  sobre `subtotal - descuento`; extra VIP = `subtotal * TASA_VIP` (sobre el
  bruto); `descuento` sin descuento es el entero `0`, no `0.0`;
  `impuesto = base * TASA_IVA` y `total = round(base + impuesto, 2)` en ese
  orden (nunca `base * 1.16` ni sumar campos redondeados); VIP con
  `cliente and cliente.startswith(PREFIJO_VIP)` (tolera `None` y `""`).
- **Archivos:** `src/gestor.py`.
- **Por qué mejora:** elimina la duplicación `registrar_venta`/`cotizar` y los números mágicos.
- **Criterio de aceptación:** ruff 6 → 1–2 (SIM102 ×3, SIM108; posiblemente
  C901). Caracterización: totales en los límites 499.99/500/999.99/1000,
  VIP con base 200 y 200.01, VIP con subtotal < 500, `"vip"` en minúsculas sin
  descuento, `descuento` de tipo `int` cuando es 0, `cotizar == registrar_venta`
  en una rejilla de precios/cantidades.
- **Zonas de riesgo:** **sí, la más alta** — redondeos (≈0.2 % de casos cambian
  con `base * 1.16`; ≈16.6 % si se suma desde campos redondeados).

## Paso 7 — Dividir `registrar_venta`

- **Qué cambia:** validación con salidas tempranas en una función auxiliar que
  regresa el mensaje de error (mismo orden: código vacío → no existe →
  cantidad inválida → stock insuficiente); armado del ticket en
  `armar_ticket(venta, descuento)`; diccionario de venta como literal con el
  mismo orden de llaves.
- **Se conserva:** `cotizar` mantiene su propia validación (N2: con código `""`
  deja `"producto no existe"`); la línea "Descuento" depende del descuento
  **sin redondear** (`> 0`); formato `str(...)` de los montos.
- **Archivos:** `src/gestor.py`.
- **Por qué mejora:** elimina la pirámide de `if/else` (N1) y separa cálculo de presentación (N3).
- **Criterio de aceptación:** ruff → 1 (solo N816). Caracterización: texto
  exacto del ticket con y sin descuento y con descuento solo VIP; cada mensaje
  de `ultimo_error`; venta fallida no altera stock ni folio.
- **Zonas de riesgo:** **sí** — formato del ticket y mensajes de error.

## Paso 8 — Estado compartido de `gestor.py`

- **Precondición (bloqueante):** `grep -rn "contadorVentas" tests/` debe
  regresar **vacío**. Si algún test lo referencia, el renombrado rompe el
  contrato con la suite (que no se puede modificar): **no se ejecuta** el
  renombrado y se replantea el alcance (p. ej., conservar el nombre y aceptar
  el N816, o consultar antes de continuar).
- **Qué cambia:** `contadorVentas` → `contador_ventas` en `gestor.py`
  (`reiniciar_sistema`, `registrar_venta`) y `almacen.py` (guardar y cargar);
  nombres descriptivos en `actualizar_stock`/`buscarProducto`; producto como
  literal (orden `codigo`, `nombre`, `precio`, `stock`); recorrer con `.values()`.
- **Se conserva:** nombres `agregarProducto`, `buscarProducto`, `INVENTARIO`,
  `VENTAS`, `ultimo_error`; mutación in situ (`clear()`) en `reiniciar_sistema`
  y `cargar_datos`; acceso siempre como `gestor.X` (nunca `from gestor import ...`);
  llave JSON `"contador"`; retornos `bool` reales y `list`.
- **Archivos:** `src/gestor.py`, `src/almacen.py`.
- **Por qué mejora:** nombres PEP 8 y consistentes en todo el estado global.
- **Criterio de aceptación:** ruff → **0**; `grep -rn contadorVentas src` sin
  resultados; el JSON guardado sigue usando `"contador"` y `datos_ejemplo.json`
  carga igual; el folio continúa tras recargar.
- **Zonas de riesgo:** **sí** — mutación in situ, nombres públicos, tipos de retorno.

## Paso 9 — Tests de caracterización (se ejecuta ANTES del Paso 1)

- **Qué cambia:** archivo nuevo `tests/test_caracterizacion.py`. No se modifica
  ningún test existente ni `tests/conftest.py` (su fixture `sistema_limpio`
  aplica automáticamente). Solo usa la API pública (`gestor`, `almacen`,
  `reportes`, `main.menu`, `main.pedir_numero`) para sobrevivir a las
  refactorizaciones; la consola se simula con `monkeypatch` sobre
  `builtins.input` + `capsys`, y el cwd con `monkeypatch.chdir(tmp_path)`.
- **Bugs que fija tal cual:**
  - **N6:** con un `datos_ejemplo.json` corrupto en el cwd, `menu()` imprime
    "Datos cargados de datos_ejemplo.json".
  - **N15:** archivo binario/UTF-8 inválido → `False` + `"archivo corrupto"`;
    JSON válido sin `"ventas"` → `KeyError` e `INVENTARIO` queda vacío; sin
    `"contador"` → el siguiente folio es 1.
  - **N19:** `pedir_numero` reintenta ante `"abc"` y acepta `"nan"`; cantidad
    `2.7` se trunca a 2; precio `nan` se acepta; `inf` en cantidad lanza `OverflowError`.
  - **N20:** `main.ARCHIVO == "datos_ejemplo.json"`; sin archivo en el cwd no
    se imprime "Datos cargados"; la opción 8 lo crea en el cwd.
- **Comportamiento sin red que también fija:** texto exacto del ticket y de
  ambos reportes, todos los mensajes de `ultimo_error` (incluida la diferencia
  `registrar_venta("")` vs `cotizar("")`), límites de descuento y VIP, tipo `int`
  del descuento 0, orden de empates en `mas_vendidos`, formato del JSON guardado.
- **Criterio de aceptación:** todos pasan contra el código original (`adb7fb1`)
  antes del Paso 1, y siguen pasando después de cada paso.
- **Zonas de riesgo:** cubre las cinco.
- **Nota:** el README y `CLAUDE.md` dicen "no modificar `tests/`". Agregar un
  archivo nuevo (sin tocar los existentes) es una decisión del autor; conviene
  justificarla en la bitácora.
