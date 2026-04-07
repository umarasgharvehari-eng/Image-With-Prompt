import json
import random
from datetime import datetime

import streamlit as st
from groq import Groq

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="AI Image Prompt Studio",
    page_icon="🎨",
    layout="wide",
)

# -----------------------------
# Constants
# -----------------------------
MODEL = "llama-3.3-70b-versatile"

STYLE_OPTIONS = [
    "Photorealistic",
    "Cinematic",
    "Anime",
    "Fantasy",
    "Cyberpunk",
    "3D Render",
    "Concept Art",
    "Watercolor",
    "Oil Painting",
    "Minimalist",
    "Fashion Editorial",
    "Product Photography",
    "Architectural Visualization",
]

LIGHTING_OPTIONS = [
    "Soft natural light",
    "Golden hour",
    "Studio lighting",
    "Neon glow",
    "Dramatic shadows",
    "Moonlight",
    "Backlit silhouette",
    "Foggy atmosphere",
    "Volumetric light rays",
]

CAMERA_OPTIONS = [
    "Close-up",
    "Medium shot",
    "Wide shot",
    "Macro",
    "Aerial view",
    "Low angle",
    "High angle",
    "Eye level",
    "Portrait lens",
    "Cinematic framing",
]

ASPECT_RATIOS = [
    "1:1",
    "16:9",
    "9:16",
    "4:5",
    "3:2",
    "21:9",
]

QUALITY_OPTIONS = [
    "Standard",
    "High",
    "Ultra detailed",
]

COLOR_MOODS = [
    "Vibrant",
    "Moody",
    "Warm",
    "Cool",
    "Pastel",
    "Monochrome",
    "Dark luxury",
]

SAMPLE_IDEAS = [
    "A futuristic city floating above the ocean at sunset",
    "A luxury perfume bottle on a glossy black reflective surface",
    "A majestic white tiger wearing royal armor in a snowy forest",
    "A cozy coffee shop in Tokyo during rain with neon signs outside",
    "A modern villa in the desert with dramatic cinematic lighting",
]

DEFAULT_RESULT = {
    "title": "",
    "prompt": "",
    "negative_prompt": "",
    "style_notes": "",
    "camera_notes": "",
    "color_notes": "",
    "hashtags": [],
}

# -----------------------------
# Session state
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = DEFAULT_RESULT.copy()

# -----------------------------
# Helper functions
# -----------------------------
def get_client() -> Groq:
    if "Image Translate" not in st.secrets:
        st.error("Missing Streamlit secret: 'Image Translate'")
        st.stop()

    api_key = st.secrets["Image Translate"]

    if not str(api_key).strip():
        st.error("The secret 'Image Translate' is empty.")
        st.stop()

    return Groq(api_key=api_key)


def clean_json_response(text: str) -> dict:
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).strip()
    if text.startswith("```"):
        text = text.replace("```", "", 1).strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    return json.loads(text)


def build_user_prompt(
    subject: str,
    style: str,
    lighting: str,
    camera: str,
    aspect_ratio: str,
    quality: str,
    color_mood: str,
    extra_details: str,
    avoid_text_in_image: bool,
    safety_filter: bool,
) -> str:
    return f"""
Create a professional image-generation prompt package.

Subject:
{subject}

Style:
{style}

Lighting:
{lighting}

Camera / Composition:
{camera}

Aspect Ratio:
{aspect_ratio}

Quality Target:
{quality}

Color Mood:
{color_mood}

Extra Details:
{extra_details}

Instructions:
- Write for modern image-generation models.
- Make the main prompt vivid, specific, visual, and production-ready.
- Keep it concise but strong.
- Include a negative prompt.
- Include short style notes and camera notes.
- Include short color notes.
- Include 6 to 10 relevant hashtags without the # symbol.
- {"Avoid visible text, letters, logos, and watermarks in the image." if avoid_text_in_image else "Visible text is allowed only if clearly requested."}
- {"Keep the content clean and safe for general audiences." if safety_filter else "Do not over-sanitize unless necessary."}

Return ONLY valid JSON in this exact schema:
{{
  "title": "string",
  "prompt": "string",
  "negative_prompt": "string",
  "style_notes": "string",
  "camera_notes": "string",
  "color_notes": "string",
  "hashtags": ["tag1", "tag2", "tag3"]
}}
""".strip()


