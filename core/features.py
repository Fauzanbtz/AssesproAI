# core/features.py
from core.similarity import sim_pair, sim_segment_max
from core.keywords import soft_coverage
from core.structure import structure_score, extract_structure_features

def compute_features(transcript: str, qspec: dict, whisper_meta: dict, cfg: dict) -> dict:
    """
    Compute and return feature dict:
      - sim (pair)
      - sim_max (segment-level)
      - must_hits, must_cov
      - nice_hits, nice_cov
      - structure (continuous)
      - structure_features (detailed)
      - length_tokens
      - asr_meta (raw)
    """
    lang = qspec.get("languages_supported", ["en"])[0]
    ideal = qspec["answers"][lang]["ideal"]
    must = qspec["answers"][lang]["keywords"]["must"]
    nice = qspec["answers"][lang]["keywords"]["nice"]

    model_name = cfg["models"]["sbert_name"]
    sim = sim_pair(model_name, transcript, ideal)
    sim_max = sim_segment_max(model_name, transcript, ideal)

    must_hits, must_cov = soft_coverage(transcript, must)
    nice_hits, nice_cov = soft_coverage(transcript, nice)

    struct = structure_score(transcript, weights=cfg.get("structure_weights") if cfg.get("structure_weights") else None)
    struct_feats = extract_structure_features(transcript)

    length_tokens = max(0, len((transcript or "").split()))

    return {
        "sim": sim,
        "sim_max": sim_max,
        "must_hits": must_hits,
        "must_cov": must_cov,
        "nice_hits": nice_hits,
        "nice_cov": nice_cov,
        "structure": struct,
        "structure_features": struct_feats,
        "length_tokens": length_tokens,
        "asr_meta": whisper_meta
    }
