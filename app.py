import os
import tempfile
import urllib.parse
import urllib.request
import json
import streamlit as st
import whisper
import moviepy as mp

# Page Configuration
st.set_page_config(page_title="Zwe Video Translation", page_icon="🎬", layout="wide")

st.title("🎬 Zwe Video Translation")
st.markdown("ဗီဒီယိုဖိုင် တင်လိုက်တာနဲ့ AI ကိုသုံးပြီး အလိုအလျောက် စာသားထုတ်၊ ဘာသာပြန်ပြီး Subtitle ထုတ်ပေးမယ့် Web App ဖြစ်ပါတယ်။")

# Sidebar - Settings
st.sidebar.header("⚙️ Settings")
source_lang_option = st.sidebar.selectbox("မူရင်းဗီဒီယို ဘာသာစကား (Source Language)", ["Chinese (တရုတ်)", "English (အင်္ဂလိပ်)", "Japanese (ဂျပန်)", "Korean (ကိုရီးယား)", "Auto-detect"])
target_lang = st.sidebar.selectbox("ဘာသာပြန်မည့် ဘာသာစကား (Target Language)", ["Burmese (မြန်မာ)", "English"])
model_size = st.sidebar.selectbox("AI Model Size (Whisper)", ["tiny", "base", "small"])

# Target Language code
if "မြန်မာ" in target_lang:
    selected_lang_code = "my"
else:
    selected_lang_code = "en"

source_lang_map = {
    "Chinese (တရုတ်)": "zh-cn",
    "English (အင်္ဂလိပ်)": "en",
    "Japanese (ဂျပန်)": "ja",
    "Korean (ကိုရီးယား)": "ko",
    "Auto-detect": "auto"
}
selected_source_lang = source_lang_map[source_lang_option]

# Direct free Google Translate function to avoid translation API blocks
def translate_text(text, target='my'):
    if not text.strip():
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + target + "&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            translated = "".join([item[0] for item in result[0] if item[0]])
            return translated
    except Exception:
        return text

# Main File Uploader
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင် တင်ပါ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.video(uploaded_file)
    
    if st.button("🚀 ဗီဒီယို ဘာသာပြန်ခြင်း စတင်ရန်"):
        with st.status("🔄 AI လုပ်ဆောင်နေပါပြီ...", expanded=True) as status:
            
            # Step 1: Extract Audio Safely as WAV
            st.write("🔊 ဗီဒီယိုမှ အသံဖိုင် (Audio) ကို ထုတ်ယူနေသည်...")
            audio_path = video_path + ".wav"
            
            video_clip = mp.VideoFileClip(video_path)
            if video_clip.audio is not None:
                video_clip.audio.write_audiofile(audio_path, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
            else:
                st.error("❌ ဤဗီဒီယိုဖိုင်တွင် အသံ (Audio) မပါရှိပါ။")
                st.stop()
            
            # Step 2: Speech to Text (Whisper)
            st.write(f"✍️ Whisper Model ({model_size}) ဖြင့် အသံများကို စာသားပြောင်းနေသည်...")
            model = whisper.load_model(model_size)
            
            if selected_source_lang != "auto":
                result = model.transcribe(audio_path, language=selected_source_lang, fp16=False)
            else:
                result = model.transcribe(audio_path, fp16=False)
                
            segments = result["segments"]
            
            # Step 3: Translation using direct translation API
            st.write(f"🌍 စာသားများကို {target_lang} သို့ ဘာသာပြန်နေသည်...")
            
            translated_segments = []
            
            for seg in segments:
                original_text = seg["text"].strip()
                if not original_text:
                    continue
                
                translated_text = translate_text(original_text, target=selected_lang_code)
                translated_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": translated_text if translated_text else original_text
                })
            
            status.update(label="✅ အောင်မြင်စွာ ပြီးဆုံးပါပြီ!", state="complete", expanded=False)
        
        st.success("🎉 ဘာသာပြန်ခြင်း ပြီးစီးပါပြီ။ Subtitle များကို အောက်တွင် ကြည့်ရှုနိုင်ပါပြီ။")
        
        # Display Subtitles
        st.subheader("📋 Generated Subtitles")
        
        srt_content = ""
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            milliseconds = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

        for i, seg in enumerate(translated_segments, start=1):
            start_t = format_time(seg["start"])
            end_t = format_time(seg["end"])
            txt = seg["text"].strip() if seg["text"] else ""
            
            srt_content += f"{i}\n{start_t} --> {end_t}\n{txt}\n\n"
            
            st.markdown(f"""
            [{start_t} - {end_t}]  
            {txt}
            """)
            st.divider()

        # Download Button for SRT File
        st.download_button(
            label="📥 Subtitle ဖိုင် (.SRT) ကို Download ရယူရန်",
            data=srt_content,
            file_name="translated_subtitle.srt",
            mime="text/plain"
        )

        # Cleanup temporary files safely
        try:
            if 'video_clip' in locals() and video_clip:
                video_clip.close()
            if os.path.exists(video_path): 
                os.remove(video_path)
            if os.path.exists(audio_path): 
                os.remove(audio_path)
        except Exception as e:
            pass
