##  Struktur Folder

```bash
ai-interview-assessment/
├─ app/
│  ├─ app.py                      # Entry Streamlit (UI)
│  ├─ components/                 # Komponen UI terpisah
│  │  ├─ __init__.py
│  │  ├─ inputs.py                # select QID, input link/upload
│  │  ├─ results.py               # panel JSON HR, download button, tables
│  │  └─ progress.py              # spinners, progress bars
│  ├─ pages/                      # (opsional) halaman tambahan streamlit
│  │  ├─ 1_Evaluation.ipynb       # halaman edukasi (notebook) – optional
│  │  └─ 2_Docs.md                # dokumentasi singkat
│  └─ __init__.py
│
├─ core/                          # Business logic (tanpa UI)
│  ├─ __init__.py
│  ├─ config.py                   # baca config.yaml & env vars
│  ├─ question_bank.py            # load YAML/JSON pertanyaan & ideal answers
│  ├─ downloader.py               # fetch video dari URL (yt-dlp, gdown, direct)
│  ├─ media.py                    # ekstraksi audio, normalisasi (ffmpeg/moviepy)
│  ├─ stt.py                      # Speech-to-Text (Whisper / faster-whisper)
│  ├─ nlp_preprocess.py           # cleaning, stopword, slang dict, stemming
│  ├─ language_router.py          # deteksi bahasa (fastText/langdetect/whisper)
│  ├─ similarity.py               # Sentence-BERT similarity
│  ├─ keywords.py                 # keyword coverage (must/nice)
│  ├─ structure.py                # skor struktur jawaban (intro-body-closing)
│  ├─ confidence.py               # gabungan ASR_conf, Lang_conf, Agree_conf, Len_conf
│  ├─ evaluator.py                # hitung PerformanceScore + ConfidenceScore
│  ├─ serializer.py               # compose output JSON untuk HR
│  └─ utils.py                    # helper umum (timer, io, text normalize)
│
├─ models/                        # cache/model artefacts
│  ├─ README.md
│  └─ (auto cached)               # SBERT, fastText lid.176.bin, dll.
│
├─ data/
│  ├─ question_bank.yaml          # definisi QID, ideal answer, keywords, weight
│  ├─ slang_dict.json             # kamus normalisasi (opsional)
│  ├─ stopwords_id.txt            # (opsional, jika custom)
│  └─ samples/                    # contoh video & GT untuk demo/test
│
├─ experiments/                   # notebook eksplorasi (bebas)
│  ├─ 01_whisper_eval.ipynb
│  ├─ 02_similarity_calibration.ipynb
│  └─ 03_streamlit_prototype.ipynb
│
├─ evaluation/                    # skrip evaluasi akurasi STT
│  ├─ compute_wer.py              # batch WER/CER → CSV + ringkasan
│  └─ datasets/
│     ├─ audio/                   # *.wav
│     └─ gt/                      # *.txt (ground truth)
│
├─ tmp/                           # artefak runtime (gitignore)
│  ├─ videos/                     # unduhan video mentah
│  ├─ audio/                      # wav 16k mono
│  └─ transcripts/                # txt/srt/json segmen
│
├─ logs/
│  └─ app.log                     # logging pipeline
│
├─ tests/
│  ├─ test_downloader.py
│  ├─ test_stt.py
│  ├─ test_evaluator.py
│  └─ test_confidence.py
│
├─ config.yaml                    # konfigurasi global (paths, model size, thresholds)
├─ requirements.txt               # dependensi
├─ .env.example                   # ENV (MODEL_SIZE, CUDA, API KEYS jika perlu)
├─ .gitignore
└─ README.md
```

---

## File Penting

### `requirements.txt`
```bash
streamlit
moviepy
ffmpeg-python
yt-dlp
requests
whisper
faster-whisper
sentence-transformers
langdetect
pyyaml
pandas
numpy
jiwer
Sastrawi
```
---

##  Cara Menjalankan

```bash
# 1. Buat virtual environment
python -m venv .venv
source .venv/bin/activate     # (Windows: .venv\Scripts\activate)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan aplikasi Streamlit
streamlit run app/app.py
```

---

##  Deskripsi Modul

| Folder | Fungsi |
|--------|---------|
| `app/` | Antarmuka Streamlit (UI HR) |
| `core/` | Logika utama: STT, NLP, scoring |
| `data/` | Bank pertanyaan & kamus teks |
| `evaluation/` | Pengujian akurasi STT (WER/CER) |
| `experiments/` | Eksperimen & notebook riset |
| `tmp/` | Artefak runtime (video/audio/temp) |
| `tests/` | Unit test modular |
| `models/` | Cache model SBERT / FastText |

---

>  **Catatan tambahan:**
> - Target akurasi *Speech-to-Text (STT)* minimal **≥ 90%** (berdasarkan Word Error Rate).  
> - Pipeline lengkap: **Video → Audio → Transkrip → Analisis → JSON HR-friendly**.  
> - Folder `data/samples/` digunakan untuk contoh video dan dataset pengujian.
> - buat file tmp yang isinya /audio, /transcripts , /videos



Video (.mp4)
   ↓
Audio (16k WAV)
   ↓
Whisper STT
   ↓
Transcript + Metadata
   ↓
 ┌─────────────────────────────┐
 │  EVALUATOR CORE             │
 │  ├─ Layer 1: SBERT Similarity│
 │  ├─ Layer 2: Keyword, Structure, Confidence │
 │  └─ Layer 3: Semantic Rubric Matching (0–4) │
 └─────────────────────────────┘
   ↓
Performance + Confidence + Rubric Grade
   ↓
JSON Output (for HR)


| Layer   | Fitur                                     |
| ------- | ----------------------------------------- |
| Layer 1 | SBERT similarity, segment-max similarity  |
| Layer 2 | keyword coverage, structure, token length |
| Layer 3 | semantic match ke rubric P0..P4           |
