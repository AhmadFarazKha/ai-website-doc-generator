import streamlit as st
import os
from src.core.doc_generator import take_screenshot, generate_description, create_documentation_report
from src.utils.file_handler import create_directories_if_not_exist
from dotenv import load_dotenv
import io
from PIL import Image

load_dotenv()

# --- Streamlit Session State Initialization ---
if 'url_input' not in st.session_state:
    st.session_state.url_input = ""
if 'doc_report_data' not in st.session_state:
    st.session_state.doc_report_data = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'final_doc_bytes' not in st.session_state:
    st.session_state.final_doc_bytes = None


# --- Page Configuration ---
st.set_page_config(
    page_title="AI Website Doc Generator",
    page_icon="🤖📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Cleaned and Correct Custom CSS ---
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    body { font-family: 'Montserrat', sans-serif; }
    .main { background-color: var(--background-color); color: var(--text-color); }
    .st-emotion-cache-z5fcl4 { padding-top: 2rem; padding-bottom: 2rem; padding-left: 1rem; padding-right: 1rem; }
    .stApp > header { background-color: transparent !important; height: 0px; }
    h1 { color: var(--primary-color); text-align: center; font-weight: 700; margin-bottom: 0.5rem; font-size: 2.5rem; }
    h3 { color: var(--primary-color); font-weight: 600; margin-top: 2rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(var(--primary-color-rgb), 0.3); }
    p { line-height: 1.6; color: var(--text-color); }

    .stTextArea label, .stTextInput label, .stFileUploader label, .stSelectbox label { color: var(--text-color); font-weight: 600; font-size: 1.05rem; margin-bottom: 0.5rem; }
    .stTextArea>div>div>textarea, .stTextInput>div>div>input, .stSelectbox>div>div {
        background-color: var(--secondary-background-color); color: var(--text-color); border: 1px solid var(--primary-color); border-radius: 8px; padding: 10px 15px;
    }
    .stTextArea>div>div>textarea:focus, .stTextInput>div>div>input:focus, .stSelectbox>div:focus-within {
        border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.4);
    }
    .stFileUploader>div>div>button {
        background-color: var(--secondary-background-color); color: white; border-radius: 8px; padding: 10px 20px; font-size: 1rem; font-weight: 600; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.3s ease;
    }
    .stFileUploader>div>div>button:hover {
        background-color: rgba(var(--secondary-background-color-rgb), 0.8); box-shadow: 0 6px 15px rgba(0,0,0,0.4); transform: translateY(-1px);
    }
    .stFileUploader>div>div>p { color: var(--text-color); font-weight: 500; margin-top: 0.5rem; }
    .stButton>button {
        background-color: var(--primary-color); color: white; border-radius: 8px; border: none; padding: 10px 20px; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 1rem;
    }
    .stButton>button:hover { background-color: rgba(var(--primary-color-rgb), 0.8); }

    .stButton:nth-of-type(2)>button, .stDownloadButton>button {
        background-color: var(--secondary-background-color); color: var(--primary-color); border: 1px solid var(--primary-color);
    }
    .stButton:nth-of-type(2)>button:hover, .stDownloadButton>button:hover {
        background-color: rgba(var(--secondary-background-color-rgb), 0.8); color: var(--primary-color);
    }
    .stDownloadButton>button { margin-top: 1rem; padding: 10px 20px; }
    .stSpinner > div > div > div { color: var(--primary-color) !important; }

    .footer-text { text-align: center; font-size: 0.85rem; color: #707070; margin-top: 3rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Application Content ---
st.title("🤖📝 AI Website Documentation Generator")
st.markdown("<p style='text-align: center; color: var(--text-color); font-size: 1.1rem; margin-bottom: 2rem;'>Automate documentation for websites by generating screenshots and AI-powered descriptions into a Word document.</p>", unsafe_allow_html=True)

st.info("⚠️ This process can be slow as it involves browser automation and multiple AI API calls. Please be patient.")

col_main_l, col_main_center, col_main_r = st.columns([1, 4, 1])

with col_main_center:
    with st.container(border=True):
        st.markdown("### 1. Enter Website Details")
        st.text_input(
            "Website URL (include http:// or https://):",
            value=st.session_state.url_input,
            placeholder="e.g., https://streamlit.io",
            key="url_input" # Letting Streamlit handle the state automatically
        )
        
        options_to_document = st.multiselect(
            "Select pages/elements to document:",
            options=[
                "Homepage",
                "About Page",
                "Pricing Page",
                "Contact Page",
                "Header & Navigation Bar",
                "Footer"
            ],
            default=["Homepage"],
            key="doc_options"
        )

    st.markdown("---")

    col_btn_generate, col_btn_clear = st.columns(2)
    with col_btn_generate:
        if st.button("Generate Documentation Report 🚀", use_container_width=True, key="btn_generate_doc"):
            if not st.session_state.url_input: # Accessing the state via the key
                st.warning("Please enter a website URL.")
                st.stop()
            
            st.session_state.is_processing = True
            st.session_state.doc_report_data = []
            st.session_state.final_doc_bytes = None
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                progress_step = 1 / (len(options_to_document) * 2)
                
                for i, doc_item in enumerate(options_to_document):
                    status_text.info(f"Step {i*2+1} of {len(options_to_document)*2}: Capturing screenshot for '{doc_item}'...")
                    progress_bar.progress(progress_step * (i*2+1))

                    selector = None
                    url_to_goto = st.session_state.url_input
                    
                    if doc_item == "Homepage":
                        selector = 'body'
                    elif doc_item == "About Page":
                        url_to_goto += '/about'
                    elif doc_item == "Pricing Page":
                        url_to_goto += '/pricing'
                    elif doc_item == "Contact Page":
                        url_to_goto += '/contact'
                    elif doc_item == "Header & Navigation Bar":
                        selector = 'header'
                    elif doc_item == "Footer":
                        selector = 'footer'
                    
                    screenshot_bytes = take_screenshot(url_to_goto, selector)
                    
                    status_text.info(f"Step {i*2+2} of {len(options_to_document)*2}: Generating AI description for '{doc_item}'...")
                    progress_bar.progress(progress_step * (i*2+2))

                    ai_description = generate_description(screenshot_bytes, f"Screenshot of the '{doc_item}' on the website.")
                    
                    st.session_state.doc_report_data.append({
                        'context': doc_item,
                        'description': ai_description,
                        'image_bytes': screenshot_bytes
                    })

                progress_bar.progress(1.0)
                status_text.success("All screenshots and descriptions generated!")

                status_text.info("Compiling all data into a Word document...")
                doc_bytes = create_documentation_report(st.session_state.doc_report_data, 'website_documentation.docx')
                st.session_state.final_doc_bytes = doc_bytes
                st.session_state.is_processing = False
                st.success("Documentation report is ready to download!")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.is_processing = False
                st.session_state.final_doc_bytes = None

    with col_btn_clear:
        if st.button("Clear All 🗑️", use_container_width=True, key="btn_clear_all"):
            st.session_state.url_input = ""
            st.session_state.doc_report_data = []
            st.session_state.final_doc_bytes = None
            st.session_state.is_processing = False
            st.success("All cleared! Ready for new documentation.")
            st.rerun()


if st.session_state.final_doc_bytes:
    with col_main_center:
        st.markdown("---")
        st.download_button(
            label="Download Documentation (.docx) ⬇️",
            data=st.session_state.final_doc_bytes,
            file_name="website_documentation.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key="btn_download_doc"
        )
    
st.markdown("---")
st.info("Powered by Playwright, Google Gemini AI, and Streamlit.")
st.markdown("<p class='footer-text'>Developed with ❤️ in Mianwali, Punjab, Pakistan</p>", unsafe_allow_html=True)