# core/llm_evaluator.py

"""
Evaluator berbasis LLM (Groq) untuk menilai jawaban interview.

Modul ini TIDAK memakai SBERT / 3-layer evaluator,
hanya mengandalkan LLM + rubric untuk memberi skor 0–4.

Didesain supaya bisa dipanggil dari mana saja, misalnya:
  - notebook
  - Streamlit
  - skrip batch
"""
import os
import json
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

# baca .env sekali saat modul di-import
load_dotenv()

GROQ_DEFAULT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_ENV_VAR = "GROQ_API_TOKEN"


class LLMEvaluatorError(Exception):
    """Error khusus untuk LLM evaluator."""
    pass


def _get_api_key_from_env(env_var: str = GROQ_ENV_VAR) -> str:
    # pastikan .env sudah diload
    load_dotenv()
    key = os.getenv(env_var)
    if not key:
        # Bisa juga tidak raise dan biarkan 401 dari Groq,
        # tapi pesan ini lebih jelas di sisi kamu.
        raise LLMEvaluatorError(
            f"API key LLM tidak ditemukan di environment variable '{env_var}'. "
            f"Pastikan file .env berisi {env_var}=YOUR_TOKEN dan sudah di-load."
        )
    return key


def _format_rubric_from_qspec(qspec: dict) -> str:
    """
    Mengubah rubric di question_bank (dict {0..4: teks}) menjadi teks panjang
    seperti yang kamu pakai di eksperimen.
    """
    rub = qspec.get("rubric", {})
    if not rub:
        return (
            "Poin 4: Jawaban sangat jelas, lengkap, dan relevan.\n"
            "Poin 3: Jawaban cukup jelas dan relevan, meskipun ada detail yang kurang.\n"
            "Poin 2: Jawaban umum, kurang detail, namun masih ada relevansi.\n"
            "Poin 1: Jawaban sangat minim atau tidak jelas.\n"
            "Poin 0: Tidak menjawab."
        )

    lines = []
    # urutkan 4 → 0 agar lebih natural dibaca
    for point in sorted(rub.keys(), reverse=True):
        desc = str(rub[point]).strip()
        lines.append(f"Poin {point}:\n{desc}\n")
    return "\n".join(lines)


def _build_prompt(
    question_text: str,
    rubric_text: str,
    answer_text: str,
    ideal_answer: Optional[str] = None,
    must_keywords: Optional[list] = None,
    context_note: Optional[str] = None,
    hard_constraints: Optional[str] = None,
    extra_guidelines: Optional[str] = None,
) -> str:
    """
    Susun prompt ke LLM, dengan konteks per-soal, ideal answer, dan keyword penting.
    """
    if not extra_guidelines:
        extra_guidelines = """
- If the answer covers most important points but lacks minor details, give 3 or 4.
- If the answer is somewhat general but still technically correct, give 2 or 3.
- Only give 0 or 1 for answers that are clearly irrelevant or incorrect.
- Focus on understanding, relevance, and completeness rather than perfect formatting.
"""

    context_block = f"\nSpecific context for this question:\n{context_note}\n" if context_note else ""
    ideal_block = f"\nReference ideal answer (for alignment, not for copying):\n{ideal_answer}\n" if ideal_answer else ""

    keywords_block = ""
    if must_keywords:
        kw_list = ", ".join(must_keywords)
        keywords_block = f"""
Important technical themes or keywords that should appear in a strong answer (in a natural way):
{kw_list}
"""

    hard_constraints_block = ""
    if hard_constraints:
        hard_constraints_block = f"\nSTRICT scoring rules for this question:\n{hard_constraints}\n"

    prompt = f"""
You are an AI evaluator for a technical interview.

Your task is to grade the candidate's answer from 0 to 4 based on the rubric
AND the specific context and constraints of this question.

Question:
{question_text}

Rubric:
{rubric_text}
{context_block}
{ideal_block}
{keywords_block}
{hard_constraints_block}

Candidate's Answer:
{answer_text}

Guidelines:
{extra_guidelines}

VERY IMPORTANT:
- You must penalize answers that are well-written but not aligned with the intended context of this question.
- If the answer mainly describes unrelated experience, other certifications, or generic topics,
  you must not give a high score, even if the explanation is technically sound.

Respond ONLY in strict JSON format with two keys:
- "score": integer (0, 1, 2, 3, or 4)
- "reason": short explanation (2-4 sentences) why this score is appropriate.
"""
    return prompt.strip()



