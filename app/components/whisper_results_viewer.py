import streamlit as st
import json
from pathlib import Path
import pandas as pd

def show_whisper_accuracy_results(folder_path="tmp/whisper_results"):
    """
    Menampilkan hasil akurasi whisper dari semua file JSON di folder tmp/whisper_results
    """
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    st.markdown("### 🎯 Rekapitulasi Akurasi Whisper")
    files = sorted(folder.glob("*.json"))

    if not files:
        st.info("📂 Belum ada hasil whisper yang tersimpan di folder `tmp/whisper_results`.")
        return

    all_data = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as j:
                data = json.load(j)
                adv = data.get("advanced_metrics", {})
                acc = adv.get("accuracy", {})
                sp = adv.get("speech_analysis", {})
                lf = adv.get("linguistic_features", {})

                all_data.append({
                    "File": f.name,
                    "WER": round(acc.get("WER", 0), 4),
                    "CER": round(acc.get("CER", 0), 4),
                    "Word Accuracy (%)": acc.get("word_accuracy", 0)*100,
                    "Speech Rate (WPM)": sp.get("speech_rate_wpm", 0),
                    "Unique Word Ratio": lf.get("unique_word_ratio", 0),
                })
        except Exception as e:
            st.error(f"Gagal membaca {f.name}: {e}")

    df = pd.DataFrame(all_data)
    st.dataframe(df, use_container_width=True)

    avg_wer = df["WER"].mean() if not df.empty else 0
    avg_cer = df["CER"].mean() if not df.empty else 0
    avg_word_acc = df["Word Accuracy (%)"].mean() if not df.empty else 0

    st.markdown("#### 📊 Rata-rata Akurasi Whisper")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rata-rata WER", f"{avg_wer:.3f}")
    col2.metric("Rata-rata CER", f"{avg_cer:.3f}")
    col3.metric("Rata-rata Word Accuracy", f"{avg_word_acc:.2f}%")
