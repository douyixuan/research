#!/usr/bin/env python3
"""Probe the two official Scitix Figshare share links from CI.

The final publication page points to one private share link while the earlier thesis
chapter names another. This probe records reachability and lightweight page metadata;
it deliberately does not treat network reachability as a paper-result reproduction.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

LINKS = {
    "final_publication_page": "https://figshare.com/s/4d14f40c988bc7c55816",
    "thesis_chapter": "https://figshare.com/s/f03c5103e2ab02125b83",
}


def probe(name: str, url: str) -> dict:
    outdir = Path("results/artifact_probe")
    outdir.mkdir(parents=True, exist_ok=True)
    body = outdir / f"{name}.html"
    headers = outdir / f"{name}.headers"

    proc = subprocess.run(
        [
            "curl",
            "-L",
            "--retry",
            "2",
            "--connect-timeout",
            "15",
            "--max-time",
            "45",
            "-A",
            "Mozilla/5.0 (compatible; reproducibility-probe/1.0)",
            "-sS",
            "-D",
            str(headers),
            "-o",
            str(body),
            "-w",
            "%{http_code}\n%{url_effective}\n%{size_download}\n",
            url,
        ],
        text=True,
        capture_output=True,
    )

    fields = proc.stdout.strip().splitlines()
    http_code = fields[0] if len(fields) >= 1 else "000"
    final_url = fields[1] if len(fields) >= 2 else ""
    size = int(fields[2]) if len(fields) >= 3 and fields[2].isdigit() else 0
    text = body.read_text(errors="replace") if body.exists() else ""

    article_ids = sorted(
        set(
            re.findall(r"/articles/(?:[^/]+/)*(\d+)", text)
            + re.findall(r'"article(?:Id|_id)"\s*:\s*"?(\d+)', text)
        )
    )
    file_ids = sorted(
        set(
            re.findall(r"(?:ndownloader\.figshare\.com|figshare\.com/ndownloader)/files/(\d+)", text)
            + re.findall(r'"(?:id|file_id)"\s*:\s*(\d+)', text)
        )
    )
    filenames = sorted(set(re.findall(r'[^"<>\\/]+\.(?:zip|tar\.gz|tgz|csv|json|jar)', text, re.I)))[:50]

    return {
        "source": name,
        "share_url": url,
        "curl_exit": proc.returncode,
        "http_code": http_code,
        "final_url": final_url,
        "downloaded_bytes": size,
        "article_ids_seen": article_ids[:20],
        "file_ids_seen": file_ids[:50],
        "archive_or_data_names_seen": filenames,
        "body_saved": str(body),
        "stderr": proc.stderr[-1000:],
    }


def main() -> None:
    reports = [probe(name, url) for name, url in LINKS.items()]
    out = Path("results/artifact_probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports, indent=2))

    # Network failure should be visible, but must not invalidate the deterministic
    # mechanism reproduction. Fail only if the probe script itself broke.
    assert all("http_code" in r for r in reports)


if __name__ == "__main__":
    main()
