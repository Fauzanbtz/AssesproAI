# components/inputs.py

import streamlit as st

def url_input():
    return st.text_input("Tempel link video (YouTube/Drive/Dropbox/Direct):", "")

def upload_input():
    return st.file_uploader("Unggah video (mp4/mov/webm)", type=["mp4","mov","webm"])

def question_video_inputs(idx: int, question_en: str, question_id: str = ""):
    """
    Render blok satu pertanyaan:
      - judul + teks
      - tab Link / Upload
    Return: (video_path, source_url) — path file lokal atau URL sumber.
    """
    st.markdown("---")
    st.subheader(f" Pertanyaan {idx}")
    st.markdown(
        f"""
        <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #ddd;">
            <h4 style="color:#222;">{question_en}</h4>
            <p style="color:#555;">{question_id}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([f" Link Video {idx}", f" Upload File {idx}"])
    video_path, source_url = None, None

    with tab1:
        url = st.text_input(f"Link Video Pertanyaan {idx}", key=f"url_{idx}")
        if url.strip():
            source_url = url

    with tab2:
        f = st.file_uploader(
            f"Upload Video Jawaban {idx}",
            type=["mp4", "mov", "webm"],
            key=f"file_{idx}"
        )
        if f:
            # path akan diset di luar, karena butuh cfg["paths"]["tmp_videos"]
            video_path = f

    return video_path, source_url
