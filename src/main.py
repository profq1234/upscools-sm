import os
import json
import re
import requests
import base64
import html
from jinja2 import Template
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Telegram Credentials (Updated to match your .env file)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_SOCIAL_MEDIA")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID_SOCIAL_MEDIA")

# Pinterest Credentials (OAuth 2.0)
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID")

def format_highlights(text, auto_keywords=None):
    if not text:
        return ""

    text = re.sub(r'\*\*(.*?)\*\*', r'<span class="bg-yellow-300/60 semantic-bold px-[0.2em] rounded">\1</span>', text)

    if auto_keywords:
        keywords = sorted([k for k in auto_keywords if k], key=len, reverse=True)
        if keywords:
            escaped_kws = [re.escape(kw.strip()) for kw in keywords if kw.strip()]
            pattern = re.compile(rf'\b({"|".join(escaped_kws)})\b', re.IGNORECASE)

            parts = re.split(r'(<[^>]+>)', text)
            for i in range(0, len(parts), 2):
                if parts[i]:
                    parts[i] = pattern.sub(r'<span class="bg-yellow-300/60 semantic-bold px-[0.2em] rounded">\1</span>', parts[i])
            text = "".join(parts)

    return text.replace("\n", "<br>")

# ---------------------------------------------------------
# 1. THE JINJA2 HTML TEMPLATE
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
        .font-primary {
            font-family: 'Poppins', sans-serif;
            letter-spacing: 0.01em;
        }
        .semantic-bold {
            font-weight: 700;
        }
    </style>
