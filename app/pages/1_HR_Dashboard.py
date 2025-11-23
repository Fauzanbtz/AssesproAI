import io
import yaml
import json
import streamlit as st
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

# ================
# Config / Paths
# ================
st.set_page_config(page_title="HR Dashboard — Question Bank Manager", layout="wide")
ROOT_DIR = Path(__file__).resolve().parents[2]  # AssesproAI root
QBANK_PATH = ROOT_DIR / "data" / "question_bank.yaml"

# ================
# Helpers
# ================
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

# ============================
# UI: Page header & controls
# ============================
st.title("HR Review Dashboard — Question Bank Manager")
st.markdown("Kelola question bank (YAML). Menambahkan, mengedit, menghapus, export/import.")

# Top actions: Download / Upload (replace)
col_top_left, col_top_right = st.columns([3,1])

qbank = load_qbank()

with col_top_right:
    if st.button("🔄 Reload question_bank.yaml"):
        st.rerun()

    st.download_button(
        label="⬇️ Download YAML",
        data=download_yaml_bytes(qbank),
        file_name="question_bank.yaml",
        mime="application/x-yaml"
    )

    uploaded = st.file_uploader("📤 Import YAML (replace)", type=["yaml","yml"], key="import_yaml")
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

# ============================
# Summary table
# ============================
st.subheader("Ringkasan Question Bank")
if not qbank:
    st.info("Belum ada pertanyaan. Silakan tambahkan.")
else:
    df = qbank_to_table(qbank)
    st.dataframe(df, use_container_width=True)

st.markdown("---")

# ============================
# CREATE: Add new full form
# ============================
st.header("➕ Tambah Pertanyaan Baru (Form Lengkap)")

with st.form(key="create_form"):
    c1, c2 = st.columns([2,4])
    with c1:
        new_qid = st.text_input("QID")
    with c2:
        new_question = st.text_area("Question Text (English)", height=80)

    st.markdown("**Rubric (0 - 4)**")
    new_rubric = {}
    rcols = st.columns(5)
    for s in range(5):
        with rcols[s]:
            new_rubric[s] = st.text_area(f"{s}", key=f"new_rubric_{s}", height=90)

    st.markdown("**LLM fields**")
    new_llm_context = st.text_area("LLM Context", height=120)
    new_llm_constraints = st.text_area("LLM Hard Constraints", height=80)

    submitted = st.form_submit_button("Tambah Pertanyaan")
    if submitted:
        if not new_qid.strip():
            st.error("QID tidak boleh kosong.")
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
            st.success(f"Pertanyaan {new_qid} berhasil ditambahkan.")
            st.rerun()

st.markdown("---")

# ============================
# READ / UPDATE / DELETE per question
# ============================
st.header("✏️ Edit / Hapus Pertanyaan")

if not qbank:
    st.info("Tidak ada pertanyaan untuk diedit.")
else:
    qids = [q.get("qid", "") for q in qbank]
    sel_qid = st.selectbox("Pilih QID untuk edit/hapus", qids, index=0)
    sel_idx = qids.index(sel_qid)
    sel_q = qbank[sel_idx]

    # ---------- EDIT FORM (inside st.form) ----------
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

        save_pressed = st.form_submit_button("💾 Simpan Perubahan")

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

    # ---------- DELETE (outside the form) ----------
    delete_key = f"delete_state_{sel_qid}"
    
    # jika tombol hapus ditekan
    if st.button("🗑 Hapus Pertanyaan", key=f"delete_btn_{sel_qid}"):
        st.session_state[delete_key] = True
    
    # kalau sedang dalam mode konfirmasi
    if st.session_state.get(delete_key, False):
        st.warning(f"Yakin ingin menghapus pertanyaan **{sel_qid}**?")
        col_c1, col_c2 = st.columns(2)
    
        with col_c1:
            delete_yes = st.button("Ya, Hapus", key=f"yes_delete_{sel_qid}")
    
        with col_c2:
            delete_no = st.button("Batal", key=f"no_delete_{sel_qid}")
    
        if delete_yes:
            qbank = [q for q in qbank if q.get("qid") != sel_qid]
            save_qbank(qbank)
            st.success("Pertanyaan berhasil dihapus.")
            st.session_state[delete_key] = False
            st.rerun()
    
        if delete_no:
            st.info("Dibatalkan.")
            st.session_state[delete_key] = False
            st.rerun()


st.markdown("---")

# ============================
# Candidate JSON viewer (existing)
# ============================
st.header("📁 Hasil Evaluasi Kandidat (JSON)")

folder = ROOT_DIR / "app" / "tmp" / "transcripts"
if not folder.exists():
    folder = ROOT_DIR / "tmp" / "transcripts"

files = sorted(folder.glob("*.json")) if folder.exists() else []

if not files:
    st.info("Belum ada hasil JSON dari kandidat.")
else:
    data = []
    for f in files:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            st.error(f"Gagal membaca {f.name}: {e}")
            continue
        scores = j.get("scores", {})
        data.append({
            "file": f.name,
            "qid": j.get("qid", "-"),
            "similarity": scores.get("similarity", 0.0),
            "keyword_must": scores.get("keyword_must_coverage", 0.0),
            "performance": scores.get("performance_score", 0.0),
            "confidence": scores.get("confidence_score", 0.0),
            "lang": j.get("language_selected", "-"),
            "timestamp": j.get("timestamp", "-"),
        })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    sel = st.selectbox("Pilih hasil untuk dilihat:", df["file"])
    if sel:
        j = json.loads((folder / sel).read_text(encoding="utf-8"))
        st.subheader(f"Detail Hasil: {sel}")
        st.json(j)
