from kokoro import KPipeline
import soundfile as sf


print("Carregando Kokoro...")

pipeline = KPipeline(
    lang_code="p"
)

print("[OK] Kokoro carregado.")

texto = (
    "O maior artilheiro da história do Flamengo "
    "é Zico, com quinhentos e oito gols."
)

print("Gerando áudio...")

generator = pipeline(
    texto,
    voice="pf_dora",
    speed=1.0
)

audio_completo = []

for _, _, audio in generator:
    audio_completo.append(audio)

import numpy as np

audio_final = np.concatenate(
    audio_completo
)

sf.write(
    "resposta.wav",
    audio_final,
    24000
)

print("[OK] Arquivo resposta.wav criado.")
