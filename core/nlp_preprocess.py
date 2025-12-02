# import re
# from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# _factory = StemmerFactory()
# _stemmer = _factory.create_stemmer()

# def clean_text(t: str) -> str:
#     t = (t or "").lower()
#     t = re.sub(r"[^0-9a-zA-ZÀ-ÿ\u00f1\u00d1\s]", " ", t)
#     t = re.sub(r"\s+", " ", t).strip()
#     return t

# def preprocess_id(t: str, stopset=None, slang=None) -> str:
#     t = clean_text(t)
#     if slang:
#         for k,v in slang.items():
#             t = re.sub(rf"\b{k}\b", v, t)
#     toks = t.split()
#     if stopset:
#         toks = [w for w in toks if w not in stopset]
#     toks = [_stemmer.stem(w) for w in toks]
#     return " ".join(toks)
