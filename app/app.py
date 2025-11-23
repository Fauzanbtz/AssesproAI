# app/app.py
import sys
from pathlib import Path
import streamlit as st

# ======================================
# Setup path ke root project
# ======================================
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from core.config import load_config
from core.question_bank import load_qbank

from components.multi_question_form import render_multi_question_form
from components.evaluation_runner import process_all_answers
from components.multi_results import show_summary_and_download
from components.whisper_viewer import show_whisper_accuracy_results

# ======================================
# Konfigurasi Streamlit
# ======================================
st.set_page_config(page_title="Assespro AI - Multi Question (LLM)", layout="wide")

cfg = load_config(str(ROOT_DIR / "config.yaml"))

# ======================================
# FUNCTION: Selalu load question bank setiap render
# ======================================
def get_qbank():
    yaml_path = ROOT_DIR / "data" / "question_bank.yaml"
    return load_qbank(str(yaml_path))


# Sidebar kandidat
st.sidebar.header(" Info Kandidat")
candidate_id = st.sidebar.text_input("Candidate ID", "1")
st.sidebar.caption("Masukkan ID unik kandidat untuk penyimpanan data")

# Tombol manual refresh YAML (opsional)
if st.sidebar.button("🔄 Reload Question Bank"):
    st.success("Question bank berhasil direload!")

st.title("Assespro AI - Multi Question Interview (LLM Evaluator)")

# ======================================
# Tabs utama
# ======================================
tab_main, tab_whisper = st.tabs([" Input & Evaluasi", " Whisper Accuracy"])

with tab_main:

    # Selalu load YAML terbaru
    qbank = get_qbank()

    # Form multi-pertanyaan → menghasilkan list video inputs
    videos_input = render_multi_question_form(qbank)

    # Proses semua jawaban
    if st.button(" Kumpulkan & Proses Semua Jawaban"):
        results_all = process_all_answers(videos_input, candidate_id, cfg)
        show_summary_and_download(results_all, candidate_id)


with tab_whisper:
    show_whisper_accuracy_results("tmp/whisper_results")
