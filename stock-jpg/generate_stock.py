import argparse
import base64
import io
import os
import time
import zipfile
from pathlib import Path

from openai import OpenAI
from PIL import Image

BASE_PROMPT = """Generate a 4K photorealistic commercial stock photo.

SCENE: {scene}

OUTPUT REQUIREMENTS:
- JPEG/JPG only
- Native 4K resolution at 3840 x 2160
- Maximum practical JPEG quality
- Ultra-sharp, highly detailed, clean, professional, commercially usable stock photography

PHOTOGRAPHY STYLE:
Photorealistic premium commercial lifestyle photography with an authentic contemporary Indonesian setting and believable real-life atmosphere.

CAMERA:
Sony A7 IV full-frame mirrorless camera

LENS:
Sony FE 50mm f/1.8 prime lens

CAMERA SETTINGS:
50mm focal length, f/2.8 aperture, 1/250s shutter speed, ISO 200, natural daylight white balance.

IMAGE CHARACTERISTICS:
Soft natural daylight, realistic moderate depth of field, precise focus on the primary subject, true-to-life colors, neutral-warm professional color grading, natural skin texture with subtle imperfections, realistic hair strands, accurate human anatomy, anatomically correct hands and fingers, realistic body proportions, detailed fabric and environmental textures, physically believable shadows, balanced highlights and exposure, candid expressions, believable body language, clean commercial composition, useful subtle copy space, authentic Indonesian lifestyle, premium full-frame photography aesthetic, unstaged documentary-style realism.

QUALITY CONTROL:
No blur, no pixelation, no low-resolution details, no broken objects, no malformed anatomy, no distorted hands, no extra fingers, no missing fingers, no plastic skin, no excessive retouching, no CGI appearance, no exaggerated HDR, no excessive artificial bokeh, no watermark, no logos, no visible brand names, no copyrighted text, no random generated text.
"""

SUBJECTS = [
    "a mature Indonesian woman in her late 40s",
    "a mature Indonesian man in his early 50s",
    "a mature Indonesian couple in their late 40s",
    "a mature Indonesian woman small-business owner",
    "a mature Indonesian man small-business owner",
]

ACTIVITIES = [
    "packing customer orders for an online shop",
    "checking ecommerce sales on a laptop",
    "replying to customers on a smartphone",
    "organizing product inventory",
    "preparing parcels for courier pickup",
    "reviewing household finances and online business income",
    "photographing handmade products for an online catalog",
    "printing and attaching shipping labels to parcels",
    "checking stock levels while holding a clipboard",
    "preparing a simple healthy breakfast before starting work",
]

SETTINGS = [
    "in a tidy small home workspace",
    "at a dining table converted into a home office",
    "in a compact modern Indonesian living room workspace",
    "inside a modest home-based packing area with shelves and boxes",
    "beside a bright window in a contemporary middle-class Indonesian home",
]

FRAMINGS = [
    "medium horizontal composition with copy space on the right",
    "natural waist-up candid composition with copy space on the left",
    "environmental medium-wide composition showing the workspace context",
]


def build_scenes(limit: int, start: int) -> list[str]:
    scenes = []
    for subject in SUBJECTS:
        for activity in ACTIVITIES:
            for setting in SETTINGS:
                for framing in FRAMINGS:
                    scenes.append(f"{subject} {activity} {setting}, {framing}.")
    return scenes[start - 1:start - 1 + limit]


def decode_image(response) -> bytes:
    item = response.data[0]
    b64 = getattr(item, "b64_json", None)
    if not b64:
        raise RuntimeError("Image API returned no base64 image data")
    return base64.b64decode(b64)


def save_verified_jpeg(raw: bytes, path: Path) -> None:
    with Image.open(io.BytesIO(raw)) as im:
        im = im.convert("RGB")
        if im.size != (3840, 2160):
            im = im.resize((3840, 2160), Image.Resampling.LANCZOS)
        im.save(path, "JPEG", quality=98, subsampling=0, optimize=False)
    with Image.open(path) as check:
        if check.format != "JPEG" or check.size != (3840, 2160):
            raise RuntimeError(f"Validation failed for {path.name}: {check.format}, {check.size}")


def generate_one(client: OpenAI, prompt: str, out_path: Path, retries: int = 3) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                size="3840x2160",
                quality="high",
                output_format="jpeg",
                output_compression=100,
                n=1,
            )
            save_verified_jpeg(decode_image(response), out_path)
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError(f"Failed after {retries} attempts: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=150)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--output", default="stock-jpg/output")
    parser.add_argument("--zip", dest="zip_name", default="stock-jpg/dist/indonesian_mature_lifestyle_4k.zip")
    args = parser.parse_args()

    if args.count < 1 or args.count > 150:
        raise SystemExit("--count must be between 1 and 150")
    if args.start < 1:
        raise SystemExit("--start must be >= 1")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    scenes = build_scenes(args.count, args.start)
    if len(scenes) != args.count:
        raise SystemExit("Not enough unique scene combinations for requested range")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path(args.zip_name)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    manifest = []

    for offset, scene in enumerate(scenes):
        idx = args.start + offset
        filename = f"{idx:03d}.jpg"
        path = out_dir / filename
        prompt = BASE_PROMPT.format(scene=scene)
        print(f"[{offset + 1}/{len(scenes)}] Generating {filename}: {scene}", flush=True)
        generate_one(client, prompt, path)
        manifest.append((filename, scene))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for filename, _ in manifest:
            zf.write(out_dir / filename, arcname=filename)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if len(names) != args.count or any(not name.lower().endswith(".jpg") for name in names):
            raise RuntimeError("ZIP validation failed: unexpected file count or non-JPG files detected")

    print(f"Done: {zip_path} contains {args.count} verified 3840x2160 JPEG files.")


if __name__ == "__main__":
    main()
