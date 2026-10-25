import os
import random
import string
import streamlit as st
import streamlit.components.v1 as components
from ai_assistant import analyze_code_error
from execution import run_code

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DevHive AI — Collaborative Workspace",
    page_icon="</>",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD EXTERNAL CSS ---
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# --- INITIALIZE SESSION STATES ---
if "in_room" not in st.session_state:
    st.session_state.in_room = False
if "room_name" not in st.session_state:
    st.session_state.room_name = ""
if "room_id" not in st.session_state:
    st.session_state.room_id = ""
if "room_link" not in st.session_state:
    st.session_state.room_link = ""
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_host" not in st.session_state:
    st.session_state.is_host = False
if "host_name" not in st.session_state:
    st.session_state.host_name = ""
if "members" not in st.session_state:
    st.session_state.members = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "screen_share_active" not in st.session_state:
    st.session_state.screen_share_active = False

# Voice & Audio State Controls (Defaulted to OFF / MUTED)
if "mic_active" not in st.session_state:
    st.session_state.mic_active = False
if "speaker_active" not in st.session_state:
    st.session_state.speaker_active = False
if "muted_peers" not in st.session_state:
    st.session_state.muted_peers = {} # Format: {username: bool}

# Code Editor Templates & Storage State (Enterprise SQL Default)
TEMPLATES = {
    "Python": '# Write your Python code here\nprint("Hello from DevHive Python!")',
    "JavaScript": '// Write your JavaScript code here\nconsole.log("Hello from DevHive JS!");',
    "Java": '// Write your Java code here\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java!");\n    }\n}',
    "SQL": '-- Enterprise Database Query\nSELECT employee_id, department, status_code FROM employees WHERE status_code = "ACTIVE";',
    "C": '// Write your C code here\n#include <stdio.h>\nint main() {\n    printf("Hello from C!\\n");\n    return 0;\n}',
    "C++": '// Write your C++ code here\n#include <iostream>\nusing namespace std;\nint main() {\n    cout << "Hello from C++!" << endl;\n    return 0;\n}',
    "HTML": '<!-- Write your HTML markup here -->\n<!DOCTYPE html>\n<html>\n<body>\n    <h1>Hello from DevHive HTML!</h1>\n</body>\n</html>',
}

if "code_map" not in st.session_state:
    st.session_state.code_map = TEMPLATES.copy()

# Helper to generate secure automated room ID and link
def generate_room_credentials(room_title):
    random_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    sanitized_name = "".join(c if c.isalnum() else "-" for c in room_title.lower()).strip("-")
    generated_id = f"{sanitized_name}-{random_code}"
    generated_link = f"https://devhive.ai/room/{generated_id}"
    return generated_id, generated_link

# ==============================================================================
# STAGE 1: LANDING PAGE / ROOM LOBBY
# ==============================================================================
if not st.session_state.in_room:
    st.title("DevHive AI — Workspace Lobby")
    st.caption("Track 2: AI for Developers | Real-Time Collaborative Developer Studio")
    
    st.divider()
    
    col_lobby1, col_lobby2 = st.columns(2, gap="large")
    
    with col_lobby1:
        st.subheader("Create a New Room")
        st.write("Provide your name and a room name. Our system will automatically generate your secure Room ID and shareable link.")
        
        create_username = st.text_input("Your Display Name (Host):", value="", placeholder="Enter your name...", key="create_user")
        create_room_name = st.text_input("Room Name:", value="", placeholder="e.g. Hackathon Final Sprint", key="create_room_name")
        
        if st.button("Create & Enter Room", type="primary"):
            if create_username.strip() and create_room_name.strip():
                gen_id, gen_link = generate_room_credentials(create_room_name.strip())
                st.session_state.username = create_username.strip()
                st.session_state.room_name = create_room_name.strip()
                st.session_state.room_id = gen_id
                st.session_state.room_link = gen_link
                st.session_state.is_host = True
                st.session_state.host_name = create_username.strip()
                st.session_state.members = [create_username.strip()]
                st.session_state.in_room = True
                st.rerun()
            else:
                st.error("Please enter both your display name and a room name.")

    with col_lobby2:
        st.subheader("Join Existing Room")
        st.write("Enter your name and the Room ID provided by your host to connect.")
        
        join_username = st.text_input("Your Display Name:", value="", placeholder="Enter your name...", key="join_user")
        join_room_id = st.text_input("Enter Room ID:", value="", placeholder="e.g. hackathon-final-sprint-9x4b2a", key="join_room_id")
        
        if st.button("Join Room"):
            if join_username.strip() and join_room_id.strip():
                st.session_state.username = join_username.strip()
                st.session_state.room_id = join_room_id.strip()
                st.session_state.room_name = join_room_id.strip().split('-')[0].capitalize()
                st.session_state.room_link = f"https://devhive.ai/room/{join_room_id.strip()}"
                st.session_state.is_host = False
                if not st.session_state.host_name:
                    st.session_state.host_name = "Host"
                if join_username.strip() not in st.session_state.members:
                    st.session_state.members.append(join_username.strip())
                st.session_state.in_room = True
                st.rerun()
            else:
                st.error("Please enter both your display name and the Room ID.")

