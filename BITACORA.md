# Bitácora de refactorización

**Nombre:**
**Matrícula:**
**Fecha:** 2026-10-06

Registra aquí **cada refactorización** que realices con Claude Code. Copia el
prompt tal cual lo escribiste (o un resumen fiel si fue una conversación larga),
describe el cambio que se aplicó al código y justifica por qué mejora la calidad.
Después de cada cambio ejecuta `pytest` y anota el resultado.

## Fase 0: Preparación y configuración del proyecto

Pasos previos a las refactorizaciones (no cuentan dentro de las 5 requeridas).

| #   | Prompt usado | Cambio realizado | Justificación | Tests OK |
|-----|--------------|------------------|---------------|----------|
| 0.1 | *(manual, sin IA)* | Se configuró el entorno con `uv` y se guardaron las líneas base: `docs/linea_base_tests.txt` (20 tests pasando) y `docs/linea_base_linter.txt` (20 errores de ruff). Commit `8ac03e8`. | Tener un punto de comparación para verificar que ninguna refactorización altere el comportamiento y medir el avance del linter. | ✅ 20/20 |
| 0.2 | `/init` — "Please analyze this codebase and create a CLAUDE.md file…" | Claude analizó `src/`, `tests/`, `pyproject.toml` y el README, y generó `CLAUDE.md` con: comandos (`uv run pytest`, `uv run ruff check src`, cómo correr un solo test), reglas del reto (no tocar `tests/` ni `pyproject.toml`, conservar `agregarProducto`/`buscarProducto`), arquitectura (estado global en `gestor.py`), reglas de negocio (descuentos, VIP, IVA 16 %, stock bajo < 5) y *code smells* conocidos. | Dar a Claude el contexto y las restricciones del proyecto desde el inicio para que sus propuestas respeten las reglas del reto. | ✅ 20/20 |
| 0.3 | "genera una copia del archivo CLAUDE.md en /tmp/claude_md_init.txt" | Se guardó una copia de la versión inicial de `CLAUDE.md` generada por `/init`. | Conservar la versión original para comparar contra los ajustes posteriores. | N/A |
| 0.4 | "ajuste mi rama, ya que esta mal nombrada, tiene que ir de refactorizacion a main y yo estoy en preparación, realiza los ajustes" | No existía la rama `main`. Se creó `main` desde la línea base (`8ac03e8`), se renombró `preparacion` → `refactorizacion`, se subieron ambas a GitHub, se configuró `main` como rama por defecto y se eliminó `preparacion` del remoto. | El reto pide entregar mediante PR de `refactorizacion` → `main`. | N/A |
| 0.5 | "Mueve mi archivo de bitacora que esta en la carpeta docs hacia la raíz y actualiza la referencia en el archivo CLAUDE.md. Tambien genera el archivo .claudeignore" | `docs/bitacora.md` → `BITACORA.md` (con `git mv`, conservando el historial); se actualizó la ruta en `CLAUDE.md`; se creó `.claudeignore` excluyendo `.venv/`, cachés (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`), `.DS_Store` y `src/datos_ejemplo.json` (datos generados por el menú). | El README pide `BITACORA.md` en la raíz. El `.claudeignore` evita que Claude lea archivos irrelevantes o generados. | N/A |
| 0.6 | "Remueve el archivo uv.lock del claudeignore y crea el archivo .claude/settings.json…" | Se quitó `uv.lock` de `.claudeignore` y se creó `.claude/settings.json` con reglas `deny` de lectura para `.env`, `.env.*`, `.venv/**`, `__pycache__/**`, `.pytest_cache/**` y `.ruff_cache/**`. | `uv.lock` describe el entorno y conviene que sea legible. `settings.json` refuerza con permisos lo que Claude no debe leer (posibles secretos y archivos generados). | N/A |

## Fase 1: Refactorizaciones

| #  | Prompt usado | Cambio realizado | Justificación | Tests OK |
|----|--------------|------------------|---------------|----------|
| 1  |              |                  |               |          |
| 2  |              |                  |               |          |
| 3  |              |                  |               |          |
| 4  |              |                  |               |          |
| 5  |              |                  |               |          |

> Agrega más filas si realizas más de 5 refactorizaciones.

## Notas / Observaciones

- **Sobre `.claudeignore`:** El reto pide `.claudeignore` y lo incluyo. No aparece
  en la documentación oficial de Claude Code, así que lo trato como señal de
  intención y no como garantía. La exclusión efectiva la hacen las reglas
  `permissions.deny` de `.claude/settings.json`, que el cliente aplica
  independientemente de lo que decida el modelo.

## Reflexión final (10-15 líneas)

Responde: ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?
¿Qué propuso la IA que tú no habías notado? ¿En qué casos tuviste que corregir
o rechazar sus sugerencias? ¿Qué aprendiste sobre refactorizar con apoyo de IA?

*(Escribe aquí tu reflexión)*
