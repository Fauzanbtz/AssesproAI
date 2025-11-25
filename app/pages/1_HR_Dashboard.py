import io
import yaml
import json
import streamlit as st
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any


st.set_page_config(page_title="HR Dashboard", layout="wide")
ROOT_DIR = Path(__file__).resolve().parents[2]  
QBANK_PATH = ROOT_DIR / "data" / "question_bank.yaml"

# Helper functions kali butuh
def ensure_data_folder():
    (ROOT_DIR / "data").mkdir(parents=True, exist_ok=True)

def load_qbank() -> List[Dict[str, Any]]:
    ensure_data_folder()
    if not QBANK_PATH.exists():
        return []
    raw = yaml.safe_load(QBANK_PATH.read_text(encoding="utf-8"))
    if raw is None:
        return []
    return normalize_qbank(raw)

def save_qbank(qbank: List[Dict[str, Any]]):
    ensure_data_folder()
    QBANK_PATH.write_text(yaml.safe_dump(qbank, sort_keys=False, allow_unicode=True), encoding="utf-8")

def normalize_qbank(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for item in raw:
        q = dict(item)  # shallow copy
        q["qid"] = str(q.get("qid", "")).strip()

        qt = q.get("question_text") or {}
        if isinstance(qt, str):
            qt = {"en": qt}
        q["question_text"] = {"en": str(qt.get("en", "")).strip()}

        ls = q.get("languages_supported")
        if not isinstance(ls, list):
            ls = ["en"]
        if "en" not in ls:
            ls.insert(0, "en")
        q["languages_supported"] = ls

        if "answers" not in q:
            q["answers"] = {"en": {"ideal": "", "keywords": {"must": [], "nice": []}}}

        raw_rubric = q.get("rubric", {}) or {}
        rubric = {}
        for i in range(5):
            v = None
            if i in raw_rubric:
                v = raw_rubric[i]
            elif str(i) in raw_rubric:
                v = raw_rubric[str(i)]
            else:
                v = raw_rubric.get(i, "")
            rubric[i] = "" if v is None else str(v).strip()
        q["rubric"] = rubric

        if "weights" not in q:
            q["weights"] = {"similarity": 0.55, "keyword_must": 0.3, "keyword_nice": 0.1, "structure": 0.05}

        q["pass_threshold"] = q.get("pass_threshold", 0.7)

        llm = q.get("llm") or {}
        q["llm"] = {
            "context": str(llm.get("context", "") or "").strip(),
            "hard_constraints": str(llm.get("hard_constraints", "") or "").strip()
        }

        out.append(q)
    return out

def qbank_to_table(qbank: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for q in qbank:
        rows.append({
            "QID": q.get("qid", ""),
            "English Question": q.get("question_text", {}).get("en", "")[:120],
            "Has Rubric": "✔" if any(v.strip() for v in q.get("rubric", {}).values()) else "✖",
            "Has LLM Context": "✔" if q.get("llm", {}).get("context", "").strip() else "✖"
        })
    return pd.DataFrame(rows)

def download_yaml_bytes(qbank: List[Dict[str, Any]]) -> bytes:
    payload = yaml.safe_dump(qbank, sort_keys=False, allow_unicode=True)
    return payload.encode("utf-8")

st.title("HR Dashboard ")
st.markdown("Manage a question bank (YAML). Add, edit, delete, export/import.")

col_top_left, col_top_right = st.columns([3,1])

qbank = load_qbank()

with col_top_right:
    if st.button("🔄 Reload question_bank.yaml"):
        st.rerun()

    st.download_button(
        label="⬇ Download YAML",
        data=download_yaml_bytes(qbank),
        file_name="question_bank.yaml",
        mime="application/x-yaml"
    )

    uploaded = st.file_uploader(" Import YAML (replace)", type=["yaml","yml"], key="import_yaml")
    if uploaded is not None:
        try:
            content = uploaded.read().decode("utf-8")
            parsed = yaml.safe_load(content)
            if not isinstance(parsed, list):
                st.error("File YAML harus berisi list (root should be a YAML list of questions).")
            else:
                qbank = normalize_qbank(parsed)
                save_qbank(qbank)
                st.success("Question bank berhasil diimpor dan disimpan.")
                st.rerun()
        except Exception as e:
            st.error(f"Gagal memuat YAML: {e}")


st.subheader("Question Bank summary")
if not qbank:
    st.info("No questions yet. Please add one.")
else:
    df = qbank_to_table(qbank)
    st.dataframe(df, use_container_width=True)

st.markdown("---")


st.header("Add New Question")

with st.form(key="create_form"):
    c1, c2 = st.columns([2,4])
    with c1:
        new_qid = st.text_input("QID")
    with c2:
        new_question = st.text_area("Question Text ", height=80)

    st.markdown("**Rubric (0 - 4)**")
    new_rubric = {}
    rcols = st.columns(5)
    for s in range(5):
        with rcols[s]:
            new_rubric[s] = st.text_area(f"{s}", key=f"new_rubric_{s}", height=90)

    st.markdown("**LLM fields**")
    new_llm_context = st.text_area("LLM Context", height=120)
    new_llm_constraints = st.text_area("LLM Hard Constraints", height=80)

    submitted = st.form_submit_button("Add Question", help=None)
    if submitted:
        if not new_qid.strip():
            st.error("QID cannot be empty.")
        else:
            new_item = {
                "qid": new_qid.strip(),
                "question_text": {"en": new_question.strip()},
                "languages_supported": ["en"],
                "answers": {"en": {"ideal": "", "keywords": {"must": [], "nice": []}}},
                "rubric": {i: (new_rubric.get(i) or "").strip() for i in range(5)},
                "weights": {"similarity": 0.55, "keyword_must": 0.3, "keyword_nice": 0.1, "structure": 0.05},
                "pass_threshold": 0.7,
                "llm": {"context": new_llm_context.strip(), "hard_constraints": new_llm_constraints.strip()}
            }
            qbank.append(new_item)
            save_qbank(qbank)
            st.success(f"Question {new_qid} successfully added.")
            st.rerun()

st.markdown("---")

st.header(" Edit / Delete Question")

if not qbank:
    st.info("No questions to edit or delete.")
else:
    qids = [q.get("qid", "") for q in qbank]
    sel_qid = st.selectbox("Select a QID to edit/delete", qids, index=0)
    sel_idx = qids.index(sel_qid)
    sel_q = qbank[sel_idx]

    # ---------- EDIT FORM ----------
    with st.form(key=f"edit_form_{sel_qid}"):
        st.subheader(f"Edit: {sel_qid}")
        eqid = st.text_input("QID", sel_q.get("qid", ""), key=f"eqid_{sel_qid}")
        eq_text = st.text_area("Question Text (English)", sel_q.get("question_text", {}).get("en", ""), height=100, key=f"eq_text_{sel_qid}")

        st.markdown("**Rubric (0 - 4)**")
        erubric = {}
        rcols = st.columns(5)
        for s in range(5):
            existing = sel_q.get("rubric", {}).get(s, "")
            if existing == "" and str(s) in sel_q.get("rubric", {}):
                existing = sel_q.get("rubric", {}).get(str(s), "")
            with rcols[s]:
                erubric[s] = st.text_area(f"{s}", existing, key=f"erubric_{sel_qid}_{s}", height=90)

        st.markdown("**LLM fields**")
        econtext = st.text_area("LLM Context", sel_q.get("llm", {}).get("context", ""), height=120, key=f"econtext_{sel_qid}")
        econst = st.text_area("LLM Hard Constraints", sel_q.get("llm", {}).get("hard_constraints", ""), height=80, key=f"econst_{sel_qid}")

        save_pressed = st.form_submit_button(" Simpan Perubahan")

    if save_pressed:
        if not eqid.strip():
            st.error("QID tidak boleh kosong.")
        else:
            qbank[sel_idx]["qid"] = eqid.strip()
            qbank[sel_idx]["question_text"]["en"] = eq_text.strip()
            qbank[sel_idx]["rubric"] = {i: (erubric.get(i) or "").strip() for i in range(5)}
            qbank[sel_idx]["llm"] = {"context": (econtext or "").strip(), "hard_constraints": (econst or "").strip()}
            save_qbank(qbank)
            st.success("Perubahan disimpan.")
            st.rerun()

    delete_key = f"delete_state_{sel_qid}"
    
    if st.button(" Delete Question", key=f"delete_btn_{sel_qid}"):
        st.session_state[delete_key] = True
    
    if st.session_state.get(delete_key, False):
        st.warning(f"Are you sure you want to delete the question? **{sel_qid}**?")
        col_c1, col_c2 = st.columns(2)
    
        with col_c1:
            delete_yes = st.button("Yes, Delete", key=f"yes_delete_{sel_qid}")
    
        with col_c2:
            delete_no = st.button("Cancel", key=f"no_delete_{sel_qid}")
    
        if delete_yes:
            qbank = [q for q in qbank if q.get("qid") != sel_qid]
            save_qbank(qbank)
            st.success("Question successfully deleted.")
            st.session_state[delete_key] = False
            st.rerun()
    
        if delete_no:
            st.info("Canceled.")
            st.session_state[delete_key] = False
            st.rerun()


st.markdown("---")

# ============================
# Candidate JSON viewer (existing)
# ============================
# st.header("Hasil Evaluasi Kandidat (JSON)")

# folder = ROOT_DIR / "app" / "tmp" / "transcripts"
# if not folder.exists():
#     folder = ROOT_DIR / "tmp" / "transcripts"

# files = sorted(folder.glob("*.json")) if folder.exists() else []

# if not files:
#     st.info("Belum ada hasil JSON dari kandidat.")
# else:
#     data = []
#     for f in files:
#         try:
#             j = json.loads(f.read_text(encoding="utf-8"))
#         except Exception as e:
#             st.error(f"Gagal membaca {f.name}: {e}")
#             continue
#         scores = j.get("scores", {})
#         data.append({
#             "file": f.name,
#             "qid": j.get("qid", "-"),
#             "similarity": scores.get("similarity", 0.0),
#             "keyword_must": scores.get("keyword_must_coverage", 0.0),
#             "performance": scores.get("performance_score", 0.0),
#             "confidence": scores.get("confidence_score", 0.0),
#             "lang": j.get("language_selected", "-"),
#             "timestamp": j.get("timestamp", "-"),
#         })

#     df = pd.DataFrame(data)
#     st.dataframe(df, use_container_width=True)
#     sel = st.selectbox("Pilih hasil untuk dilihat:", df["file"])
#     if sel:
#         j = json.loads((folder / sel).read_text(encoding="utf-8"))
#         st.subheader(f"Detail Hasil: {sel}")
#         st.json(j)

# st.markdown("---")

# ============================
# Candidate Answers Viewer (LLM) - HR
# ============================
st.header("Candidate Answer Results")


def show_candidate_answers_for_hr(
    candidate_id: str,
    base_folder: str = "data/candidate_answers",
):
    import os 

    root_dir = ROOT_DIR
    answers_path = root_dir / base_folder / f"{candidate_id}.json"

    st.markdown(f"##### Candidate: `{candidate_id}`")

    if not answers_path.exists():
        st.warning(f"No candidate answer file found at: `{answers_path}`")
        return

    # load JSON
    try:
        with open(answers_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Failed to read the candidate answer file.: {e}")
        return

    results_all = data.get("results", []) or []
    total_q = data.get("totalQuestions", len(results_all))

    if not results_all:
        st.info("The candidate_answers file exists, but does not contain any question results.")
    else:
        st.caption(f"Total stored questions: **{total_q}**")
        st.caption(f"Source file: `{answers_path.relative_to(root_dir)}`")

        st.markdown("#### Detailed Answers & Scoring per Question")

        for idx, item in enumerate(results_all, start=1):
            qid = item.get("qid", f"Q{idx:02d}")
            qtext = item.get("question_text", "") or ""
            transcript = item.get("transcript", "") or ""

            # info rubric / LLM
            rubric = item.get("rubric", {}) or {}
            score = (
                rubric.get("predicted_point")
                or rubric.get("llm_score")
                or None
            )
            reason = (
                rubric.get("reason")
                or rubric.get("llm_reason")
                or "No written explanation "
            )

            with st.expander(f"{qid} – {qtext[:80]}", expanded=False):
                st.markdown(f"**Skor LLM (0–4):** `{score}`")
                st.markdown("**Rubric Explanation / Justification:**")
                st.write(reason)

                # ASR / Whisper Meta (jika ada)
                asr = item.get("asr", {})
                if asr:
                    st.markdown("**ASR / Whisper Metadata:**")
                    c1, c2, c3 = st.columns(3)
                    try:
                        c1.metric("Avg Logprob", f"{asr.get('avg_logprob', 0.0):.4f}")
                        c2.metric("No Speech Prob", f"{asr.get('no_speech_prob', 0.0):.4f}")
                        c3.metric("Duration (s)", f"{asr.get('duration_sec', 0.0):.2f}")
                    except Exception:
                        st.json(asr)

                st.markdown("**Candidate Answer Transcript from video:**")
                st.write(transcript)

                vid_meta = item.get("video_meta", {})
                if vid_meta:
                    st.markdown("**Video Metadata:**")
                    st.json(vid_meta)

    with st.expander("View Raw JSON (Raw Candidate Answers)"):
        st.json(data)

#remove candidate 
    st.markdown("---")
    st.subheader("Manage This Candidates Storage")

    delete_state_key = f"delete_candidate_{candidate_id}"

    if st.button("Delete This Candidate’s Answer File", key=f"btn_delete_{candidate_id}"):
        st.session_state[delete_state_key] = True

    if st.session_state.get(delete_state_key, False):
        st.warning(
            f"You are about to delete the candidate’s evaluation results file. **{candidate_id}** "
            f"at `{answers_path.relative_to(root_dir)}`.\n\n"
            "This action cannot be undone."
        )
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            confirm_yes = st.button("Yes, Delete this file", key=f"confirm_yes_{candidate_id}")
        with col_d2:
            confirm_no = st.button("Cancel", key=f"confirm_no_{candidate_id}")

        if confirm_yes:
            try:
                if answers_path.exists():
                    answers_path.unlink()
                st.success(f"Candidate answer file{candidate_id} sudah dihapus.")
            except Exception as e:
                st.error(f"Failed to delete the file.: {e}")
            st.session_state[delete_state_key] = False
            st.rerun()

        if confirm_no:
            st.info("Deletion canceled.")
            st.session_state[delete_state_key] = False



ANS_FOLDER = ROOT_DIR / "data" / "candidate_answers"
ANS_FOLDER.mkdir(parents=True, exist_ok=True)

files = sorted(ANS_FOLDER.glob("*.json"))

if not files:
    st.info("No candidate answer file available.")
else:
    options = []
    for f in files:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            cid = str(j.get("candidateId", f.stem))
            saved_at = j.get("savedAt", "-")
            total = j.get("totalQuestions", len(j.get("results", [])))
            label = f"{cid}  |  {total} pertanyaan  |  {saved_at}"
            options.append({"id": cid, "label": label})
        except Exception:
            options.append({"id": f.stem, "label": f"{f.stem} (invalid json)"})

    labels = [o["label"] for o in options]
    selected_label = st.selectbox("Select a candidate to review:", labels)

    selected = next(o for o in options if o["label"] == selected_label)
    show_candidate_answers_for_hr(selected["id"])
