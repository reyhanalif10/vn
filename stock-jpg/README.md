# 4K Stock JPG Automation

This workflow generates a batch of photorealistic Indonesian commercial stock images and packages only JPEG files into one ZIP artifact.

## Output

- `001.jpg` ... `150.jpg`
- Each file is validated as JPEG and 3840 x 2160 pixels.
- Final archive: `indonesian_mature_lifestyle_4k.zip`
- The ZIP contains JPG files only.

## Visual profile

- Mature Indonesian lifestyle / small business niche
- Sony A7 IV look
- Sony FE 50mm f/1.8 prime lens aesthetic
- 50mm, f/2.8, 1/250s, ISO 200
- Natural daylight, realistic anatomy and skin texture
- No logos, watermarks, visible brand names, or random generated text

## Required repository secret

Create a GitHub Actions repository secret named:

`OPENAI_API_KEY`

The key is read only by GitHub Actions and must never be committed to the repository.

## Run

Open **Actions > Generate 4K Stock JPG Batch > Run workflow**.

Inputs:
- `count`: 1-150, default 150
- `start`: starting file index, default 1

The workflow generates each image independently, retries failed API requests, validates JPEG dimensions, creates the final ZIP, validates the ZIP contents, and uploads it as a GitHub Actions artifact for seven days.

## Cost warning

Generating 150 high-quality 4K images can consume significant API credits. The workflow intentionally does not start automatically; it uses `workflow_dispatch` so the batch runs only when manually triggered.
