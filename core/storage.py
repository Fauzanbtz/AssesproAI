import json
from pathlib import Path
from datetime import datetime
from typing import Union, Optional, Dict, List


def save_candidate_metadata(
    candidate_id: str,
    review_data: Optional[Union[dict, None]] = None,
    question: Optional[str] = None,
    recorded_video_url: Optional[str] = None,
    is_video_exist: bool = True,
    base_folder: str = "data/candidates_metadata"
) -> Path:
    folder = Path(base_folder)
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{candidate_id}.json"

    # Mode 1 (full review_data → overwrite)
    if review_data is not None:
        full_data = {
            "candidateId": candidate_id,
            "savedAt": datetime.now().isoformat(),
            **review_data
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        print(f"[storage]  Disimpan (multi-entry) ke {filepath}")
        return filepath

    # Mode 2 (append single interview entry)
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {
                "candidateId": candidate_id,
                "createdAt": datetime.now().isoformat(),
                "reviewChecklists": {"project": "", "interviews": []}
            }
    else:
        data = {
            "candidateId": candidate_id,
            "createdAt": datetime.now().isoformat(),
            "reviewChecklists": {"project": "", "interviews": []}
        }

    next_pos = len(data["reviewChecklists"].get("interviews", [])) + 1
    new_entry = {
        "positionId": f"Q{next_pos:02}",
        "question": question or "N/A",
        "isVideoExist": is_video_exist,
        "recordedVideoUrl": recorded_video_url or "N/A"
    }

    data["reviewChecklists"].setdefault("interviews", []).append(new_entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[storage] Disimpan (single entry) ke {filepath}")
    return filepath


def save_candidate_answers(
    candidate_id: str,
    results_all: List[dict],
    base_folder: str = "data/candidate_answers"
) -> Path:
    folder = Path(base_folder)
    folder.mkdir(parents=True, exist_ok=True)

    payload = {
        "candidateId": candidate_id,
        "savedAt": datetime.now().isoformat(),
        "totalQuestions": len(results_all),
        "results": results_all,
    }

    out_path = folder / f"{candidate_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[storage] candidate_answers disimpan ke {out_path}")
    return out_path
