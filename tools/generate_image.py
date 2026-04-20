#!/usr/bin/env python3
"""
Image generation interface for formattion.ai services.

Interface contract:
  generate_image(slug, prompt) -> str
    slug   : URL-safe service ID, e.g. "variations-automation"
    prompt : Plain-English description from the 'image_prompt' column in Google Sheets
    returns: Relative path to the saved image, e.g. "images/services/variations-automation.jpg"
    effect : Saves a JPEG to images/services/{slug}.jpg

Replace the body of generate_image() with the real Flux2 call when the engine is ready.
The interface must remain unchanged — sync_services.py imports and calls this function directly.
"""

import os
import sys


def generate_image(slug: str, prompt: str, output_dir: str = "images/services") -> str:
    output_path = os.path.join(output_dir, f"{slug}.jpg")

    # TODO: wire up Flux2 engine here
    # Example expected implementation:
    #   image_bytes = call_flux2_api(prompt)
    #   with open(output_path, "wb") as f:
    #       f.write(image_bytes)

    print(f"  [image-stub] slug={slug}")
    print(f"  [image-stub] prompt={prompt!r}")
    print(f"  [image-stub] output={output_path}  (not written — stub only)")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_image.py <slug> <prompt>")
        sys.exit(1)
    path = generate_image(sys.argv[1], sys.argv[2])
    print(f"Result: {path}")
