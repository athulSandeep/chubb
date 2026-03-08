import streamlit as st
import streamlit.components.v1 as components
import os
import email
from email.policy import default
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Chubb POC", layout="wide", initial_sidebar_state="expanded")

FOLDER_1 = "primary_emails"
FOLDER_2 = "generated_email"

# Ensure the directories exist
os.makedirs(FOLDER_1, exist_ok=True)
os.makedirs(FOLDER_2, exist_ok=True)

# --- CUSTOM CSS FOR GMAIL LOOK ---
st.markdown("""
    <style>
    /* Target buttons only in the sidebar to make them look like a flat list */
    [data-testid="stSidebar"] .stButton > button {
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
    
    /* Hover effect mimicking */
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(150, 150, 150, 0.1) !important;
    }
    
    /* Active/Focus state */[data-testid="stSidebar"] .stButton > button:focus {
        background-color: rgba(150, 150, 150, 0.2) !important;
        outline: none !important;
    }
    
    /* Ensure the text inside the button stays left-aligned */[data-testid="stSidebar"] .stButton > button div {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def parse_email(file_path):
    """Parses an .eml file and returns its components."""
    try:
        with open(file_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=default)

        subject = msg['subject'] or "(No Subject)"
        sender = msg['from'] or "(Unknown Sender)"
        date = msg['date'] or "(Unknown Date)"

        body = ""
        html_body = ""
        attachments =[]

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Check if it's an attachment
                if "attachment" in content_disposition or part.get_filename():
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "content": part.get_payload(decode=True)
                        })
                # Check for plain text body
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                # Check for HTML body
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body += payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
        else:
            # Not multipart, just a single text payload
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or 'utf-8', errors='replace')

        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": html_body if html_body else body,
            "is_html": bool(html_body),
            "attachments": attachments
        }
    except Exception as e:
        return None


def display_email(parsed_data, key_prefix):
    """Renders the parsed email data in the Streamlit UI."""
    st.subheader(parsed_data['subject'])
    st.caption(f"**From:** {parsed_data['sender']} &nbsp;|&nbsp; **Date:** {parsed_data['date']}")
    
    st.divider()

    # Display Body
    if parsed_data['is_html']:
        components.html(parsed_data['body'], height=400, scrolling=True)
    else:
        st.text(parsed_data['body'])

    st.divider()

    # Display Attachments
    if parsed_data['attachments']:
        st.write("**Attachments:**")
        for idx, att in enumerate(parsed_data['attachments']):
            st.download_button(
                label=f"Download {att['filename']}",
                data=att['content'],
                file_name=att['filename'],
                key=f"{key_prefix}_att_{idx}_{att['filename']}"
            )


# --- STATE MANAGEMENT ---
if 'selected_mail' not in st.session_state:
    st.session_state.selected_mail = None
if 'generated_mail' not in st.session_state:
    st.session_state.generated_mail = None


# --- MAIN APP LAYOUT ---

# App Title in the main area
st.title("Chubb POC")

# SIDEBAR: List of emails from Folder 1
with st.sidebar:
    st.title("Inbox")
    mails =[f for f in os.listdir(FOLDER_1) if f.endswith('.eml')]
    
    if not mails:
        st.info(f"No emails found in `{FOLDER_1}`.")
    else:
        for m in mails:
            # Strip the .eml extension for a cleaner Gmail-like look
            display_name = m.replace('.eml', '')
            
            # When an email button is clicked, load it and reset the generated email
            if st.button(f"{display_name}", key=f"btn_{m}"):
                st.session_state.selected_mail = os.path.join(FOLDER_1, m)
                st.session_state.generated_mail = None

# MAIN AREA: Display selected email and generated email
if st.session_state.selected_mail:
    # 1. Display Primary Selected Email
    parsed_primary = parse_email(st.session_state.selected_mail)
    
    if parsed_primary:
        # Putting it in a visual container for neatness
        with st.container(border=True):
            display_email(parsed_primary, key_prefix="primary")
        
        # 2. Generate Button
        st.write("") # slight spacing
        if st.button("Generate Reply", type="primary"):
            folder2_mails =[f for f in os.listdir(FOLDER_2) if f.endswith('.eml')]
            if folder2_mails:
                random_mail = random.choice(folder2_mails)
                st.session_state.generated_mail = os.path.join(FOLDER_2, random_mail)
            else:
                st.warning(f"No '.eml' files found in `{FOLDER_2}` directory.")
    else:
        st.error("Failed to parse the selected email.")

    # 3. Display Generated Email Below (if the button was clicked)
    if st.session_state.generated_mail:
        st.markdown("---")
        st.markdown("### Reply Email")
        parsed_generated = parse_email(st.session_state.generated_mail)
        
        if parsed_generated:
            with st.container(border=True):
                display_email(parsed_generated, key_prefix="generated")
        else:
            st.error("Failed to parse the generated email.")
            
else:
    st.info("Please select an email from the inbox on the left to view it.")