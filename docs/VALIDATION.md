# Validación — 2026-10-07

**Infraestructura comprobada; organización multiagente todavía no operativa.** ChatGPT no está autenticado en este entorno. El usuario eligió completar el login en Windows. No se verificaron modelos disponibles, llamadas reales, contrataciones del CEO ni análisis de una empresa real.

## Evidencia ejecutada

| Comprobación | Resultado y alcance |
|---|---|
| Ruff y pytest | 26 pruebas aprobadas en Python 3.12. Fuentes/corte/hash, ausentes, identidad, balances incompletos/descuadrados bloqueados, DCF conocido, revisión, bootstrap, auth, DAG y recuperación ante respuesta perdida |
| Docker/Paperclip | Servidor real, usuario node, PostgreSQL incorporado, migraciones aplicadas, API health OK, modo authenticated/private, puerto host solo 127.0.0.1:3107 |
| Alta oficial | Sign-up/sign-in y `/bootstrap/claim`, creación de una compañía independiente, Hermes CEO y tarea en backlog |
| Repetición bootstrap | Dos invocaciones consecutivas conservan IDs, un agente y una tarea; no duplican registros |
| Perfiles | Seis directorios distintos con 5/4/5/3/3/4 skills respectivamente, comandos legibles por node |
| Hermes | CLI ejecutable, Python 3.14.8, SDK 2.24.0. Reporta `vunknown (2026.9.24)` al empaquetarse sin .git; el commit fijado es la referencia de versión |
| Adaptador oficial | Test-environment ejecutado por Paperclip; CLI/modelo configurado detectados. Advertencia `hermes_no_api_keys`; no acredita OAuth ni inferencia |
| PDF | Extracción de ingresos sintéticos 1000 y tabla de dos ejercicios contra contenido conocido |
| XBRL | Fixture companyfacts; concepto/unidad/período/corte; ambigüedad rechazada; original_verified sigue falso hasta cotejo documental |
| DCF | Perpetuidad conocida EV 1500 y puente ADR 27,10; escenarios con implementación independiente |
| Excel | Ocho hojas, fórmulas editables/cachés inspeccionados; **LibreOffice 25.2.3.2 recalculó el archivo** y los resultados coinciden con el revisor independiente |
| Error deliberado | Valor base alterado +2 detectado como material; publicación bloqueada por el control de revisión |
| DOCX/PPTX | Archivos sintéticos generados y reabiertos por las librerías; no se afirma revisión visual humana |
| DAG/reanudación | Mock de API con respuesta perdida después de escritura; seis etapas únicas, dependencias y revisor distinto. Handoffs reales entre modelos pendientes |

Registros: [integración Paperclip](evidence/paperclip-integration.json), [doctor](evidence/doctor.json), [prueba financiera](evidence/financial-technical.json). Los IDs pertenecen al entorno cloud de prueba, no a la futura instancia Windows. No contienen secretos. El aviso de backup de la instancia nueva indica que todavía no se ejecutó su primer backup programado.

## Docker y alcance de reproducibilidad

Se construyó la base de la imagen con fuentes/locks fijados y se ejecutó la integración en Docker. El driver `vfs` de Codex y su disco limitado agotaron espacio al duplicar capas; se compactó exclusivamente la imagen Ares de prueba. Las correcciones finales de permisos, configuración de origen, código y LibreOffice se aplicaron en ese contenedor y en Dockerfile/Compose. **No se repitió un build limpio completo del Dockerfile final ni se ejecutó Docker Desktop en Windows.** Ese build y el login local son parte de la puesta en marcha pendiente; no se distribuye la imagen temporal compactada como artefacto de producción.

Las pruebas unitarias usan mocks solo para comportamiento del cliente, permisos y recuperación. La evidencia de alta/health/adaptador proviene de Paperclip real. Las herramientas numéricas se ejecutaron realmente, sin modelo. Ningún fixture, mock o cálculo determinista se presenta como trabajo de agentes.

## Pendientes para aceptación operativa

1. Clonar y construir en Docker Desktop Linux en Windows; verificar `doctor` y acceso al panel.
2. Login oficial Hermes con la suscripción ChatGPT; comprobar un modelo habilitado y activarlo.
3. Hermes CEO debe ejecutar su búsqueda/decisiones GitHub y contratar los cinco especialistas desde su identidad.
4. Probar runs reales de cada rol, acceso a fuentes/skills, artefactos, handoffs/dependencias y recuperación; revisor debe detectar un error sin conocer dónde se introdujo.
5. CEO adjunta evidencia/run IDs y consumo disponible; solo entonces cierra la tarea de constitución. Tokens/costo no medidos quedan como no disponibles.
6. Usuario indica la primera empresa, instrumento, mercado, moneda y corte. No se eligió ninguna empresa real.

`doctor.operational` requiere autenticación, seis roles, runs exitosos y constitución terminada. Su estado no sustituye revisar la evidencia de calidad adjunta a esa tarea.