def _call_groq_chat(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    api_key: Optional[str] = None,
    api_url: str = GROQ_DEFAULT_URL,
    max_tokens: int = 400,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """
    Panggil Groq Chat Completions API dan kembalikan JSON mentah dari Groq.
    """
    if api_key is None:
        api_key = _get_api_key_from_env()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict but fair technical interview evaluator."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise LLMEvaluatorError(
            f"Groq API error {resp.status_code}: {resp.text[:300]}"
        )

    try:
        data = resp.json()
    except Exception as e:
        raise LLMEvaluatorError(f"Gagal parse respons Groq sebagai JSON: {e}") from e

    return data


def _extract_score_from_llm_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ambil 'score' dan 'reason' dari respons Groq.
    Respons diharapkan berupa JSON string di content.
    """
    try:
        content = raw["choices"][0]["message"]["content"]
    except Exception as e:
        raise LLMEvaluatorError(f"Struktur respons Groq tidak terduga: {e}. Raw: {raw}") from e

    # content diharapkan berupa JSON string
    try:
        parsed = json.loads(content)
    except Exception as e:
        raise LLMEvaluatorError(
            f"Content bukan JSON valid. Content: {content}"
        ) from e

    score = int(parsed.get("score", 0))
    reason = str(parsed.get("reason", "")).strip()

    # jaga-jaga kalau LLM keluarin skor diluar 0–4
    if score < 0:
        score = 0
    if score > 4:
        score = 4

    return {
        "score": score,
        "reason": reason,
        "raw_content": content,
    }


def evaluate_answer_llm(
    transcript_text: str,
    qspec: dict,
    cfg: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Fungsi utama yang bisa dipanggil dari luar.

    Args:
        transcript_text: jawaban kandidat (hasil Whisper / manual).
        qspec: 1 item dari question_bank (berisi qid, question_text, rubric, llm, dll.).
        cfg: optional config global; kalau ada, dipakai untuk baca pengaturan LLM.
             Misalnya:
             cfg["llm"] = {
                "backend": "groq",
                "model": "llama-3.1-8b-instant",
                "api_url": "https://api.groq.com/openai/v1/chat/completions",
                "api_key_env": "GROQ_API_TOKEN"
             }

    Returns:
        {
          "qid": ...,
          "llm_score": int 0..4,
          "llm_reason": str,
          "llm_model": str,
          "llm_backend": str,
          "llm_raw_content": str
        }
    """
    # pilih bahasa utama
    lang = qspec.get("languages_supported", ["en"])[0]

    # teks pertanyaan
    question_text = qspec.get("question_text", {}).get(lang) or next(
        iter(qspec.get("question_text", {}).values()), ""
    )

    # rubric 0–4
    rubric_text = _format_rubric_from_qspec(qspec)

    # ideal answer & keywords dari question_bank
    ans_spec = qspec.get("answers", {}).get(lang, {})
    ideal_answer = ans_spec.get("ideal", "")
    must_keywords = ans_spec.get("keywords", {}).get("must", [])

    # konteks spesifik LLM per soal (opsional)
    llm_spec = qspec.get("llm", {}) or {}
    llm_context = llm_spec.get("context", "")
    llm_hard_constraints = llm_spec.get("hard_constraints", "")

    # susun prompt lengkap
    prompt = _build_prompt(
        question_text=question_text,
        rubric_text=rubric_text,
        answer_text=transcript_text,
        ideal_answer=ideal_answer,
        must_keywords=must_keywords,
        context_note=llm_context,
        hard_constraints=llm_hard_constraints,
    )

    # baca pengaturan LLM dari cfg jika ada
    llm_cfg = (cfg or {}).get("llm", {}) if cfg is not None else {}
    model = llm_cfg.get("model", "llama-3.1-8b-instant")
    api_url = llm_cfg.get("api_url", GROQ_DEFAULT_URL)
    api_key_env = llm_cfg.get("api_key_env", GROQ_ENV_VAR)
    backend = llm_cfg.get("backend", "groq")

    api_key = _get_api_key_from_env(api_key_env)

    raw_response = _call_groq_chat(
        prompt=prompt,
        model=model,
        api_key=api_key,
        api_url=api_url,
        max_tokens=llm_cfg.get("max_tokens", 400),
        temperature=float(llm_cfg.get("temperature", 0.0)),
    )

    parsed = _extract_score_from_llm_response(raw_response)

    return {
        "qid": qspec.get("qid"),
        "llm_score": parsed["score"],
        "llm_reason": parsed["reason"],
        "llm_model": model,
        "llm_backend": backend,
        "llm_raw_content": parsed["raw_content"],
    }

