# components/inputs.py
import streamlit as st

def url_input():
    return st.text_input("Paste video link (YouTube/Drive/Dropbox/Direct):", "")

def upload_input():
    return st.file_uploader("Upload video (mp4/mov/webm)", type=["mp4","mov","webm"])

def question_video_inputs(idx: int, question_en: str, question_id: str = ""):

    st.markdown("---")
    st.subheader(f" Question {idx}")
    st.markdown(
        f"""
        <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #ddd;">
            <h4 style="color:#222;">{question_en}</h4>
            <p style="color:#555;">{question_id}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([f" Video Link {idx}", f" Upload Video {idx}"])
    video_path, source_url = None, None

    with tab1:
        url = st.text_input(f"Input Video Link {idx}", key=f"url_{idx}")
        if url.strip():
            source_url = url

    with tab2:
        f = st.file_uploader(
            f"Upload Answer Video {idx}",
            type=["mp4", "mov", "webm"],
            key=f"file_{idx}"
        )
        if f:
            video_path = f

    return video_path, source_url
