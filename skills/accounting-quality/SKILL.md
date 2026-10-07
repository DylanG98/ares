---
name: accounting-quality
description: Normalizar estados, ratios y evaluar ganancias/caja.
version: 1.0.0
license: MIT
---

# accounting-quality

Origen: adaptación local Ares, sin afirmar respaldo comunitario.

## Cuándo usar
Normalizar estados, ratios y evaluar ganancias/caja.

## Entradas
Cinco años e intermedios, notas y fuentes.

## Procedimiento
Conciliar activos=pasivos+patrimonio y caja. Preservar reportado, puente por ajuste y explicación. Revisar SBC/dilución, no GAAP, deuda/leases, vencimientos, recompras y capex. Ratios con fórmula explícita; ROE/ROA con promedios. TTM anual+YTD actual−YTD comparable, sin mezclar períodos. Argentina: inflación/moneda homogénea y conversión explícitas.

## Herramientas
Python/ares, terminal, archivos, API Paperclip; web/regulador solo si accesible. Sin herramientas exclusivas de Codex. Las skills nativas Hermes se fijan por submódulo; nuevas instalaciones deben revisarse antes de activarse.

## Salidas
Históricos, puentes, ratios y hallazgos de calidad.

## Errores frecuentes
Anualizar YTD sin advertencia, mezclar nominal/real, tratar gastos recurrentes como extraordinarios.

## Verificación
Pruebas de balance/caja, comparación con notas, registro de faltantes como null.
