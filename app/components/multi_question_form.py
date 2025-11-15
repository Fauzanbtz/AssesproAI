# components/multi_question_form.py
from typing import List, Dict, Any
from pathlib import Path
import streamlit as st

def render_multi_question_form(qbank: List[dict]) -> List[Dict[str, Any]]:
    """
    Render form untuk beberapa pertanyaan (maksimal 5 pertama di qbank).
    Menghasilkan list dict:
      {
        "qid": str,
        "qspec": dict,
        "uploaded_file": UploadedFile | None,
        "source_url": str | None,
        "index": int
      }
    """
    videos_input = []

    for idx, qspec in enumerate(qbank[:5], start=1):
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
        uploaded_file, source_url = None, None

        # TAB 1 - via Link Video
        with tab1:
            url = st.text_input(f"Link Video Pertanyaan {idx}", key=f"url_{idx}")
            if url.strip():
                source_url = url

        # TAB 2 - via Upload File
        with tab2:
            uploaded_file = st.file_uploader(
                f"Upload Video Jawaban {idx}",
                type=["mp4", "mov", "webm"],
                key=f"file_{idx}"
            )

        videos_input.append({
            "qid": qspec["qid"],
            "qspec": qspec,
            "uploaded_file": uploaded_file,  # belum disimpan ke disk
            "source_url": source_url,
            "index": idx,
        })

    return videos_input
