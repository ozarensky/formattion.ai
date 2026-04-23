"""
Image generation interface for the formattion.ai web page.
Routes all generation through the centralised engine.

Interface contract (unchanged — sync_services.py imports this directly):
  generate_image(slug, prompt, output_dir) -> str
    slug       : URL-safe service ID, e.g. "variations-automation"
    prompt     : Composition description (what to show) — passed as --subject to engine
    output_dir : Directory for the saved image (default: "images/services")
    returns    : Relative path to the saved image

Brand style is owned by the engine. Do not define style here.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = _ROOT / "image generator" / "tools" / "generate_image.py"


def generate_image(slug: str, prompt: str, output_dir: str = "images/services", purpose: str = "supporting") -> str:
    output_path = os.path.join(output_dir, f"{slug}.jpg")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, str(ENGINE_PATH),
            "--subject", prompt,
            "--purpose", purpose,
            "--aspect-ratio", "16:9",
            "--output-path", output_path,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Engine error for {slug}: {result.stderr or result.stdout or 'no output'}")

    if not data.get("success"):
        raise RuntimeError(f"Image generation failed for {slug}: {data.get('error')}")

    print(f"  [{slug}] Saved: {output_path} ({data.get('duration_s', '?')}s)")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_image.py <slug> <subject>")
        sys.exit(1)
    path = generate_image(sys.argv[1], sys.argv[2])
    print(f"Result: {path}")
