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

    now = datetime.now().astimezone().isoformat()
# Support format baru dan lama

# format baru: meta["asr_metrics"]["avg_logprob"]
    asr_metrics = meta.get("asr_metrics", {})

    asr_avg = meta.get("avg_logprob") or asr_metrics.get("avg_logprob")
    asr_ns  = meta.get("no_speech_prob") or asr_metrics.get("no_speech_prob")
    asr_dur = meta.get("duration_sec") or asr_metrics.get("duration_sec")


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

        # "keyword_hits": result.get("hits", {}),
        # "structure_features": result.get("structure_features", {}),

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
            # "rubric_similarity": result.get("rubric_similarity"),
            # "rubric_sims": result.get("rubric_sims", {}),
        }

    # include advanced ASR metrics if present
    if "advanced_metrics" in meta:
        base["asr_advanced"] = meta["advanced_metrics"]

    # optional: raw LLM info kalau kamu simpan di evaluator
    if "llm_raw" in result:
        base["llm"] = result["llm_raw"]

    return base
