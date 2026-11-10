#!/usr/bin/env python3
"""Upload curated Nutanix front/rear PNG elevations to existing NetBox Device Types.

Inputs in /images: NX-8170A-G10.front.png, NX-8170A-G10.rear.png, etc.
DRY-RUN by default; use --apply after reviewing. Never replaces existing images.
Only Device Types whose manufacturer is exactly Nutanix are eligible.

Environment: NETBOX_URL, NETBOX_TOKEN; optional NETBOX_CA_BUNDLE,
NETBOX_TLS_VERIFY=false (insecure; testing only).
"""
import argparse
import mimetypes
import os
from pathlib import Path
from contextlib import ExitStack

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--images-dir", default="/images")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

root = Path(args.images_dir)
if not root.is_dir():
    parser.error(f"Missing input directory: {root}")
files = sorted(root.glob("*.png"))
if not files:
    parser.error("No *.png images in input directory")

base_url = os.environ["NETBOX_URL"].rstrip("/") + "/api/"
token = os.environ["NETBOX_TOKEN"].strip()
auth_scheme = "Bearer" if token.startswith("nbt_") else "Token"
session = requests.Session()
session.headers.update({"Authorization": f"{auth_scheme} {token}", "Accept": "application/json"})

ca_bundle = os.getenv("NETBOX_CA_BUNDLE")
tls_mode = os.getenv("NETBOX_TLS_VERIFY", "true").lower()
session.verify = ca_bundle if ca_bundle else tls_mode not in ("0", "false", "no")
if session.verify is False:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print("WARNING: TLS certificate verification disabled for this execution")

by_model = {}
for file in files:
    if file.is_symlink():
        raise SystemExit(f"Symlink forbidden: {file}")
    if file.stat().st_size > 15 * 1024 * 1024:
        raise SystemExit(f"File exceeds 15 MB: {file}")
    if file.name.endswith(".front.png"):
        model, side = file.name[:-10], "front_image"
    elif file.name.endswith(".rear.png"):
        model, side = file.name[:-9], "rear_image"
    else:
        print(f"SKIP unrecognized filename: {file.name}")
        continue
    if not model.startswith("NX-") or not model.isascii():
        print(f"SKIP non-Nutanix model naming: {file.name}")
        continue
    if side in by_model.setdefault(model, {}):
        raise SystemExit(f"Duplicate image for {model} / {side}")
    # Require PNG magic, not just a file extension.
    with file.open("rb") as fh:
        if fh.read(8) != b"\x89PNG\r\n\x1a\n":
            raise SystemExit(f"Not a valid PNG header: {file}")
    by_model[model][side] = file

found = created = unchanged = errors = 0
for model in sorted(by_model):
    response = session.get(
        base_url + "dcim/device-types/", params={"model": model, "limit": 100},
        timeout=40
    )
    response.raise_for_status()
    data = response.json()
    matched = [
        item for item in data["results"]
        if item.get("model") == model
        and item.get("manufacturer", {}).get("name", "").casefold() == "nutanix"
    ]
    if data.get("next"):
        raise SystemExit(f"Unusually many device types for {model}; abort")
    if len(matched) != 1:
        errors += 1
        print(f"REVIEW {model}: Nutanix device type matches = {len(matched)}")
        continue
    dt = matched[0]
    found += 1
    pending = {}
    for side, file in by_model[model].items():
        if dt.get(side):
            unchanged += 1
            print(f"EXISTS {model}: {side} (not overwritten)")
        else:
            pending[side] = file
            print(f"{'UPLOAD' if args.apply else 'PLAN'} {model}: {side} -> {file.name}")

    if pending and args.apply:
        with ExitStack() as stack:
            payload = {}
            for field, file in pending.items():
                fh = stack.enter_context(file.open("rb"))
                payload[field] = (file.name, fh, "image/png")
            result = session.patch(
                base_url + f"dcim/device-types/{dt['id']}/", files=payload, timeout=120
            )
            if not result.ok:
                errors += 1
                print(f"ERROR {model}: HTTP {result.status_code}: {result.text[:500]}")
                continue
            updated = result.json()
            successful = sum(bool(updated.get(field)) for field in pending)
            if successful != len(pending):
                errors += 1
                print(f"REVIEW {model}: API response missing one or more image URLs")
            else:
                created += successful

print(
    f"SUMMARY mode={'APPLY' if args.apply else 'DRY-RUN'} "
    f"models_matched={found} images_uploaded={created} "
    f"images_existing={unchanged} unresolved_models_or_errors={errors}"
)
if errors:
    raise SystemExit(1)
