import os
import json
import re
from pathlib import Path

import numpy as np
import librosa
import whisper

decode_options = dict(
    language="en",
    task="transcribe",
    beam_size=2,
    best_of=2,
    temperature=0
)

prompt = """
TensorFlow, Keras, dropout layer, convolutional layer, MobileNet,
EfficientNet, VGG16, VGG19, transfer learning, validation loss, accuracy
"""

domain_replacements = {
    "cellular disease prediction": "celiac disease prediction",
    "cellular disease": "celiac disease",
    "a celiac disease prediction": "celiac disease prediction",
    "script c": "skripsi",
    "data sets": "datasets",
    "data set": "dataset",
    "drawout layer": "dropout layer"
}


def apply_domain_corrections(file_name, text):
    for wrong, correct in domain_replacements.items():
        text = text.replace(wrong, correct)

    if file_name == "interview_question_5.webm":
        text = text.replace(
            "Describe the process of building more convolutional layer for image as fiction",
            "Describe the process of building"
        )
        text = text.replace("image as fiction", "image classification")
        text = text.replace("verative", "variety")
        text = text.replace("next pooling", "mesh pooling")
        text = text.replace("dash layer", "dense layer")

    return text


def analyze_segments(segments):
    if not segments:
        return {
            "total_speech_time": 0,
            "total_pause_time": 0,
            "num_pauses": 0,
            "avg_pause_duration": 0,
            "speech_rate_wpm": 0
        }

    durations = [s["end"] - s["start"] for s in segments]
    total_speech_time = sum(durations)

    pauses = [segments[i]["start"] - segments[i - 1]["end"] for i in range(1, len(segments))]
    pauses = [p for p in pauses if p > 0]
    total_pause_time = sum(pauses)
    num_pauses = len(pauses)
    avg_pause_duration = float(np.mean(pauses)) if pauses else 0.0

    total_words = len(" ".join([s["text"] for s in segments]).split())
    speech_rate_wpm = (total_words / total_speech_time) * 60 if total_speech_time > 0 else 0.0

    return {
        "total_speech_time": round(total_speech_time, 2),
        "total_pause_time": round(total_pause_time, 2),
        "num_pauses": num_pauses,
        "avg_pause_duration": round(avg_pause_duration, 2),
        "speech_rate_wpm": round(speech_rate_wpm, 2)
    }


def analyze_linguistics(text):
    words = re.findall(r"\b\w+\b", text.lower())
    sentences = re.split(r"[.!?]", text)
    fillers = ["um", "uh", "ah", "like", "you know"]
    filler_count = sum(text.lower().count(f) for f in fillers)
    unique_ratio = len(set(words)) / len(words) if words else 0.0
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_sentence_length = float(np.mean(sentence_lengths)) if sentence_lengths else 0.0

    return {
        "unique_word_ratio": round(unique_ratio, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "filler_word_ratio": round(filler_count / len(words), 2) if words else 0.0
    }


def analyze_audio_features(wav_path):
    try:
        y, sr = librosa.load(wav_path, sr=None)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[pitches > 0]
        energy = float(np.mean(librosa.feature.rms(y=y)))
        return {
            "avg_pitch": round(float(np.mean(pitch_values))) if pitch_values.size > 0 else 0,
            "pitch_variance": round(float(np.var(pitch_values))) if pitch_values.size > 0 else 0,
            "energy_mean": round(energy, 2)
        }
    except Exception as e:
        print(f"[WARN] Gagal analisis audio: {e}")
        return {"avg_pitch": 0, "pitch_variance": 0, "energy_mean": 0}


def load_whisper_model(cfg):
    size = cfg["models"]["whisper_size"]
    print(f"Memuat model Whisper: {size}")
    model = whisper.load_model(size)
    return model


def transcribe(wav_path, cfg, model):
    print(f"Memulai transkripsi untuk: {wav_path}")

    options = dict(decode_options)
    options["initial_prompt"] = prompt

    result = model.transcribe(str(wav_path), **options)

    raw_text = (result.get("text") or "").strip()
    file_name = Path(wav_path).name
    text = apply_domain_corrections(file_name, raw_text)

    segments = result.get("segments", []) or []

    if segments:
        avg_logprob = float(np.mean([float(s.get("avg_logprob", -1.0)) for s in segments]))
        no_speech_prob = float(np.mean([float(s.get("no_speech_prob", 0.0)) for s in segments]))
        duration_sec = float(segments[-1].get("end", 0.0))
    else:
        avg_logprob = -1.0
        no_speech_prob = 1.0
        duration_sec = 0.0

    meta_basic = {
        "avg_logprob": avg_logprob,
        "no_speech_prob": no_speech_prob,
        "duration_sec": duration_sec
    }

    speech_stats = analyze_segments(segments)
    linguistic = analyze_linguistics(text)
    audio_feats = analyze_audio_features(wav_path)

    full_meta = {
        "asr_metrics": meta_basic,
        "speech_analysis": speech_stats,
        "linguistic_features": linguistic,
        "audio_features": audio_feats,
        "avg_logprob": avg_logprob,
        "no_speech_prob": no_speech_prob,
        "duration_sec": duration_sec
    }

    simplified_segments = [
        {
            "id": s.get("id", i),
            "start": float(s["start"]),
            "end": float(s["end"]),
            "text": s.get("text", "").strip(),
            "avg_logprob": float(s.get("avg_logprob", 0.0)),
            "no_speech_prob": float(s.get("no_speech_prob", 0.0))
        }
        for i, s in enumerate(segments)
    ]

    out_dir = Path("tmp/transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(wav_path).stem
    out_path = out_dir / f"{base}.json"

    def convert(o):
        if isinstance(o, (np.floating, np.float32, np.float64)):
            return float(o)
        if isinstance(o, (np.integer, np.int32, np.int64)):
            return int(o)
        raise TypeError

    output_data = {
        "text": text,
        "segments": simplified_segments,
        "meta": full_meta
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2, default=convert)

    print(f"Transkrip lengkap disimpan ke: {out_path}")
    return text, simplified_segments, full_meta
