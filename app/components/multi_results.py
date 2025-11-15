# app/components/multi_results.py
from pathlib import Path
import json
import streamlit as st

from core.downloader import fetch_video_to_local
from core.media import extract_wav16k
from core.stt import transcribe
from core.evaluator import evaluate_answer
from core.serializer import compose_hr_json
from core.storage import save_candidate_metadata

from app.components.progress import step
from app.components.result import show_json_download

def process_all_answers(videos_input, candidate_id: str, cfg: dict):
    """
    Loop semua pertanyaan:
      - simpan upload ke tmp (kalau ada)
      - download dari URL (kalau ada)
      - extract audio
      - transcribe
      - evaluate
      - simpan metadata + whisper results
    Return: list hasil HR JSON.
    """
    results_all = []

    for entry in videos_input:
        idx = entry["index"]
        qspec = entry["qspec"]
        upload_file = entry["upload_file"]
        video_path = entry["video_path"]
        source_url = entry["source_url"]

        if not upload_file and not video_path and not source_url:
            st.warning(f"Pertanyaan {idx} belum memiliki video, dilewati.")
            continue

        # Jika ada file upload, simpan ke tmp/videos
        if upload_file is not None:
            tmp_dir = Path(cfg["paths"]["tmp_videos"])
            tmp_dir.mkdir(parents=True, exist_ok=True)
            out_path = tmp_dir / upload_file.name
            out_path.write_bytes(upload_file.read())
            video_path = out_path

        # Jika hanya ada link, unduh dulu
        if source_url and not video_path:
            with step(f"Mengunduh video pertanyaan {idx}..."):
                video_path = fetch_video_to_local(source_url, cfg)

        with step(f"Memproses audio & transkrip (Pertanyaan {idx})..."):
            wav = extract_wav16k(video_path, cfg)
            text, segments, meta = transcribe(wav, cfg)

            # Simpan hasil Whisper ke folder baru
            whisper_folder = Path("tmp/whisper_results")
            whisper_folder.mkdir(parents=True, exist_ok=True)
            whisper_file = whisper_folder / f"{candidate_id}_q{idx}.json"

            whisper_data = {
                "candidate_id": candidate_id,
                "question_id": idx,
                "question": qspec["question_text"]["en"],
                "transcript": text,
                "segments": segments,
                "meta": meta,
            }

            with open(whisper_file, "w", encoding="utf-8") as f:
                json.dump(whisper_data, f, ensure_ascii=False, indent=2)

        with step(f"Mengevaluasi jawaban (Pertanyaan {idx})..."):
            result = evaluate_answer(text, qspec, meta, cfg)

        out = compose_hr_json(qspec, text, result, meta, source_url, video_path)
        results_all.append(out)

        # Simpan metadata kandidat
        save_candidate_metadata(
            candidate_id=candidate_id,
            question=qspec["question_text"]["en"],
            recorded_video_url=source_url if source_url else str(video_path),
            is_video_exist=True
        )

        st.success(f"Pertanyaan {idx} berhasil dievaluasi dan disimpan untuk kandidat {candidate_id}")

        # Ekspander untuk lihat hasil Whisper
        with st.expander(f"Transkrip Pertanyaan {idx}"):
            st.text_area("Transkrip", text, height=200)
            st.json(meta)

    return results_all

def show_summary_and_download(results_all, candidate_id: str):
    """
    Tampilkan rekap semua hasil + download JSON (pakai komponen result).
    """
    if not results_all:
        return

    st.markdown("---")
    st.subheader("Rekapitulasi Hasil Evaluasi Seluruh Pertanyaan")

    all_json = {
        "candidateId": candidate_id,
        "totalQuestions": len(results_all),
        "results": results_all
    }

    # Bisa pakai komponen yang sudah ada
    show_json_download(all_json, filename=f"{candidate_id}_all_results.json")