</head>
<body class="m-0 p-0 w-screen h-screen flex flex-col overflow-hidden">

    <div class="relative w-full h-full bg-gradient-to-br from-slate-300 via-slate-400 to-slate-500 p-[8px] flex flex-col">

        <div class="relative flex-1 bg-[#fcfcfc] rounded-sm shadow-[inset_0_4px_20px_rgba(0,0,0,0.15)] overflow-hidden flex flex-col p-6 pb-10">

            <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/50 to-transparent pointer-events-none z-0"></div>
            <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-white/40 to-transparent pointer-events-none z-0"></div>

            <div class="relative z-10 w-full h-full flex flex-col">

                <div class="text-center mb-3 relative shrink-0">
                    <div class="flex justify-between items-center font-primary text-[11px] font-semibold text-slate-500 mb-1 px-2 uppercase tracking-wider">
                        <span class="text-slate-600">{{ category }}</span>
                        <div class="flex items-center">
                            <span class="mr-1">📍</span> {{ exam }}
                        </div>
                    </div>
                    <h2 class="font-primary text-[15px] font-bold text-slate-700 uppercase tracking-widest underline decoration-[1.5px] decoration-slate-300 underline-offset-4 mb-2">
                        {{ format_title }}
                    </h2>
                </div>

                <div id="content-boundary" class="flex-1 flex flex-col justify-center w-full min-h-0 relative mb-4">

                    {% if not is_explanation %}

                    <!-- QUESTION SLIDE -->
                    <div id="scale-target" class="flex flex-col space-y-[0.8em] w-full" style="font-size: 14px;">
                        <div class="w-[98%] mx-auto transform -translate-x-[2%] border-[0.13em] border-red-800 rounded-[1em] p-[1em] bg-white/70 backdrop-blur-sm shadow-sm">
                            <p class="font-primary text-[1.05em] text-red-950 leading-relaxed font-semibold">
                                <span class="semantic-bold mr-1 text-red-700">Q.</span> {{ question_text }}
                            </p>
                        </div>

                        <div class="w-[98%] mx-auto space-y-[0.7em] font-primary font-medium text-[0.9em] text-blue-950 leading-relaxed text-left">
                            {% for stmt in statements %}
                            <div class="flex items-start border-[0.12em] border-blue-800/40 rounded-[0.8em] py-[0.8em] px-[0.9em] bg-white/80 shadow-sm">
                                <span class="mr-2 semantic-bold">{{ loop.index }}.</span>
                                <p class="leading-relaxed">{{ stmt | safe }}</p>
                            </div>
                            {% endfor %}
                        </div>

                        <div class="w-[98%] mx-auto transform translate-x-[2%] grid grid-cols-2 gap-[0.8em] mt-[0.5em] font-primary font-medium text-[0.85em] text-green-950 text-left">
                            {% for key, val in options.items() %}
                            <div class="flex items-center border-[0.12em] border-green-700/40 rounded-[0.8em] py-[0.8em] px-[0.9em] bg-green-50/80 shadow-sm">
                                <span class="border-[0.12em] border-green-800 rounded-full w-[1.6em] h-[1.6em] flex items-center justify-center shrink-0 mr-[0.7em] text-[0.75em] semantic-bold bg-green-100/50 text-green-900">{{ key }}</span>
                                <span class="leading-tight my-auto">{{ val | safe }}</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>

                    {% else %}

                    <!-- ANSWER SLIDE -->
                    <div id="scale-target" class="flex flex-col space-y-[1.2em] w-full" style="font-size: 14px;">
                        <div class="w-[98%] mx-auto border-[0.2em] border-green-800 rounded-[1em] p-[1.5em] bg-green-50 backdrop-blur-sm shadow-sm text-center transform -translate-x-[2%]">
                            <p class="font-primary text-[2.4em] text-green-900 font-bold tracking-widest leading-none">
                                CORRECT: {{ correct_answer }}
                            </p>
                        </div>

                        <div class="relative overflow-hidden w-[98%] mx-auto border-[0.14em] border-yellow-600 rounded-[1em] p-[1.3em] bg-yellow-50 backdrop-blur-sm shadow-sm transform translate-x-[2%]">
                            <svg class="absolute -right-4 -bottom-4 w-[7em] h-[7em] text-yellow-600/10 transform -rotate-12" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7zM9 21a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-1H9v1z"/></svg>
                            <div class="relative z-10 font-primary text-[0.95em] font-medium text-yellow-950 space-y-[0.7em]">
                                {% for point in explanation_points %}
                                <div class="flex items-start">
                                    <span class="mr-[0.5em] text-yellow-700 font-bold text-[1.2em] leading-tight">•</span>
                                    <p class="leading-relaxed">{{ point | safe }}</p>
                                </div>
                                {% endfor %}
                            </div>
                        </div>

                        {% if distractor_logic %}
                        <div class="relative overflow-hidden w-[98%] mx-auto border-[0.14em] border-red-700 rounded-[1em] p-[1.3em] bg-red-50 backdrop-blur-sm shadow-sm transform -translate-x-[2%]">
                            <span class="absolute -right-2 -bottom-4 text-[6em] opacity-10 select-none">🚨</span>
                            <p class="relative z-10 font-primary font-medium text-[0.95em] text-red-950 leading-relaxed">
                                {{ distractor_logic | safe }}
                            </p>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}

                </div>
            </div>

            <div class="absolute bottom-3 right-4 flex items-center opacity-85">
                {% if logo_base64 %}
                <img src="data:image/svg+xml;base64,{{ logo_base64 }}" alt="Logo" class="w-7 h-7 rounded-md shadow-sm border border-slate-300 bg-white">
                {% endif %}
            </div>

        </div>

        <div class="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-3/4 h-3 bg-gradient-to-b from-slate-400 to-slate-600 rounded-t-sm shadow-2xl border-t border-slate-500 z-20"></div>
    </div>
