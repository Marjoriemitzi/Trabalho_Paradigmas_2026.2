import shutil
import subprocess
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"


def test_as_regras_carregam_juntas_sem_aviso() -> None:
    swipl = shutil.which("swipl")
    assert swipl is not None, "swipl não encontrado"
    arquivos = sorted(str(p) for p in RULES_DIR.rglob("*.pl"))

    resultado = subprocess.run(  # noqa: S603
        [
            swipl,
            "--on-error=status",
            "--on-warning=status",
            "-q",
            "-g",
            "halt",
            *arquivos,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert len(arquivos) >= 2
    assert resultado.returncode == 0, resultado.stderr
