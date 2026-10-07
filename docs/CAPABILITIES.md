# Matriz de capacidades

Especificación inicial implementada. El CEO debe confirmar o ajustar esta matriz con decisiones y runs propios. Tener una skill instalada no acredita competencia del agente.

| Responsable | Skills y herramientas | Prueba técnica disponible | Aceptación del agente tras login |
|---|---|---|---|
| Hermes CEO | research-governance, fuentes/citas, docx, powerpoint; API Paperclip | Bootstrap, idempotencia, DOCX/PPTX generados y abiertos | Buscar GitHub, decidir contrataciones, delegar, resolver dependencias, integrar informe |
| Research y Fuentes | source-evidence, grounded-citations, PDF, xbrl-validation; pypdf/pdfplumber | PDF con ingresos conocidos; companyfacts sintético con períodos ambiguos rechazados | Identificar fuente/página, guardar original, comprobar la extracción con el documento |
| Análisis Contable | accounting-quality, fuentes, PDF, xlsx, XBRL | Cinco años sintéticos, conciliación patrimonial y ratios con ausentes | Normalizar cifras reportadas/ajustadas, notas, TTM y puentes; explicar faltantes |
| Negocio y Perspectivas | business-outlook, fuentes y citas | Tres narrativas sintéticas vinculadas a supuestos | Investigar motores y riesgos; distinguir evidencia de hipótesis, justificar escenarios |
| Modelado y Valuación | financial-model, accounting-quality, xlsx; Decimal/XlsxWriter/LibreOffice | FCFF conocido, puente EV/equity/ADR, escenarios y sensibilidad, Excel editable | Elegir método apropiado, fórmulas recalculadas, fuentes, controles y supuestos explícitos |
| Revisión Independiente | independent-review, fuentes, PDF/xlsx; motor separado/openpyxl | Detectar resultado alterado y bloquear hallazgo material | Cotejar originales, descubrir error sin conocer ubicación, cuestionar tesis y emitir hallazgos |

Se incorporan siete skills locales y cinco familias de skills oficiales Hermes, distribuidas por rol. El adaptador oficial añade sus propias skills de coordinación Paperclip. Los archivos locales documentan entradas, salidas, procedimiento, herramientas, errores y controles.

Límites: sin OCR habilitado; no se asume acceso a APIs de búsqueda pagas ni proveedores privados; XBRL soporta extracción acotada SEC companyfacts, no toda la taxonomía de un filing; DCF industrial no reemplaza métodos bancarios/seguros/SOTP. DOCX/PPTX se verifican por apertura de formato; la revisión visual final del informe corresponde al CEO. Las restricciones de red y autenticación se deben diagnosticar por tarea.

La librería PDF/Excel/Office de Ares está en su entorno Python separado. Usar `ares`, `/opt/ares/.venv/bin/python` o los procedimientos locales; no instalar paquetes en Hermes para resolver un import faltante de Ares.
