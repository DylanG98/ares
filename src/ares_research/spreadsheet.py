"""Recalculate Excel with a real engine in a disposable user profile."""

import shutil
import subprocess
import tempfile
from pathlib import Path


class SpreadsheetRecalculator:
    def recalculate(self, source: Path, destination: Path) -> Path:
        binary = shutil.which("libreoffice") or shutil.which("soffice")
        if not binary:
            raise RuntimeError("LibreOffice absent; Excel formula recalculation remains unverified")
        source = source.resolve()
        if source.suffix.lower() != ".xlsx" or source.stat().st_size > 50 * 1024 * 1024:
            raise ValueError("Expected xlsx under 50 MiB")
        if source == destination.resolve():
            raise ValueError("Preserve original; recalculate into a new artifact")
        with tempfile.TemporaryDirectory(prefix="ares-recalc-") as temp:
            work = Path(temp)
            result = subprocess.run(
                [
                    binary,
                    f"-env:UserInstallation={(work / 'profile').as_uri()}",
                    "--headless",
                    "--convert-to",
                    "xlsx",
                    "--outdir",
                    str(work),
                    str(source),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            output = work / source.name
            if result.returncode or not output.exists():
                raise RuntimeError("Spreadsheet engine did not produce a recalculated workbook")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output, destination)
        return destination
