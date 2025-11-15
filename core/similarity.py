# core/similarity.py
from sentence_transformers import SentenceTransformer, util
import re

_models = {}

def _get(model_name: str):
    if model_name not in _models:
        # store cache in repo models/ folder
        _models[model_name] = SentenceTransformer(model_name, cache_folder="models")
    return _models[model_name]

def sim_pair(model_name: str, a: str, b: str, normalize: bool = True) -> float:
    if not a or not b:
        return 0.0
    m = _get(model_name)
    ea = m.encode(a, convert_to_tensor=True, normalize_embeddings=normalize)
    eb = m.encode(b, convert_to_tensor=True, normalize_embeddings=normalize)
    return float(util.cos_sim(ea, eb))

def sim_segment_max(model_name: str, text: str, ideal: str, splitter=r"[.!?\\n]+") -> float:
    if not text or not ideal:
        return 0.0
    parts = [p.strip() for p in re.split(splitter, text) if p.strip()]
    if not parts:
        return sim_pair(model_name, text, ideal)
    m = _get(model_name)
    # encode all parts + ideal at once
    emb = m.encode(parts + [ideal], convert_to_tensor=True, normalize_embeddings=True)
    parts_emb = emb[:-1]
    ideal_emb = emb[-1:]
    sims = util.cos_sim(parts_emb, ideal_emb).cpu().numpy().ravel()
    try:
        return float(sims.max())
    except Exception:
        return 0.0
