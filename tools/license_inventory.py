#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Record installed Python dependency provenance and preserve bundled license texts."""
import argparse
import importlib.metadata
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    packages = []
    for dist in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata.get("Name", "").lower()):
        name = dist.metadata.get("Name", "unknown")
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        item = {"name": name, "version": dist.version, "author": dist.metadata.get("Author"),
                "author_email": dist.metadata.get("Author-email"),
                "license_expression": dist.metadata.get("License-Expression"),
                "license_metadata": dist.metadata.get("License"),
                "home_page": dist.metadata.get("Home-page"),
                "project_urls": dist.metadata.get_all("Project-URL") or [], "license_files": []}
        for relative in dist.files or []:
            if any(word in Path(relative).name.lower() for word in ("license", "copying", "copyright", "notice")):
                source = Path(dist.locate_file(relative))
                if source.is_file():
                    # Preserve hierarchy below the distribution to avoid collisions.
                    target = args.output / safe / str(relative).replace("..", "__")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
                    item["license_files"].append(str(target.relative_to(args.output)))
        packages.append(item)
    (args.output / "packages.json").write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(packages)} installed package metadata entries and their available license files.")


if __name__ == "__main__":
    main()
