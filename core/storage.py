import json
from pathlib import Path
from datetime import datetime
from typing import Union, Optional, Dict


def save_candidate_metadata(
    candidate_id: str,
    review_data: Optional[Union[dict, None]] = None,
    question: Optional[str] = None,
    recorded_video_url: Optional[str] = None,
    is_video_exist: bool = True,
    base_folder: str = "data/candidates"
) -> Path:
    """
    Menyimpan metadata kandidat dalam format JSON.
    Bisa dipanggil dengan dua cara:
    1️⃣ save_candidate_metadata(candidate_id, review_data={...})
        → Untuk menyimpan semua hasil interview sekaligus.
    2️⃣ save_candidate_metadata(candidate_id, question="...", recorded_video_url="...", is_video_exist=True)
        → Untuk menambahkan satu hasil upload video.

    Args:
        candidate_id (str): ID unik kandidat.
        review_data (dict, optional): Data lengkap kandidat.
        question (str, optional): Pertanyaan (untuk single mode).
        recorded_video_url (str, optional): Path atau URL video.
        is_video_exist (bool): True jika ada video.
        base_folder (str): Folder penyimpanan (default "data/candidates").

    Returns:
        Path: Lokasi file JSON kandidat.
    """

    folder = Path(base_folder)
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{candidate_id}.json"

    # Jika mode 1 (pakai review_data dict)
    if review_data is not None:
        full_data = {
            "candidateId": candidate_id,
            "savedAt": datetime.now().isoformat(),
            **review_data
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        print(f"[storage] ✅ Disimpan (multi-entry) ke {filepath}")
        return filepath

    # Jika mode 2 (single question upload)
    # Load file lama kalau ada
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"candidateId": candidate_id, "createdAt": datetime.now().isoformat(),
                    "reviewChecklists": {"project": "", "interviews": []}}
    else:
        data = {"candidateId": candidate_id, "createdAt": datetime.now().isoformat(),
                "reviewChecklists": {"project": "", "interviews": []}}

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

    print(f"[storage] ✅ Disimpan (single entry) ke {filepath}")
    return filepath
