from pathlib import Path

from nightcut.media import AudioStream, MediaInfo

OBS = ["GAME", "MIC Main Headset", "MIC Tonor", "DESKTOP", "DISCORD, TS und TIPEESTREAM", "STREAM"]
INFO = MediaInfo(Path("x.mkv"), 60.0, 2560, 1440, 60.0,
                 [AudioStream(i + 1, i, t, 2, 48000) for i, t in enumerate(OBS)])


def test_exact_title_wins():
    assert INFO.find_audio({"title": "GAME", "index": 2}).title == "GAME"


def test_title_matches_start_of_longer_name():
    assert INFO.find_audio({"title": "MIC", "index": 5}).title == "MIC Main Headset"
    assert INFO.find_audio({"title": "MIC Tonor", "index": 0}).title == "MIC Tonor"


def test_title_list_and_whole_words_only():
    spec = {"title": ["PARTY", "DISCORD", "TEAMSPEAK"], "index": 3}
    assert INFO.find_audio(spec).title.startswith("DISCORD")
    # "STREAM" must not be found by a name that is only part of a word
    assert INFO.find_audio({"title": "STREA", "index": None}) is None


def test_falls_back_to_position():
    assert INFO.find_audio({"title": "PARTY", "index": 3}).title == "DESKTOP"
    assert INFO.find_audio(None) is None


def test_audio_only_file_gets_a_clear_error(tmp_path, monkeypatch):
    import json
    import subprocess

    import pytest

    from nightcut import media

    streams = {"streams": [{"index": 0, "codec_type": "audio", "channels": 2, "sample_rate": "48000"}],
               "format": {"duration": "1306.5"}}
    monkeypatch.setattr(media, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps(streams), ""))
    with pytest.raises(ValueError, match="no video stream"):
        media.probe(tmp_path / "audio_only.mp4")
