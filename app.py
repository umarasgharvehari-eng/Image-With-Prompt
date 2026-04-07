import base64
from io import BytesIO

import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
)

MODEL = "gpt-image-1"

STYLES = [
    "Photorealistic",
    "Cinematic",
    "Anime",
    "3D Render",
    "Fantasy",
    "Cyberpunk",
    "Watercolor",
    "Oil Painting",
    "Minimalist",
    "Concept Art",
]

SIZES = [
    "1024x1024",
    "1024x1536",
    "1536x1024",
]

QUALITIES = [
    "low",
    "medium",
    "high",
]


def get_client() -> OpenAI:
    if "Image Generation" not in st.secrets:
        st.error("Missing Streamlit secret: 'Image Generation'")
        st.stop()

    api_key = st.secrets["Image Generation"]

    if not str(api_key).strip():
        st.error("The secret 'Image Generation' is empty.")
        st.stop()

    return OpenAI(api_key=api_key)


def build_prompt(subject: str, style: str, details: str, avoid_text: bool) -> str:
    rules = []
    if avoid_text:
        rules.append("Do not include any text, letters, logos, captions, or watermarks in the image.")
    rules.append("Make the image visually strong, polished, detailed, and high quality.")

    rules_text = " ".join(rules)

    return f"""
Create a professional image with the following concept.

Subject:
{subject}

Style:
{style}

Extra details:
{details}

Instructions:
{rules_text}
""".strip()


def generate_image(prompt: str, size: str, quality: str) -> bytes:
    client = get_client()

    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        quality=quality,
    )

    image_b64 = response.data[0].b64_json
    return base64.b64decode(image_b64)


st.title("🎨 AI Image Generator")
st.caption("Built with Streamlit + OpenAI")

with st.sidebar:
    st.header("Image Settings")
    style = st.selectbox("Style", STYLES, index=0)
    size = st.selectbox("Size", SIZES, index=0)
    quality = st.selectbox("Quality", QUALITIES, index=1)
    avoid_text = st.toggle("Avoid text / logos / watermarks", value=True)

    st.markdown("---")
    st.markdown("### Streamlit Secret")
    st.code('"Image Generation" = "your_openai_api_key_here"', language="toml")

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Prompt")
    subject = st.text_input(
        "What do you want to generate?",
        placeholder="Example: A futuristic white sports car parked in neon-lit Tokyo at night",
    )
    details = st.text_area(
        "Extra details",
        height=200,
        placeholder="Example: cinematic lighting, rain reflections, ultra detailed, dramatic angle, realistic shadows",
    )

    generate_btn = st.button("Generate Image", type="primary", use_container_width=True)

with right_col:
    st.subheader("Output")

    if generate_btn:
        if not subject.strip():
            st.warning("Please enter an image idea first.")
        else:
            try:
                final_prompt = build_prompt(subject, style, details, avoid_text)

                with st.spinner("Generating image..."):
                    image_bytes = generate_image(final_prompt, size, quality)

                st.image(image_bytes, caption=subject, use_container_width=True)
                st.download_button(
                    label="Download Image",
                    data=image_bytes,
                    file_name="generated_image.png",
                    mime="image/png",
                    use_container_width=True,
                )

                with st.expander("Show final prompt"):
                    st.code(final_prompt, language="text")

            except Exception as e:
                st.error(f"Image generation failed: {e}")
    else:
        st.info("Your generated image will appear here.")
