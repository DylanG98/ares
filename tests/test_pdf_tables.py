import pdfplumber
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


def test_pdf_table_extraction_matches_synthetic_original(tmp_path):
    path = tmp_path / "synthetic-table.pdf"
    rows = [
        ["SYNTHETIC USD", "2023", "2024"],
        ["Revenue", "950", "1000"],
        ["Assets", "1450", "1500"],
    ]
    table = Table(rows)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
    SimpleDocTemplate(str(path)).build([table])
    with pdfplumber.open(path) as pdf:
        assert pdf.pages[0].extract_table() == rows
