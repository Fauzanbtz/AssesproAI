import math

def asr_confidence(avg_logprob: float, no_speech_prob: float, asr_weight=0.7):
    x = (avg_logprob + 2.0) / (2.0 - 0.1)
    x = max(0.0, min(1.0, x))
    y = 1.0 - no_speech_prob
    return max(0.0, min(1.0, asr_weight*x + (1-asr_weight)*y))

def geom_mean(vals):
    vals = [max(1e-6, min(1.0, v)) for v in vals]
    return float(math.exp(sum(math.log(v) for v in vals)/len(vals)))

def confidence_score(whisper_meta, lang_det, sim, must_cov, length_tokens, cfg):
    if "asr_metrics" in whisper_meta:
        whisper_meta = whisper_meta["asr_metrics"]
        
    asr = asr_confidence(whisper_meta["avg_logprob"], whisper_meta["no_speech_prob"], cfg["confidence"]["asr_weight"])
    langc = lang_det.get("confidence", 0.6)
    agree = max(1e-6, min(1.0, (sim + must_cov)/2))
    lenf = min(1.0, length_tokens/ cfg["confidence"]["min_len_tokens"])
    return geom_mean([asr, langc, agree, lenf])
