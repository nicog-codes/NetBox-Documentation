#!/usr/bin/env python3
"""Nutanix VSSX -> PNG -> NetBox elevations. Dry run by default.
Use --apply only AFTER reviewing /data/controle.html.
Requires NETBOX_URL and NETBOX_TOKEN; NETBOX_TLS_VERIFY=false for temporary local TLS exception.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path

import requests
from lxml import etree
from PIL import Image

SOURCES = (
    "NTNX-stencil_G10_2026-03-17.zip",
    "NTNX-stencil_G9_2025-05-14.zip",
    "NTNX-stencil_G8_2022-03-10.zip",
    "NTNX-stencil_2019-08-01.zip",
)
SOURCE_BASE = "https://www.visiocafe.com/downloads/nutanix/"
PNG = b"\x89PNG\r\n\x1a\n"


def netbox_models():
    host = os.environ["NETBOX_URL"].rstrip("/")
    token = os.environ["NETBOX_TOKEN"]
    session = requests.Session()
    session.headers["Authorization"] = (
        ("Bearer" if token.startswith("nbt_") else "Token") + " " + token
    )
    bundle = os.getenv("NETBOX_CA_BUNDLE")
    session.verify = bundle if bundle else os.getenv("NETBOX_TLS_VERIFY", "true").lower() not in ("false", "0", "no")
    if session.verify is False:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("WARNING: TLS verification disabled for this run")
    url = host + "/api/dcim/device-types/"
    params = {"manufacturer": "nutanix", "limit": 100}
    items = []
    while url:
        response = session.get(url, params=params, timeout=40)
        response.raise_for_status()
        result = response.json()
        items += result["results"]
        url, params = result.get("next"), None
        if len(items) > 1000:
            raise RuntimeError("Abnormal pagination from NetBox; abort")
    models = {
        i["model"] for i in items
        if i.get("manufacturer", {}).get("name", "").casefold() == "nutanix"
    }
    if not models:
        raise RuntimeError("No Nutanix Device Types found in NetBox")
    print(f"NetBox: {len(models)} Nutanix Device Types")
    return models


def download(name, cache):
    path = cache / name
    if path.is_file():
        try:
            with zipfile.ZipFile(path) as z:
                if z.testzip() is None:
                    print("CACHED", name)
                    return path
        except zipfile.BadZipFile:
            pass
        path.unlink()
    print("DOWNLOAD", name, flush=True)
    response = requests.get(SOURCE_BASE + name, timeout=100)
    response.raise_for_status()
    if len(response.content) > 35_000_000:
        raise RuntimeError("Archive too large")
    temp = path.with_suffix(".tmp")
    temp.write_bytes(response.content)
    with zipfile.ZipFile(temp) as z:
        if z.testzip() is not None:
            raise RuntimeError("Corrupted archive")
    temp.replace(path)
    return path


def stencils(archive, folder):
    with zipfile.ZipFile(archive) as z:
        for n, info in enumerate(z.infolist()):
            if not info.filename.lower().endswith((".vssx", ".vss")):
                continue
            if info.file_size > 60_000_000:
                continue
            dest = folder / (archive.stem + "-" + str(n) + Path(info.filename).suffix.lower())
            if not dest.exists():
                dest.write_bytes(z.read(info))
            yield dest


def master_names(file):
    if file.suffix != ".vssx":
        return []
    try:
        with zipfile.ZipFile(file) as z:
            name = next((n for n in z.namelist() if n.lower().endswith("/masters/masters.xml")), None)
            if not name:
                return []
            root = etree.fromstring(z.read(name), etree.XMLParser(resolve_entities=False, no_network=True))
            return [
                m.get("NameU") or m.get("Name") or ""
                for m in root.xpath('//*[local-name()="Master"]')
            ]
    except (zipfile.BadZipFile, etree.XMLSyntaxError):
        return []


def shapes(file, names):
    if not names:
        return []
    try:
        run = subprocess.run(
            ["vss2xhtml", str(file)], capture_output=True, timeout=240
        )
        if run.returncode:
            print("CONVERT FAILED", file.name, run.stderr[:150])
            return []
        root = etree.fromstring(
            run.stdout,
            etree.XMLParser(resolve_entities=False, no_network=True, recover=True)
        )
        svgs = root.xpath(
            '//*[local-name()="svg" and not(ancestor::*[local-name()="svg"])]'
        )
        if len(svgs) != len(names):
            print("SKIP UNKNOWN MASTER ORDER", file.name, len(names), len(svgs))
            return []
        return list(zip(names, svgs))
    except (subprocess.TimeoutExpired, etree.XMLSyntaxError) as exc:
        print("CONVERT ERROR", file.name, exc)
        return []


def identify(title, models):
    matching = [
        model for model in models
        if re.search(r'(?<![A-Za-z0-9])' + re.escape(model) + r'(?![A-Za-z0-9])', title, re.I)
    ]
    if len(matching) != 1:
        return None
    # Exclude option-only views that do not represent the entire server.
    if re.search(r'(?<![A-Za-z])(?:aiom|pcie|gpu|nic|bezel|option)(?![A-Za-z])', title, re.I):
        return None
    front = bool(re.search(r'(?<![A-Za-z])front(?![A-Za-z])', title, re.I))
    rear = bool(re.search(r'(?<![A-Za-z])(?:rear|back)(?![A-Za-z])', title, re.I))
    if front == rear:
        return None
    return matching[0], "front" if front else "rear"


def render(svg, out):
    content = etree.tostring(svg, encoding="utf-8", xml_declaration=True)
    if any(x in content.lower() for x in (b"image/x-emf", b"image/emf", b"image/x-wmf", b"image/wmf")):
        return "EMF/WMF requires enhanced converter (RackLibrary)"
    run = subprocess.run(
        ["rsvg-convert", "-w", "1200"], input=content, capture_output=True, timeout=60
    )
    if run.returncode or not run.stdout.startswith(PNG):
        return "SVG -> PNG failed"
    try:
        im = Image.open(BytesIO(run.stdout)).convert("RGBA")
        if im.width < 150 or im.height < 10 or im.getchannel("A").getbbox() is None:
            return "Empty or implausible PNG"
        im.save(out, "PNG", optimize=True)
    except Exception as exc:
        return str(exc)
    return None


def racklibrary_zip_candidates(folder, models, issues):
    """Optional: process PNGs and manifest.json exported from RackLibrary, in bulk."""
    result = defaultdict(list)
    folder.mkdir(exist_ok=True)
    for path in folder.glob("*.zip"):
        try:
            with zipfile.ZipFile(path) as z:
                manifest = json.loads(z.read("manifest.json"))
                for item in manifest.get("shapes", []):
                    view = item.get("view", "")
                    title = str(item.get("name") or "") + " " + str(view or "")
                    model_side = identify(title, models)
                    member = item.get("files", {}).get("png")
                    if not model_side or not member or member not in z.namelist():
                        continue
                    if z.getinfo(member).file_size > 15_000_000:
                        continue
                    content = z.read(member)
                    if content.startswith(PNG):
                        result[model_side].append((title, content))
        except (KeyError, zipfile.BadZipFile, ValueError) as exc:
            issues.append(f"Bad RackLibrary ZIP {path.name}: {exc}")
    return result


def gallery(root, entries, warnings):
    cells = []
    for e in entries:
        image = html.escape("png/" + e["file"], quote=True)
        title = html.escape(e["model"] + " " + e["side"])
        source = html.escape(e["master"])
        cells.append(f"<article><h3>{title}</h3><img src='{image}'><small>{source}</small></article>")
    page = (
        "<!doctype html><meta charset='utf-8'><title>Nutanix PNG review</title>"
        "<style>body{font:14px Arial;background:#f1f2f5;padding:20px}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:14px}"
        "article{background:white;padding:12px}img{width:100%;height:140px;object-fit:contain}</style>"
        "<h1>Vérification des vues Nutanix avant import NetBox</h1>"
        "<p>Vérifier modèle, face et qualité d'image avant --apply.</p><main>"
        + "\n".join(cells) + "</main><h2>Points à revoir</h2><pre>"
        + html.escape("\n".join(warnings)) + "</pre>"
    )
    (root / "controle.html").write_text(page, encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    root = Path("/data")
    for sub in ("archives", "stencils", "png", "racklibrary"):
        (root / sub).mkdir(exist_ok=True, parents=True)
    models = netbox_models()
    candidates = defaultdict(list)
    issues = []
    for name in SOURCES:
        try:
            archive = download(name, root / "archives")
        except Exception as exc:
            print("SOURCE FAILED", name, exc)
            issues.append(f"Failed source {name}: {exc}")
            continue
        for file in stencils(archive, root / "stencils"):
            for title, svg in shapes(file, master_names(file)):
                key = identify(title, models)
                if key:
                    candidates[key].append((title, svg))
    # RackLibrary handles embedded EMF/WMF more faithfully. Prefer its bulk PNGs.
    candidates.update(racklibrary_zip_candidates(root / "racklibrary", models, issues))
    ready = []
    for (model, side), variants in sorted(candidates.items()):
        if len(variants) != 1:
            issues.append(f"AMBIGUOUS {model}.{side}: {len(variants)} variants; skipped")
            continue
        title, artwork = variants[0]
        file = f"{model}.{side}.png"
        dest = root / "png" / file
        if not dest.exists():
            if isinstance(artwork, bytes):
                dest.write_bytes(artwork)
                error = None
            else:
                error = render(artwork, dest)
            if error:
                issues.append(f"SKIP {model}.{side}: {error}")
                continue
        ready.append({"model": model, "side": side, "file": file, "master": title})
    valid = {i["file"] for i in ready}
    for old in (root / "png").glob("*.png"):
        if old.name not in valid:
            old.unlink()
    (root / "manifest.json").write_text(
        json.dumps({"images": ready, "issues": issues}, ensure_ascii=False, indent=2)
    )
    gallery(root, ready, issues)
    print(f"BILAN: {len(ready)} images candidates; {len(issues)} alertes")
    print("Verification visuelle: /data/controle.html")
    if not ready:
        print("No usable PNGs automatically extracted. Review manifest.json; use RackLibrary ZIP fallback.")
        return 1
    cmd = [
        sys.executable, "/app/import_nutanix_elevation_images.py",
        "--images-dir", "/data/png"
    ]
    if args.apply:
        cmd.append("--apply")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
