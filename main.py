import os
import io
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image

# 1. Native Page Config
st.set_page_config(
    layout="centered",
    page_title="SilverGuide Workspace",
    page_icon="👵"
)

# 2. Inject Container CSS Styles for Gemini-Style chat bar
st.markdown('''
<style>
/* Artistic Cyberpunk Gradient Background */
.stApp {
    background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #06040a 100%) !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* Transparent Frosted Glass Cards for Messages */
div[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    margin-bottom: 12px !important;
    padding: 16px !important;
}

/* Neon Left Accents for Active Mode */
div[data-testid="stNotification"] {
    background: rgba(138, 43, 226, 0.1) !important;
    border-left: 4px solid #8a2be2 !important;
    border-radius: 8px !important;
}

/* Unified Glowing Bottom Chat Capsule */
div[data-testid="stForm"] {
    background: rgba(20, 15, 35, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(138, 43, 226, 0.4) !important;
    box-shadow: 0 0 15px rgba(138, 43, 226, 0.2) !important;
    border-radius: 30px !important;
    padding: 8px 16px !important;
    margin-top: 10px !important;
}

/* Make form submit buttons circular */
div[data-testid="stForm"] button {
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.3rem !important;
    background: #8a2be2 !important;
    border: none !important;
    color: #fff !important;
}

/* Make the media plus button circular */
div[data-testid="column"]:first-child button {
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.3rem !important;
    background: rgba(138, 43, 226, 0.2) !important;
    border: 1px solid rgba(138, 43, 226, 0.4) !important;
    color: #fff !important;
}
</style>
''', unsafe_allow_html=True)

# Initialize session state variables
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_media_panel" not in st.session_state:
    st.session_state.show_media_panel = False
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False
if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0
if "last_media_key" not in st.session_state:
    st.session_state.last_media_key = None

def add_tts_button(text_to_speak):
    safe_text = text_to_speak.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    html_code = f"""
    <button onclick="speak()" style="
        font-size: 1.2rem;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 8px;
        border: 2px solid #854D0E;
        background-color: #FEF08A;
        color: #854D0E;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 15px;
        width: 100%;
        justify-content: center;
    ">
        🔊 Read Last Response Aloud
    </button>
    <script>
        function speak() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.rate = 0.85;
            window.speechSynthesis.speak(msg);
        }}
    </script>
    """
    components.html(html_code, height=60)

# Onboarding Greeting Workflow
if not st.session_state.user_name:
    st.title("👵👴 SilverGuide Workspace")
    st.write("Welcome! Let's get to know you first.")
    name_input = st.text_input("Please enter your name:")
    if st.button("Start Workspace 🚀"):
        if name_input.strip():
            st.session_state.user_name = name_input.strip()
            st.session_state.chat_history = []
            st.rerun()
        else:
            st.warning("Please tell us your name first!")
