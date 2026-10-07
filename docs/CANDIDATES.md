# Evaluación inicial de repositorios — 7 de octubre de 2026

Esta es la preselección del implementador. Hermes CEO debe realizar su búsqueda, registrar decisiones y contratar desde su ejecución real. No se le atribuyen estas decisiones ni se simulan especialistas.

Datos completos: `candidates.json` (URL, autor, commit, archivo, fecha, licencia, estrellas, actividad, puntuaciones y límites) y `repository-checks.json` (releases, muestra de issues/PRs, tests y ejemplos). Las estrellas son una señal de adopción, no evidencia de corrección. Consultar issues no equivale a resolverlos; no se ejecutaron suites completas de candidatos no instalados.

Puntuación de 1 a 5; pesos: adecuación 30%, corrección/verificabilidad 25%, compatibilidad 20%, mantenimiento/procedencia 15%, adopción 5%, costo/complejidad 5%. Es un juicio técnico de selección, no un benchmark empírico. Las pruebas ejecutadas figuran en `VALIDATION.md`.

| Familia | Alternativas comparadas | Selección y razón |
|---|---|---|
| Roles y metodología financiera | Hermes skills oficiales; Anthropic financial-services; agency-agents Finance Tracker | Hermes como runtime y skills operativas. Metodología financiera Ares acotada, contrastada con DCF/3-state/audit-xls de Anthropic. Finance Tracker es más apto para finanzas internas; se descarta su lenguaje STRONG BUY y su memoria de cifras. |
| Fuentes regulatorias/XBRL | EdgarTools; Arelle; sec-edgar | Extractor local SEC companyfacts acotado, con rechazo de ambigüedades y cotejo original obligatorio. Los tres quedan candidatos del CEO para casos que requieran más cobertura. |
| PDF y tablas | pypdf; pdfplumber; PyMuPDF | pypdf + pdfplumber, utilizados por la skill oficial Hermes. PyMuPDF no se instala: no es necesario y agrega alcance/licencia AGPL. OCR queda explícitamente no habilitado. |
| Excel | Hermes xlsx/openpyxl; XlsxWriter; ClosedXML | openpyxl para lectura/edición/revisión y XlsxWriter para fórmulas/cachés. ClosedXML agrega .NET innecesario. Un cache no acredita recalculo de la fórmula. |
| Valuación/revisión | Anthropic DCF/audit-xls; FinanceToolkit; adaptación local Ares | Motor local Decimal con reinversión terminal explícita y revisor independiente float. FinanceToolkit es referencia y posible extensión; no se instala su stack/datos por defecto. |
| Informes/presentaciones | Hermes docx/powerpoint; skills Anthropic xlsx/pptx; generación local Python | Helpers oficiales Hermes con python-docx/python-pptx y prueba de apertura. No se importan herramientas exclusivas de Claude/Codex. |

## Archivos originales inspeccionados

- Hermes: `skills/research/grounded-citations/SKILL.md` y `skills/productivity/{pdf,xlsx,docx,powerpoint}/SKILL.md` en el commit del submódulo. Se instalan copias completas con sus scripts/licencias, sin modificar secretos ni instrucciones globales.
- [Anthropic financial-services](https://github.com/anthropics/financial-services/tree/574ed3624aebd0418c7e96cd101262f30210ab26): `plugins/agent-plugins/model-builder/skills/{dcf-model,3-statement-model,audit-xls}/SKILL.md`. La antigua URL financial-services-plugins redirige a este repositorio; se verificó la identidad mediante su ID de GitHub.
- [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit/blob/a232ddf84d4bb2da17e5385b7862873b6943c2a8/financetoolkit/models/intrinsic_model.py): FCFF/FCFE, descuento y métodos alternativos. No se copió su código.
- Los demás archivos exactos y commits están en `candidates.json`. Los refs de paquetes instalados quedan en `uv.lock`; los commits de evaluación pueden ser más recientes que la versión Python elegida.

## Adaptaciones y dependencias

No se copian los flujos de Office JS, MCP privado, `recalc.py` no suministrado ni confirmaciones paso a paso de Anthropic. El usuario ya autorizó decisiones rutinarias: se sustituyen por checkpoints y revisión del CEO. Se conserva la exigencia de fórmulas editables, escenarios y revisión, implementada con herramientas disponibles en Hermes. Las siete skills locales Ares son autoría local y no tienen respaldo comunitario atribuido.

pypdf no hace OCR. pdfplumber depende de pdfminer.six/pypdfium2; los resultados de tablas requieren cotejo visual. XlsxWriter no recalcula; openpyxl no es motor de cálculo. python-docx y python-pptx crean/abren formatos Office. El runtime Hermes usa su propio lock y Python 3.14. El paquete Ares tiene su entorno separado; nunca se instala un framework completo adicional.

Los accesos necesarios son archivos del volumen Ares, HTTP a Paperclip y lectura de fuentes públicas. No hay broker, correo, publicación pública ni proveedor de datos pago habilitado. EdgarTools requiere User-Agent/identificación SEC; el CEO no debe inventarla. Este cloud restringe dominios, y no se probó descarga de una empresa real.

## Hallazgos concretos del muestreo

EdgarTools reportaba problemas abiertos de precisión de valor par y pérdida de etiquetas de períodos al convertir tablas a Markdown; justifican cotejar originales aunque la API sea estructurada. XlsxWriter tenía un issue sobre comillas en formatos condicionales de texto; la plantilla Ares no usa esa función. Los repositorios de plantillas no prueban por sí solos capacidad de análisis. Issues que sean PRs se distinguen expresamente en el registro.
