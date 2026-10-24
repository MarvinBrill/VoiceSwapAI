"""Refresh the checked-in asset manifest explicitly, never at application startup."""

import hashlib
import json
import re
import urllib.request
from pathlib import Path

revision = "e6d0c1a17da07c33557852f9dfa2bd44cc75737d"
with urllib.request.urlopen(
    f"https://huggingface.co/api/models/lj1995/VoiceConversionWebUI/tree/{revision}?recursive=true&limit=1000"
) as response:
    tree = json.load(response)
files = {}
for entry in tree:
    if entry["type"] != "file" or not re.match(
        r"^hubert_base/|^rmvpe.pt$|^pretrained_v2/f0[GD](32|40|48)k.pth$", entry["path"]
    ):
        continue
    name = entry["path"]
    digest = entry.get("lfs", {}).get("oid")
    if not digest:
        with urllib.request.urlopen(
            f"https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/{revision}/{name}"
        ) as response:
            digest = hashlib.sha256(response.read()).hexdigest()
    key = "rmvpe/rmvpe.pt" if name == "rmvpe.pt" else name
    files[key] = {"source": name, "size": entry["size"], "sha256": digest}
Path("engine/assets.json").write_text(
    json.dumps({"revision": revision, "files": files}, indent=2) + "\n", encoding="utf-8"
)
