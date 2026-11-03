import os
import tempfile
import urllib.parse
import urllib.request
import json

import streamlit as st
import whisper
import moviepy as mp


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Zwe Video Translator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Zwe Video Translator")

st.markdown(
    "ဗီဒီယိုတင်လိုက်ရုံဖြင့် AI က အသံကို "
    "စာသားထုတ်ပြီး မြန်မာဘာသာသို့ အလိုအလျောက် "
    "ဘာသာပြန်ပေးမည့် Web App ဖြစ်ပါတယ်။"
)


# =====================================
# SIDEBAR SETTINGS
# =====================================

st.sidebar.header("⚙️ Settings")

source_lang_option = st.sidebar.selectbox(
    "မူရင်းဗီဒီယို ဘာသာစကား",
    [
        "English (အင်္ဂလိပ်)",
        "Chinese (တရုတ်)",
        "Japanese (ဂျပန်)",
        "Korean (ကိုရီးယား)",
        "Auto-detect"
    ]
)

target_lang = st.sidebar.selectbox(
    "ဘာသာပြန်မည့် ဘာသာစကား",
    [
        "Burmese (မြန်မာ)",
        "English"
    ]
)

model_size = st.sidebar.selectbox(
    "AI Model Size (Whisper)",
    ["tiny", "base", "small"]
)


# =====================================
# LANGUAGE SETTINGS
# =====================================

source_lang_map = {
    "English (အင်္ဂလိပ်)": "en",
    "Chinese (တရုတ်)": "zh",
    "Japanese (ဂျပန်)": "ja",
    "Korean (ကိုရီးယား)": "ko",
    "Auto-detect": None
}

selected_source_lang = source_lang_map[
    source_lang_option
]

if "မြန်မာ" in target_lang:
    selected_lang_code = "my"
else:
    selected_lang_code = "en"


# =====================================
# GOOGLE TRANSLATE FUNCTION
# =====================================

def translate_text(text, target="my"):

    if not text or not text.strip():
        return text

    try:

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            "?client=gtx&sl=auto&tl="
            + target
            + "&dt=t&q="
            + urllib.parse.quote(text)
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=15
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        translated = "".join(
            item[0]
            for item in result[0]
            if item[0]
        )

        return translated if translated else text

    except Exception as e:

        print("Translation Error:", e)

        return text


# =====================================
# TIME FORMAT FUNCTION
# =====================================

def format_time(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = int(seconds % 60)

    milliseconds = int(
        (seconds - int(seconds)) * 1000
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


# =====================================
# VIDEO UPLOADER
# =====================================

uploaded_file = st.file_uploader(
    "📁 ဗီဒီယိုဖိုင် တင်ပါ",
    type=["mp4", "mkv", "mov"]
)


# =====================================
# MAIN PROCESS
# =====================================

if uploaded_file is not None:

    st.video(uploaded_file)

    if st.button(
        "🚀 ဗီဒီယို ဘာသာပြန်ခြင်း စတင်ရန်",
        type="primary"
    ):

        video_path = None
        audio_path = None
        video_clip = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp4"
            ) as tfile:

                tfile.write(uploaded_file.getvalue())

                video_path = tfile.name

            audio_path = video_path + ".wav"

            with st.status(
                "🔄 AI လုပ်ဆောင်နေပါပြီ...",
                expanded=True
            ) as status:
# =================================
                # STEP 1: EXTRACT AUDIO
                # =================================

                st.write(
                    "🔊 ဗီဒီယိုမှ အသံထုတ်ယူနေသည်..."
                )

                video_clip = mp.VideoFileClip(
                    video_path
                )

                if video_clip.audio is None:

                    raise ValueError(
                        "ဗီဒီယိုတွင် အသံမပါရှိပါ။"
                    )

                video_clip.audio.write_audiofile(
                    audio_path,
                    fps=16000,
                    nbytes=2,
                    codec="pcm_s16le",
                    logger=None
                )

                video_clip.close()
                video_clip = None

                # =================================
                # STEP 2: WHISPER AI
                # =================================

                st.write(
                    f"✍️ Whisper AI ({model_size}) "
                    "ဖြင့် အသံမှ စာသားထုတ်နေသည်..."
                )

                model = whisper.load_model(
                    model_size
                )

                if selected_source_lang:

                    result = model.transcribe(
                        audio_path,
                        language=selected_source_lang,
                        fp16=False
                    )

                else:

                    result = model.transcribe(
                        audio_path,
                        fp16=False
                    )

                segments = result["segments"]

                if not segments:

                    raise ValueError(
                        "အသံမှ စာသား မတွေ့ရှိပါ။"
                    )

                # =================================
                # STEP 3: TRANSLATION
                # =================================

                st.write(
                    f"🌍 {target_lang} သို့ "
                    "ဘာသာပြန်နေသည်..."
                )

                translated_segments = []

                progress = st.progress(0)

                total = len(segments)

                for index, seg in enumerate(
                    segments
                ):

                    original_text = (
                        seg["text"].strip()
                    )

                    if original_text:

                        translated_text = (
                            translate_text(
                                original_text,
                                target=selected_lang_code
                            )
                        )

                        translated_segments.append({
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": translated_text
                        })

                    progress.progress(
                        (index + 1) / total
                    )

                progress.empty()

                status.update(
                    label="✅ အောင်မြင်စွာ ပြီးဆုံးပါပြီ!",
                    state="complete",
                    expanded=False
                )

            # =================================
            # STEP 4: DISPLAY SUBTITLES
            # =================================

            st.success(
                "🎉 ဘာသာပြန်ခြင်း ပြီးဆုံးပါပြီ။"
            )

            st.subheader(
                "📋 Generated Subtitles"
            )

            srt_content = ""

            for i, seg in enumerate(
                translated_segments,
                start=1
            ):

                start_t = format_time(
                    seg["start"]
                )

                end_t = format_time(
                    seg["end"]
                )

                txt = seg["text"].strip()

                srt_content += (
                    f"{i}\n"
                    f"{start_t} --> {end_t}\n"
                    f"{txt}\n\n"
                )
st.markdown(
                    f"[{start_t} - {end_t}]"
                )

                st.write(txt)

                st.divider()

            # =================================
            # STEP 5: DOWNLOAD SRT
            # =================================

            st.download_button(
                label="📥 Subtitle ဖိုင် (.SRT) Download",
                data=srt_content.encode("utf-8-sig"),
                file_name="zwe_myanmar_subtitle.srt",
                mime="application/x-subrip"
            )

            st.balloons()

        except Exception as e:

            st.error(
                f"❌ အမှားဖြစ်နေပါသည်: {str(e)}"
            )

        finally:

            if video_clip is not None:

                video_clip.close()

            for path in [
                video_path,
                audio_path
            ]:

                if path and os.path.exists(path):

                    try:
                        os.remove(path)

                    except OSError:
                        pass


# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
    "© 2026 Zwe Video Translator | "
    "Powered by Whisper AI"
)
