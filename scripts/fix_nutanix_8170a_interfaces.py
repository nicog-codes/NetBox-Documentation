#!/usr/bin/env python3
"""NetBox 4.6.x: add six observed Ethernet templates to the Nutanix NX-8170A-G10 device type.

Dry-run by default. Requires NETBOX_URL and NETBOX_TOKEN in the environment.
Optional: NETBOX_CA_BUNDLE=/path/to/CA.pem; NETBOX_TLS_VERIFY=false is insecure.
This script does not modify physical Device interfaces or other Device Types.
"""
import argparse
import os
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

url = os.environ["NETBOX_URL"].rstrip("/") + "/api/"
token = os.environ["NETBOX_TOKEN"].strip()
auth = "Bearer" if token.startswith("nbt_") else "Token"
session = requests.Session()
session.headers.update({"Authorization": f"{auth} {token}", "Accept": "application/json"})
ca = os.getenv("NETBOX_CA_BUNDLE")
verify_option = os.getenv("NETBOX_TLS_VERIFY", "true").lower()
session.verify = ca if ca else verify_option not in ("0", "false", "no")
if session.verify is False:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print("ATTENTION: validation du certificat TLS desactivee temporairement.")


def get_all(endpoint, params=None):
    next_url = url + endpoint
    results = []
    for page in range(20):
        response = session.get(next_url, params=params if page == 0 else None, timeout=30)
        response.raise_for_status()
        data = response.json()
        results.extend(data["results"])
        next_url = data.get("next")
        if not next_url:
            return results
    raise RuntimeError("Pagination anormale, abandon")


models = get_all("dcim/device-types/", {"model": "NX-8170A-G10"})
models = [
    m for m in models if m.get("model") == "NX-8170A-G10"
    and m.get("manufacturer", {}).get("name", "").casefold() == "nutanix"
]
if len(models) != 1:
    raise SystemExit(f"Modele Nutanix NX-8170A-G10: {len(models)} correspondances; abandon")
dt_id = models[0]["id"]

interfaces = get_all("dcim/interface-templates/", {"devicetype_id": dt_id})
if any(
    isinstance(i.get("device_type"), dict) and i["device_type"].get("id") != dt_id
    for i in interfaces
):
    raise SystemExit("Filtre interface templates non applique, abandon")
existing = {i["name"]: i for i in interfaces}
expected = {
    "eth0": "Intel X710", "eth2": "Intel X710",
    "eth3": "Intel X710", "eth5": "Intel X710",
    "eth1": "Broadcom BCM57416", "eth4": "Broadcom BCM57416",
}
conflicts = []
missing = []
for nic, controller in expected.items():
    item = existing.get(nic)
    if item:
        actual = item.get("type")
        actual = actual.get("value", actual) if isinstance(actual, dict) else actual
        if actual != "10gbase-t" or item.get("mgmt_only", False):
            conflicts.append((nic, actual, item.get("mgmt_only")))
        else:
            print(f"EXISTANT: {nic} = 10gbase-t")
    else:
        missing.append(nic)
        print(f"AJOUT PREVU: {nic} = 10gbase-t ({controller})")
if conflicts:
    raise SystemExit(f"Conflits a examiner manuellement, aucune ecriture: {conflicts}")

if not args.apply:
    print(f"BILAN SIMULATION: {len(missing)} a creer, {len(expected)-len(missing)} deja presents")
else:
    created = 0
    for nic in missing:
        payload = {"device_type": dt_id, "name": nic, "type": "10gbase-t", "mgmt_only": False}
        response = session.post(url + "dcim/interface-templates/", json=payload, timeout=30)
        if response.status_code != 201:
            raise SystemExit(
                f"Erreur creation {nic}: HTTP {response.status_code}: {response.text[:500]}"
            )
        created += 1
        print(f"CREE: {nic}")
    print(f"BILAN IMPORT: {created} crees, {len(expected)-len(missing)} deja presents, 0 erreur")
