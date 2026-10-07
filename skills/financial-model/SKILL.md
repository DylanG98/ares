---
name: financial-model
description: Proyectar y valuar después de normalizar.
version: 1.0.0
license: MIT
---

# financial-model

Origen: adaptación local Ares, sin afirmar respaldo comunitario.

## Cuándo usar
Proyectar y valuar después de normalizar.

## Entradas
ValuationInputs completos, fuentes y narrativas.

## Procedimiento
Elegir método sectorial. FCFF industrial con DcfModel solo si corresponde; terminal usa reinversión g/ROIC. Documentar tasas/moneda/base, equity bridge, leases/ADR/dilución. Generar FinancialWorkbook; recalcular en Excel o LibreOffice y contrastar resultados. Para bancos/seguros diseñar modelo sectorial revisable; no forzar FCFF.

## Herramientas
Python/ares, terminal, archivos, API Paperclip; web/regulador solo si accesible. Sin herramientas exclusivas de Codex. Las skills nativas Hermes se fijan por submódulo; nuevas instalaciones deben revisarse antes de activarse.

## Salidas
JSON, scripts, Excel con ocho hojas, sensibilidades y supuestos.

## Errores frecuentes
g>=WACC, doble conteo leases, unidades inconsistentes, terminal sin reinversión, caches tratados como fórmulas calculadas.

## Verificación
ares model; reviewer independiente; recálculo de libro; no publicar si controles materiales fallan.
