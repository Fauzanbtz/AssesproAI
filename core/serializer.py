# core/serializer.py
from datetime import datetime

def compose_hr_json(qspec, transcript, result, meta, source_url, video_path):
    now = datetime.now().astimezone().isoformat()
    base = {
        "qid": qspec["qid"],
        "question_text": qspec["question_text"].get("id") or next(iter(qspec["question_text"].values())),
        "language_selected": result.get("lang_selected"),
        "asr": {
            "avg_logprob": round(meta.get("avg_logprob", -99.0), 4),
            "no_speech_prob": round(meta.get("no_speech_prob", 1.0), 4),
            "duration_sec": round(meta.get("duration_sec", 0.0), 2)
        },
        "transcript": transcript,
        "scores": {
            "similarity": round(result.get("sim", 0.0), 4),
            "similarity_max": round(result.get("sim_max", 0.0), 4) if result.get("sim_max") is not None else None,
            "keyword_must_coverage": round(result.get("keyword_must_coverage", 0.0), 4),
            "keyword_nice_coverage": round(result.get("keyword_nice_coverage", 0.0), 4),
            "structure": result.get("structure"),
            "performance_score": round(result.get("performance_score", 0.0), 4),
            "confidence_score": round(result.get("confidence_score", 0.0), 4),
            "calibrated_score": result.get("calibrated_score", None)
        },
        "keyword_hits": result.get("hits", {}),
        "structure_features": result.get("structure_features", {}),
        "video_meta": {
            "source_url": source_url,
            "saved_video": str(video_path)
        },
        "timestamp": now
    }

    # optional rubric info
    if "rubric_point" in result:
        base["rubric"] = {
            "predicted_point": int(result.get("rubric_point")) if result.get("rubric_point") is not None else None,
            "rubric_similarity": result.get("rubric_similarity"),
            "rubric_sims": result.get("rubric_sims", {})
        }

    # include advanced ASR metrics if present
    if "advanced_metrics" in meta:
        base["asr_advanced"] = meta["advanced_metrics"]

    return base