def generate_prompt_package(
    subject: str,
    style: str,
    lighting: str,
    camera: str,
    aspect_ratio: str,
    quality: str,
    color_mood: str,
    extra_details: str,
    avoid_text_in_image: bool,
    safety_filter: bool,
) -> dict:
    client = get_client()

    system_prompt = (
        "You are an expert prompt engineer for AI image generation. "
        "You produce clean, accurate, highly visual prompt packages. "
        "Always return strict JSON only."
    )

    user_prompt = build_user_prompt(
        subject=subject,
        style=style,
        lighting=lighting,
        camera=camera,
        aspect_ratio=aspect_ratio,
        quality=quality,
        color_mood=color_mood,
        extra_details=extra_details,
        avoid_text_in_image=avoid_text_in_image,
        safety_filter=safety_filter,
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content.strip()

    try:
        data = clean_json_response(content)
    except Exception:
        data = {
            "title": "Generated Prompt Package",
            "prompt": content,
            "negative_prompt": "low quality, blurry, distorted, deformed, watermark, text, logo, cropped",
            "style_notes": style,
            "camera_notes": camera,
            "color_notes": color_mood,
            "hashtags": ["aiart", "concept", "visual"],
        }

    # Normalize
    result = {
        "title": str(data.get("title", "")).strip(),
        "prompt": str(data.get("prompt", "")).strip(),
        "negative_prompt": str(data.get("negative_prompt", "")).strip(),
        "style_notes": str(data.get("style_notes", "")).strip(),
        "camera_notes": str(data.get("camera_notes", "")).strip(),
        "color_notes": str(data.get("color_notes", "")).strip(),
        "hashtags": data.get("hashtags", []),
    }

    if not isinstance(result["hashtags"], list):
        result["hashtags"] = []

    return result


def build_download_text(result: dict) -> str:
    hashtags_line = ", ".join([f"#{tag}" for tag in result.get("hashtags", [])])

    return f"""TITLE
{result.get("title", "")}

MAIN PROMPT
{result.get("prompt", "")}

NEGATIVE PROMPT
{result.get("negative_prompt", "")}

STYLE NOTES
{result.get("style_notes", "")}

CAMERA NOTES
{result.get("camera_notes", "")}

COLOR NOTES
{result.get("color_notes", "")}

HASHTAGS
{hashtags_line}
"""


def add_to_history(result: dict) -> None:
    item = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": result.get("title", "Untitled"),
        "prompt": result.get("prompt", ""),
        "negative_prompt": result.get("negative_prompt", ""),
    }
    st.session_state.history.insert(0, item)
    st.session_state.history = st.session_state.history[:10]


# -----------------------------
# Header
# -----------------------------
st.title("🎨 AI Image Prompt Studio")
st.caption("Professional image prompt creation with Streamlit + Groq")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Creative Controls")

    style = st.selectbox("Style", STYLE_OPTIONS, index=0)
    lighting = st.selectbox("Lighting", LIGHTING_OPTIONS, index=0)
    camera = st.selectbox("Camera / Composition", CAMERA_OPTIONS, index=0)
    aspect_ratio = st.selectbox("Aspect Ratio", ASPECT_RATIOS, index=0)
    quality = st.selectbox("Quality", QUALITY_OPTIONS, index=1)
    color_mood = st.selectbox("Color Mood", COLOR_MOODS, index=0)

    avoid_text_in_image = st.toggle("Avoid text / logos / watermarks", value=True)
    safety_filter = st.toggle("Safe-for-general-audience prompts", value=True)

    st.markdown("---")
    if st.button("Load Random Idea", use_container_width=True):
        st.session_state["random_subject"] = random.choice(SAMPLE_IDEAS)

    st.markdown("### Streamlit Secret")
    st.code('"Image Translate" = "your_groq_api_key_here"', language="toml")

# -----------------------------
# Main layout
# -----------------------------
left_col, right_col = st.columns([1.1, 1])

