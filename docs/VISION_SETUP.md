# Vision Model Setup Guide

## What's New

Your image uploads now get **true visual understanding** when you ask about them. The system intelligently routes image queries to a vision model instead of just OCR text extraction.

## Two Vision Options

### 1. **Claude Vision (Recommended, Fast)**

Better image understanding + text extraction combined.

**Setup:**
```bash
# Add to your .env file in apps/backend/
ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"
```

Get your key from: https://console.anthropic.com/account/keys

**Cost:** $3 per million input tokens. A typical image is ~600 tokens.

### 2. **Local BLIP Model (Free, First Run Slow)**

Runs on your machine – no API key needed.

**Cost:** Free, but slow on first use (downloads ~400MB model on first request; then cached)

**Performance:** Slightly less detailed than Claude, but good enough for content understanding

## How It Works

When you ask an image question:

1. **System detects image upload** → "what is this?" / "describe what's in this"
2. **Routes to vision model** → Claude (if key set) or BLIP (local fallback)
3. **Returns visual understanding** → "This is a photo of..." + can answer follow-up questions

## Example Usage

```
You: "Summarize what's visible in this image"
AI: [Detailed description from Claude or BLIP vision model]

You: "What text is in this?"
AI: [Can combine vision + OCR for best results]

You: "Explain the context"
AI: [Uses vision model's understanding, not just text extraction]
```

## Forced Fallback to OCR

If you ask "What text is extracted?" or "Show extracted text", the system knows you want OCR-only results and skips the vision model.

## Performance Notes

- **Claude Vision:** ~2 seconds per image (includes API latency)
- **Local BLIP:** 
  - First request: 30-90 seconds (downloads model)
  - Subsequent: ~8-15 seconds per image
  - Runs on your CPU (GPU much faster if available)

## Disabling Vision (Use OCR Only)

If you don't want vision models:

1. Don't set `ANTHROPIC_API_KEY`
2. Set in .env: `VISION_USE_LOCAL_FALLBACK=false`
3. Restart backend

Then images will use OCR extraction only (faster, less capable).

## Testing

```powershell
# Direct vision endpoint (if you want standalone analysis)
$body = @{ 
    message="Describe this image"
    document_id="YOUR_IMAGE_DOC_ID"
    user_id="YOUR_USER_ID"
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d $body
```

## Troubleshooting

**Q: Request times out on first image**
- A: BLIP model is downloading (~400MB). Wait 1-2 minutes, then retry.

**Q: Want to use Claude instead of local BLIP**
- A: Set `ANTHROPIC_API_KEY` in .env and restart backend.

**Q: "No vision model available" error**
- A: Install dependencies: `pip install anthropic` or `pip install transformers pillow torch`

**Q: New image uploads return only OCR summary, not vision**
- A: Old chunks don't have vision. Re-upload the image to get full vision analysis.
