# app/components/multi_results.py

import io
import json
from typing import List, Dict

import pandas as pd
import streamlit as st


def build_summary_table(results_all: List[Dict]) -> pd.DataFrame:
    """
    Bangun DataFrame ringkasan dari list hasil HR (output compose_hr_json).
    Setiap elemen di results_all adalah dict satu pertanyaan.
    """
    rows = []
    for idx, item in enumerate(results_all, start=1):
        qid = item.get("qid")
        qtext = item.get("question_text", "")[:80]
        scores = item.get("scores", {})
        rubric = item.get("rubric", {})

        rows.append({
            "No": idx,
            "QID": qid,
            "Question": qtext,
            "Rubric Point (0–4)": rubric.get("predicted_point"),
            "Performance Score (0–1)": scores.get("performance_score"),
            "Avg Logprob": item.get("asr", {}).get("avg_logprob"),
            "Duration (s)": item.get("asr", {}).get("duration_sec"),
        })

    df = pd.DataFrame(rows)
    return df


def show_summary_and_download(results_all: List[Dict], candidate_id: str):
    """
    Tampilkan ringkasan tabel + JSON download untuk semua pertanyaan.
    """
    if not results_all:
        st.info("Belum ada hasil evaluasi untuk ditampilkan.")
        return

    st.markdown("### Rekap Hasil Evaluasi Interview (LLM)")

    # 1) Tabel ringkasan
    df = build_summary_table(results_all)
    st.dataframe(df, use_container_width=True)

    # 2) Detail alasan rubric per pertanyaan
    st.markdown("#### Detail Penilaian per Pertanyaan")
    for idx, item in enumerate(results_all, start=1):
        rubric = item.get("rubric", {})
        with st.expander(f"Q{idx:02d} – {item.get('question_text','')[:70]}"):
            st.write(f"Skor LLM (0–4): **{rubric.get('predicted_point')}**")
            reason = rubric.get("reason") or "Tidak ada alasan dari LLM."
            st.write("Alasan:")
            st.write(reason)
            st.write("Transkrip:")
            st.write(item.get("transcript", ""))

    # 3) JSON full + download
    st.markdown("#### JSON Lengkap (Untuk HR / Integrasi API)")

    all_json = {
        "candidateId": candidate_id,
        "totalQuestions": len(results_all),
        "results": results_all,
    }
    st.json(all_json)

    buf = io.BytesIO(json.dumps(all_json, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button(
        "Download Semua Hasil Evaluasi (JSON)",
        data=buf,
        file_name=f"{candidate_id}_all_results.json",
        mime="application/json",
    )

    st.success(f"Semua hasil evaluasi ({len(results_all)} pertanyaan) berhasil diproses & disimpan.")