# ==============================================================================
# STAGE 2: ACTIVE COLLABORATIVE WORKSPACE
# ==============================================================================
else:
    # --- HEADER SECTION ---
    st.title(f"Room: `{st.session_state.room_name}`")
    role_badge = "[HOST]" if st.session_state.is_host else "[MEMBER]"
    st.caption(f"Logged in as: **{st.session_state.username}** `{role_badge}` | Room ID: `{st.session_state.room_id}`")

    # --- SIDEBAR: Room Members, High-End Audio & Controls ---
    with st.sidebar:
        st.header("Workspace Control Center")
        st.write(f"**Room Name:** {st.session_state.room_name}")
        st.markdown(f"**Room ID:** `{st.session_state.room_id}`")
        st.markdown(f"**Share Link:**\n`{st.session_state.room_link}`")
        st.write(f"**Host:** {st.session_state.host_name} `[HOST]`")
        
        st.divider()
        
        # --- VOICE & AUDIO CHANNELS (ENTERPRISE GRADE) ---
        st.subheader("Voice & Audio Channels")
        
        mic_label = "Mic: TRANSMITTING" if st.session_state.mic_active else "Mic: MUTED"
        if st.button(mic_label, use_container_width=True):
            st.session_state.mic_active = not st.session_state.mic_active
            st.rerun()
            
        speaker_label = "Master Speaker: ACTIVE" if st.session_state.speaker_active else "Master Speaker: MUTED"
        if st.button(speaker_label, use_container_width=True):
            st.session_state.speaker_active = not st.session_state.speaker_active
            st.rerun()
            
        ai_noise_filter = st.toggle("AI Noise Suppression", value=True)
        if ai_noise_filter:
            st.caption("Background typing & noise filtered via AI.")
            
        st.divider()
        st.subheader(f"Active Members ({len(st.session_state.members)})")
        
        for member in st.session_state.members:
            is_self = (member == st.session_state.username)
            role_tag = "[HOST]" if member == st.session_state.host_name else "[Active]"
            
            col_m1, col_m2 = st.columns([1.4, 1])
            with col_m1:
                st.write(f"**{member}** `{role_tag}`")
            with col_m2:
                if not is_self and st.session_state.speaker_active:
                    is_muted = st.session_state.muted_peers.get(member, False)
                    mute_btn_label = "Unmute" if is_muted else "Mute Peer"
                    if st.button(mute_btn_label, key=f"mute_{member}"):
                        st.session_state.muted_peers[member] = not is_muted
                        st.rerun()
                elif is_self:
                    st.caption("(You)")
                else:
                    st.caption("Muted")
                
        st.divider()
        
        # --- HOST PRIVILEGE: Screen Sharing Control ---
        if st.session_state.is_host:
            st.subheader("Host Controls")
            if not st.session_state.screen_share_active:
                if st.button("Start Screen Share Broadcast"):
                    st.session_state.screen_share_active = True
                    st.rerun()
            else:
                if st.button("Stop Screen Share"):
                    st.session_state.screen_share_active = False
                    st.rerun()
        else:
            if st.session_state.screen_share_active:
                st.info("Host is currently broadcasting screen share stream.")
        
        st.divider()
        
        if st.button("Leave Room"):
            if st.session_state.username in st.session_state.members:
                st.session_state.members.remove(st.session_state.username)
            st.session_state.in_room = False
            st.rerun()

    # --- SCREEN SHARE MODULE (If Active) ---
    if st.session_state.screen_share_active:
        st.subheader("Host Screen Share Stream")
        if st.session_state.is_host:
            st.info("Screen Share is active. Select the browser window or desktop tab to broadcast.")
            screen_share_html = """
            <div style="background-color:#020617; padding:15px; border-radius:10px; border:1px solid #334155; text-align:center;">
                <video id="screenVideo" autoplay playsinline style="width:100%; max-height:400px; border-radius:8px; background:#000;"></video>
                <br/><br/>
                <button onclick="startSharing()" style="background:linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:600; cursor:pointer;">
                    Select Screen / Window to Share
                </button>
            </div>
            <script>
                async function startSharing() {
                    try {
                        const mediaStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                        const videoElement = document.getElementById('screenVideo');
                        videoElement.srcObject = mediaStream;
                    } catch (err) {
                        console.error("Error sharing screen: " + err);
                    }
                }
            </script>
            """
            components.html(screen_share_html, height=480)
        else:
            st.warning("Viewing host broadcast feed...")
            components.html("""
            <div style="background-color:#020617; padding:20px; border-radius:10px; border:1px solid #334155; text-align:center; color:#10B981;">
                <h3>Live Stream Active from Host</h3>
                <p style="color:#94A3B8;">Connecting to host WebRTC stream feed...</p>
            </div>
            """, height=150)

    # --- MAIN WORKSPACE SPLIT ---
    col_left, col_right = st.columns([1.2, 1], gap="large")

    with col_left:
        st.subheader("Collaborative Code Editor")

        # Bulletproof language selector bound directly to isolated code state map
        language = st.selectbox(
            "Select Programming Language:",
            list(TEMPLATES.keys()),
            key="current_language_selection"
        )

        # Ensure active language buffer is initialized
        if language not in st.session_state.code_map:
            st.session_state.code_map[language] = TEMPLATES.get(language, "")

        # Text area synchronized with language-specific key
        user_code = st.text_area(
            "Code Editor:", 
            value=st.session_state.code_map[language], 
            height=320,
            key=f"editor_box_{language}"
        )

        # Keep code map updated as user types
        st.session_state.code_map[language] = user_code

        if st.button("Run Code / Preview", type="primary"):
            with st.spinner(f"Executing {language} code..."):
                result = run_code(language, user_code)
                st.session_state.last_result = result

        st.subheader("Execution Terminal / Preview View")

        if language == "HTML":
            st.info("Rendering HTML Live Preview:")
            components.html(user_code, height=200, scrolling=True)
        else:
            if st.session_state.last_result:
                res = st.session_state.last_result
                if res["status"] == "Success":
                    st.markdown('<span class="status-badge-success">EXECUTED SUCCESSFULLY</span>', unsafe_allow_html=True)
                    st.code(
                        res["output"] if res["output"] else "Executed successfully.",
                        language="text",
                    )
                else:
                    st.markdown('<span class="status-badge-error">EXECUTION FAILED</span>', unsafe_allow_html=True)
                    st.code(res["error"], language="python")

    with col_right:
        st.subheader("AI Debugger & Task Handoff")

        if st.session_state.last_result and st.session_state.last_result["error"]:
            if st.button("Analyze & Fix Error with AI"):
                with st.spinner("Analyzing error context..."):
                    ai_fix = analyze_code_error(
                        user_code, st.session_state.last_result["error"]
                    )
                    st.markdown(ai_fix)
        else:
            st.info("Run code containing an error to unlock AI debugging recommendations.")

        st.divider()

        st.subheader("Room Chat & Snippet Stream")
        chat_input = st.text_input(
            "Send note to team in room:", placeholder="Type a message..."
        )
        if st.button("Send"):
            if chat_input:
                sender = st.session_state.username
                role_tag = "[HOST]" if st.session_state.is_host else "[MEMBER]"
                st.session_state.chat_history.append(f"{sender} {role_tag}: {chat_input}")

        for msg in reversed(st.session_state.chat_history):
            st.write(f"**{msg}**")