else:
    # Warm greeting banner inside a stylized glassmorphic card presentation
    st.markdown(
        f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
            text-align: center;
        ">
            <h1 style="color: #A78BFA; margin: 0; font-size: 2.2rem;">✨ SilverGuide Workspace ✨</h1>
            <p style="color: #E2E8F0; font-size: 1.2rem; margin: 10px 0 0 0;">
                Hello, <b>{st.session_state.user_name}</b>! We are ready to make things simple and clear for you today.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Change Name 🔄"):
            st.session_state.user_name = ""
            st.session_state.chat_history = []
            st.session_state.show_media_panel = False
            st.session_state.camera_active = False
            st.session_state.camera_key += 1
            st.session_state.last_media_key = None
            st.rerun()
            
    # Accessibility Mode Selector
    app_mode = st.radio(
        'Choose your guide style:',
        ['🔍 Help me fix a Software Update / Screen Issue', '💬 General Conversation'],
        horizontal=True
    )

    # Display running chat history
    if len(st.session_state.chat_history) > 0:
        st.write("### 💬 Workspace Conversation")
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if "image" in msg and msg["image"] is not None:
                    st.image(msg["image"], caption="📸 Support Feed Image")
                st.write(msg["text"])
                
        # TTS Button
        last_model_msg = None
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "assistant":
                last_model_msg = msg["text"]
                break
        if last_model_msg:
            add_tts_button(last_model_msg)

    # Real Visual/Text Chat Pipeline Processing
    if len(st.session_state.chat_history) > 0 and st.session_state.chat_history[-1]["role"] == "user":
        # Initialize Client SECURELY using Streamlit Cloud secrets management
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        except Exception:
            # Fallback for local terminal testing if secrets file isn't populated locally
            client = genai.Client()
        
        # Jargon-Free System Instruction conditional on selected app mode
        if "Help me fix" in app_mode:
            system_instruction = (
                f"You are SilverGuide, an empathetic, highly specialized tech accessibility companion for elderly users "
                f"and people experiencing frustration with software updates. Never use technical jargon or words like UI, "
                f"Interface, Button, Click, or Hamburger Menu. When presented with a screenshot or photo of a device, "
                f"describe what is on the screen in simple household terms. Force yourself to describe things using "
                f"physical spatial orientation (e.g., 'Look at the top right corner, find the three stacked lines that look "
                f"like a small sandwich...'). Restrict yourself to giving exactly ONE clear, physical, step-by-step action "
                f"at a time, followed by: 'Let me know when you have done this, {st.session_state.user_name}, and we will take "
                f"the next step together.' Keep your tone incredibly warm, encouraging, and patient."
            )
        else:
            system_instruction = (
                f"You are SilverGuide, a warm, patient, and empathetic conversational AI companion helping "
                f"{st.session_state.user_name} with their tech or general queries. Always respond in large, simple, "
                f"senior-friendly language. Address the user directly by name."
            )
        
        config = {
            'system_instruction': system_instruction
        }
        
        # Extract the image if any is present in history
        uploaded_image = None
        for msg in st.session_state.chat_history:
            if "image" in msg and msg["image"] is not None:
                uploaded_image = msg["image"]
                break
                
        # Format the chat history as a flat text context
        formatted_history = ""
        for msg in st.session_state.chat_history[:-1]:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role_label}: {msg['text']}\n\n"
            
        current_query = st.session_state.chat_history[-1]["text"]
        
        user_text_query = f"""
        Conversation History so far:
        {formatted_history}
        
        Current Question:
        "{current_query}"
        """
        
        contents_payload = []
        if uploaded_image is not None:
            contents_payload.append(uploaded_image)
        contents_payload.append(user_text_query)
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_text = ""
            try:
                response_stream = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=contents_payload,
                    config=config
                )
                for chunk in response_stream:
                    full_text += chunk.text
                    placeholder.write(full_text)
                    
                # Save response to history log
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "text": full_text
                })
                # Webcam unmount lifecycle sequence reset to default
                st.session_state.camera_active = False
                st.session_state.camera_key += 1
                st.session_state.show_media_panel = False
                st.rerun()
            except Exception as e:
                st.error(f"Error communicating with Gemini: {str(e)}")

    # Integrated Input Bar
    col_btn, col_form = st.columns([1, 9])
    with col_btn:
        st.write(" ")
        st.write(" ")
        media_clicked = st.button("➕", help="Add Media")
        
    with col_form:
        with st.form(key='gemini_chat_bar', clear_on_submit=True):
            col_text, col_submit = st.columns([9, 1])
            with col_text:
                user_msg = st.text_input("Enter your message", placeholder="Ask SilverGuide or attach media...", label_visibility="collapsed")
            with col_submit:
                submit_clicked = st.form_submit_button("➔", help="Send Message")
            
    # Process toolbar toggles immediately outside the form
    if media_clicked:
        st.session_state.show_media_panel = not st.session_state.show_media_panel
        if not st.session_state.show_media_panel:
            st.session_state.camera_active = False
            st.session_state.camera_key += 1
        st.rerun()

    # Trigger Overlays - Media Collection Tray
    camera_file = None
    uploaded_file = None
    if st.session_state.show_media_panel:
        with st.expander("📷 Add Photos or Screenshot Files", expanded=True):
            col_cam, col_file = st.columns(2)
            with col_cam:
                if not st.session_state.camera_active:
                    if st.button("📸 Open Camera Device", key="open_cam_btn"):
                        st.session_state.camera_active = True
                        st.rerun()
                else:
                    camera_file = st.camera_input("Capture Screen", key=f"webcam_{st.session_state.camera_key}")
                    if camera_file:
                        st.session_state.camera_active = False
                        st.session_state.camera_key += 1
                        st.session_state.show_media_panel = False
            with col_file:
                uploaded_file = st.file_uploader(
                    "Upload screenshot file",
                    type=["png", "jpg", "jpeg", "pdf", "txt"]
                )
                if uploaded_file:
                    st.session_state.show_media_panel = False

    # Active media asset resolver
    active_file = None
    if uploaded_file is not None:
        file_key = f"upload_{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.last_media_key != file_key:
            st.session_state.last_media_key = file_key
            active_file = uploaded_file
    elif camera_file is not None:
        file_key = f"camera_{camera_file.size}"
        if st.session_state.last_media_key != file_key:
            st.session_state.last_media_key = file_key
            active_file = camera_file

    if active_file is not None:
        img_obj = Image.open(io.BytesIO(active_file.read()))
        # Reset visual stream flags and force camera unmount
        st.session_state.camera_active = False
        st.session_state.camera_key += 1
        st.session_state.show_media_panel = False
        
        user_text = "I have uploaded a screenshot. Please explain what is on my screen and tell me what to do next in simple, jargon-free steps."
        st.session_state.chat_history.append({
            "role": "user",
            "text": user_text,
            "image": img_obj
        })
        st.rerun()

    # Submit Chat Message
    if submit_clicked and user_msg.strip():
        st.session_state.camera_active = False
        st.session_state.camera_key += 1
        st.session_state.chat_history.append({
            "role": "user",
            "text": user_msg.strip()
        })
        st.rerun()