---
name: xbrl-validation
description: Usar hechos XBRL de estados regulatorios.
version: 1.0.0
license: MIT
---

# xbrl-validation

Origen: adaptación local Ares, sin afirmar respaldo comunitario.

## Cuándo usar
Usar hechos XBRL de estados regulatorios.

## Entradas
Documento original, taxonomy concept, contextRef/unitRef, período y consolidación.

## Procedimiento
Inspeccionar facts JSON/instance y contextos. Comparar conceptos extensiones con etiquetas y notas. Seleccionar unidades/escalas; distinguir instant/duration y anual/YTD/trimestre, restatements, segmentos. Confirmar cada cifra material en documento antes de original_verified=true.

## Herramientas
Python/ares, terminal, archivos, API Paperclip; web/regulador solo si accesible. Sin herramientas exclusivas de Codex. Las skills nativas Hermes se fijan por submódulo; nuevas instalaciones deben revisarse antes de activarse.

## Salidas
Hechos extraídos más evidencia de cotejo y discrepancias.

## Errores frecuentes
Elegir automáticamente primer tag, mezclar USD/millones, tomar frame como período contable.

## Verificación
ares extract-xbrl rechaza ambigüedad de unidad/período y deja hechos NO validados. Revisión humana/agente contra original obligatoria.
