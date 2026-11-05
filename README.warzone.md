# nightcut für Warzone

Dieser Fork von [Nilson89/nightcut](https://github.com/Nilson89/nightcut) ergänzt ein Profil für **Call of Duty: Warzone** und macht nightcut fit für zwei Fälle, die im Original nicht abgedeckt sind:

1. **Dein Name ist im Spiel ausgeblendet.** Dann stehen deine Kills im Killfeed ohne Schützennamen, und nightcut kann sie nicht zuordnen. Das Warzone-Profil liest stattdessen das Banner **„ELIMINIERT: Name“** unten in der Mitte. Es erscheint nur bei deinen eigenen Kills.
2. **OBS nimmt nur eine Tonspur auf** (Mikro, Spiel und Discord gemischt). Dann ist das Spiel oft so laut wie deine Stimme, und Whisper erfindet Sätze auf Schüssen. `split_tracks.py` trennt vorher Stimmen und Spielsound mit [Demucs](https://github.com/facebookresearch/demucs).

Installation, OBS-Einrichtung und alles andere: [README.de.md](README.de.md).

## Schnellstart (Windows)

1. nightcut wie im Original installieren (`install.bat`), aber dieses Repository verwenden.
2. `config/examples/warzone.yaml` nach `config/local.yaml` kopieren (optional, sonst nimmt `warzone.bat` das Beispiel).
3. Eine oder mehrere Aufnahmen auf **`warzone.bat`** ziehen.

Das Skript trennt die Spuren (etwa 2 Minuten pro 12-Minuten-Runde auf der CPU), schneidet mit dem Warzone-Profil und öffnet den Ergebnisordner. Die getrennte Kopie landet im Ordner `getrennt` neben der Aufnahme; das Original bleibt unverändert.

Von Hand:

```
uv run python split_tracks.py "D:/Aufnahmen/runde.mkv"
uv run nightcut run "D:/Aufnahmen/getrennt/runde.mkv" --profile warzone --config config/local.yaml --no-fill
```

Nimmst du schon mit getrennten OBS-Spuren auf, brauchst du `split_tracks.py` nicht. Benenne die Spuren dann wie in `config/default.yaml` (MIC, GAME, PARTY).

## Was geändert ist

| Datei | Änderung |
| --- | --- |
| `profiles/warzone.yaml` | Neues Profil: Ausrufe (deutsch, auch türkische Ausrufe), Bildhinweise, Gewichtung (Kills vor Reaktionen, ein Tod allein zählt kaum), Banner-Erkennung |
| `config/examples/warzone.yaml` | Einstellungen für Ein-Spur-Aufnahmen: getrennte Spuren, Kills über das Banner, Ziellänge 5 Minuten pro Runde |
| `split_tracks.py` | Trennt Stimmen und Spielsound; schreibt eine Kopie mit den Spuren MIC, GAME und MIX |
| `warzone.bat` | Aufnahmen draufziehen: trennen, schneiden, Ordner öffnen |
| `src/nightcut/killfeed.py` | Ein Profil kann eine eigene Anweisung zum Lesen mitbringen (`killfeed_prompt`) |
| `src/nightcut/vision.py` | Mit `killfeed_confirms_kills: true` zählt ein Kill nur, wenn ihn das Banner bestätigt. Bestätigte Kills stehen in der Beschreibung, damit Titel und Kapitel stimmen |
| `src/nightcut/transcribe.py` | Filter gegen erfundene Sätze („Vielen Dank.“, „Bis zum nächsten Mal“), Wortgruppen in Schleife und denselben Satz Sekunde für Sekunde |
| `src/nightcut/shorts.py` | Shorts-Untertitel ohne Schleifen; reiner Unsinn wird gar nicht angezeigt |
| `tests/test_warzone.py` | Tests für alles oben |

Andere Profile verhalten sich wie im Original. Die Filter gegen erfundene Sätze gelten für alle Spiele.

## Grenzen

- Kalibriert an Resurgence-Aufnahmen in 1920x1080 mit deutscher Spieloberfläche. Andere Auflösungen, Seitenverhältnisse oder HUD-Einstellungen können die Lage des Banners verschieben. Dann `killfeed_region` in `profiles/warzone.yaml` anpassen.
- Die Sprachansagen deines Operators („Letztes Magazin“, „Feind lokalisiert“) landen mit auf der Stimmspur und tauchen manchmal falsch geschrieben in Untertiteln auf.
- Die Performance-Leiste von Warzone (FPS, Latenz) ist in jedem Clip zu sehen, wenn sie beim Aufnehmen eingeschaltet ist. Am besten im Spiel ausblenden.
- Titel, Beschreibung und Kapitel bleiben KI-Entwürfe.

## Lizenz

MIT wie das Original. Urheber von nightcut ist [Nilson89](https://github.com/Nilson89); die Warzone-Ergänzungen stammen von [ademtasdemir-dev](https://github.com/ademtasdemir-dev).
