# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto

Reto académico de refactorización: una app de consola en Python (inventario y ventas de la tienda "La Esquina") que **funciona correctamente pero está mal escrita a propósito**. El objetivo es mejorar la calidad del código en `src/` **sin cambiar su comportamiento observable**. El código, los comentarios y la documentación están en español; mantén ese idioma.

## Comandos

El entorno se gestiona con `uv` (`.venv/` ya creado; dependencias en `requirements.txt`: pytest y ruff).

```bash
uv run pytest                                   # suite completa (20 tests, deben pasar todos)
uv run pytest tests/test_gestor.py              # un archivo
uv run pytest tests/test_gestor.py::test_actualizar_stock_suma_y_resta   # un test
uv run ruff check src                           # linter; meta final: 0 errores
uv run ruff check src --fix                     # solo corrige los triviales
cd src && uv run python main.py                 # menú interactivo (usa datos_ejemplo.json relativo al cwd)
```

Líneas base registradas antes de refactorizar: `docs/linea_base_tests.txt` (20 passed) y `docs/linea_base_linter.txt` (20 errores de ruff).

## Reglas obligatorias

- **No modificar nada en `tests/` ni `pyproject.toml`.** Si un test falla, el error está en la refactorización, no en el test.
- Ejecutar `pytest` y `ruff check src` **después de cada refactorización**.
- El comportamiento observable debe quedar idéntico: mensajes de `ultimo_error`, valores de retorno (`True`/`False`/`None`), formato del ticket y de los reportes, redondeos, estructura del JSON persistido (`inventario`, `ventas`, `contador`).
- `agregarProducto` y `buscarProducto` **conservan su nombre** (los usan los tests; están en `ignore-names` de ruff). Cualquier otro nombre camelCase sí debe pasar a snake_case.
- Una refactorización por commit (commits atómicos). Entrega vía PR de la rama `refactorizacion` → `main`.
- Cada refactorización se documenta en la bitácora (`BITACORA.md` en la raíz, basada en `docs/BITACORA_TEMPLATE.md`): prompt usado, cambio, justificación y resultado de tests.

## Arquitectura

Módulos planos en `src/` que se importan entre sí por nombre (`import gestor`), sin paquete. `tests/conftest.py` agrega `src/` al `sys.path` y llama `gestor.reiniciar_sistema()` antes y después de cada test.

- **`gestor.py`** — dueño del **estado global mutable**: `INVENTARIO` (dict código → dict producto), `VENTAS` (lista de dicts de venta), `contadorVentas` (folio), `ultimo_error` (mensaje del último fallo). Las funciones reportan errores devolviendo `False`/`None` y escribiendo en `ultimo_error`, que `main.py` imprime.
- **`almacen.py`** y **`reportes.py`** leen/escriben directamente el estado de `gestor` (`gestor.INVENTARIO`, `gestor.contadorVentas`, etc.). `cargar_datos` muta `INVENTARIO`/`VENTAS` **in situ** (`clear()` + reinsertar) en vez de reasignarlos, para que las referencias importadas sigan siendo válidas; al refactorizar, conserva esa semántica (los tests acceden a `gestor.INVENTARIO`/`gestor.VENTAS`). Si renombras `contadorVentas`, actualiza también `almacen.py`.
- **`main.py`** — solo E/S: menú `input()`/`print()` que delega en los otros módulos.

Reglas de negocio (hoy como números mágicos, duplicadas entre `registrar_venta` y `cotizar`):
- Descuento por volumen sobre el subtotal: 10% si ≥ 1000, 5% si ≥ 500.
- Extra VIP: cliente cuyo código empieza con `"VIP"` recibe +2% del subtotal si `subtotal - descuento > 200`. `cotizar` **no** aplica VIP.
- IVA 16% sobre la base (subtotal − descuento). Total redondeado a 2 decimales.
- Stock bajo: `stock < 5` (usado en `productos_stock_bajo` y `reporte_inventario`).

Code smells conocidos (los que reporta ruff): `registrar_venta` y `menu` exceden complejidad 10; `if` anidados; `open()` sin `with`; nombres camelCase (`contadorVentas`, `hayArchivo`, `reporteViejoCSV`); import `os` sin usar; cabeceras `# -*- coding -*-` innecesarias. Otros no detectados por ruff: nombres crípticos (`aux`, `temp2`, `hacer_cosa`), código muerto (`calcular_descuento_viejo`, `reporteViejoCSV`, `exportar_txt` comentado, `MODO_DEBUG`), burbuja manual en `mas_vendidos`. Antes de borrar código "muerto", confirma con `grep` que ni `src/` ni `tests/` lo usan.
