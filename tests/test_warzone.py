"""Warzone profile and the clean-ups it needs: hidden player name, single-track recordings."""

from pathlib import Path

from nightcut import killfeed, vision
from nightcut.config import load_config
from nightcut.shorts import clean_words
from nightcut.transcribe import drop_repeats, is_noise

ROOT = Path(__file__).resolve().parents[1]


def _words(text: str) -> list[dict]:
    return [{"start": float(i), "end": i + 0.3, "text": w} for i, w in enumerate(text.split())]


def test_profile_and_example_config_load():
    cfg = load_config(ROOT / "config" / "examples" / "warzone.yaml", "warzone")
    assert cfg["profile"]["name"] == "Warzone"
    assert cfg["killfeed"]["player_names"] == ["ME"]
    assert cfg["audio"]["mic"]["title"] == "MIC" and cfg["audio"]["party"] is None
    prompt = cfg["profile"]["killfeed_prompt"].format(n=6)          # braces escaped for .format
    assert "stack of 6 panels" in prompt and "ELIMINIERT" in prompt and '{"panels": []}' in prompt


def test_banner_readings_count_as_player_kills():
    answer = {"panels": [{"panel": 1, "kills": [{"killer": "ME", "victim": "Gegner_Eins"}]},
                         {"panel": 2, "kills": [{"killer": "ME", "victim": "Gegner_Eins"}]},
                         {"panel": 4, "kills": [{"killer": "ME", "victim": "Gegner_Zwei"}]}]}
    readings = killfeed.parse_answer(answer, [100.0, 102.0, 104.0, 106.0])
    kills = killfeed.player_kills(readings, ["ME"])
    assert [k["victim"] for k in kills] == ["Gegner_Eins", "Gegner_Zwei"]   # banner stays visible: counted once


def test_unconfirmed_kill_becomes_reaction_only_with_the_switch():
    def cands():
        return [{"score": 2.5, "vision": {"event": "multikill", "intensity": 9, "summary": "Absprung"}},
                {"score": 1.0, "kills": 3, "vision": {"event": "nothing", "intensity": 2, "summary": "Dach"}}]

    cfg = {"profile": {"killfeed_confirms_kills": True}, "killfeed": {"player_names": ["ME"]}}
    on = cands()
    vision.rescore(on, cfg)
    assert on[0]["vision"]["event"] == "reaction" and on[0]["vision"]["intensity"] == 5
    assert on[1]["vision"]["event"] == "multikill"
    assert on[1]["final_score"] > on[0]["final_score"]
    assert on[1]["vision"]["summary"].startswith("Kill feed: 3 kills")

    off = cands()                                                    # other profiles keep the old behaviour
    vision.rescore(off, {"profile": {}, "killfeed": {"player_names": ["Nilson1489"]}})
    assert off[0]["vision"]["event"] == "multikill"


def test_summary_prefix_is_added_once():
    c = [{"score": 1.0, "kills": 1, "vision": {"event": "kill", "intensity": 7, "summary": "x"}}]
    vision.rescore(c)
    vision.rescore(c)
    assert c[0]["vision"]["summary"] == "Kill feed: 1 kill by the player. x"


def test_invented_phrases_and_loops_are_noise():
    for text in ("Du bist der Nacht du bist der Nacht du bist der Nacht du bist der Nacht",
                 "die gibt's, die gibt's, die gibt's, die gibt's, die gibt's",
                 "Bis zum nächsten Mal.", "Das war's für heute.", "Vielen Dank."):
        assert is_noise(text), text
    for text in ("Nein, nein, nein!", "Ja, jetzt hab ich ihn!", "Oh mein Gott, alter!",
                 "Vielen Dank, Bruder, hast mich gerettet"):
        assert not is_noise(text), text


def test_repeated_segments_keep_the_first_two():
    segs = [{"start": float(t), "end": t + 0.5, "text": "Was ist das?"} for t in range(280, 310)]
    segs += [{"start": 300.5, "end": 301.0, "text": "Boah!"}, {"start": 400.0, "end": 401.0, "text": "was ist das"}]
    out = drop_repeats(segs)
    assert [(s["start"], s["text"]) for s in out] == [(280.0, "Was ist das?"), (281.0, "Was ist das?"),
                                                       (300.5, "Boah!"), (400.0, "was ist das")]


def test_caption_loops_are_cut():
    text = lambda ws: [w["text"] for w in ws]   # noqa: E731
    assert text(clean_words(_words("Oh mein Gott Oh mein Gott du bist der Nacht du bist der Nacht"))) == \
        ["Oh", "mein", "Gott", "du", "bist", "der", "Nacht"]
    assert text(clean_words(_words("Nein nein nein der ist down"))) == ["Nein", "nein", "nein", "der", "ist", "down"]
    assert text(clean_words(_words("Ja hab ihn"))) == ["Ja", "hab", "ihn"]
    assert clean_words(_words("Vielen Dank")) == []
