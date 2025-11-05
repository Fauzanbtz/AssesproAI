import io
import json
import sys
from pathlib import Path
import streamlit as st

# Tambahkan path agar bisa impor modul dari folder core
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.config import load_config
from core.question_bank import load_qbank
from core.downloader import fetch_video_to_local
from core.media import extract_wav16k
from core.stt import transcribe
from core.evaluator import evaluate_answer
from core.serializer import compose_hr_json
from core.storage import save_candidate_metadata

# =======================================================
# KONFIGURASI
# =======================================================
st.set_page_config(page_title="Assespro AI - Multi Question", layout="wide")
cfg = load_config()
qbank = load_qbank("data/question_bank.yaml")

st.sidebar.header("🧑‍💼 Info Kandidat")
candidate_id = st.sidebar.text_input("Candidate ID", "001")
st.sidebar.caption("Masukkan ID unik kandidat untuk penyimpanan data")

st.title("🎯 Assespro AI - Multi Question Interview")

# =======================================================
# INPUT VIDEO UNTUK 5 PERTANYAAN
# =======================================================
videos_input = []

for idx, qspec in enumerate(qbank[:5], start=1):
    st.markdown("---")
    st.subheader(f"🧩 Pertanyaan {idx}")
    st.markdown(
        f"""
        <div style="background-color:#f8f9fa; padding:20px; border-radius:15px; border:1px solid #ddd;">
            <h4 style="color:#222;">{qspec['question_text']['en']}</h4>
            <p style="color:#555;">{qspec['question_text'].get('id','')}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([f"🔗 Link Video {idx}", f"📤 Upload File {idx}"])
    video_path, source_url = None, None

    # ---------------------------------------------------
    # TAB 1 - via Link Video
    # ---------------------------------------------------
    with tab1:
        url = st.text_input(f"Link Video Pertanyaan {idx}", key=f"url_{idx}")
        if url.strip():
            source_url = url
            video_path = None  # video akan diunduh nanti saat tombol "Kumpulkan" ditekan

    # ---------------------------------------------------
    # TAB 2 - via Upload File
    # ---------------------------------------------------
    with tab2:
        f = st.file_uploader(f"Upload Video Jawaban {idx}", type=["mp4", "mov", "webm"], key=f"file_{idx}")
        if f:
            tmp_path = Path(cfg["paths"]["tmp_videos"]) / f.name
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_bytes(f.read())
            video_path = tmp_path

    videos_input.append({
        "qid": qspec["qid"],
        "qspec": qspec,
        "video_path": video_path,
        "source_url": source_url
    })

# =======================================================
# 🚀 SATU TOMBOL UNTUK PROSES SEMUA
# =======================================================
if st.button("🚀 Kumpulkan & Proses Semua Jawaban"):
    results_all = []

    for idx, entry in enumerate(videos_input, start=1):
        qspec = entry["qspec"]
        video_path = entry["video_path"]
        source_url = entry["source_url"]

        if not video_path and not source_url:
            st.warning(f"⚠️ Pertanyaan {idx} belum memiliki video, dilewati.")
            continue

        # Jika hanya ada link, baru unduh saat ini
        if source_url and not video_path:
            with st.spinner(f"📥 Mengunduh video pertanyaan {idx}..."):
                video_path = fetch_video_to_local(source_url, cfg)

        with st.spinner(f"🎧 Memproses audio & transkrip (Pertanyaan {idx})..."):
            wav = extract_wav16k(video_path, cfg)
            text, segments, meta = transcribe(wav, cfg)

        with st.spinner(f"🧠 Mengevaluasi jawaban (Pertanyaan {idx})..."):
            result = evaluate_answer(text, qspec, meta, cfg)

        out = compose_hr_json(qspec, text, result, meta, source_url, video_path)
        results_all.append(out)

        # Simpan metadata per pertanyaan
        save_candidate_metadata(
            candidate_id=candidate_id,
            question=qspec["question_text"]["en"],
            recorded_video_url=source_url if source_url else str(video_path),
            is_video_exist=True
        )

        st.success(f"✅ Pertanyaan {idx} berhasil dievaluasi dan disimpan untuk kandidat {candidate_id}")

        # Ekspander untuk lihat transkrip
        with st.expander(f"🗣️ Transkrip Pertanyaan {idx}"):
            st.write(segments)

    # =======================================================
    # OUTPUT SEMUA HASIL
    # =======================================================
    if results_all:
        st.markdown("---")
        st.subheader("📊 Rekapitulasi Hasil Evaluasi Seluruh Pertanyaan")

        all_json = {
            "candidateId": candidate_id,
            "totalQuestions": len(results_all),
            "results": results_all
        }

        st.json(all_json)

        buf = io.BytesIO(json.dumps(all_json, ensure_ascii=False, indent=2).encode("utf-8"))
        st.download_button(
            "💾 Download Semua Hasil Evaluasi (JSON)",
            data=buf,
            file_name=f"{candidate_id}_all_results.json",
            mime="application/json"
        )

        st.success(f"🎉 Semua hasil evaluasi ({len(results_all)} pertanyaan) berhasil diproses & disimpan.")
