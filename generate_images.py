"""Generate README images using Gemini Nano Banana Pro API."""
import urllib.request
import json
import os
import base64
import sys

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

MODEL = "gemini-2.5-flash-image"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_image(prompt: str, filename: str, aspect_ratio: str = "16:9") -> bool:
    """Call Gemini API to generate an image and save it."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }).encode()

    req = urllib.request.Request(
        BASE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"  API error for {filename}: {e}")
        return False

    # Extract image from response
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        if "inlineData" in part:
            img_data = base64.b64decode(part["inlineData"]["data"])
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "wb") as f:
                f.write(img_data)
            size_kb = len(img_data) / 1024
            print(f"  Saved: {path} ({size_kb:.0f} KB)")
            return True
        elif "text" in part:
            print(f"  Text response: {part['text'][:100]}")

    print(f"  No image in response for {filename}")
    return False


# --- Image Prompts ---

IMAGES = [
    {
        "filename": "hero_banner.png",
        "prompt": (
            "Create a sleek, modern tech hero banner for an enterprise AI platform called 'Entobot Enterprise'. "
            "Dark gradient background (deep navy to dark purple). Center a stylized shield icon containing a robot/AI brain symbol, "
            "glowing with electric blue and cyan accent lines. Around the shield, show subtle connecting nodes and circuit-like lines "
            "representing a network. The text 'ENTOBOT' should appear below the icon in clean, modern sans-serif font (white), "
            "with 'ENTERPRISE' in smaller tracking below it. Add a subtle grid pattern in the background. "
            "Style: premium tech product, minimal, high contrast. No people. 16:9 aspect ratio."
        ),
    },
    {
        "filename": "architecture_diagram.png",
        "prompt": (
            "Create a clean, professional software architecture diagram with a dark background (dark slate/navy). "
            "Show 4 horizontal layers connected by vertical arrows:\n"
            "TOP LAYER (blue boxes): 'Mobile App (Flutter)' | 'Web Dashboard' | 'REST Clients'\n"
            "SECOND LAYER (green box, full width): 'Security Gateway' with labels: JWT Auth, Rate Limiting, TLS, Audit Log\n"
            "THIRD LAYER (purple boxes): 'WebSocket Server' | 'Message Bus' | 'Agent Loop' | 'Session Manager'\n"
            "BOTTOM LAYER (orange boxes, grid): 'Gemini' | 'Claude' | 'GPT-4' | 'DeepSeek' | 'Groq' | 'vLLM' | '+ 5 more'\n"
            "Label the bottom layer 'Intelligent Model Routing (11 Providers)'. "
            "Use rounded rectangles, thin white connecting arrows, and a clean modern look. "
            "Each layer should have a subtle label on the left. "
            "Style: technical documentation diagram, clean lines, readable text. 16:9 aspect ratio."
        ),
    },
    {
        "filename": "mobile_security_flow.png",
        "prompt": (
            "Create a technical flow diagram showing a secure mobile device pairing process. Dark background. "
            "Show these 4 steps flowing left to right with arrows:\n"
            "1. Phone icon with camera scanning a QR code (label: 'Scan QR Code')\n"
            "2. A lock/shield icon with a key (label: 'JWT Authentication')\n"
            "3. Two arrows between a phone and server icon (label: 'Secure WebSocket')\n"
            "4. A chat bubble with an AI sparkle icon (label: 'AI Conversation')\n"
            "Below each step show a small timer: '< 3 sec' | 'Auto' | 'Persistent' | 'Real-time'\n"
            "Use electric blue and cyan colors on dark slate. Clean, modern, minimal tech style. "
            "Add a subtle 'Entobot Enterprise' watermark in bottom right. 16:9 aspect ratio."
        ),
    },
    {
        "filename": "provider_routing.png",
        "prompt": (
            "Create a technical diagram showing intelligent AI model routing. Dark background (dark navy). "
            "On the left, show a single input arrow labeled 'User Request'. "
            "In the center, show a hexagonal router node labeled 'Smart Router' glowing with cyan. "
            "From the router, show 6 output arrows fanning out to the right, each going to a labeled box:\n"
            "- 'Gemini Nano Banana' (Google blue) - labeled 'Images'\n"
            "- 'Claude 4.5' (orange) - labeled 'Reasoning'\n"
            "- 'GPT-4' (green) - labeled 'General'\n"
            "- 'DeepSeek' (purple) - labeled 'Budget'\n"
            "- 'Groq' (red) - labeled 'Speed'\n"
            "- 'vLLM' (gray) - labeled 'Air-Gap'\n"
            "Below the router add text: 'Automatic keyword-based routing across 11 providers'. "
            "Style: clean tech diagram, neon accent lines, minimal. 16:9 aspect ratio."
        ),
    },
]


if __name__ == "__main__":
    print(f"Generating {len(IMAGES)} images using {MODEL}...\n")
    success = 0
    for i, img in enumerate(IMAGES, 1):
        print(f"[{i}/{len(IMAGES)}] Generating {img['filename']}...")
        if generate_image(img["prompt"], img["filename"]):
            success += 1
        print()

    print(f"Done: {success}/{len(IMAGES)} images generated in {OUTPUT_DIR}/")
