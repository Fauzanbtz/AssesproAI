# app/components/multi_question_form.py

import streamlit as st
from pathlib import Path

def render_multi_question_form(qbank, max_questions: int = 5):

    videos_input = []

    for idx, qspec in enumerate(qbank[:max_questions], start=1):
        st.markdown("---")
        st.subheader(f" Question {idx}")

        st.markdown(
            f"""
            <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #ddd;">
                <h4 style="color:#222;">{qspec['question_text']['en']}</h4>
                <p style="color:#555;">{qspec['question_text'].get('id','')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs([f" Video Link {idx}", f" Upload File {idx}"])

        source_url = None
        upload_file = None

        with tab1:
            url = st.text_input(
                f"Question Video Link {idx}",
                key=f"url_{idx}"
            )
            if url.strip():
                source_url = url.strip()

        with tab2:
            f = st.file_uploader(
                f"Upload Answer Video {idx}",
                type=["mp4", "mov", "webm"],
                key=f"file_{idx}"
            )
            if f is not None:
                upload_file = f

        videos_input.append({
            "qid": qspec["qid"],
            "qspec": qspec,
            "upload_file": upload_file, 
            "source_url": source_url,    
            "video_path": None,         
        })

    return videos_input
