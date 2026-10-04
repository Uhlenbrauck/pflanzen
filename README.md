# 🌿 Unsere Pflanzen

Pflanzendatenbank mit Wunschliste und 3D-druckbaren QR-Etiketten.
Seite: **https://uhlenbrauck.github.io/pflanzen/**

## Benutzen

- **Neue Pflanze / neuer Wunsch:** Auf der Seite unten rechts „+ Pflanze“ bzw. „+ Wunsch“ antippen und das Formular ausfüllen. Nach 1–2 Minuten ist sie auf der Seite, samt Etiketten.
- **Ändern, gekauft, löschen:** Pflanze öffnen → „Ändern“.
- **Pflegeinfos:** Claude sagen „recherchier die neuen Pflanzen“, dann werden Licht, Wasser usw. mit Quellen ergänzt.

Formulare werden nur von dir und eingeladenen Mitwirkenden (Settings → Collaborators) verarbeitet.

## Etiketten drucken (Bambu Studio, AMS)

Pro Pflanze gibt es drei 3MF-Dateien: Klebeschild (1,6 mm), Stecker (2,4 mm) und Anhänger (2,0 mm).

- Jede Datei enthält ein Objekt aus zwei Teilen: **Grundkörper → Filament 1** (hell), **Code + Text → Filament 2** (dunkel).
- Der Code ist 0,6 mm tief bündig eingelegt, gedruckt mit 0,2 mm Schichthöhe.
- Falls die Farben nicht automatisch zugeordnet sind: in der Objektliste den Teil anklicken → Filament wählen.
- Matte Filamente lesen sich am besten; PETG oder ASA für feuchte Standorte.

## Technik

| Datei | Zweck |
|---|---|
| `pflanzen.json` | alle Daten |
| `index.html` | Webseite |
| `tools/etiketten.py` | erzeugt die 3MF-Etiketten |
| `tools/build.py` | baut die Seite nach `_site/` |
| `tools/issue.py` | übernimmt Formulare in `pflanzen.json` |
| `.github/workflows/pflanzen.yml` | Automatik: Formular → Daten → Seite |

## Fotos und Bildnachweis

Eigene Fotos liegen unter `fotos/`. Fremde Bilder nur mit freier Lizenz (Creative Commons): `foto` zeigt dann direkt auf die Quelle, und `bildnachweis` (Urheber, Lizenz, Link) wird unter dem Bild angezeigt. Shop-Fotos nicht kopieren.

## Merkliste

Der Tab „Merkliste“ sammelt Zubehör, Händler, Veranstaltungen, Internetseiten und Sonstiges. Neuer Eintrag über „+ Eintrag“, abhaken oder löschen über „Erledigt / ändern“. Die Daten liegen in `merkliste.json`.

## Gießübersicht

Der Tab „Gießen“ fasst alle Pflanzen nach Standort zusammen. Die Angaben stehen je Pflanze im Feld `giessen` in `pflanzen.json`:

| Feld | Werte |
|---|---|
| `wasser` | `weich` (Regen-, destilliertes, Osmosewasser) oder `leitung` |
| `stufe` | `nass`, `feucht`, `antrocknen`, `trocken`, `tauchen` |
| `methode` | frei, z. B. „Anstau“ |
| `kurz`, `winter` | je ein Satz |

## Recherche-Quellen

Wunschlisten-Einträge werden genauso gründlich recherchiert wie Pflanzen im Besitz: Shopseite plus mindestens eine unabhängige Quelle, Namen prüfen.

Bestimmung und Namen: Fachgesellschaften (International Aroid Society, American Begonia Society, American Orchid Society, Bromeliad Society International, Gesneriad Reference Web, LLIFLE für Sukkulenten und Kakteen), dazu GBIF, Tropicos und die Biodiversity Heritage Library. Für Karnivoren zusätzlich die International Carnivorous Plant Society, für akzeptierte Namen Plants of the World Online (Kew).
