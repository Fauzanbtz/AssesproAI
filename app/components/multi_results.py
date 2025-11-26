# app/components/multi_results.py
import io
import json
from typing import List, Dict

import pandas as pd
import streamlit as st


def build_summary_table(results_all: List[Dict]) -> pd.DataFrame:

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
    if not results_all:
        st.info("No evaluation results available to display.")
        return

    st.markdown("### Interview Evaluation Summary")

    df = build_summary_table(results_all)
    st.dataframe(df, use_container_width=True)

    st.markdown("#### Detailed Assessment per Question")
    for idx, item in enumerate(results_all, start=1):
        rubric = item.get("rubric", {})
        with st.expander(f"Q{idx:02d} – {item.get('question_text','')[:70]}"):
            st.write(f"Score (0–4): **{rubric.get('predicted_point')}**")
            reason = rubric.get("reason") or "There is no explanation"
            st.write("Reason:")
            st.write(reason)
            st.write("transcript:")
            st.write(item.get("transcript", ""))

    st.markdown("#### Complete JSON ")

    all_json = {
        "candidateId": candidate_id,
        "totalQuestions": len(results_all),
        "results": results_all,
    }
    st.json(all_json)

    buf = io.BytesIO(json.dumps(all_json, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button(
        "Download All Evaluation Results (JSON)",
        data=buf,
        file_name=f"{candidate_id}_all_results.json",
        mime="application/json",
    )

    st.success(f"All evaluation results ({len(results_all)} questions) have been successfully processed and saved.")
