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

QUALITY_HINTS = {
    "Fast": "Keep it clean and simple with strong composition.",
    "Balanced": "Use rich detail, good lighting, and polished composition.",
    "Detailed": "Use highly detailed textures, premium lighting, strong realism, and refined composition.",
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


def build_prompt(
    subject: str,
    style: str,
    details: str,
    quality_label: str,
    avoid_text: bool,
) -> str:
    rules = []

    if avoid_text:
        rules.append("Do not include any text, letters, logos, captions, signatures, or watermarks.")

    rules.append("Create a visually strong, polished, high-quality image.")
    rules.append(QUALITY_HINTS.get(quality_label, ""))

    parts = [
        subject.strip(),
        f"Style: {style}",
        details.strip(),
        " ".join([r for r in rules if r]),
    ]

    return ", ".join([p for p in parts if p]).strip()


def call_stability_api(
    api_key: str,
    model_slug: str,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
    output_format: str,
    seed: Optional[int] = None,
    init_image_bytes: Optional[bytes] = None,
    init_image_name: Optional[str] = None,
    init_image_type: Optional[str] = None,
    strength: Optional[float] = None,
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

    files = {}

    if init_image_bytes is not None:
        file_name = init_image_name or "input.png"
        mime_type = init_image_type or "image/png"
        files["image"] = (file_name, init_image_bytes, mime_type)

        if strength is not None:
            data["strength"] = str(strength)
    else:
        # Keep request as multipart/form-data even without an input image
        files["none"] = ("", b"")

    response = requests.post(
        url,
        headers=headers,
        files=files,
        data=data,
        timeout=180,
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


def display_generated_image(image_bytes: bytes, output_format: str) -> None:
    image = Image.open(io.BytesIO(image_bytes))
    st.image(image, use_container_width=True)
    st.download_button(
        label="Download Image",
        data=image_bytes,
        file_name=f"generated_image.{output_format}",
        mime=f"image/{output_format}",
        use_container_width=True,
    )


st.title("🎨 AI Image Generator")
st.caption("Text-to-image and image-to-image with Stability AI + Streamlit")

with st.sidebar:
    st.header("Global Settings")

    model_name = st.selectbox("Model", list(MODEL_OPTIONS.keys()), index=0)
    style = st.selectbox("Style", STYLE_PRESETS, index=0)
    aspect_ratio = st.selectbox("Aspect Ratio", ASPECT_RATIOS, index=0)
    output_format = st.selectbox("Output Format", OUTPUT_FORMATS, index=0)
    quality_label = st.selectbox("Quality Preset", list(QUALITY_HINTS.keys()), index=1)

    avoid_text = st.toggle("Avoid text / logos / watermarks", value=True)
    use_random_seed = st.toggle("Use random seed", value=True)

    st.markdown("---")
    st.markdown("### Streamlit Secret")
    st.code('"Image Generation" = "your_stability_api_key_here"', language="toml")

model_slug = MODEL_OPTIONS[model_name]
api_key = get_api_key()

tab1, tab2 = st.tabs(["Text to Image", "Image + Prompt"])

with tab1:
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Prompt")

        subject = st.text_input(
            "What do you want to generate?",
            placeholder="Example: A stylish young man wearing a modern black suit in a luxury studio",
            key="txt_subject",
        )

        details = st.text_area(
            "Extra details",
            height=180,
            placeholder="Example: realistic skin texture, soft studio lighting, premium fashion photography, sharp focus, elegant pose",
            key="txt_details",
        )

        negative_prompt = st.text_area(
            "Negative prompt",
            height=120,
            placeholder="Example: blurry, low quality, distorted face, extra fingers, watermark, text",
            key="txt_negative",
        )

        generate_text_btn = st.button("Generate from Prompt", type="primary", use_container_width=True)

    with right_col:
        st.subheader("Output")

        if generate_text_btn:
            if not subject.strip():
                st.warning("Please enter an image idea first.")
            else:
                try:
                    final_prompt = build_prompt(
                        subject=subject,
                        style=style,
                        details=details,
                        quality_label=quality_label,
                        avoid_text=avoid_text,
                    )

                    seed = random.randint(1, 999999999) if use_random_seed else None

                    with st.spinner("Generating image..."):
                        image_bytes = call_stability_api(
                            api_key=api_key,
                            model_slug=model_slug,
                            prompt=final_prompt,
                            negative_prompt=negative_prompt,
                            aspect_ratio=aspect_ratio,
                            output_format=output_format,
                            seed=seed,
                        )

                    display_generated_image(image_bytes, output_format)

                    with st.expander("Show final prompt"):
                        st.code(final_prompt, language="text")

                    if seed is not None:
                        st.info(f"Seed used: {seed}")

                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Your generated image will appear here.")

with tab2:
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Upload Image + Prompt")

        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg", "webp"],
            key="img_upload",
        )

        transform_prompt = st.text_input(
            "How should the image change?",
            placeholder="Example: Turn this into a cinematic luxury fashion portrait with dramatic studio lighting",
            key="img_subject",
        )

        transform_details = st.text_area(
            "Extra details",
            height=160,
            placeholder="Example: sharper face, premium black outfit, elegant pose, realistic skin, magazine-style composition",
            key="img_details",
        )

        transform_negative_prompt = st.text_area(
            "Negative prompt",
            height=120,
            placeholder="Example: blurry, low quality, extra fingers, distorted face, watermark, text",
            key="img_negative",
        )

        strength = st.slider(
            "Transformation strength",
            min_value=0.1,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Lower values keep more of the original image. Higher values change it more.",
        )

        generate_image_btn = st.button("Generate from Image + Prompt", type="primary", use_container_width=True)

    with right_col:
        st.subheader("Output")

        if uploaded_file is not None:
            st.markdown("**Input Image Preview**")
            st.image(uploaded_file, use_container_width=True)

        if generate_image_btn:
            if uploaded_file is None:
                st.warning("Please upload an image first.")
            elif not transform_prompt.strip():
                st.warning("Please enter a prompt describing the changes.")
            else:
                try:
                    init_bytes = uploaded_file.getvalue()

                    final_prompt = build_prompt(
                        subject=transform_prompt,
                        style=style,
                        details=transform_details,
                        quality_label=quality_label,
                        avoid_text=avoid_text,
                    )

                    seed = random.randint(1, 999999999) if use_random_seed else None

                    with st.spinner("Transforming image..."):
                        image_bytes = call_stability_api(
                            api_key=api_key,
                            model_slug=model_slug,
                            prompt=final_prompt,
                            negative_prompt=transform_negative_prompt,
                            aspect_ratio=aspect_ratio,
                            output_format=output_format,
                            seed=seed,
                            init_image_bytes=init_bytes,
                            init_image_name=uploaded_file.name,
                            init_image_type=uploaded_file.type,
                            strength=strength,
                        )

                    display_generated_image(image_bytes, output_format)

                    with st.expander("Show final prompt"):
                        st.code(final_prompt, language="text")

                    st.info(f"Strength used: {strength}")
                    if seed is not None:
                        st.info(f"Seed used: {seed}")

                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Your transformed image will appear here.")
