# core/confidence.py
import math

def asr_confidence(avg_logprob: float, no_speech_prob: float, asr_weight: float = 0.7) -> float:
    # map avg_logprob roughly into [0,1]; using same heuristic as before but robust
    x = (avg_logprob + 2.0) / (2.0 - 0.1)
    x = max(0.0, min(1.0, x))
    y = 1.0 - max(0.0, min(1.0, no_speech_prob))
    return max(0.0, min(1.0, asr_weight * x + (1 - asr_weight) * y))

def geom_mean(vals):
    vals = [max(1e-6, min(1.0, float(v))) for v in vals]
    return float(math.exp(sum(math.log(v) for v in vals) / len(vals)))

def confidence_score(whisper_meta: dict, lang_det: dict, sim: float, must_cov: float, length_tokens: int, cfg: dict) -> float:
    """
    Combine ASR confidence, language confidence, agreement, and length factor via geometric mean.
    whisper_meta may contain nested "asr_metrics".
    """
    if not isinstance(whisper_meta, dict):
        whisper_meta = {}
    if "asr_metrics" in whisper_meta:
        metrics = whisper_meta["asr_metrics"]
    else:
        metrics = whisper_meta

    avg_logprob = float(metrics.get("avg_logprob", -2.0))
    no_speech_prob = float(metrics.get("no_speech_prob", 1.0))
    asr = asr_confidence(avg_logprob, no_speech_prob, cfg.get("confidence", {}).get("asr_weight", 0.7))
    langc = float(lang_det.get("confidence", 0.6))
    agree = max(1e-6, min(1.0, (sim + must_cov) / 2.0))
    min_len = max(1, cfg.get("confidence", {}).get("min_len_tokens", 120))
    lenf = min(1.0, float(length_tokens) / float(min_len))
    return geom_mean([asr, langc, agree, lenf])
