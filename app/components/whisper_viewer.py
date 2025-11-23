import streamlit as st
import json
from pathlib import Path
import pandas as pd

def show_whisper_accuracy_results(folder_path: str):
    """
    Menampilkan hasil akurasi Whisper dari file JSON yang tersimpan di folder.
    Folder default: tmp/whisper_results/
    """
    st.header("📊 Whisper Accuracy Results")

    folder = Path(folder_path)
    if not folder.exists():
        st.warning(f"Folder hasil Whisper belum ditemukan: {folder}")
        return

    files = list(folder.glob("*.json"))
    if not files:
        st.info("Belum ada hasil transkripsi Whisper yang tersimpan.")
        return

    st.write(f"Ditemukan **{len(files)}** hasil Whisper di `{folder}`")

    data_rows = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)

            candidate_id = data.get("candidate_id", "-")
            qid = data.get("question_id", "-")
            question = data.get("question", "")[:80]
            meta = data.get("meta", {})

            data_rows.append({
                "Candidate": candidate_id,
                "QID": qid,
                "Question": question,
                "Duration (s)": round(meta.get("duration_sec", 0.0), 2),
                "Avg Logprob": round(meta.get("avg_logprob", 0.0), 4),
                "No Speech Prob": round(meta.get("no_speech_prob", 0.0), 4),
            })
        except Exception as e:
            st.error(f"Gagal memproses file {f.name}: {e}")

    if not data_rows:
        st.info("Tidak ada data valid untuk ditampilkan.")
        return

    df = pd.DataFrame(data_rows)

    # ✅ Tampilkan tabel hasil Whisper
    st.dataframe(df, use_container_width=True)

    # ✅ Visualisasi sederhana
    st.markdown("### 📈 Whisper Confidence Overview")
    st.bar_chart(df.set_index("QID")[["Avg Logprob", "No Speech Prob"]])

    # ✅ Download seluruh hasil sebagai JSON gabungan
    combined_json = json.dumps(data_rows, ensure_ascii=False, indent=2)
    st.download_button(
        "💾 Download All Whisper Results (JSON)",
        data=combined_json,
        file_name="whisper_results_summary.json",
        mime="application/json"
    )
