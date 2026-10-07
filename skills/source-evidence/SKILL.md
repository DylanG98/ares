---
name: source-evidence
description: Recolectar o citar cifras materiales.
version: 1.0.0
license: MIT
---

# source-evidence

Origen: adaptación local Ares, sin afirmar respaldo comunitario.

## Cuándo usar
Recolectar o citar cifras materiales.

## Entradas
Identidad, corte y documentos.

## Procedimiento
Priorizar regulador/emisor. Preservar original con SHA256 en Dossier.add_source; registrar publicación y consulta. Extraer FinancialFact con localizador; comprobar original. Citas por case_id, no ledger global.

## Herramientas
Python/ares, terminal, archivos, API Paperclip; web/regulador solo si accesible. Sin herramientas exclusivas de Codex. Las skills nativas Hermes se fijan por submódulo; nuevas instalaciones deben revisarse antes de activarse.

## Salidas
Registro de fuentes y hechos trazables.

## Errores frecuentes
Usar conocimiento posterior al corte, ticker ambiguo, cifra ausente como cero, PDF escaneado sin OCR.

## Verificación
Hash original, fecha pública <= corte, entidad/unidad/período; Dossier.validate_fact.
