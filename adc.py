import streamlit as st
import os
import email
from email.policy import default
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Chubb POC", layout="wide", initial_sidebar_state="expanded")

FOLDER_1 = "primary_emails"

# Ensure the inbox directory exists
os.makedirs(FOLDER_1, exist_ok=True)

# --- CUSTOM CSS FOR GMAIL LOOK ---
st.markdown("""
    <style>
    /* Target buttons only in the sidebar to make them look like a flat list */[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border: none !important;
        background-color: transparent !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 10px 15px !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        color: inherit !important;
        transition: background-color 0.2s;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(150, 150, 150, 0.1) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:focus {
        background-color: rgba(150, 150, 150, 0.2) !important;
        outline: none !important;
    }[data-testid="stSidebar"] .stButton > button div {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def clean_html_for_streamlit(html_str):
    """Safely strips out structure/style tags so the email HTML doesn't break Streamlit."""
    clean = re.sub(r'<head[^>]*>.*?</head>', '', html_str, flags=re.IGNORECASE|re.DOTALL)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.IGNORECASE|re.DOTALL)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.IGNORECASE|re.DOTALL)
    clean = re.sub(r'<meta[^>]*>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<link[^>]*>', '', clean, flags=re.IGNORECASE)
    
    clean = re.sub(r'</?html[^>]*>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</?body[^>]*>', '', clean, flags=re.IGNORECASE)
    
    return clean

def parse_email(file_path):
    """Parses an .eml file and returns its components."""
    try:
        with open(file_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=default)

        subject = msg['subject'] or "(No Subject)"
        sender = msg['from'] or "(Unknown Sender)"
        recipient = msg['to'] or "(Unknown Recipient)"
        date = msg['date'] or "(Unknown Date)"

        body = ""
        html_body = ""
        attachments =[]

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition or part.get_filename():
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "content": part.get_payload(decode=True)
                        })
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body += payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')

        return {
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "date": date,
            "body": html_body if html_body else body,
            "is_html": bool(html_body),
            "attachments": attachments
        }
    except Exception as e:
        return None

def generate_reply_data(primary_email_data, generated_body_string):
    """Creates a dictionary representing the generated reply email."""
    
    # 1. Prefix 'Re: ' to the subject if it's not already there
    subject = primary_email_data['subject']
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
        
    # 2. Swap Sender and Recipient
    # The original "To" becomes the new "From". If "To" was missing, default to a standard sender.
    new_sender = primary_email_data.get('recipient', 'me@chubb.com')
    # The original "From" becomes the new "To".
    new_recipient = primary_email_data.get('sender', '(Unknown Recipient)')
    
    # 3. Get Current Time formatted like a standard email date
    current_time_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    return {
        "subject": subject,
        "sender": new_sender,
        "recipient": new_recipient,
        "date": current_time_str,
        "body": generated_body_string,
        "is_html": False, # Setting False since we are passing a plain string
        "attachments":[] # No attachments for the generated string reply
    }

def display_email(parsed_data, key_prefix):
    """Renders the parsed email data in the Streamlit UI."""
    st.subheader(parsed_data['subject'])
    st.caption(f"**From:** {parsed_data['sender']} &nbsp;|&nbsp; **To:** {parsed_data.get('recipient', '(Unknown)')} &nbsp;|&nbsp; **Date:** {parsed_data['date']}")
    
    st.divider()

    if parsed_data['is_html']:
        cleaned_body = clean_html_for_streamlit(parsed_data['body'])
        st.markdown(f"""
            <style>
                .email-container-{key_prefix} * {{
                    color: white !important;
                    background-color: transparent !important;
                    font-family: "Source Sans Pro", sans-serif !important;
                    line-height: 1.6;
                }}
                .email-container-{key_prefix} a {{
                    color: #4da6ff !important; 
                    text-decoration: underline !important;
                }}
                .email-container-{key_prefix} img {{
                    max-width: 100% !important;
                    height: auto !important;
                }}
            </style>
            <div class="email-container-{key_prefix}">
                {cleaned_body}
            </div>
        """, unsafe_allow_html=True)
    else:
        safe_body = parsed_data['body'].replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f"""
            <div style="color: white; font-family: 'Source Sans Pro', sans-serif; white-space: pre-wrap; line-height: 1.6;">
                {safe_body}
            </div>
        """, unsafe_allow_html=True)

    if parsed_data.get('attachments'):
        st.divider()
        st.write("📎 **Attachments:**")
        for idx, att in enumerate(parsed_data['attachments']):
            st.download_button(
                label=f"Download {att['filename']}",
                data=att['content'],
                file_name=att['filename'],
                key=f"{key_prefix}_att_{idx}_{att['filename']}"
            )

