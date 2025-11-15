import json
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="HR Dashboard", layout="wide")

st.title("HR Review Dashboard")

folder = Path("tmp/transcripts")
files = sorted(folder.glob("*.json"))

if not files:
    st.warning("Belum ada hasil JSON dari kandidat.")
else:
    data = []
    for f in files:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            st.error(f"Gagal membaca {f.name}: {e}")
            continue

        # Aman dari KeyError
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

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        sel = st.selectbox("Pilih hasil untuk dilihat:", [d["file"] for d in data])
        if sel:
            j = json.loads((folder / sel).read_text(encoding="utf-8"))
            st.subheader(f"Detail Hasil: {sel}")
            st.json(j)
    else:
        st.info("Belum ada file JSON dengan struktur lengkap (punya 'scores').")
