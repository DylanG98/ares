"""Editable formulas with initial caches; cached values are not formula verification."""

from decimal import Decimal
from pathlib import Path

import xlsxwriter

from .domain import ValuationInputs
from .finance import DcfModel


class FinancialWorkbook:
    SHEETS = (
        "Fuentes",
        "Historicos",
        "Ajustes",
        "Supuestos",
        "Proyecciones",
        "Valuacion",
        "Sensibilidades",
        "Controles",
    )

    def write(
        self,
        path: Path,
        inputs: ValuationInputs,
        historical: list[dict],
        sources: list[dict],
        *,
        synthetic: bool,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with xlsxwriter.Workbook(
            path, {"strings_to_formulas": False, "strings_to_urls": False}
        ) as book:
            book.set_calc_mode("auto")
            header = book.add_format({"bold": True, "bg_color": "#17334D", "font_color": "white"})
            num = book.add_format({"num_format": "#,##0.00;[Red](#,##0.00)"})
            pct = book.add_format({"num_format": "0.00%"})
            sheets = {name: book.add_worksheet(name) for name in self.SHEETS}
            for sheet in sheets.values():
                sheet.set_column(0, 0, 26)
                sheet.set_column(1, 18, 18)
                sheet.freeze_panes(2, 1)
                sheet.write(
                    0,
                    0,
                    "SINTÉTICO — NO ES UNA INVERSIÓN"
                    if synthetic
                    else "BORRADOR — requiere revisión independiente",
                )

            def table(name, columns, rows):
                sheets[name].write_row(1, 0, columns, header)
                for i, row in enumerate(rows, 2):
                    sheets[name].write_row(i, 0, row)

            source_keys = [
                "source_id",
                "url",
                "title",
                "published_on",
                "retrieved_on",
                "sha256",
                "locator",
            ]
            table(
                "Fuentes", source_keys, [[str(s.get(k, "")) for k in source_keys] for s in sources]
            )
            history_keys = [
                "year",
                "revenue",
                "ebit",
                "net_income",
                "cfo",
                "capex",
                "assets",
                "liabilities",
                "equity",
                "source_id",
            ]
            table(
                "Historicos",
                history_keys,
                [[row.get(k) for k in history_keys] for row in historical],
            )
            table(
                "Ajustes",
                ["Concepto", "Reportado", "Ajuste", "Normalizado", "Motivo", "Fuente"],
                [
                    [
                        "Ingresos último año",
                        float(inputs.revenue),
                        0,
                        None,
                        "Sin ajustes; documentar cada ajuste real",
                        inputs.source_ids[0],
                    ]
                ],
            )
            sheets["Ajustes"].write_formula("D3", "=B3+C3", num, float(inputs.revenue))
            a = sheets["Supuestos"]
            a.write_row(
                1,
                0,
                [
                    "Escenario",
                    "Margen EBIT",
                    "Impuesto",
                    "D&A/ventas",
                    "Capex/ventas",
                    "CT/ventas",
                    "WACC",
                    "g terminal",
                    "ROIC terminal",
                    "Narrativa",
                ],
                header,
            )
            for i, s in enumerate(inputs.scenarios, 2):
                a.write(i, 0, s.name)
                for col, value in enumerate(
                    [
                        s.ebit_margin,
                        s.tax_rate,
                        s.da_to_sales,
                        s.capex_to_sales,
                        s.nwc_to_sales,
                        s.wacc,
                        s.terminal_growth,
                        s.terminal_roic,
                    ],
                    1,
                ):
                    a.write_number(i, col, float(value), pct)
                a.write(i, 9, s.narrative)
                for j, growth in enumerate(s.revenue_growth, 10):
                    a.write(1, j, f"Crecimiento año {j - 9}", header)
                    a.write_number(i, j, float(growth), pct)
            fields = [
                ("Moneda", inputs.currency),
                ("Base flujos", inputs.basis),
                ("Base tasas", inputs.rate_basis),
                ("Ingresos iniciales", float(inputs.revenue)),
                ("Deuda", float(inputs.debt)),
                ("Caja", float(inputs.cash)),
                ("Activos no operativos", float(inputs.non_operating_assets)),
                ("Minorías", float(inputs.minority_interest)),
                ("Acciones diluidas", float(inputs.diluted_shares)),
                ("Acciones/instrumento", float(inputs.shares_per_instrument)),
                ("Pasivos arrendamientos", float(inputs.lease_liabilities)),
                ("Tratamiento leases", inputs.lease_treatment),
            ]
            for i, row in enumerate(fields, 7):
                a.write_row(i, 0, row)
            p = sheets["Proyecciones"]
            p.write_row(
                1,
                0,
                [
                    "Escenario",
                    "Año",
                    "Ingresos",
                    "EBIT",
                    "NOPAT",
                    "D&A",
                    "Capex",
                    "Delta CT",
                    "FCFF",
                    "VP",
                ],
                header,
            )
            v = sheets["Valuacion"]
            v.write_row(
                1,
                0,
                [
                    "Escenario",
                    "FCFF terminal",
                    "Valor terminal",
                    "VP terminal",
                    "EV",
                    "Equity",
                    "Por acción",
                    "Por instrumento",
                    "Peso terminal",
                ],
                header,
            )
            engine, ranges, cursor = DcfModel(inputs), {}, 2
            for si, scenario in enumerate(inputs.scenarios):
                result = engine.calculate(scenario)
                ar, start = si + 3, cursor + 1
                for j, projection in enumerate(result.projections):
                    r = cursor + 1
                    gc = xlsxwriter.utility.xl_col_to_name(j + 10)
                    prior = "Supuestos!$B$11" if j == 0 else f"C{r - 1}"
                    p.write_row(cursor, 0, [scenario.name, projection.year])
                    formulas = [
                        (f"={prior}*(1+Supuestos!{gc}{ar})", projection.revenue),
                        (f"=C{r}*Supuestos!B{ar}", projection.ebit),
                        (f"=D{r}*(1-Supuestos!C{ar})", projection.nopat),
                        (f"=C{r}*Supuestos!D{ar}", projection.depreciation),
                        (f"=C{r}*Supuestos!E{ar}", projection.capex),
                        (f"=(C{r}-{prior})*Supuestos!F{ar}", projection.delta_nwc),
                        (f"=E{r}+F{r}-G{r}-H{r}", projection.fcff),
                        (f"=I{r}/(1+Supuestos!G{ar})^B{r}", projection.present_value),
                    ]
                    for col, (formula, cache) in enumerate(formulas, 2):
                        p.write_formula(cursor, col, formula, num, float(cache))
                    cursor += 1
                end, vr = cursor, si + 3
                ranges[scenario.name] = (start, end, ar)
                v.write(si + 2, 0, scenario.name)
                formulas = [
                    (
                        f"=Proyecciones!E{end}*(1+Supuestos!H{ar})*(1-Supuestos!H{ar}/Supuestos!I{ar})",
                        result.terminal_cashflow,
                    ),
                    (f"=B{vr}/(Supuestos!G{ar}-Supuestos!H{ar})", result.terminal_value),
                    (
                        f"=C{vr}/(1+Supuestos!G{ar})^Proyecciones!B{end}",
                        result.terminal_present_value,
                    ),
                    (f"=SUM(Proyecciones!J{start}:J{end})+D{vr}", result.enterprise_value),
                    (
                        f"=E{vr}-Supuestos!$B$12+Supuestos!$B$13+Supuestos!$B$14-Supuestos!$B$15-Supuestos!$B$18",
                        result.equity_value,
                    ),
                    (f"=F{vr}/Supuestos!$B$16", result.per_share),
                    (f"=G{vr}*Supuestos!$B$17", result.per_instrument),
                    (f'=IF(E{vr}=0,"N/D",D{vr}/E{vr})', result.terminal_weight),
                ]
                for col, (formula, cache) in enumerate(formulas, 1):
                    v.write_formula(
                        si + 2,
                        col,
                        formula,
                        pct if col == 8 else num,
                        float(cache) if cache is not None else "N/D",
                    )
            sens = sheets["Sensibilidades"]
            sens.write_row(1, 0, ["WACC", "g", "Por instrumento (base)"], header)
            base = next(s for s in inputs.scenarios if s.name == "base")
            start, end, ar = ranges["base"]
            cursor = 2
            for dw in [Decimal("-.01"), Decimal(0), Decimal(".01")]:
                for dg in [Decimal("-.005"), Decimal(0), Decimal(".005")]:
                    try:
                        altered = type(base).model_validate(
                            {
                                **base.model_dump(),
                                "wacc": base.wacc + dw,
                                "terminal_growth": base.terminal_growth + dg,
                            }
                        )
                    except ValueError:
                        continue
                    r = cursor + 1
                    sens.write_number(cursor, 0, float(altered.wacc), pct)
                    sens.write_number(cursor, 1, float(altered.terminal_growth), pct)
                    terms = "+".join(
                        f"Proyecciones!I{k}/(1+A{r})^Proyecciones!B{k}"
                        for k in range(start, end + 1)
                    )
                    terminal = f"Proyecciones!E{end}*(1+B{r})*(1-B{r}/Supuestos!I{ar})/(A{r}-B{r})/(1+A{r})^Proyecciones!B{end}"
                    formula = f"=({terms}+{terminal}-Supuestos!$B$12+Supuestos!$B$13+Supuestos!$B$14-Supuestos!$B$15-Supuestos!$B$18)/Supuestos!$B$16*Supuestos!$B$17"
                    sens.write_formula(
                        cursor, 2, formula, num, float(engine.calculate(altered).per_instrument)
                    )
                    cursor += 1
            c = sheets["Controles"]
            c.write_row(1, 0, ["Control", "Resultado", "Criterio"], header)
            for i, row in enumerate(historical, 2):
                hr = i + 1
                c.write(i, 0, f"Balance {row['year']}")
                c.write_formula(
                    i,
                    1,
                    f'=IF(COUNT(Historicos!G{hr}:I{hr})=3,Historicos!G{hr}-Historicos!H{hr}-Historicos!I{hr},"N/D")',
                    num,
                    row["assets"] - row["liabilities"] - row["equity"]
                    if all(row.get(k) is not None for k in ("assets", "liabilities", "equity"))
                    else "N/D",
                )
                c.write(i, 2, "Debe ser cero; N/D bloquea conciliación")
            controls_row = max(9, len(historical) + 3)
            c.write(controls_row, 0, "Base flujos = tasas")
            c.write_formula(controls_row, 1, "=Supuestos!B9=Supuestos!B10", None, True)
            c.write_row(
                controls_row + 2,
                0,
                ["Revisión independiente", "PENDIENTE: evidencia y revisor distinto del autor"],
            )
            c.write_row(
                controls_row + 4,
                0,
                [
                    "Cachés iniciales",
                    "Calculados en Python; recalcular fórmulas tras editar en Excel/LibreOffice",
                ],
            )
