from pathlib import Path
import subprocess
from moviepy import VideoFileClip  

def extract_wav16k(video_path: Path, cfg) -> Path:
    """
    Extracts 16kHz mono WAV audio from a given video file.
    Falls back to ffmpeg subprocess if MoviePy fails (e.g. for webm/Opus audio).
    """
    outdir = Path(cfg["paths"]["tmp_audio"])
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / (video_path.stem + ".16k.wav")

    try:
        # ✅ Bungkus keseluruhan blok MoviePy dalam try
        clip = VideoFileClip(video_path.as_posix())
        clip.audio.write_audiofile(
            out.as_posix(),
            fps=16000,
            nbytes=2,
            codec="pcm_s16le",
            ffmpeg_params=["-ac", "1"]
        )
        clip.close()
        print(f"[INFO] Audio extracted with MoviePy → {out.name}")

    except Exception as e:
        # 🔄 Fallback kalau MoviePy gagal (umumnya untuk .webm Opus)
        print(f"[WARN] MoviePy failed for {video_path.name}: {e}")
        print("[INFO] Falling back to ffmpeg...")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path.as_posix(),
            "-vn",              # no video
            "-ar", "16000",     # 16kHz sample rate
            "-ac", "1",         # mono
            "-c:a", "pcm_s16le",  # 16-bit PCM
            out.as_posix()
        ]
        subprocess.run(cmd, check=True)
        print(f"[INFO] Audio extracted with ffmpeg → {out.name}")

    return out
