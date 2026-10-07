# Ares · Research y Valuación

Organización **independiente** para Paperclip + Hermes, con Docker, perfiles separados, trazabilidad y cálculos reproducibles. No toca la instalación ni el equipo de marketing existente. No conecta brokers ni ejecuta operaciones.

**Estado:** infraestructura y herramientas técnicas implementadas. La autenticación de ChatGPT se completa en tu Windows. Hermes CEO realiza la selección y contratación real de los cinco especialistas después de autenticarte; no se atribuyen decisiones ni ejecuciones a agentes que todavía no trabajaron. Consultá [la evidencia y los pendientes](docs/VALIDATION.md).

## Dónde vive cada cosa

El desarrollo y las pruebas se hicieron en `/workspace/ares`, en el Linux cloud de Codex. No se accedió a tu PC. El código se entrega en este repositorio; los datos operativos se crean **en la máquina donde ejecutes Docker**. Los volúmenes de cloud no se transfieren automáticamente a Windows. Ejecutar el arranque local crea tu propia instancia reproducible.

| Elemento | Destino |
|---|---|
| Panel nuevo | `http://127.0.0.1:3107` en la máquina de Docker |
| Paperclip anterior | No se lee ni modifica; puede seguir usando `3100` |
| Organización | Research y Valuación |
| Volúmenes nuevos | `ares-research_paperclip-data`, `ares-research_research-data` |
| Autenticación Hermes | `/data/hermes/auth.json` dentro del volumen; no se copia a perfiles |
| Perfiles | `/data/hermes/profiles/{ceo,research,accounting,business,valuation,review}` |
| Expedientes | `/data/dossiers/<identidad-y-corte>` |

## Arranque en Windows

Necesitás Git, Python 3.11+ y Docker Desktop **con contenedores Linux**. Recomendado: 4 CPU, 8 GB RAM y al menos 25 GB libres para descarga/build; más espacio si tu storage driver duplica capas. No hace falta activar Developer Mode ni dar privilegios de symlink de Windows.

```powershell
git clone --recurse-submodules https://github.com/DylanG98/ares.git
cd ares
.\scripts\start.ps1
```

El script genera `.env` una sola vez, construye/arranca Docker y registra la organización, el CEO y una tarea de constitución. Es idempotente: repetirlo conserva agentes y tareas. El panel usa autenticación: el email y contraseña **locales** están en `.env`; no los subas a GitHub. El puerto queda ligado a `127.0.0.1`, sin exposición pública.

Si PowerShell impide ejecutar scripts, usá los mismos comandos directamente, sin cambiar políticas globales:

```powershell
python scripts/setup.py
git submodule update --init --recursive
docker compose up -d --build --wait
docker compose run --rm operator bootstrap
```

## Conectar tu suscripción de ChatGPT

```powershell
docker compose exec --user node -e HERMES_HOME=/data/hermes paperclip hermes model
```

Elegí **OpenAI Codex / ChatGPT** en el flujo oficial de Hermes y completá el login en el navegador. No pegues tokens en el chat ni en archivos versionados. Este es un login nuevo dentro del volumen Ares, separado de tu Hermes anterior. Si ofrece flujo device-code, seguí ese flujo; no habilites un API key pago como alternativa automática.

Hermes muestra los modelos de tu conexión. Usá el identificador que efectivamente te permita seleccionar:

```powershell
docker compose run --rm operator activate --model IDENTIFICADOR_VERIFICADO
```

La activación comprueba el estado de autenticación con la API interna soportada de Hermes y el entorno del adaptador. Luego habilita la tarea del CEO en Paperclip. Eso **no** equivale a probar inferencia: los runs reales y sus entregables deben confirmar que el modelo funciona. No hay un modelo prefijado ni fallback a un proveedor pago.

El CEO recibe instrucciones para buscar candidatos en GitHub, decidir y contratar mediante `/agent-hires`, probar a cada especialista con datos sintéticos y registrar revisión independiente. Revisá esa tarea en Paperclip. Si hay una denegación de permisos, no se elude: queda bloqueada con la acción necesaria.

## Encargar la primera empresa

Cuando el CEO complete las pruebas reales, creá una tarea asignada a **Hermes CEO** con:

> Analizá [razón social], ticker [ticker], mercado [mercado], instrumento [acción/ADR], moneda [moneda], con fecha de corte [AAAA-MM-DD]. Entendé su negocio, revisá sus estados, calculá ratios y construí una valuación adversa/base/favorable con fuentes, Excel editable y revisión independiente. Identificá faltantes y no uses información publicada después del corte.

También podés copiar `templates/request.json`, completar todos los campos y enviarlo por CLI. Copiá el archivo dentro del volumen y ejecutá:

```powershell
docker compose cp solicitud.json paperclip:/data/solicitud.json
docker compose run --rm operator request /data/solicitud.json
```

La CLI exige que la constitución del equipo esté terminada. El CEO ejecuta `ares plan --case <case_id> --parent <issue_id>` para registrar las etapas/dependencias en Paperclip. No existe un scheduler paralelo en Ares.

## Verificar, parar y conservar datos

```powershell
docker compose run --rm operator doctor
docker compose run --rm operator smoke --output /data/technical-tests
docker compose logs --tail 100 paperclip
docker compose stop
```

`smoke` prueba software con una empresa ficticia, sin llamadas a modelos. Para recuperar entregables:

```powershell
docker compose cp paperclip:/data/technical-tests ./artifacts
```

`docker compose down` conserva volúmenes. **No usar `down -v`** si querés conservar trabajo. Para backup consistente, asegurate de que no haya tareas activas, detené **solo este proyecto**, ejecutá `docker compose cp paperclip:/data ./backups/research-data` y `docker compose cp paperclip:/paperclip ./backups/paperclip-data`, y volvé a arrancar. Guardá también `.env` de forma privada. Ver [operación y recuperación](docs/OPERATIONS.md).

## Entregables y arquitectura

- [Diseño y aislamiento](docs/ARCHITECTURE.md), [diagnóstico](docs/DIAGNOSIS.md), [matriz de capacidades](docs/CAPABILITIES.md).
- [Repositorios evaluados](docs/CANDIDATES.md), [registro estructurado](docs/candidates.json), [versiones fijadas](config/upstream.lock.json).
- [Roles](agents/), [política común](agents/POLICY.md), [skills propias](skills/), [plantillas](templates/).
- [Ejemplo sintético descargable](templates/synthetic-example/), [validación](docs/VALIDATION.md), [código Python](src/ares_research/), [pruebas](tests/).

El motor DCF suministrado es una **plantilla industrial FCFF** con terminal por reinversión g/ROIC; no pretende cubrir automáticamente bancos, seguros, SOTP ni todos los modelos de tres estados. El modelador debe adaptar y validar el método para la empresa indicada. Missing ≠ zero. Los originales quedan identificados por hash; el revisor tiene código de recálculo separado.

## Desarrollo

```bash
uv sync --frozen --group dev
uv run ruff check src tests scripts
uv run pytest -q
uv run ares smoke --output artifacts/synthetic
```

Paperclip: última release estable publicada al diagnóstico, fijada por commit y digest. Hermes: código oficial fijado por commit. No actualizar submódulos ni locks automáticamente. Las dependencias de ambos viven en entornos separados. En Codex cloud se usa el overlay opcional `docker/compose.cloud.yaml` para conservar CA/proxy; no lo uses en Windows.
