---
name: independent-review
description: Revisar modelo y narrativa después del autor.
version: 1.0.0
license: MIT
---

# independent-review

Origen: adaptación local Ares, sin afirmar respaldo comunitario.

## Cuándo usar
Revisar modelo y narrativa después del autor.

## Entradas
Originales y versiones/hash de modelo/supuestos.

## Procedimiento
Contrastar cifras; recalcular mediante IndependentReviewer (fórmula separada). Revisar fórmulas/referencias/unidades/períodos; recalcular libro con motor de planilla. Cuestionar comparables, tasas y terminal. Buscar contradicciones. Registrar severidad/autor, devolver corrección y revalidar versión final.

## Herramientas
Python/ares, terminal, archivos, API Paperclip; web/regulador solo si accesible. Sin herramientas exclusivas de Codex. Las skills nativas Hermes se fijan por submódulo; nuevas instalaciones deben revisarse antes de activarse.

## Salidas
Hallazgos y evidencia con decisión de revisión analítica.

## Errores frecuentes
Corregir archivo del autor, aprobar trabajo propio, confundir código de verificación con ejecución real de un agente.

## Verificación
Error material introducido debe detectarse. assert_publishable exige IDs distintos, evidencia y ausencia de hallazgos materiales.
