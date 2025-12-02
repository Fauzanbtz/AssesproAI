Berikut **README baru** yang sudah disesuaikan dengan arsitektur TERBARU project kamu (full LLM evaluator, pipeline Whisper sederhana, storage kandidat, dan HR Dashboard). Struktur dan penjelasan dibuat **rapih, profesional, dan ringkas**, sesuai standar project production.

---

# **Assespro AI — Automated Interview Assessment (LLM + Whisper)**

Sistem penilaian interview berbasis video menggunakan:

* **Audio Extraction (FFmpeg)**
* **Whisper Speech-to-Text**
* **Groq LLM Scoring** (llama-3.1-8b-instant)
* **Structured Question Bank YAML**
* **Streamlit UI (Candidate & HR Dashboard)**

Pipeline otomatis:
**Video → Audio → Transcription → LLM Evaluator → Candidate JSON → HR Dashboard Review**

---

# **📁 Struktur Folder**

```bash
AssesproAI/
├─ app/
│  ├─ app.py                      # Kandidat upload + kirim jawaban
│  ├─ Assespro.jpg                # Logo header
│  ├─ dev.png                     # Gambar untuk halaman Dev
│  ├─ components/                 # Komponen Streamlit
│  │  ├─ evaluation_runner.py     # Jalankan pipeline STT → LLM
│  │  ├─ multi_question_form.py   # UI multi-pertanyaan (upload video)
│  │  ├─ multi_results.py         # Summary hasil evaluasi kandidat
│  │  ├─ progress.py              # Long-running indicators
│  │  ├─ whisper_viewer.py        # Analisis whisper (opsional)
│  │  └─ result.py                # UI kecil untuk hasil tunggal
│  ├─ pages/
│  │  ├─ 1_HR_Dashboard.py        # Dashboard HR untuk review kandidat
│  │  └─ 2_About_Dev.py           # Halaman profil tim Developer
│
├─ core/
│  ├─ config.py                   # Baca config.yaml
│  ├─ question_bank.py            # Load dan normalisasi YAML pertanyaan
│  ├─ llm_evaluator.py            # Evaluasi jawaban dengan Groq LLM
│  ├─ evaluator.py                # Wrapper pipeline STT + LLM
│  ├─ stt.py                      # Whisper transcription
│  ├─ media.py                    # Extract audio 16k mono
│  ├─ downloader.py               # Download video dari URL (opsional)
│  ├─ serializer.py               # Format final JSON bagi HR
│  ├─ storage.py                  # Simpan jawaban kandidat ke /data
│  └─ utils.py                    # Helper umum
│
├─ data/
│  ├─ question_bank.yaml          # Bank pertanyaan (rubric, context, constraints)
│  ├─ candidate_answers/          # Hasil evaluasi setiap kandidat
│  └─ candidates_metadata/        # Metadata kandidat (opsional)
│
├─ tmp/
│  ├─ videos/                     # Video upload kandidat
│  ├─ audio/                      # Audio setelah extract
│  └─ transcripts/                # Transkripsi Whisper
│
├─ tests/
│  ├─ app.py                      # Testing manual (opsional)
│
├─ config.yaml                    # Konfigurasi model + LLM
├─ requirements.txt               # Dependencies
├─ .env.example                   # Template API keys (Groq)
└─ README.md
```

---

# **⚙️ Teknologi yang Digunakan**

| Komponen       | Teknologi                       |
| -------------- | ------------------------------- |
| Speech-to-Text | Whisper (openAI / CTranslate2)  |
| LLM Scoring    | Groq API – llama-3.1-8b-instant |
| Video → Audio  | FFmpeg                          |
| UI             | Streamlit multipage             |
| Data Storage   | JSON structured per candidate   |
| Config         | YAML-based question bank        |

---

# **🚀 Cara Menjalankan Project**

## **1. Install Requirements**

```bash
pip install -r requirements.txt
```

## **2. Siapkan file `.env`**

```
GROQ_API_TOKEN=your_api_key_here
```

## **3. Jalankan Aplikasi**

```bash
streamlit run app/app.py
```

## **4. HR Dashboard**

Streamlit otomatis memuat halaman HR:

```
app/pages/1_HR_Dashboard.py
```

---

# **🧩 Arsitektur Pipeline**

```
[1] Video Upload Kandidat
     ↓
[2] Extract Audio (FFmpeg → WAV 16k)
     ↓
[3] Speech-to-Text (Whisper)
     ↓
[4] Ambil Question Spec dari YAML (rubric + context)
     ↓
[5] Kirim ke Groq LLM Evaluator
     ↓
[6] LLM menghasilkan skor 0–4 + alasan
     ↓
[7] Simpan JSON ke /data/candidate_answers/<ID>.json
     ↓
[8] HR Dashboard membaca & menampilkan secara lengkap
```

---

# **📝 Format Output Candidate Answers**

Contoh ringkas file:

```json
{
  "candidateId": "C123",
  "savedAt": "...",
  "totalQuestions": 5,
  "results": [
    {
      "qid": "Q01",
      "question_text": "...",
      "transcript": "...",
      "asr": { "avg_logprob": -4.1, "no_speech_prob": 0.17 },
      "rubric": {
        "predicted_point": 2,
        "reason": "Candidate explained..."
      },
      "llm": {
        "model": "llama-3.1-8b-instant",
        "backend": "groq"
      }
    }
  ]
}
```

---

# **💡 Fitur Utama Project**

### **1. Full LLM Scoring**

Tidak lagi memakai similarity, SBERT, keywords, atau struktur jawaban.
Hanya:

* whisper transcript
* question<context + rubric + constraints>
* LLM scoring (0–4)

### **2. YAML Question Bank yang Fleksibel**

Per-pertanyaan dapat mengatur:

* rubric 0–4
* llm_context
* hard_constraints
* ideal answer
* must keywords (jika ingin)

### **3. HR Dashboard Profesional**

HR dapat:

* memilih kandidat
* membuka hasil per-pertanyaan
* melihat reasoning LLM
* melihat transcript
* download JSON

### **4. Storage Otomatis**

* `/data/candidate_answers/<ID>.json`
* `/tmp/videos`
* `/tmp/audio`
* `/tmp/transcripts`

