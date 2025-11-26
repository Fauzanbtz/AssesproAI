# app/components/evaluation_runner.py

from pathlib import Path
import json
import streamlit as st

from core.downloader import fetch_video_to_local
from core.media import extract_wav16k
from core.stt import transcribe
from core.evaluator import evaluate_answer
from core.serializer import compose_hr_json
from core.storage import save_candidate_metadata

from components.progress import step


def process_all_answers(videos_input, candidate_id: str, cfg: dict):
    results_all = []

    for idx, entry in enumerate(videos_input, start=1):
        qspec = entry["qspec"]
        source_url = entry.get("source_url")
        upload_file = entry.get("upload_file")
        video_path = entry.get("video_path") 

        if upload_file is not None and video_path is None:
            tmp_dir = Path(cfg["paths"]["tmp_videos"])
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / upload_file.name
            tmp_path.write_bytes(upload_file.read())
            video_path = tmp_path

        if not video_path and not source_url:
            st.warning(f"Question {idx} has no video, skipped.")
            continue

        if source_url and not video_path:
            with step(f"Downloading the question video {idx}..."):
                video_path = fetch_video_to_local(source_url, cfg)

        with step(f"Processing audio & transcript (Question{idx})..."):
            wav = extract_wav16k(video_path, cfg)
            text, segments, meta = transcribe(wav, cfg)

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

        with step(f"Evaluating answer (Question {idx})"):
            result = evaluate_answer(text, qspec, meta, cfg)

        out = compose_hr_json(qspec, text, result, meta, source_url, video_path)
        results_all.append(out)

        save_candidate_metadata(
            candidate_id=candidate_id,
            question=qspec["question_text"]["en"],
            recorded_video_url=source_url if source_url else str(video_path),
            is_video_exist=True,
        )

        st.success(f"Question {idx} successfully saved")

    return results_all