# Callback to start the app
def start_app():
    st.session_state.app_started = True

# --- STATE MANAGEMENT ---
if 'app_started' not in st.session_state:
    st.session_state.app_started = False
if 'selected_mail' not in st.session_state:
    st.session_state.selected_mail = None
if 'generated_reply_data' not in st.session_state:
    st.session_state.generated_reply_data = None


# --- MAIN APP LAYOUT ---

# App Title stuck on top of the main screen
st.title("🛡️ Chubb POC")
st.markdown("<hr style='margin-top: 0; margin-bottom: 2rem;'>", unsafe_allow_html=True)

# SIDEBAR: Search and List of emails
with st.sidebar:
    st.markdown("### 📥 Inbox")
    
    if not st.session_state.app_started:
        st.info("Click below to load your inbox.")
        st.markdown("""
            <style>
            [data-testid="stSidebar"] button[kind="primary"] {
                background-color: #FF4B4B !important; 
                color: white !important;
                text-align: center !important;
                justify-content: center !important;
            }
            [data-testid="stSidebar"] button[kind="primary"] div {
                justify-content: center !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.button("🚀 Start App", type="primary", use_container_width=True, on_click=start_app)
        
    else:
        # 1. Search Box
        search_query = st.text_input("🔍 Search emails...", placeholder="Type subject here...")
        st.markdown("<hr style='margin-top: 0; margin-bottom: 1rem;'>", unsafe_allow_html=True)

        # 2. Get all emails
        all_mails = sorted([f for f in os.listdir(FOLDER_1) if f.endswith('.eml')])
        
        # 3. Filter emails based on search query
        if search_query:
            filtered_mails =[m for m in all_mails if search_query.lower() in m.lower()]
        else:
            filtered_mails = all_mails
        
        # 4. Display the filtered results
        if not all_mails:
            st.info(f"No emails found in `{FOLDER_1}` directory.")
        elif not filtered_mails:
            st.warning(f"No emails matched '{search_query}'.")
        else:
            for m in filtered_mails:
                display_name = m.replace('.eml', '')
                # On click, clear previous reply data and load new mail
                if st.button(f"✉️ {display_name}", key=f"btn_{m}"):
                    st.session_state.selected_mail = os.path.join(FOLDER_1, m)
                    st.session_state.generated_reply_data = None

# MAIN AREA: Display selected email and generated email
if st.session_state.selected_mail:
    parsed_primary = parse_email(st.session_state.selected_mail)
    
    if parsed_primary:
        with st.container(border=True):
            display_email(parsed_primary, key_prefix="primary")
        
        st.write("") 
        
        # --- GENERATE REPLY LOGIC ---
        if st.button("✨ Generate Reply", type="primary"):
            
            # --- REPLACE THIS STRING WITH YOUR LLM OUTPUT LATER ---
            generated_body_text = f"""Hello,

Thank you for reaching out. We have received your email and are currently reviewing your request regarding "{parsed_primary['subject']}".

A representative from the Chubb support team will follow up with you shortly. 

Best regards,
Chubb Automated Assistant
"""
            # Create the reply dictionary dynamically
            st.session_state.generated_reply_data = generate_reply_data(
                primary_email_data=parsed_primary,
                generated_body_string=generated_body_text
            )

    else:
        st.error("Failed to parse the selected email.")

    # Display the generated reply if it exists in the session state
    if st.session_state.generated_reply_data:
        st.markdown("---")
        st.markdown("### 🪄 Generated Reply")
        with st.container(border=True):
            display_email(st.session_state.generated_reply_data, key_prefix="generated")
            
else:
    if not st.session_state.app_started:
        st.info("👈 Press the 'Start App' button in the sidebar to load your emails.")
    else:
        st.info("👈 Please select an email from the inbox to get started.")
