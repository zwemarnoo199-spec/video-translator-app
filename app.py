import os
import json
import html
import tempfile
import urllib.parse
import urllib.request

import streamlit as st
import whisper
import moviepy as mp


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Zwe Video Translator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Zwe Video Translator")

st.markdown("""
ဗီဒီယိုတင်လိုက်ရုံဖြင့် AI က အသံကို စာသားထုတ်ယူပြီး
မြန်မာဘာသာသို့ အလိုအလျောက် ဘာသာပြန်ပေးမည့် App ဖြစ်ပါတယ်။
""")


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.header("⚙️ Settings")

source_options = {
    "English (အင်္ဂလိပ်)": "en",
    "Chinese (တရုတ်)": "zh",
    "Japanese (ဂျပန်)": "ja",
    "Korean (ကိုရီးယား)": "ko",
    "Auto Detect": None
}

source_choice = st.sidebar.selectbox(
    "မူရင်းဘာသာစကား",
    list(source_options.keys())
)

target_options = {
    "Burmese (မြန်မာ)": "my",
    "English": "en"
}

target_choice = st.sidebar.selectbox(
    "ဘာသာပြန်မည့် ဘာသာစကား",
    list(target_options.keys())
)

model_size = st.sidebar.selectbox(
    "Whisper AI Model",
    ["tiny", "base", "small"]
)

source_code = source_options[source_choice]
target_code = target_options[target_choice]


# ==========================================
# TRANSLATION FUNCTION
# ==========================================

def translate_text(text, target="my", source="en"):

    if not text or not text.strip():
        return text, False

    # Google Translate

    try:

        url = (
            "https://translate.googleapis.com/"
            "translate_a/single"
            "?client=gtx&sl=auto&tl="
            + target
            + "&dt=t&q="
            + urllib.parse.quote(text)
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        translated = "".join(
            item[0]
            for item in data[0]
            if item and item[0]
        )

        if translated.strip():
            return translated, True

    except Exception as error:

        print("Google Translate Error:", repr(error))


    # MyMemory Backup

    try:

        language_map = {
            "zh": "zh-CN",
            "ja": "ja",
            "ko": "ko",
            "en": "en",
            "my": "my"
        }

        source = language_map.get(source, source)

        url = (
            "https://api.mymemory.translated.net/get"
            "?q=" + urllib.parse.quote(text)
            + "&langpair="
            + source + "|" + target
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ZweVideoTranslator/1.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        if data.get("responseStatus") == 200:

            translated = html.unescape(
                data["responseData"]["translatedText"]
            )

            if translated.strip():
                return translated, True

    except Exception as error:

        print("MyMemory Error:", repr(error))

    return text, False


# ==========================================
# TIME FORMAT
# ==========================================

def format_time(seconds):

    total_ms = round(seconds * 1000)

    hours = total_ms // 3600000

    minutes = (total_ms % 3600000) // 60000

    secs = (total_ms % 60000) // 1000

    milliseconds = total_ms % 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


# ==========================================
# VIDEO UPLOAD
# ==========================================
uploaded_file = st.file_uploader(
    "📁 ဗီဒီယိုဖိုင် တင်ပါ",
    type=["mp4", "mov", "mkv"]
)


# ==========================================
# MAIN PROCESS
# ==========================================

if uploaded_file is not None:

    st.video(uploaded_file)

    if st.button(
        "🚀 ဘာသာပြန်ခြင်း စတင်ရန်",
        type="primary"
    ):

        video_path = None
        audio_path = None
        clip = None

        try:

            # SAVE VIDEO

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp4"
            ) as temp:

                temp.write(uploaded_file.getvalue())

                video_path = temp.name

            audio_path = video_path + ".wav"


            with st.status(
                "AI လုပ်ဆောင်နေပါပြီ...",
                expanded=True
            ) as status:

                # EXTRACT AUDIO

                st.write("🔊 အသံထုတ်ယူနေသည်...")

                clip = mp.VideoFileClip(video_path)

                if clip.audio is None:

                    raise ValueError(
                        "ဗီဒီယိုတွင် အသံမပါရှိပါ။"
                    )

                clip.audio.write_audiofile(
                    audio_path,
                    fps=16000,
                    nbytes=2,
                    codec="pcm_s16le",
                    logger=None
                )

                clip.close()
                clip = None


                # WHISPER

                st.write("✍️ Whisper AI အသံဖော်ထုတ်နေသည်...")

                model = whisper.load_model(model_size)

                if source_code:

                    result = model.transcribe(
                        audio_path,
                        language=source_code,
                        fp16=False
                    )

                else:

                    result = model.transcribe(
                        audio_path,
                        fp16=False
                    )

                segments = result.get("segments", [])

                detected_language = result.get(
                    "language", "en"
                )

                if not segments:

                    raise ValueError(
                        "အသံမှ စာသားမတွေ့ပါ။"
                    )


                # TRANSLATION

                st.write("🌍 ဘာသာပြန်နေသည်...")

                translated_segments = []

                total = len(segments)

                progress = st.progress(0)

                failed_count = 0

                for index, segment in enumerate(segments):

                    original = segment["text"].strip()

                    if original:

                        translated, success = translate_text(
                            original,
                            target=target_code,
                            source=detected_language
                        )

                        if not success:
                            failed_count += 1

                        translated_segments.append({
                            "start": segment["start"],
                            "end": segment["end"],
                            "text": translated,
                            "original": original
                        })

                    progress.progress(
                        (index + 1) / total
                    )

                progress.empty()

                status.update(
                    label="✅ ပြီးဆုံးပါပြီ!",
                    state="complete",
                    expanded=False
                )


            # RESULTS

            st.success("🎉 ဘာသာပြန်ခြင်း ပြီးဆုံးပါပြီ။")

            st.info(
                f"Detected Language: {detected_language}"
            )

            if failed_count:

                st.warning(
                    f"{failed_count} ပိုင်း ဘာသာပြန်မအောင်မြင်ပါ။"
                )


            # DISPLAY

            st.subheader("📋 Generated Subtitles")

            srt_content = ""
            for index, segment in enumerate(
                translated_segments,
                start=1
            ):

                start = format_time(segment["start"])

                end = format_time(segment["end"])

                text = segment["text"]

                srt_content += (
                    f"{index}\n"
                    f"{start} --> {end}\n"
                    f"{text}\n\n"
                )

                with st.container():

                    st.caption(
                        f"[{start} - {end}]"
                    )

                    st.write(text)

                    with st.expander("မူရင်းစာသားကြည့်ရန်"):

                        st.write(segment["original"])

                st.divider()


            # DOWNLOAD

            st.download_button(
                label="📥 မြန်မာ Subtitle Download (.SRT)",
                data=srt_content.encode("utf-8-sig"),
                file_name="zwe_myanmar_subtitle.srt",
                mime="application/x-subrip"
            )

            st.balloons()


        except Exception as error:

            st.error(
                f"❌ Error: {str(error)}"
            )

            st.exception(error)


        finally:

            if clip is not None:

                try:
                    clip.close()
                except Exception:
                    pass

            for path in [video_path, audio_path]:

                if path and os.path.exists(path):

                    try:
                        os.remove(path)
                    except OSError:
                        pass


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "© 2026 Zwe Video Translator | Powered by Whisper AI"
)
