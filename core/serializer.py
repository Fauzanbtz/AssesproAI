# core/serializer.py
from datetime import datetime


def _round_or_none(val, ndigits: int = 4):
    """
    Helper: kalau val bisa di-cast ke float → round,
    kalau None / tidak bisa → kembalikan None.
    """
    if val is None:
        return None
    try:
        return round(float(val), ndigits)
    except (TypeError, ValueError):
        return None


def compose_hr_json(qspec, transcript, result, meta, source_url, video_path):
    """
    Susun output JSON per-pertanyaan yang ramah HR.

    qspec   : satu entri dari question_bank.yaml
    transcript : teks jawaban
    result  : dict dari core.evaluator (sekarang LLM-based)
    meta    : meta dari STT (avg_logprob, no_speech_prob, duration_sec, dst.)
    """

    now = datetime.now().astimezone().isoformat()

    # ASR meta bisa datang langsung dari STT, atau nested dalam asr_metrics
    asr_avg = meta.get("avg_logprob", None)
    asr_ns = meta.get("no_speech_prob", None)
    asr_dur = meta.get("duration_sec", None)

    base = {
        "qid": qspec["qid"],
        "question_text": qspec["question_text"].get("id") or next(
            iter(qspec["question_text"].values())
        ),
        "language_selected": result.get("lang_selected"),

        "asr": {
            "avg_logprob": _round_or_none(asr_avg),
            "no_speech_prob": _round_or_none(asr_ns),
            "duration_sec": _round_or_none(asr_dur, 2),
        },

        "transcript": transcript,

        "scores": {
            "similarity": _round_or_none(result.get("sim", 0.0)),
            "similarity_max": _round_or_none(result.get("sim_max")),
            "keyword_must_coverage": _round_or_none(result.get("keyword_must_coverage", 0.0)),
            "keyword_nice_coverage": _round_or_none(result.get("keyword_nice_coverage", 0.0)),
            "structure": result.get("structure"),
            "performance_score": _round_or_none(result.get("performance_score", 0.0)),
            "confidence_score": _round_or_none(result.get("confidence_score")),
            "calibrated_score": _round_or_none(result.get("calibrated_score")),
        },

        "keyword_hits": result.get("hits", {}),
        "structure_features": result.get("structure_features", {}),

        "video_meta": {
            "source_url": source_url,
            "saved_video": str(video_path),
        },

        "timestamp": now,
    }

    # optional rubric info (LLM)
    if "rubric_point" in result:
        base["rubric"] = {
            "predicted_point": int(result.get("rubric_point")) if result.get("rubric_point") is not None else None,
            "reason": result.get("rubric_reason"),
            "rubric_similarity": result.get("rubric_similarity"),
            "rubric_sims": result.get("rubric_sims", {}),
        }

    # include advanced ASR metrics if present
    if "advanced_metrics" in meta:
        base["asr_advanced"] = meta["advanced_metrics"]

    # optional: raw LLM info kalau kamu simpan di evaluator
    if "llm_raw" in result:
        base["llm"] = result["llm_raw"]

    return base
