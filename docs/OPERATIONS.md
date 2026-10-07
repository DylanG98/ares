# Operación y recuperación

## Ciclo normal

`docker compose up -d --wait` inicia únicamente Ares. `docker compose run --rm operator bootstrap` reconcilia la compañía marcada, CEO y tarea de constitución. No reemplaza perfiles ni `.env` existentes. `doctor` consulta identidad, agentes, autenticación, runs exitosos y estado de constitución; no prueba la calidad de entregables por el solo estado de un run.

Después de `hermes model` y `operator activate --model ...`, Paperclip inicia la tarea del CEO. Las tareas dependientes se crean bloqueadas; el CEO verifica entregables y habilita la siguiente etapa usando Paperclip. Si se recibe una denegación, no usar otra identidad para ocultarla: registrar el bloqueo y la autorización necesaria.

Perfiles separados, 40 turnos/run, timeout de 900 segundos, 15 segundos de gracia, una ejecución simultánea por agente, persistencia/checkpoints y ningún timer. El CEO mantiene como política un máximo de dos especialistas a la vez; no hay semáforo global adicional. El timeout es una interrupción, no prueba de que no se escribió nada.

## Inspección y recuperación

1. Consultar tarea, runs y logs en Paperclip; leer handoff/checkpoint y artefactos persistidos.
2. Comparar estado remoto y marcadores antes de repetir una mutación. La CLI no reintenta POST automáticamente.
3. Si quedó un lock en `/data/state` o en el expediente, confirmar primero que no hay operación en curso. Respaldar el lock y quitar únicamente ese lock residual; no borrar el expediente ni la base.
4. Volver a lanzar la misma tarea/identidad una vez resuelto el error. Los comandos bootstrap/request/plan/hire reconcilian IDs y marcadores.
5. Si hay agentes/tareas duplicados o una compañía homónima sin la marca Ares, la CLI se detiene. Investigar con el operador; nunca adoptar/eliminar automáticamente.

Credenciales vencidas: repetir el login oficial `docker compose exec --user node -e HERMES_HOME=/data/hermes paperclip hermes model`. No copiar auth.json a perfiles, imprimirlo, versionarlo ni pegarlo en conversaciones. Falta de cuota/modelo: bloquear y elegir solo un modelo efectivamente disponible; no activar otro proveedor pago.

## Artefactos y modelo

`ares smoke --output /data/technical-tests` genera originales sintéticos, expediente, inputs.json, modelo.xlsx, DOCX, PPTX y acceptance.json. Su ejecución es software determinista, no constituye trabajo de especialistas.

```sh
ares recalculate /data/technical-tests/synthetic-model.xlsx --output /data/technical-tests/recalculated/synthetic-model.xlsx
ares review --inputs /data/technical-tests/inputs.json --workbook /data/technical-tests/recalculated/synthetic-model.xlsx
```

`ares review` compara resultados con un cálculo separado y examina errores/referencias/cachés. No sustituye el cotejo original, la revisión económica ni la firma del revisor. `ares model` permite construir otro libro a partir de ValuationInputs JSON, históricos y fuentes explícitos. Todos los cálculos deben conservar su versión e inputs; nunca presentar el ejemplo sintético como valuación de una empresa real.

## Backup y restauración

Crear `backups` y detener Ares cuando no haya runs activos con `docker compose stop`. Conservar los contenedores detenidos durante la copia:

```sh
docker compose cp paperclip:/data ./backups/research-data
docker compose cp paperclip:/paperclip ./backups/paperclip-data
```

Conservar también `.env` por un medio privado. Estos backups contienen autenticación y documentos: no subirlos al repositorio. Reiniciar con `docker compose start`.

Restaurar únicamente con los servicios detenidos, en un proyecto Ares nuevo o después de respaldar el destino. Copiar el contenido de cada backup al volumen correspondiente y restablecer propietario UID/GID 1000; verificar versión, health, IDs y artefactos antes de activar agentes. No se ejecutó un simulacro completo de restauración con datos reales en esta implementación.

No ejecutar `docker compose down -v` ni una limpieza global Docker para resolver un problema de Ares. No modificar el directorio del Paperclip de marketing. Para actualizar, respaldar primero, revisar cambios upstream y repetir controles; no usar `git submodule update --remote` sin una decisión explícita.
