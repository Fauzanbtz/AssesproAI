from core.language_router import detect_language
from core.similarity import sbert_similarity
from core.keywords import coverage
from core.structure import structure_score
from core.confidence import confidence_score

def evaluate_answer(transcript_text: str, qspec: dict, whisper_meta: dict, cfg: dict):
    lang_det = detect_language(transcript_text)
    lang = lang_det["lang"] if lang_det["lang"] in qspec["languages_supported"] else qspec["languages_supported"][0]

    ideal = qspec["answers"][lang]["ideal"]
    must = qspec["answers"][lang]["keywords"]["must"]
    nice = qspec["answers"][lang]["keywords"]["nice"]

    sim = sbert_similarity(transcript_text, ideal, cfg["models"]["sbert_name"])
    must_hits, must_cov = coverage(transcript_text, must)
    nice_hits, nice_cov = coverage(transcript_text, nice)
    struct = structure_score(transcript_text)

    w = qspec["weights"]
    perf = w["similarity"]*sim + w["keyword_must"]*must_cov + w["keyword_nice"]*nice_cov + w["structure"]*struct

    # ✅ Ambil nilai logprob/no_speech dari struktur baru bila ada
    asr_meta = whisper_meta.get("asr_metrics", whisper_meta)
    conf = confidence_score(asr_meta, lang_det, sim, must_cov, len(transcript_text.split()), cfg)

    return {
        "lang_selected": lang,
        "sim": sim,
        "keyword_must_coverage": must_cov,
        "keyword_nice_coverage": nice_cov,
        "structure": float(struct),
        "performance_score": perf,
        "confidence_score": conf,
        "hits": {"must": must_hits, "nice": nice_hits}
    }

