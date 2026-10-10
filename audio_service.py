from pathlib import Path
import subprocess
import tempfile

BASE_DIR = Path(__file__).resolve().parent

PIPER_MODEL = (
    BASE_DIR
    / "modelos"
    / "piper"
    / "pt_BR-faber-medium"
    / "pt_BR-faber-medium.onnx"
)

PIPER_EXEC = BASE_DIR / ".venv" / "bin" / "piper"


def gerar_audio_ogg(texto: str) -> bytes:
    if not texto or not texto.strip():
        raise ValueError("Texto vazio")

    with tempfile.TemporaryDirectory() as pasta:
        wav = Path(pasta) / "resposta.wav"
        ogg = Path(pasta) / "resposta.ogg"

        subprocess.run(
            [
                str(PIPER_EXEC),
                "--model", str(PIPER_MODEL),
                "--output_file", str(wav),
            ],
            input=texto,
            text=True,
            check=True,
            timeout=60,
        )

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loglevel", "error",
                "-i", str(wav),
                "-c:a", "libopus",
                str(ogg),
            ],
            check=True,
            timeout=30,
        )

        return ogg.read_bytes()
