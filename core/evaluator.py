# core/evaluator.py

from __future__ import annotations
from typing import Dict, Any
from core.llm_evaluator import evaluate_answer_llm

def evaluate_answer(transcript_text: str, qspec: dict, whisper_meta: dict, cfg: dict) -> Dict[str, Any]:
    llm_res = evaluate_answer_llm(transcript_text, qspec, cfg)
    llm_score = llm_res.get("llm_score", 0)
    llm_reason = llm_res.get("llm_reason", "")

    performance_score = float(llm_score) / 4.0
    lang = qspec.get("languages_supported", ["en"])[0]

    if isinstance(whisper_meta, dict):
        asr_meta = whisper_meta.get("asr_metrics", whisper_meta)
    else:
        asr_meta = {}

    result = {
        "lang_selected": lang,

        # # field lama → diisi default saja
        # "sim": 0.0,
        # "sim_max": None,
        # "keyword_must_coverage": 0.0,
        # "keyword_nice_coverage": 0.0,
        # "structure": None,
        # "structure_features": None,
        # "hits": {"must": [], "nice": []},

        # # # skor utama
        # "performance_score": performance_score,
        # "confidence_score": None,

        "rubric_point": int(llm_score),
        "rubric_reason": llm_reason,
        "rubric_similarity": None,
        "rubric_sims": {},

        "calibrated_score": None,
    }

    result["llm_raw"] = {
        "model": llm_res.get("llm_model"),
        "backend": llm_res.get("llm_backend"),
        "raw_content": llm_res.get("llm_raw_content"),
    }

    return result
