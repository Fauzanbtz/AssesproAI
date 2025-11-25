# app/app.py
import sys
from pathlib import Path
import streamlit as st

# ======================================
# Setup path ke root project
# ======================================
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent   # folder tempat app.py berada

sys.path.append(str(ROOT_DIR))

from core.config import load_config
from core.question_bank import load_qbank
from components.multi_question_form import render_multi_question_form
from components.evaluation_runner import process_all_answers
from core.storage import save_candidate_answers

# ======================================
# Konfigurasi Streamlit
# ======================================
st.set_page_config(page_title="Assespro AI ", layout="wide")

logo_path = APP_DIR / "Assespro.jpg"
if logo_path.exists():
    st.image(str(logo_path), width=230)
else:
    st.warning(f"Logo tidak ditemukan: {logo_path}")

cfg = load_config(str(ROOT_DIR / "config.yaml"))

# ======================================
# FUNCTION: Selalu load question bank setiap render
# ======================================
def get_qbank():
    yaml_path = ROOT_DIR / "data" / "question_bank.yaml"
    return load_qbank(str(yaml_path))


# Sidebar kandidat
st.sidebar.header("input candidate ID")
candidate_id = st.sidebar.text_input(
    "Candidate ID",
    value="",
    placeholder="enter your ID"
)


st.title("Assespro AI ")

# ======================================
# Tabs utama
# ======================================
tab_main, = st.tabs([" Input & Evaluasi"])

with tab_main:
    qbank = get_qbank()

    videos_input = render_multi_question_form(qbank)

    if st.button("Submit Answers"):
        results_all = process_all_answers(videos_input, candidate_id, cfg)

        if not results_all:
            st.warning("No answers have been successfully saved.")
        else:
            out_path = save_candidate_answers(candidate_id, results_all)
            st.success(f"Candidate answer successfully saved.")
            # st.caption(f"File: {out_path}")