</body>
</html>
"""

# ---------------------------------------------------------
# 2. IMAGE GENERATION ENGINE
# ---------------------------------------------------------
AUTO_SCALE_JS = """
() => {
    const boundary = document.getElementById('content-boundary');
    const target = document.getElementById('scale-target');

    if (!boundary || !target) return;

    let currentSize = 14.0;
    const minSize = 9.0;
    const maxSize = 26.0;
    const step = 0.5;

    while (target.scrollHeight > boundary.clientHeight && currentSize > minSize) {
        currentSize -= step;
        target.style.fontSize = currentSize + 'px';
    }

    while (target.scrollHeight < (boundary.clientHeight - 20) && currentSize < maxSize) {
        currentSize += step;
        target.style.fontSize = currentSize + 'px';

        if (target.scrollHeight > boundary.clientHeight) {
            currentSize -= step;
            target.style.fontSize = currentSize + 'px';
            break;
        }
    }
}
"""

def create_images_for_question(item, output_dir="temp"):
    os.makedirs(output_dir, exist_ok=True)
    template = Template(HTML_TEMPLATE)
    generated_formats = {}

    logo_base64 = ""
    logo_path = os.path.join(os.getcwd(), "assets", "square-logo.svg")
    try:
        with open(logo_path, "rb") as image_file:
            logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Warning: Could not load square-logo.svg. Error: {e}")

    formats = {
        "format_1_evidence_inference": "UPSC Type I: Evidence & Inference",
        "format_2_assertion_reason": "UPSC Type II: Assertion & Reason",
        "format_3_scenario": "UPSC Type III: Scenario Based",
        "format_4_how_many": "UPSC Type IV: Multiple Pairings"
    }

    category = item.get("concept_map", {}).get("primary_theme", "Polity Practice")
    exam = item.get("schema_metadata", {}).get("source_exam", "Prelims")
    item_id = item.get("original_id", "unknown_id")

    semantic_keywords = item.get("seo", {}).get("default_semantic_keywords", [])
    related_entities = [ent.get("name") for ent in item.get("concept_map", {}).get("related_entities", []) if "name" in ent]
    dynamic_keywords_list = semantic_keywords + related_entities

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 540, "height": 675},
            device_scale_factor=2.0
        )
        page = context.new_page()

        for format_key, title in formats.items():
            if format_key not in item:
                continue

            q_data = item[format_key]

            distractor_logic = (
                q_data.get("distractor_logic") or
                item.get("distractor_logic") or
                item.get("concept_map", {}).get("distractor_logic") or
                ""
            )

            raw_exp = q_data.get("explanation", "")
            exp_points = []
            if "\n" in raw_exp:
                lines = raw_exp.split("\n")
            else:
                lines = raw_exp.split(". ")

            for s in lines:
                s = s.strip()
                if not s: continue
                if not s.endswith("."): s += "."
                exp_points.append(format_highlights(s, dynamic_keywords_list))

            context_data = {
                "logo_base64": logo_base64,
                "category": category,
                "exam": exam,
                "format_title": title,
                "distractor_logic": format_highlights(distractor_logic, dynamic_keywords_list),
                "question_text": format_highlights(q_data.get("question_text", ""), dynamic_keywords_list),
                "statements": [format_highlights(s, dynamic_keywords_list) for s in q_data.get("statements", [])],
                "options": {k.upper(): format_highlights(v, dynamic_keywords_list) for k, v in q_data.get("options", {}).items()},
                "correct_answer": q_data.get("correct_answer", "").upper(),
                "correct_option_text": q_data.get("options", {}).get(q_data.get("correct_answer"), ""),
                "explanation_points": exp_points
            }

            # Render Question
            context_data["is_explanation"] = False
            page.set_content(template.render(**context_data))
            page.evaluate("document.fonts.ready")
            page.evaluate(AUTO_SCALE_JS)
            q_filename = f"{output_dir}/{item_id}_{format_key}_Q.png"
            page.screenshot(path=q_filename)

            # Render Answer
            context_data["is_explanation"] = True
            page.set_content(template.render(**context_data))
            page.evaluate("document.fonts.ready")
            page.evaluate(AUTO_SCALE_JS)
            a_filename = f"{output_dir}/{item_id}_{format_key}_A.png"
            page.screenshot(path=a_filename)

            generated_formats[format_key] = [q_filename, a_filename]

        browser.close()
        return generated_formats

# ---------------------------------------------------------
# 3. SOCIAL MEDIA APIs
# ---------------------------------------------------------
def send_album_to_telegram(image_paths, caption):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram Error: TELEGRAM_BOT_TOKEN_SOCIAL_MEDIA or TELEGRAM_CHAT_ID_SOCIAL_MEDIA missing in .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
    media = []
    files = {}
    for i, path in enumerate(image_paths):
        file_key = f"photo_{i}"
        media_item = {"type": "photo", "media": f"attach://{file_key}"}
        if i == 0: media_item["caption"] = caption
        media.append(media_item)
        files[file_key] = open(path, 'rb')

    payload = {"chat_id": TELEGRAM_CHAT_ID, "media": json.dumps(media)}
    try:
        response = requests.post(url, data=payload, files=files, timeout=30)
        if response.status_code != 200:
            print(f"❌ Telegram Album API Error ({response.status_code}): {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram Network error: {e}")
        return False
    finally:
        for f in files.values(): f.close()

def send_text_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram Error: TELEGRAM_BOT_TOKEN_SOCIAL_MEDIA or TELEGRAM_CHAT_ID_SOCIAL_MEDIA missing in .env")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"❌ Telegram Text API Error ({response.status_code}): {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram text error: {e}")
        return False

def send_pin_to_pinterest(image_path, title, description, destination_link):
    if not PINTEREST_ACCESS_TOKEN or not PINTEREST_BOARD_ID:
        print("Skipping Pinterest: API keys not configured in .env")
        return False
    try:
        api_base = os.getenv("PINTEREST_API_BASE", "https://api-sandbox.pinterest.com/v5")
        pin_create_url = f"{api_base}/pins"

        headers = {
            "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "board_id": PINTEREST_BOARD_ID,
            "title": str(title)[:100],
            "description": str(description)[:500],
            "link": destination_link,
            "media_source": {
                "source_type": "image_base64",
                "content_type": "image/jpeg",
                "data": image_base64
            }
        }

        response = requests.post(pin_create_url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Successfully posted pin to Pinterest!")
            return True
        else:
            print(f"Pinterest Error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"Pinterest exception: {e}")
        return False

def main():
    TEST_MODE = False        # Set to False to run API calls live
    ENABLE_PINTEREST = False # Disabled for testing mode as requested

    state_file = "state/processed_history.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f: processed_history = json.load(f)
    else: processed_history = []

    data_file = "data/polity/upsc_polity_data.json"
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict): data = [data]

    for item in data:
        item_id = item.get("original_id")
        if item_id in processed_history and not TEST_MODE:
            print(f"Skipping {item_id}")
            continue

        print(f"Processing target: {item_id}")

        url_slug = item.get("url_slug", item_id)
        destination_url = f"https://upscools.com/upsc-practice-questions/polity/{url_slug}"
        meta_title = html.escape(item.get("seo", {}).get("base_meta_title", "UPSC Practice"))
        keywords_list = item.get("seo", {}).get("default_semantic_keywords", [])
        keywords_str = html.escape(", ".join(keywords_list))

        social_media = item.get("social_media_export", {})
        hashtags = html.escape(" ".join(social_media.get("hashtags", [])))

        captions_dict = social_media.get("ctr_booster_captions", {})
        fallback_caption = social_media.get("ctr_booster_caption", "")

        generated_formats = create_images_for_question(item)

        if TEST_MODE:
            print(f"\n🛑 TEST MODE ACTIVE. Images generated in temp folder.")
            break

        all_formats_success = True

        # ==========================================
        # WORKFLOW A: NEW DATA (Sequential Posts)
        # ==========================================
        if captions_dict:
            print("🟢 NEW DATA DETECTED: Triggering separate posts workflow...")
            for format_key, image_paths in generated_formats.items():
                short_format_key = f"{format_key.split('_')[0]}_{format_key.split('_')[1]}"
                
                specific_caption = captions_dict.get(short_format_key, fallback_caption)
                full_caption = f"{specific_caption}\n\n{hashtags}".strip()

                print(f"Sending {short_format_key} images to Telegram...")
                tg_success = send_album_to_telegram(image_paths, full_caption)
                if not tg_success: all_formats_success = False

                q_text = html.escape(item.get(format_key, {}).get("question_text", "N/A"))
                exp_text = html.escape(item.get(format_key, {}).get("explanation", "N/A"))
                alt_message = (
                    f"📝 <b>Metadata & Alt Text ({short_format_key})</b>\n\n"
                    f"<b>Title:</b> {meta_title}\n"
                    f"<b>Keywords:</b> {keywords_str}\n"
                    f"<b>Hashtags:</b> {hashtags}\n\n"
                    f"<b>Question:</b> {q_text}\n\n"
                    f"<b>Explanation:</b> {exp_text}"
                )
                print(f"Sending {short_format_key} metadata to Telegram...")
                txt_success = send_text_to_telegram(alt_message)
                if not txt_success: all_formats_success = False

                if ENABLE_PINTEREST:
                    q_image_path = image_paths[0]
                    print(f"Sending {short_format_key} to Pinterest...")
                    send_pin_to_pinterest(q_image_path, meta_title, full_caption, destination_url)

                for img in image_paths:
                    if os.path.exists(img): os.remove(img)

        # ==========================================
        # WORKFLOW B: OLD DATA (Combined Post)
        # ==========================================
        else:
            print("🟡 OLD DATA DETECTED: Triggering combined album workflow...")
            all_image_paths = []
            for paths in generated_formats.values():
                all_image_paths.extend(paths)

            full_caption = f"{fallback_caption}\n\n{hashtags}".strip()

            print("Sending Combined Album to Telegram...")
            tg_success = send_album_to_telegram(all_image_paths, full_caption)
            if not tg_success: all_formats_success = False

            combined_alt_message = (
                f"📝 <b>Metadata & Alt Text (All Formats)</b>\n\n"
                f"<b>Title:</b> {meta_title}\n"
                f"<b>Keywords:</b> {keywords_str}\n"
                f"<b>Hashtags:</b> {hashtags}\n\n"
            )
            
            for format_key in generated_formats.keys():
                short_format_key = f"{format_key.split('_')[0]}_{format_key.split('_')[1]}"
                q_text = html.escape(item.get(format_key, {}).get("question_text", "N/A"))
                exp_text = html.escape(item.get(format_key, {}).get("explanation", "N/A"))
                
                combined_alt_message += (
                    f"<b>--- {short_format_key} ---</b>\n"
                    f"<b>Q:</b> {q_text}\n"
                    f"<b>A:</b> {exp_text}\n\n"
                )
            
            print(f"Sending combined metadata to Telegram...")
            txt_success = send_text_to_telegram(combined_alt_message)
            if not txt_success: all_formats_success = False

            if ENABLE_PINTEREST and all_image_paths:
                print("Sending first image to Pinterest...")
                send_pin_to_pinterest(all_image_paths[0], meta_title, full_caption, destination_url)

            for img in all_image_paths:
                if os.path.exists(img): os.remove(img)

        if all_formats_success and not TEST_MODE:
            print(f"Successfully processed {item_id}!")
            processed_history.append(item_id)
            break
        elif not all_formats_success:
            print(f"❌ Failed to process {item_id} due to API errors.")
            break

    if not TEST_MODE:
        with open(state_file, "w") as f:
            json.dump(processed_history, f, indent=4)
            print("State history updated.")

if __name__ == "__main__":
    main()