with left_col:
    st.subheader("Create")

    default_subject = st.session_state.get("random_subject", "")
    subject = st.text_input(
        "What image do you want to create?",
        value=default_subject,
        placeholder="Example: A cinematic portrait of a royal falcon made of gold and glass",
    )

    extra_details = st.text_area(
        "Extra details",
        height=220,
        placeholder=(
            "Example: ultra detailed, elegant luxury aesthetic, shallow depth of field, "
            "dramatic rim light, black background, glossy reflections"
        ),
    )

    button_col1, button_col2 = st.columns(2)
    with button_col1:
        generate_btn = st.button("Generate Prompt Package", type="primary", use_container_width=True)
    with button_col2:
        clear_btn = st.button("Clear", use_container_width=True)

    if clear_btn:
        st.session_state.last_result = DEFAULT_RESULT.copy()
        st.session_state["random_subject"] = ""
        st.rerun()

    st.markdown("### Quick templates")
    template_cols = st.columns(3)

    templates = [
        "Luxury product photo",
        "Fantasy character art",
        "Modern architecture",
    ]

    for i, template in enumerate(templates):
        if template_cols[i].button(template, use_container_width=True):
            if template == "Luxury product photo":
                st.session_state["random_subject"] = "A premium watch placed on a polished black marble surface"
            elif template == "Fantasy character art":
                st.session_state["random_subject"] = "A legendary warrior queen standing in a glowing ancient forest"
            else:
                st.session_state["random_subject"] = "A modern minimalist villa with floor-to-ceiling glass walls"
            st.rerun()

with right_col:
    st.subheader("Output")

    result = st.session_state.last_result

    if generate_btn:
        if not subject.strip():
            st.warning("Please enter an image idea first.")
        else:
            try:
                with st.spinner("Generating your professional prompt package..."):
                    result = generate_prompt_package(
                        subject=subject,
                        style=style,
                        lighting=lighting,
                        camera=camera,
                        aspect_ratio=aspect_ratio,
                        quality=quality,
                        color_mood=color_mood,
                        extra_details=extra_details,
                        avoid_text_in_image=avoid_text_in_image,
                        safety_filter=safety_filter,
                    )

                st.session_state.last_result = result
                add_to_history(result)
            except Exception as e:
                st.error(f"Request failed: {e}")
                result = st.session_state.last_result

    if result.get("prompt"):
        st.markdown(f"### {result.get('title', 'Generated Prompt Package')}")

        st.markdown("**Main Prompt**")
        st.code(result.get("prompt", ""), language="text")

        st.markdown("**Negative Prompt**")
        st.code(result.get("negative_prompt", ""), language="text")

        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.metric("Style", style)
        info_col2.metric("Aspect Ratio", aspect_ratio)
        info_col3.metric("Quality", quality)

        st.markdown("**Creative Notes**")
        st.write(f"**Style Notes:** {result.get('style_notes', '')}")
        st.write(f"**Camera Notes:** {result.get('camera_notes', '')}")
        st.write(f"**Color Notes:** {result.get('color_notes', '')}")

        hashtags = result.get("hashtags", [])
        if hashtags:
            st.markdown("**Suggested Tags**")
            st.write(" ".join([f"#{tag}" for tag in hashtags]))

        download_text = build_download_text(result)
        st.download_button(
            label="Download Prompt Package",
            data=download_text,
            file_name="image_prompt_package.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.info("Your generated prompt package will appear here.")

# -----------------------------
# History
# -----------------------------
st.markdown("---")
st.subheader("Recent Prompt History")

if st.session_state.history:
    for item in st.session_state.history:
        with st.expander(f"{item['time']} — {item['title']}"):
            st.write("**Main Prompt**")
            st.code(item["prompt"], language="text")
            st.write("**Negative Prompt**")
            st.code(item["negative_prompt"], language="text")
else:
    st.caption("No prompt history yet.")

# -----------------------------
# Footer note
# -----------------------------
st.markdown("---")
st.info(
    "This app uses Groq to generate professional image prompts and prompt packs. "
    "It does not render images directly."
)
