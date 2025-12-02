# # core/structure.py
# import re

# def extract_structure_features(text: str):
#     """
#     Return dictionary with structure-related features.
#     """
#     t = (text or "").lower()
#     tokens = len(t.split())
#     sentences = [s.strip() for s in re.split(r"[.!?\n]+", t) if s.strip()]
#     n_sent = max(1, len(sentences))
#     avg_sent_len = sum(len(s.split()) for s in sentences) / n_sent
#     intro = int(any(p in t for p in ["perkenalkan", "nama saya", "i am", "my name", "hello my name"]))
#     close = int(any(p in t for p in ["motivasi", "tertarik", "value", "nilai", "kontribusi", "in summary", "overall", "conclusion"]))
#     effect = int(any(p in t for p in ["overfitting", "validation loss", "generalization", "improve", "accuracy", "reduce overfit"]))
#     return {
#         "tokens": tokens,
#         "sentences": n_sent,
#         "avg_sent_len": avg_sent_len,
#         "intro": intro,
#         "close": close,
#         "effect": effect
#     }

# def structure_score(text: str, weights: dict = None) -> float:
#     """
#     Continuous structure score in [0,1].
#     Default weights: tokens high, then intro/close/effect.
#     """
#     if weights is None:
#         weights = {"tokens": 0.45, "intro": 0.2, "close": 0.2, "effect": 0.15}
#     f = extract_structure_features(text)
#     # token-based subscore: linear up to 60 tokens
#     tok_score = min(1.0, f["tokens"] / 60.0)
#     score = tok_score * weights.get("tokens", 0.45) + f["intro"] * weights.get("intro", 0.2) + f["close"] * weights.get("close", 0.2) + f["effect"] * weights.get("effect", 0.15)
#     return round(float(min(1.0, score)), 3)
