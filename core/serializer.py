from datetime import datetime

def compose_hr_json(qspec, transcript, result, meta, source_url, video_path):
    now = datetime.now().astimezone().isoformat()
    base = {
        "qid": qspec["qid"],
        "question_text": qspec["question_text"].get("id") or next(iter(qspec["question_text"].values())),
        "language_selected": result["lang_selected"],
        "asr": {
            "avg_logprob": round(meta["avg_logprob"],4),
            "no_speech_prob": round(meta["no_speech_prob"],4),
            "duration_sec": round(meta["duration_sec"],2)
        },
        "transcript": transcript,
        "scores": {
            "similarity": round(result["sim"],4),
            "keyword_must_coverage": round(result["keyword_must_coverage"],4),
            "keyword_nice_coverage": round(result["keyword_nice_coverage"],4),
            "structure": result["structure"],
            "performance_score": round(result["performance_score"],4),
            "confidence_score": round(result["confidence_score"],4)
        },
        "keyword_hits": result["hits"],
        "video_meta": {
            "source_url": source_url,
            "saved_video": str(video_path)
        },
        "timestamp": now
    }

    # 🆕 Tambahkan advanced metrics (kalau ada)
    if "advanced_metrics" in meta:
        base["asr_advanced"] = meta["advanced_metrics"]

    return base
