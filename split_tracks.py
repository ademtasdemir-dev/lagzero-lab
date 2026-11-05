"""Split the voices from the game sound in recordings with a single audio track (Demucs).

nightcut finds reactions on the mic track. When OBS recorded mic, game and Discord into one
track, the game is often as loud as the voice and Whisper invents sentences on gunfire.
This script writes a copy with three audio tracks next to the original, in a folder "getrennt":

  MIC  = voices (you + voice chat), GAME = game sound without voices, MIX = the original track

The video stream is copied, not re-encoded. The original file is not changed.
Demucs runs in its own uvx environment on the CPU (about 2 minutes for a 12-minute round),
so the nightcut environment and its CUDA PyTorch stay untouched.

  uv run python split_tracks.py "D:/Aufnahmen/runde.mkv" ["D:/Aufnahmen/runde2.mkv" ...]
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEMUCS = ["uvx", "--python", "3.12", "--with", "torch==2.5.1", "--with", "torchaudio==2.5.1",
          "--with", "soundfile", "--from", "demucs==4.0.1", "demucs"]


def check_streams(src: Path) -> None:
    """Stop right away for files without picture or sound (e.g. a Twitch download "audio only")."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                          str(src)], capture_output=True, text=True).stdout.split()
    if "video" not in out:
        sys.exit(f"No video stream in {src.name}: the file has sound only (e.g. a Twitch download with "
                 f"quality \"audio only\"). nightcut needs the picture; download it with video.")
    if "audio" not in out:
        sys.exit(f"No audio stream in {src.name}.")


def split(src: Path) -> Path:
    check_streams(src)
    out_dir = src.parent / "getrennt"
    out_dir.mkdir(exist_ok=True)
    target = out_dir / src.name
    if target.exists():
        print(f"Already there: {target}")
        return target
    with tempfile.TemporaryDirectory(prefix="split_") as tmp:
        tmp = Path(tmp)
        wav = tmp / "audio.wav"
        print("1/3 Extracting the audio track ...")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0:a:0", "-ac", "2", "-ar", "44100",
                        str(wav)], check=True)
        print("2/3 Splitting voices from game sound (Demucs, a few minutes) ...")
        subprocess.run(DEMUCS + ["--two-stems", "vocals", "-n", "htdemucs", "-j", "4", "-o", str(tmp / "sep"),
                                 str(wav)], check=True)
        stems = tmp / "sep" / "htdemucs" / "audio"
        print("3/3 Writing the recording with three audio tracks ...")
        part = target.with_suffix(".part.mkv")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(stems / "vocals.wav"),
                        "-i", str(stems / "no_vocals.wav"),
                        "-map", "0:v:0", "-map", "1:a", "-map", "2:a", "-map", "0:a:0",
                        "-c:v", "copy", "-c:a:0", "aac", "-b:a:0", "192k", "-c:a:1", "aac", "-b:a:1", "192k",
                        "-c:a:2", "copy",
                        "-metadata:s:a:0", "title=MIC", "-metadata:s:a:1", "title=GAME",
                        "-metadata:s:a:2", "title=MIX", str(part)], check=True)
        shutil.move(part, target)
    print(f"Done: {target}")
    return target


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        split(Path(arg))
