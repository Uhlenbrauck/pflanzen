"""Erzeugt 3D-druckbare Pflanzenetiketten (3MF) mit QR-Code und Namen.

Drei Varianten pro Pflanze: Klebeschild, Stecker, Anhänger.
Jede 3MF enthält EIN Objekt aus zwei Teilen:
  - "Grundkörper" -> Filament 1 (hell, z. B. weiß)
  - "Code + Text" -> Filament 2 (dunkel, z. B. schwarz), bündig eingelegt
"""
import io
import zipfile

import segno
import shapely
import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely.affinity import scale, translate
from shapely.geometry import Point, Polygon, box

# ---------------------------------------------------------------- Maße (mm)
QR = 27.0            # Kantenlänge QR-Code
RAND = 3.0           # Ruhezone um den Code
W = QR + 2 * RAND    # Breite des Schilds (33)
TEXT_H = 4.0         # max. Schrifthöhe
TEXT_MIN_H = 2.1     # kleiner wird der Text nicht, sonst gekürzt
KOPF_H = RAND + QR + 1.5 + TEXT_H + 2.5   # Höhe Schildkopf (38)
INLAY = 0.6          # Tiefe der Einlage (3 Schichten à 0,2 mm)
ECKE = 3.0           # Eckenradius

VARIANTEN = {
    "klebeschild": {"dicke": 1.6},
    "anhaenger": {"dicke": 2.0},
    "stecker": {"dicke": 2.4},
}

FONT = FontProperties(family="DejaVu Sans", weight="bold")


def _abgerundet(w, h, r):
    return box(r, r, w - r, h - r).buffer(r, resolution=16)


def _qr_flaeche(url, x0, y0):
    qr = segno.make(url, error="m", micro=False)
    matrix = [list(row) for row in qr.matrix]
    n = len(matrix)
    m = QR / n
    felder = []
    for r, row in enumerate(matrix):
        for c, dunkel in enumerate(row):
            if dunkel:
                x = x0 + c * m
                y = y0 + (n - 1 - r) * m
                felder.append(box(x, y, x + m, y + m))
    # minimal aufweiten, damit diagonal berührende Module sauber verschmelzen
    return shapely.union_all(felder).buffer(0.02, join_style="mitre"), qr.version, m


def _text_flaeche(text, max_w, max_h):
    def bauen(t):
        pfad = TextPath((0, 0), t, size=10, prop=FONT)
        geom = Polygon()
        for p in pfad.to_polygons():
            if len(p) >= 3:
                geom = geom.symmetric_difference(Polygon(p).buffer(0))
        return geom

    t = text
    while True:
        g = bauen(t)
        minx, miny, maxx, maxy = g.bounds
        # Schrifthöhe über Versalhöhe skalieren (unabhängig von Unterlängen)
        faktor = min(max_h / 7.3, max_w / (maxx - minx))
        if faktor * 7.3 >= TEXT_MIN_H or len(t) <= 4:
            break
        t = t[:-2].rstrip() + "…"
    g = scale(g, faktor, faktor, origin=(0, 0))
    return g


def _umriss(variante, dicke):
    kopf = _abgerundet(W, KOPF_H, ECKE)
    if variante == "anhaenger":
        lasche = _abgerundet(12, 16, 6)
        lasche = translate(lasche, W / 2 - 6, KOPF_H - 8)
        form = kopf.union(lasche).difference(Point(W / 2, KOPF_H + 3.5).buffer(2.2, resolution=24))
        return form
    if variante == "stecker":
        spiess = Polygon([(W / 2 - 3.5, 1), (W / 2 + 3.5, 1),
                          (W / 2 + 0.6, -75), (W / 2 - 0.6, -75)])
        return kopf.union(spiess)
    return kopf


def _extrudieren(flaeche, hoehe, z0=0.0):
    teile = []
    geoms = getattr(flaeche, "geoms", [flaeche])
    for g in geoms:
        if g.is_empty or g.area < 1e-6:
            continue
        m = trimesh.creation.extrude_polygon(g, hoehe)
        m.apply_translation([0, 0, z0])
        teile.append(m)
    return trimesh.util.concatenate(teile)


def etikett(url, text, variante):
    """Gibt (grundkoerper, einlage) als trimesh-Objekte zurück."""
    dicke = VARIANTEN[variante]["dicke"]
    umriss = _umriss(variante, dicke)
    qr, _, _ = _qr_flaeche(url, RAND, KOPF_H - RAND - QR)
    txt = _text_flaeche(text, W - 3.0, TEXT_H)
    tb = txt.bounds
    txt = translate(txt, W / 2 - (tb[0] + tb[2]) / 2, 2.5 - 0)
    einlage2d = qr.union(txt).intersection(umriss)

    grund2d_oben = umriss.difference(einlage2d)
    unten = _extrudieren(umriss, dicke - INLAY)
    oben = _extrudieren(grund2d_oben, INLAY, dicke - INLAY)
    grund = trimesh.boolean.union([unten, oben], engine="manifold")
    einlage = _extrudieren(einlage2d, INLAY, dicke - INLAY)
    return grund, einlage


# ---------------------------------------------------------------- 3MF
def _mesh_xml(obj_id, mesh, name):
    v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
    t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
    return (f'<object id="{obj_id}" name="{name}" type="model"><mesh>'
            f'<vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')


def als_3mf(grund, einlage, name):
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="de-DE" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{_xml(name)}</metadata>'
        '<metadata name="Application">pflanzen-etiketten</metadata>'
        '<resources>'
        + _mesh_xml(1, grund, "Grundkörper")
        + _mesh_xml(2, einlage, "Code + Text")
        + f'<object id="3" name="{_xml(name)}" type="model"><components>'
        '<component objectid="1"/><component objectid="2"/></components></object>'
        '</resources><build><item objectid="3" transform="1 0 0 0 1 0 0 0 1 100 100 0"/></build></model>'
    )
    # Bambu Studio / OrcaSlicer: Filamentzuordnung pro Teil
    config = (
        '<?xml version="1.0" encoding="UTF-8"?><config>'
        f'<object id="3"><metadata key="name" value="{_xml(name)}"/>'
        '<metadata key="extruder" value="1"/>'
        '<part id="1" subtype="normal_part"><metadata key="name" value="Grundkörper"/>'
        '<metadata key="extruder" value="1"/></part>'
        '<part id="2" subtype="normal_part"><metadata key="name" value="Code + Text"/>'
        '<metadata key="extruder" value="2"/></part>'
        '</object></config>'
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '<Default Extension="config" ContentType="text/xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", config)
    return buf.getvalue()


def _xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://uhlenbrauck.github.io/pflanzen/#1"
    for v in VARIANTEN:
        g, e = etikett(url, "#1 Testetikett", v)
        print(v, g.is_watertight, e.is_watertight, g.bounds.round(2).tolist())
        open(f"test-{v}.3mf", "wb").write(als_3mf(g, e, f"Test {v}"))
