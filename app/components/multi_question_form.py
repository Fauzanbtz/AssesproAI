# app/components/multi_question_form.py

import streamlit as st
from pathlib import Path

def render_multi_question_form(qbank, max_questions: int = 5):
    """
    Render form multi-pertanyaan (link / upload) dan
    mengembalikan list of dict seperti:
      {
        "qid": str,
        "qspec": dict,
        "upload_file": UploadedFile | None,
        "source_url": str | None,
        "video_path": None,   # selalu None, akan diisi di evaluation_runner
      }
    """
    videos_input = []

    for idx, qspec in enumerate(qbank[:max_questions], start=1):
        st.markdown("---")
        st.subheader(f" Pertanyaan {idx}")

        st.markdown(
            f"""
            <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #ddd;">
                <h4 style="color:#222;">{qspec['question_text']['en']}</h4>
                <p style="color:#555;">{qspec['question_text'].get('id','')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs([f" Link Video {idx}", f" Upload File {idx}"])

        source_url = None
        upload_file = None

        # Tab 1: link video
        with tab1:
            url = st.text_input(
                f"Link Video Pertanyaan {idx}",
                key=f"url_{idx}"
            )
            if url.strip():
                source_url = url.strip()

        # Tab 2: upload file
        with tab2:
            f = st.file_uploader(
                f"Upload Video Jawaban {idx}",
                type=["mp4", "mov", "webm"],
                key=f"file_{idx}"
            )
            if f is not None:
                upload_file = f

        videos_input.append({
            "qid": qspec["qid"],
            "qspec": qspec,
            "upload_file": upload_file,  # UploadedFile (belum disimpan)
            "source_url": source_url,    # string URL (bisa None)
            "video_path": None,          # akan diisi di evaluation_runner
        })

    return videos_input
