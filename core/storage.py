# core/storage.py
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

def save_candidate_metadata(
    candidate_id: str,
    question: str,
    recorded_video_url: str,
    is_video_exist: bool = True,
    base_folder: str = "data/candidates"
) -> Path:
    """
    Save or append a single interview metadata entry for a candidate.
    - candidate_id: unique id for candidate (e.g. "001")
    - question: question text (string)
    - recorded_video_url: url or local path to the video
    - is_video_exist: boolean flag
    - base_folder: folder where candidate json files are stored
    Returns Path to saved file.
    """

    folder = Path(base_folder)
    folder.mkdir(parents=True, exist_ok=True)

    filepath = folder / f"{candidate_id}.json"

    # If file exists, load it; otherwise create base structure
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # If file is corrupted, create new structure instead of crashing
            data = {"candidateId": candidate_id, "createdAt": datetime.now().isoformat(),
                    "reviewChecklists": {"project": [], "interviews": []}}
    else:
        data = {"candidateId": candidate_id, "createdAt": datetime.now().isoformat(),
                "reviewChecklists": {"project": [], "interviews": []}}

    # Build new interview entry and append
    next_pos = len(data["reviewChecklists"].get("interviews", [])) + 1
    new_entry = {
        "positionId": next_pos,
        "question": question,
        "isVideoExist": is_video_exist,
        "recordedVideoUrl": recorded_video_url
    }

    data["reviewChecklists"].setdefault("interviews", []).append(new_entry)

    # Save back to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[storage] saved metadata for candidate {candidate_id} -> {filepath}")
    return filepath
