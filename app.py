import os
import streamlit as st
import whisper
import moviepy as mp
from deep_translator import GoogleTranslator

# Page Configuration
st.set_page_config(page_title="Zwe Video Translation", page_icon="🎬", layout="wide")

st.title("🎬 Zwe Video Translation")
st.markdown("ဗီဒီယိုဖိုင် တင်လိုက်တာနဲ့ AI ကိုသုံးပြီး အလိုအလျောက် စာသားထုတ်၊ ဘာသာပြန်ပြီး Subtitle ထုတ်ပေးမယ့် Web App ဖြစ်ပါတယ်။")

# Sidebar - Settings
st.sidebar.header("⚙️ Settings")
target_lang = st.sidebar.selectbox("ဘာသာပြန်မည့် ဘာသာစကား (Target Language)", ["Burmese (မြန်မာ)", "English", "Chinese"])
model_size = st.sidebar.selectbox("AI Model Size (Whisper)", ["tiny", "base", "small"])

lang_code_map = {
    "Burmese (မြန်မာ)": "my",
    "English": "en",
    "Chinese": "zh-cn"
}
selected_lang_code = lang_code_map[target_lang]

# Main File Uploader
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင် တင်ပါ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

if uploaded_file is not None:
    video_path = "temp_video.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.video(video_path)
    
    if st.button("🚀 ဗီဒီယို ဘာသာပြန်ခြင်း စတင်ရန်"):
        with st.status("🔄 AI လုပ်ဆောင်နေပါပြီ...", expanded=True) as status:
            
            # Step 1: Extract Audio Safely
            st.write("🔊 ဗီဒီယိုမှ အသံဖိုင် (Audio) ကို ထုတ်ယူနေသည်...")
            audio_path = "temp_audio.mp3"
            
            video_clip = mp.VideoFileClip(video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_path, logger=None)
            
            # Step 2: Speech to Text (Whisper)
            st.write(f"✍️ Whisper Model ({model_size}) ဖြင့် အသံများကို စာသားပြောင်းနေသည်...")
            model = whisper.load_model(model_size)
            result = model.transcribe(audio_path)
            segments = result["segments"]
            
            # Step 3: Translation using deep-translator
            st.write(f"🌍 စာသားများကို {target_lang} သို့ ဘာသာပြန်နေသည်...")
            translator = GoogleTranslator(source='auto', target=selected_lang_code)
            translated_segments = []
            
            for seg in segments:
                original_text = seg["text"]
                try:
                    translated_text = translator.translate(original_text)
                except Exception:
                    translated_text = original_text
                    
                translated_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": translated_text
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
        # Cleanup clips and temporary files safely
        try:
            if 'audio_clip' in locals() and audio_clip:
                audio_clip.close()
            if 'video_clip' in locals() and video_clip:
                video_clip.close()
            if os.path.exists(video_path): 
                os.remove(video_path)
            if os.path.exists(audio_path): 
                os.remove(audio_path)
        except Exception as e:
            pass
