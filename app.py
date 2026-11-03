import os
import json
import tempfile
import urllib.parse
import urllib.request

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
    "AI အသုံးပြုပြီး ဗီဒီယိုမှ အသံကို စာသားထုတ်ယူကာ "
    "မြန်မာဘာသာသို့ အလိုအလျောက် ဘာသာပြန်ပေးမည့် App ဖြစ်ပါတယ်။"
)


# =====================================
# SIDEBAR SETTINGS
# =====================================

st.sidebar.header("⚙️ Settings")

source_lang_option = st.sidebar.selectbox(
    "မူရင်းဗီဒီယို ဘာသာစကား (Source Language)",
    [
        "English (အင်္ဂလိပ်)",
        "Chinese (တရုတ်)",
        "Japanese (ဂျပန်)",
        "Korean (ကိုရီးယား)",
        "Auto-detect"
    ]
)

target_lang = st.sidebar.selectbox(
    "ဘာသာပြန်မည့် ဘာသာစကား (Target Language)",
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
# LANGUAGE CODE
# =====================================

source_lang_map = {
    "English (အင်္ဂလိပ်)": "en",
    "Chinese (တရုတ်)": "zh",
    "Japanese (ဂျပန်)": "ja",
    "Korean (ကိုရီးယား)": "ko",
    "Auto-detect": None
}

selected_source_lang = source_lang_map[source_lang_option]

selected_target_code = (
    "my" if "မြန်မာ" in target_lang else "en"
)


# =====================================
# TRANSLATION FUNCTION
# =====================================

def translate_text(text, target="my"):

    if not text or not text.strip():
        return text, False

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

            result = json.loads(
                response.read().decode("utf-8")
            )

        translated = "".join(
            item[0]
            for item in result[0]
            if item and item[0]
        )

        if translated:
            return translated, True

        return text, False

    except Exception as error:
        print("Translation Error:", error)
        return text, False


# =====================================
# TIME FORMAT
# =====================================

def format_time(seconds):

    hours = int(seconds // 3600)

    minutes = int((seconds % 3600) // 60)

    secs = int(seconds % 60)

    milliseconds = int(
        round((seconds - int(seconds)) * 1000)
    )

    if milliseconds >= 1000:
        secs += 1
        milliseconds = 0

    if secs >= 60:
        minutes += 1
        secs = 0

    if minutes >= 60:
        hours += 1
        minutes = 0

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
    "📁 ဗီဒီယိုဖိုင် တင်ပါ (MP4, MKV, MOV)",
    type=["mp4", "mkv", "mov"]
)


# =====================================
# MAIN APP
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

            # STEP 1: SAVE VIDEO

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp4"
            ) as temp_video:
                temp_video.write(
                    uploaded_file.getvalue()
                )

                video_path = temp_video.name

            audio_path = video_path + ".wav"

            with st.status(
                "🔄 AI လုပ်ဆောင်နေပါပြီ...",
                expanded=True
            ) as status:

                # STEP 2: EXTRACT AUDIO

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

                # STEP 3: WHISPER AI

                st.write(
                    f"✍️ Whisper AI ({model_size}) "
                    "ဖြင့် အသံကို စာသားပြောင်းနေသည်..."
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

                segments = result.get("segments", [])

                if not segments:
                    raise ValueError(
                        "အသံမှ စာသားမတွေ့ရှိပါ။"
                    )

                # STEP 4: TRANSLATION

                st.write(
                    f"🌍 {target_lang} သို့ "
                    "ဘာသာပြန်နေသည်..."
                )

                translated_segments = []

                progress = st.progress(0)

                failed_count = 0
                total = len(segments)

                for index, segment in enumerate(segments):

                    original_text = (
                        segment["text"].strip()
                    )

                    if original_text:

                        translated_text, success = translate_text(
                            original_text,
                            target=selected_target_code
                        )

                        if not success:
                            failed_count += 1

                        translated_segments.append({
                            "start": segment["start"],
                            "end": segment["end"],
                            "text": translated_text
                        })

                    progress.progress(
                        (index + 1) / total
                    )

                progress.empty()

                status.update(
                    label="✅ လုပ်ဆောင်မှု ပြီးဆုံးပါပြီ!",
                    state="complete",
                    expanded=False
                )

            # STEP 5: DISPLAY RESULT

            st.success(
                "🎉 ဗီဒီယို ဘာသာပြန်ခြင်း ပြီးဆုံးပါပြီ။"
            )

            if failed_count > 0:

                st.warning(
                    f"ဘာသာပြန်မှု {failed_count} ပိုင်း "
                    "မအောင်မြင်ပါ။ အချို့စာသားများမှာ "
                    "မူရင်းအတိုင်း ကျန်ရှိနိုင်ပါတယ်။"
                )

            st.subheader("📋 Generated Subtitles")

            srt_content = ""

            for index, segment in enumerate(
                translated_segments,
                start=1
            ):

                start_time = format_time(
                    segment["start"]
                )

                end_time = format_time(
                    segment["end"]
                )
                subtitle_text = segment["text"]

                srt_content += (
                    f"{index}\n"
                    f"{start_time} --> {end_time}\n"
                    f"{subtitle_text}\n\n"
                )

                st.markdown(
                    f"[{start_time} - {end_time}]"
                )

                st.write(subtitle_text)

                st.divider()

            # STEP 6: DOWNLOAD SRT

            st.download_button(
                label="📥 Subtitle (.SRT) Download",
                data=srt_content.encode("utf-8-sig"),
                file_name="zwe_myanmar_subtitle.srt",
                mime="application/x-subrip"
            )

            st.balloons()

        except Exception as error:

            st.error(
                f"❌ Error: {str(error)}"
            )

        finally:

            if video_clip is not None:

                try:
                    video_clip.close()
                except Exception:
                    pass

            for file_path in [
                video_path,
                audio_path
            ]:

                if file_path and os.path.exists(file_path):

                    try:
                        os.remove(file_path)
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
