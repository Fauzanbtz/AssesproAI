import os
import json
import re
import numpy as np
import librosa
import whisper
from datetime import timedelta

def _whisper(wav_path, cfg):
    import whisper
    model = whisper.load_model(cfg["models"]["whisper_size"])
    result = model.transcribe(str(wav_path), language="id", word_timestamps=False)
    text = (result.get("text") or "").strip()
    segs = result.get("segments", [])
    if segs:
        avg_logprob = sum(s.get("avg_logprob",-1.0) for s in segs)/len(segs)
        ns_prob = sum(s.get("no_speech_prob",0.0) for s in segs)/len(segs)
        dur = float(segs[-1]["end"] - segs[0]["start"])
    else:
        avg_logprob, ns_prob, dur = -2.0, 1.0, 0.0
    return text, segs, {"avg_logprob": avg_logprob, "no_speech_prob": ns_prob, "duration_sec": dur}

# ============================================================
# 🔹 Helper Functions
# ============================================================

def analyze_segments(segments):
    """Analisis statistik dari hasil segmen Whisper."""
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
    avg_pause_duration = np.mean(pauses) if pauses else 0

    total_words = len(" ".join([s["text"] for s in segments]).split())
    speech_rate_wpm = (total_words / total_speech_time) * 60 if total_speech_time > 0 else 0

    return {
        "total_speech_time": round(total_speech_time, 2),
        "total_pause_time": round(total_pause_time, 2),
        "num_pauses": num_pauses,
        "avg_pause_duration": round(avg_pause_duration, 2),
        "speech_rate_wpm": round(speech_rate_wpm, 2)
    }


def analyze_linguistics(text):
    """Analisis fitur linguistik dari teks hasil transkrip."""
    words = re.findall(r'\b\w+\b', text.lower())
    sentences = re.split(r'[.!?]', text)
    fillers = ['um', 'uh', 'ah', 'like', 'you know']
    filler_count = sum(text.lower().count(f) for f in fillers)
    unique_ratio = len(set(words)) / len(words) if words else 0
    avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0

    return {
        "unique_word_ratio": round(unique_ratio, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "filler_word_ratio": round(filler_count / len(words), 2) if words else 0
    }


def analyze_audio_features(wav_path):
    """Analisis fitur audio sederhana seperti pitch & energy."""
    try:
        y, sr = librosa.load(wav_path, sr=None)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[pitches > 0]
        energy = np.mean(librosa.feature.rms(y=y))
        return {
            "avg_pitch": round(float(np.mean(pitch_values))) if len(pitch_values) > 0 else 0,
            "pitch_variance": round(float(np.var(pitch_values))) if len(pitch_values) > 0 else 0,
            "energy_mean": round(float(energy), 2)
        }
    except Exception as e:
        print(f"[WARN] Gagal analisis audio: {e}")
        return {"avg_pitch": 0, "pitch_variance": 0, "energy_mean": 0}


# ============================================================
# 🔹 Fungsi Utama Whisper
# ============================================================

def _whisper(wav_path, cfg):
    """Transkripsi audio menggunakan Whisper (internal use)."""
    model = whisper.load_model(cfg["models"]["whisper_size"])
    result = model.transcribe(str(wav_path), language="id", word_timestamps=False)

    text = (result.get("text") or "").strip()
    segs = result.get("segments", [])
    if segs:
        avg_logprob = sum(s.get("avg_logprob", -1.0) for s in segs) / len(segs)
        ns_prob = sum(s.get("no_speech_prob", 0.0) for s in segs) / len(segs)
        dur = float(segs[-1]["end"] - segs[0]["start"])
    else:
        avg_logprob, ns_prob, dur = -2.0, 1.0, 0.0

    return text, segs, {
        "avg_logprob": avg_logprob,
        "no_speech_prob": ns_prob,
        "duration_sec": dur
    }


def transcribe(wav_path, cfg):
    """Transkripsi audio + analisis statistik & simpan hasil ke JSON dengan segments yang disederhanakan."""
    import os
    import json
    import numpy as np
    import whisper

    print(f"🎧 Memulai transkripsi untuk: {wav_path}")
    model = whisper.load_model(cfg["models"]["whisper_size"])
    result = model.transcribe(str(wav_path), language="en")

    text = (result.get("text") or "").strip()
    segments = result.get("segments", [])

    # Hitung meta ASR
    meta = {
        "avg_logprob": float(np.mean([float(s.get("avg_logprob", -1.0)) for s in segments])) if segments else -1.0,
        "no_speech_prob": float(np.mean([float(s.get("no_speech_prob", 0.0)) for s in segments])) if segments else 1.0,
        "duration_sec": float(segments[-1]["end"]) if segments else 0.0
    }

    # 🔍 Analisis tambahan
    speech_stats = analyze_segments(segments)
    linguistic = analyze_linguistics(text)
    audio_feats = analyze_audio_features(wav_path)

    # Full meta tetap ada untuk kompatibilitas evaluator
    full_meta = {
        "asr_metrics": meta,
        "speech_analysis": speech_stats,
        "linguistic_features": linguistic,
        "audio_features": audio_feats,
        "avg_logprob": meta["avg_logprob"],
        "no_speech_prob": meta["no_speech_prob"],
        "duration_sec": meta["duration_sec"]
    }

    simplified_segments = [
        {
            "id": s["id"],
            "start": float(s["start"]),
            "end": float(s["end"]),
            "text": s["text"].strip(),
            "avg_logprob": float(s.get("avg_logprob", 0.0)),
            "no_speech_prob": float(s.get("no_speech_prob", 0.0))
        }
        for s in segments
    ]

    # Simpan hasil ke file JSON
    os.makedirs("tmp/transcripts", exist_ok=True)
    base = os.path.splitext(os.path.basename(wav_path))[0]
    out_path = f"tmp/transcripts/{base}.json"

    output_data = {
        "text": text,
        "segments": simplified_segments,  
        "meta": full_meta
    }

    def convert(o):
        if isinstance(o, (np.floating, np.float32, np.float64)):
            return float(o)
        if isinstance(o, (np.integer, np.int32, np.int64)):
            return int(o)
        raise TypeError

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2, default=convert)

    print(f" Transkrip lengkap disimpan ke: {out_path}")
    return text, simplified_segments, full_meta
