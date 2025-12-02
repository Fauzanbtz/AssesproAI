# # core/keywords.py
# import re
# try:
#     from rapidfuzz import fuzz
# except Exception:
#     fuzz = None  # fuzzy matching optional

# def _normalize(s: str) -> str:
#     s = (s or "").lower()
#     s = re.sub(r"[()\[\],.:;\"']", " ", s)
#     s = re.sub(r"\s+", " ", s).strip()
#     return s

# def _soft_contains(text: str, phrase: str, thresh: int = 85) -> bool:
#     T = f" {_normalize(text)} "
#     P = _normalize(phrase)
#     if f" {P} " in T:
#         return True
#     if fuzz:
#         # partial ratio works well for phrase matching in noisy ASR
#         score = fuzz.partial_ratio(T, P)
#         return score >= thresh
#     return False

# def soft_coverage(text: str, keywords: list, thresh: int = 85):
#     """
#     Soft coverage: fuzzy/partial match plus exact fallback.
#     Returns: (hits_list, coverage_fraction)
#     """
#     hits = []
#     for kw in (keywords or []):
#         if _soft_contains(text, kw, thresh=thresh):
#             hits.append(kw)
#     cov = len(hits) / max(1, len(keywords or []))
#     return hits, cov

# # Backwards-compatible alias for old name `coverage`
# def coverage(text: str, keywords: list):
#     return soft_coverage(text, keywords)
