"""Übernimmt ein ausgefülltes Issue-Formular in pflanzen.json.

Umgebung: ISSUE_BODY, ISSUE_TITLE. Schreibt die Antwort für den Issue-Kommentar nach antwort.md.
"""
import datetime
import io
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATEI = ROOT / "pflanzen.json"

FELDER = {
    "Status": "status", "Name": "name", "Botanischer Name": "botanisch", "Standort": "standort",
    "Herkunft": "herkunft", "Kaufdatum": "kaufdatum", "Shop-Link": "shop_link", "Preis": "preis",
    "Etikett-Text": "etikett", "Foto": "foto", "Neues Foto": "foto", "Notizen": "notizen",
    "Notiz ergänzen": "notiz_neu", "Pflanzen-Nr.": "id",
}


def parsen(body):
    werte = {}
    for block in re.split(r"^### ", body or "", flags=re.M)[1:]:
        label, _, wert = block.partition("\n")
        wert = wert.strip()
        if label.strip() in FELDER and wert and wert != "_No response_":
            werte[FELDER[label.strip()]] = wert
    return werte


def bild_url(text):
    m = re.search(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", text) or re.search(r'<img[^>]+src="(https?://[^"]+)"', text)
    return m.group(1) if m else ""


def foto_speichern(text, pid):
    quelle = bild_url(text)
    if not quelle:
        return ""
    try:
        from PIL import Image, ImageOps
        with urllib.request.urlopen(quelle, timeout=30) as r:
            bild = Image.open(io.BytesIO(r.read()))
        bild = ImageOps.exif_transpose(bild).convert("RGB")
        bild.thumbnail((1400, 1400))
        ziel = ROOT / "fotos" / f"{pid}.jpg"
        ziel.parent.mkdir(exist_ok=True)
        bild.save(ziel, "JPEG", quality=82, optimize=True)
        return f"fotos/{pid}.jpg"
    except Exception as e:  # Fallback: Link direkt verwenden
        print("Foto nicht übernommen:", e)
        return quelle


def main():
    titel = os.environ.get("ISSUE_TITLE", "")
    w = parsen(os.environ.get("ISSUE_BODY", ""))
    pflanzen = json.loads(DATEI.read_text(encoding="utf-8"))
    heute = datetime.date.today().isoformat()

    if titel.startswith("[Ändern]") or "id" in w:
        pid = int(re.sub(r"\D", "", w.get("id", "")) or -1)
        p = next((x for x in pflanzen if x["id"] == pid), None)
        if not p:
            raise SystemExit(f"Pflanze #{pid} nicht gefunden.")
        status = w.pop("status", "unverändert")
        if status == "Löschen":
            pflanzen.remove(p)
            antwort = f"🗑️ #{pid} {p['name']} wurde entfernt."
        else:
            if status in ("Besitz", "Wunsch"):
                p["status"] = status.lower()
                if status == "Besitz" and not p.get("kaufdatum") and "kaufdatum" not in w:
                    p["kaufdatum"] = heute[:7]
            if "foto" in w:
                p["foto"] = foto_speichern(w.pop("foto"), pid) or p.get("foto", "")
            if "notiz_neu" in w:
                neu = f"{heute}: {w.pop('notiz_neu')}"
                p["notizen"] = (p.get("notizen", "") + "\n\n" + neu).strip()
            for k, v in w.items():
                if k != "id":
                    p[k] = v
            antwort = f"✏️ #{pid} {p['name']} wurde aktualisiert."
    else:
        if "name" not in w:
            raise SystemExit("Kein Name angegeben.")
        pid = max([x["id"] for x in pflanzen] + [0]) + 1
        foto = foto_speichern(w.get("foto", ""), pid)
        p = {
            "id": pid, "status": w.get("status", "Besitz").lower(), "name": w["name"],
            "botanisch": w.get("botanisch", ""), "etikett": w.get("etikett", ""),
            "herkunft": w.get("herkunft", ""), "kaufdatum": w.get("kaufdatum", ""),
            "standort": w.get("standort", ""), "shop_link": w.get("shop_link", ""),
            "preis": w.get("preis", ""), "foto": foto, "notizen": w.get("notizen", ""),
            "pflege": {}, "quellen": [],
        }
        pflanzen.append(p)
        antwort = f"🌱 {p['name']} ist jetzt #{pid} ({'Wunschliste' if p['status'] == 'wunsch' else 'Sammlung'})."

    DATEI.write_text(json.dumps(pflanzen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seite = "https://uhlenbrauck.github.io/pflanzen/"
    if any(x["id"] == pid for x in pflanzen):
        antwort += f"\n\nSeite (in 1–2 Minuten aktuell): {seite}#{pid}"
    (ROOT / "antwort.md").write_text(antwort, encoding="utf-8")
    print(antwort)


if __name__ == "__main__":
    main()
