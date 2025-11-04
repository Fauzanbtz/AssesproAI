import io, json
from pathlib import Path
import streamlit as st
import sys

# Tambahkan path agar bisa impor modul dari folder core
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import load_config
from core.question_bank import load_qbank
from core.downloader import fetch_video_to_local
from core.media import extract_wav16k
from core.stt import transcribe
from core.evaluator import evaluate_answer
from core.serializer import compose_hr_json

# Konfigurasi halaman
st.set_page_config(page_title="Assespro AI", layout="wide")

cfg = load_config()
qbank = load_qbank("data/question_bank.yaml")
qids = [q["qid"] for q in qbank]

# Sidebar untuk memilih pertanyaan
st.sidebar.header("🎯 Pilih Pertanyaan Interview")
sel_qid = st.sidebar.selectbox("Pilih Pertanyaan", qids, index=0)
qspec = next(q for q in qbank if q["qid"] == sel_qid)

st.sidebar.caption(qspec["question_text"].get("id", ""))

# =======================================================
# TAMPILAN UTAMA KANDIDAT
# =======================================================
st.title("Assespro AI ")

# --- Tampilkan pertanyaan besar di halaman utama ---
st.markdown(
    f"""
    <div style="background-color:#f8f9fa; padding:25px; border-radius:15px; border:1px solid #ddd; margin-bottom:20px;">
        <h2 style="color:#222; text-align:center;">{qspec['question_text']['en']}</h2>
        <p style="text-align:center; color:#555; font-size:16px;">{qspec['question_text'].get('id','')}</p>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2 = st.tabs(["🎬 Link Video", "📤 Upload File"])

video_path, source_url = None, None

# -------------------------------------------------------
# TAB 1 - Link Video
# -------------------------------------------------------
with tab1:
    url = st.text_input("Tempel link video:", "")
    if st.button("Proses dari Link"):
        if not url.strip():
            st.error("URL kosong")
        else:
            with st.spinner("Mengunduh video..."):
                video_path = fetch_video_to_local(url, cfg)
                source_url = url

# -------------------------------------------------------
# TAB 2 - Upload File
# -------------------------------------------------------
with tab2:
    f = st.file_uploader("Unggah video (mp4/mov/webm)", type=["mp4", "mov", "webm"])
    if st.button("Proses dari Upload"):
        if not f:
            st.error("Pilih file dulu")
        else:
            p = Path(cfg["paths"]["tmp_videos"]) / f.name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(f.read())
            video_path = p

# -------------------------------------------------------
# PROSES PIPELINE: audio → transkrip → evaluasi
# -------------------------------------------------------
if video_path:
    with st.spinner("🎧 Ekstrak audio & transkrip..."):
        wav = extract_wav16k(video_path, cfg)
        text, segments, meta = transcribe(wav, cfg)

    with st.spinner("🧠 Mengevaluasi jawaban..."):
        result = evaluate_answer(text, qspec, meta, cfg)

    out = compose_hr_json(qspec, text, result, meta, source_url, video_path)

    st.subheader("📋 Hasil Evaluasi (untuk HR)")
    st.json(out)

    buf = io.BytesIO(json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button(
        "💾 Download JSON Hasil",
        data=buf,
        file_name=f"{qspec['qid']}_result.json",
        mime="application/json"
    )

    with st.expander("🗣️ Lihat Segmen Transkrip"):
        st.write(segments)
