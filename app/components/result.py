import io, json
import streamlit as st

def show_json_download(payload: dict, filename: str):
    st.json(payload)
    buf = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button("Download JSON", data=buf, file_name=filename, mime="application/json")
