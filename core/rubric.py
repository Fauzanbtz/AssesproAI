# core/rubric.py
import numpy as np
from sentence_transformers import SentenceTransformer, util

_models = {}
_rubric_cache = {}

def _get_model(name: str):
    if name not in _models:
        _models[name] = SentenceTransformer(name, cache_folder="models")
    return _models[name]

def rubric_semantic_grader(answer: str, rubric_texts: dict, model_name: str):
    """
    rubric_texts: dict of {int_point: "description text"} (e.g., 0..4)
    returns: predicted_point:int, sim_score:float, sims_map:dict
    """
    if not rubric_texts:
        return None, None, {}
    model = _get_model(model_name)
    keys = sorted(rubric_texts.keys())
    refs = [rubric_texts[k] for k in keys]
    emb_refs = model.encode(refs, convert_to_tensor=True, normalize_embeddings=True)
    emb_ans = model.encode(answer, convert_to_tensor=True, normalize_embeddings=True)
    sims = util.cos_sim(emb_ans, emb_refs).cpu().numpy().ravel()
    idx = int(np.argmax(sims))
    pred = keys[idx]
    sims_map = {k: float(s) for k, s in zip(keys, sims)}
    return pred, float(sims[idx]), sims_map
