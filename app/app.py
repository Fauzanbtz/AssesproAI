# app/app.py
import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from core.config import load_config
from core.question_bank import load_qbank

from components.multi_question_form import render_multi_question_form
from components.evaluation_runner import process_all_answers, show_summary_and_download
from components.whisper_viewer import show_whisper_accuracy_results

# KONFIGURASI STREAMLIT
st.set_page_config(page_title="Assespro AI - Multi Question", layout="wide")
cfg = load_config()
qbank = load_qbank("data/question_bank.yaml")

# Sidebar kandidat
st.sidebar.header(" Info Kandidat")
candidate_id = st.sidebar.text_input("Candidate ID", "1")
st.sidebar.caption("Masukkan ID unik kandidat untuk penyimpanan data")

st.title("Assespro AI - Multi Question Interview")

# TAB UTAMA
tab_main, tab_whisper = st.tabs([" Input & Evaluasi", " Whisper Accuracy"])

with tab_main:
    # Form multi-pertanyaan (link / upload) → list videos_input
    videos_input = render_multi_question_form(qbank)

    # tombol proses
    if st.button(" Kumpulkan & Proses Semua Jawaban"):
        results_all = process_all_answers(videos_input, candidate_id, cfg)
        show_summary_and_download(results_all, candidate_id)

with tab_whisper:
    show_whisper_accuracy_results("tmp/whisper_results")
