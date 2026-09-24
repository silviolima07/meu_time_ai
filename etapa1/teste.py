from faster_whisper import WhisperModel

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    "audio.ogg",
    language="pt"
)

texto = " ".join(
    segment.text
    for segment in segments
)
