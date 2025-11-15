# core/evaluator.py
from core.language_router import detect_language
from core.features import compute_features
from core.confidence import confidence_score
from core.rubric import rubric_semantic_grader
from core.calibrator import load_calibrator, predict_calibrated
import os

def evaluate_answer(transcript_text: str, qspec: dict, whisper_meta: dict, cfg: dict):
    """
    Full evaluation pipeline:
      - compute features (similarity, coverage, structure)
      - compute performance_score (weighted)
      - compute confidence_score
      - optional rubric semantic grade (layer 3)
      - optional calibrated score via pretrained calibrator
    """
    # 1) language detection & pick language
    lang_det = detect_language(transcript_text)
    lang = lang_det["lang"] if lang_det["lang"] in qspec.get("languages_supported", [lang_det.get("lang")]) else qspec.get("languages_supported", [lang_det.get("languages_supported", ["en"])[0]])[0]

    # 2) features (layer 1 + 2)
    feats = compute_features(transcript_text, qspec, whisper_meta, cfg)
    sim = feats["sim"]
    must_cov = feats["must_cov"]
    nice_cov = feats["nice_cov"]
    struct = feats["structure"]
    length_tokens = feats["length_tokens"]

    # 3) performance (weighted)
    w = qspec.get("weights", cfg.get("scoring", {}).get("weights", {}))
    # Ensure keys exist
    sim_w = w.get("similarity", cfg.get("scoring", {}).get("weights", {}).get("similarity", 0.55))
    must_w = w.get("keyword_must", cfg.get("scoring", {}).get("weights", {}).get("keyword_must", 0.30))
    nice_w = w.get("keyword_nice", cfg.get("scoring", {}).get("weights", {}).get("keyword_nice", 0.10))
    struct_w = w.get("structure", cfg.get("scoring", {}).get("weights", {}).get("structure", 0.05))

    performance_score = sim_w * sim + must_w * must_cov + nice_w * nice_cov + struct_w * struct

    # 4) confidence
    asr_meta = whisper_meta.get("asr_metrics", whisper_meta) if isinstance(whisper_meta, dict) else {}
    conf = confidence_score(asr_meta, lang_det, sim, must_cov, length_tokens, cfg)

    result = {
        "lang_selected": lang,
        "sim": sim,
        "sim_max": feats.get("sim_max"),
        "keyword_must_coverage": must_cov,
        "keyword_nice_coverage": nice_cov,
        "structure": float(struct),
        "structure_features": feats.get("structure_features"),
        "performance_score": float(performance_score),
        "confidence_score": float(conf),
        "hits": {"must": feats.get("must_hits"), "nice": feats.get("nice_hits")}
    }

    # 5) Layer 3 - rubric semantic matching (if rubric texts present in qspec)
    rubric_texts = {}
    try:
        # Expect qspec to contain rubric texts keyed by ints e.g. qspec["rubric"][0],..[4]
        rubric_texts = qspec.get("rubric", {})
    except Exception:
        rubric_texts = {}

    if rubric_texts:
        pred_point, sim_score, sims_map = rubric_semantic_grader(transcript_text, rubric_texts, cfg["models"]["sbert_name"])
        result.update({
            "rubric_point": int(pred_point) if pred_point is not None else None,
            "rubric_similarity": sim_score,
            "rubric_sims": sims_map
        })

    # 6) optional: calibrated score using pretrained calibrator in cfg (if present)
    calib_path = cfg.get("calibration", {}).get("calibrator_path")
    if calib_path and os.path.exists(calib_path):
        try:
            calib = load_calibrator(calib_path)
            # build feature vector ordering consistent with training; here we glue a default vector:
            Xvec = [
                result["sim"],
                result.get("sim_max", result["sim"]),
                result["keyword_must_coverage"],
                result["keyword_nice_coverage"],
                result["structure"],
                result["confidence_score"],
                result["structure"]  # duplicate allowed if trained so; adjust as needed
            ]
            pred = predict_calibrated(calib, [Xvec])
            # normalized cast
            result["calibrated_score"] = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
        except Exception:
            # if calibrator fails, skip gracefully
            result["calibrated_score"] = None

    return result
