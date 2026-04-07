import io
import random
from typing import Optional

import requests
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
)

API_BASE = "https://api.stability.ai/v2beta/stable-image/generate"

MODEL_OPTIONS = {
    "Stable Image Core": "core",
    "Stable Image Ultra": "ultra",
}

STYLE_PRESETS = [
    "Photographic",
    "Cinematic",
    "Anime",
    "Digital Art",
    "Fantasy",
    "Cyberpunk",
    "3D Render",
    "Minimalist",
    "Concept Art",
    "Watercolor",
]

ASPECT_RATIOS = [
    "1:1",
    "16:9",
    "9:16",
    "4:5",
    "3:2",
    "21:9",
]

OUTPUT_FORMATS = [
    "png",
    "jpeg",
    "webp",
]

QUALITY_PRESETS = {
    "Fast": "fast",
    "Balanced": "balanced",
    "Detailed": "detailed",
}


def get_api_key() -> str:
    if "Image Generation" not in st.secrets:
        st.error("Missing Streamlit secret: 'Image Generation'")
        st.stop()

    api_key = str(st.secrets["Image Generation"]).strip()
    if not api_key:
        st.error("The secret 'Image Generation' is empty.")
        st.stop()

    return api_key


def enhance_prompt(subject: str, style: str, details: str, quality: str, avoid_text: bool) -> str:
    text_rules = "No text, letters, logos, captions, or watermarks." if avoid_text else ""
    quality_rules = {
        "fast": "Keep it clean and simple with strong composition.",
        "balanced": "Use rich detail, good lighting, and polished composition.",
        "detailed": "Use highly detailed textures, premium lighting, strong realism, and refined composition.",
    }

    parts = [
        subject.strip(),
        f"Style: {style}",
        details.strip(),
        quality_rules.get(quality, ""),
        text_rules,
    ]

    return ", ".join([p for p in parts if p])


def generate_image(
    api_key: str,
    model_slug: str,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
    output_format: str,
    seed: Optional[int] = None,
) -> bytes:
    url = f"{API_BASE}/{model_slug}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }

    data = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }

    if negative_prompt.strip():
        data["negative_prompt"] = negative_prompt.strip()

    if seed is not None:
        data["seed"] = str(seed)

    # Stability examples commonly use multipart/form-data for v2beta image generation.
    response = requests.post(
        url,
        headers=headers,
        files={"none": ("", b"")},
        data=data,
        timeout=120,
    )

    content_type = response.headers.get("content-type", "")

    if response.status_code != 200:
        try:
            error_json = response.json()
            message = error_json.get("errors") or error_json.get("message") or error_json
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
        raise RuntimeError(f"Stability API error: {message}")

    if "image" not in content_type:
        raise RuntimeError("The API did not return an image.")

    return response.content


st.title("🎨 AI Image Generator")
st.caption("Professional Streamlit UI with Stability AI")

with st.sidebar:
    st.header("Image Settings")

    model_name = st.selectbox("Model", list(MODEL_OPTIONS.keys()), index=0)
    style = st.selectbox("Style", STYLE_PRESETS, index=0)
    aspect_ratio = st.selectbox("Aspect Ratio", ASPECT_RATIOS, index=0)
    output_format = st.selectbox("Output Format", OUTPUT_FORMATS, index=0)
    quality_label = st.selectbox("Quality Preset", list(QUALITY_PRESETS.keys()), index=1)

    avoid_text = st.toggle("Avoid text / logos / watermarks", value=True)
    use_random_seed = st.toggle("Use random seed", value=True)

    st.markdown("---")
    st.markdown("### Streamlit Secret")
    st.code('"Image Generation" = "your_stability_api_key_here"', language="toml")

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Prompt")

    subject = st.text_input(
        "What do you want to generate?",
        placeholder="Example: A stylish young man wearing a modern black suit in a luxury studio",
    )

    details = st.text_area(
        "Extra details",
        height=180,
        placeholder="Example: realistic skin texture, soft studio lighting, premium fashion photography, sharp focus, elegant pose",
    )

    negative_prompt = st.text_area(
        "Negative prompt",
        height=120,
        placeholder="Example: blurry, deformed hands, extra fingers, low quality, watermark, text",
    )

    generate_btn = st.button("Generate Image", type="primary", use_container_width=True)

with right_col:
    st.subheader("Output")

    if generate_btn:
        if not subject.strip():
            st.warning("Please enter an image idea first.")
        else:
            try:
                api_key = get_api_key()
                model_slug = MODEL_OPTIONS[model_name]
                quality = QUALITY_PRESETS[quality_label]

                final_prompt = enhance_prompt(
                    subject=subject,
                    style=style,
                    details=details,
                    quality=quality,
                    avoid_text=avoid_text,
                )

                seed = random.randint(1, 999999999) if use_random_seed else None

                with st.spinner("Generating image..."):
                    image_bytes = generate_image(
                        api_key=api_key,
                        model_slug=model_slug,
                        prompt=final_prompt,
                        negative_prompt=negative_prompt,
                        aspect_ratio=aspect_ratio,
                        output_format=output_format,
                        seed=seed,
                    )

                image = Image.open(io.BytesIO(image_bytes))
                st.image(image, caption=model_name, use_container_width=True)

                st.download_button(
                    label="Download Image",
                    data=image_bytes,
                    file_name=f"generated_image.{output_format}",
                    mime=f"image/{output_format}",
                    use_container_width=True,
                )

                with st.expander("Show final prompt"):
                    st.code(final_prompt, language="text")

                if seed is not None:
                    st.info(f"Seed used: {seed}")

            except Exception as e:
                st.error(str(e))
    else:
        st.info("Your generated image will appear here.")
