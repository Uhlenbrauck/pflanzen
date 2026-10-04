"""Baut die Webseite nach _site/ und erzeugt die Etiketten für alle Pflanzen im Besitz."""
import json
import os
import shutil
from pathlib import Path

from etiketten import VARIANTEN, als_3mf, etikett

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
BASIS_URL = os.environ.get("BASIS_URL", "https://uhlenbrauck.github.io/pflanzen/")


def main():
    pflanzen = json.loads((ROOT / "pflanzen.json").read_text(encoding="utf-8"))
    ids = [p["id"] for p in pflanzen]
    assert len(ids) == len(set(ids)), "Doppelte IDs in pflanzen.json"

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    for datei in ("index.html", "pflanzen.json", "merkliste.json"):
        shutil.copy(ROOT / datei, SITE / datei)
    if (ROOT / "fotos").exists():
        shutil.copytree(ROOT / "fotos", SITE / "fotos")

    for p in pflanzen:
        if p.get("status") != "besitz":
            continue
        text = p.get("etikett") or f"#{p['id']} {p['name']}"
        url = f"{BASIS_URL}#{p['id']}"
        ordner = SITE / "etiketten" / str(p["id"])
        ordner.mkdir(parents=True)
        for v in VARIANTEN:
            grund, einlage = etikett(url, text, v)
            (ordner / f"{p['id']}-{v}.3mf").write_bytes(als_3mf(grund, einlage, f"{text} ({v})"))
        print(f"Etiketten #{p['id']}: {text}")


if __name__ == "__main__":
    main()
