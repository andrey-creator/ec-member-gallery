import streamlit as st
import os
import requests
from urllib.parse import unquote

DAFTAR_BATCH = ["batch-2025-2026", "batch-2026-2027"]
DAFTAR_KELAS = ["kelas-x", "kelas-xi"]

st.set_page_config(
    page_title="EC Integral Members", 
    page_icon="🎙️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    
    .header-container { text-align: center; padding: 20px 0; }
    .logo-img { width: 90px; filter: invert(1) drop-shadow(0 0 12px #00f2ff); border-radius: 50%; }
    .glow-text {
        font-family: 'Orbitron', sans-serif;
        color: white;
        text-shadow: 0 0 10px #00f2ff;
        font-size: 2.2rem;
        margin: 10px 0 0 0;
    }
    .sub-text {
        font-family: 'Rajdhani', sans-serif;
        color: #00f2ff;
        letter-spacing: 3px;
        font-size: 0.95rem;
        margin-bottom: 25px;
    }
    div.stButton > button {
        transition: all 0.3s ease;
        border: 1px solid #00f2ff !important;
        background-color: transparent;
        color: white !important;
        font-family: 'Orbitron', sans-serif;
        border-radius: 10px;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 15px #00f2ff !important;
        transform: translateY(-2px);
        background-color: #00f2ff !important;
        color: black !important;
    }

    /* Fixed inline grid layout forcing elements side-by-side everywhere */
    .flex-roster-container {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        gap: 16px !important;
        width: 100% !important;
        margin-top: 20px;
    }

    .flex-member-card {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        width: 135px !important;
        text-align: center !important;
    }

    .flex-member-card img {
        width: 135px !important;
        height: 175px !important;
        object-fit: cover !important;
        border-radius: 12px !important;
        border: 1px solid rgba(0, 242, 255, 0.3) !important;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.15) !important;
    }

    .flex-img-label {
        font-family: 'Rajdhani', sans-serif !important; 
        color: #00f2ff !important; 
        font-size: 0.85rem !important; 
        margin-top: 8px !important;
        letter-spacing: 1px !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=2)
def muat_foto_member(target_path):
    if os.path.exists(os.path.join("photos", target_path)):
        lokal_dir = os.path.join("photos", target_path)
        try:
            files = os.listdir(lokal_dir)
            return [os.path.join(lokal_dir, f) for f in files if f.lower().endswith(('png', 'jpg', 'jpeg', 'webp'))]
        except Exception:
            return []
    else:
        username = "andrey-creator"
        repo = "ec-member-gallery" 
        url = f"https://api.github.com/repos/{username}/{repo}/contents/{target_path}"
        
        headers = {"Accept": "application/vnd.github.v3+json"}
        if "GITHUB_TOKEN" in st.secrets:
            headers["Authorization"] = f"token {st.secrets['GITHUB_TOKEN']}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                files = response.json()
                if isinstance(files, list):
                    return [file['download_url'] for file in files if file['name'].lower().endswith(('png', 'jpg', 'jpeg', 'webp'))]
        except Exception:
            return []
    return []

st.markdown("""
    <div class="header-container">
        <img src="https://raw.githubusercontent.com/andrey-creator/say-it-play-it/main/logo_ec.jpeg" class="logo-img">
        <h1 class="glow-text">INTEGRAL MEMBERS</h1>
        <p class="sub-text">ENGLISH CLUB • SMAN 1 DEPOK</p>
    </div>
    """, unsafe_allow_html=True)

col_back, _ = st.columns([1, 4])
with col_back:
    st.link_button("⬅️ MAIN DASHBOARD", "https://ec-sman1depok.streamlit.app/")

st.write("##")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    pilihan_batch = st.selectbox("CHOOSE BATCH / ANGKATAN", DAFTAR_BATCH)
with col_filter2:
    pilihan_kelas = st.selectbox("CHOOSE CLASS / TINGKATAN", DAFTAR_KELAS)

path_pencarian = f"{pilihan_batch}/{pilihan_kelas}"

st.write("---")

with st.spinner("Retrieving Roster..."):
    daftar_foto = muat_foto_member(path_pencarian)

if daftar_foto:
    # Building a direct raw HTML element compilation to perfectly retain image paths and layout structural alignment
    html_output = '<div class="flex-roster-container">'
    
    for url_atau_path in daftar_foto:
        if "\\" in url_atau_path or "/" in url_atau_path:
            nama_file = url_atau_path.replace("\\", "/").split('/')[-1].split('.')[0]
        else:
            nama_file = url_atau_path.split('.')[0]
            
        clean_name = unquote(nama_file).replace('-', ' ').replace('_', ' ').upper()
        
        # Resolving relative paths cleanly for inline element binding
        src_path = url_atau_path
        if not (src_path.startswith('http://') or src_path.startswith('https://')):
            # Direct check conversion for standard system deployment paths
            if os.path.exists(src_path):
                # When using local media assets in pure markdown blocks inside Streamlit app structures,
                # referencing them directly via file system links requires standard component configurations. 
                # If path errors occur locally, fallback to serving them explicitly.
                pass

        html_output += f'''
        <div class="flex-member-card">
            <img src="{src_path}">
            <div class="flex-img-label">{clean_name}</div>
        </div>
        '''
        
    html_output += '</div>'
    st.markdown(html_output, unsafe_allow_html=True)
else:
    st.info(f"Belum ada data member untuk {pilihan_batch.replace('-', ' ').upper()} - {pilihan_kelas.replace('-', ' ').upper()}.")

st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid rgba(0, 242, 255, 0.2);">
        <p style="font-family: 'Rajdhani', sans-serif; color: #00f2ff; letter-spacing: 2px; font-size: 1.1rem; font-weight: 500; font-style: italic;">
            "United we stand • Divided we fall • Never be defeated"
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(5, 7, 10, 0.9);
        color: #00f2ff;
        text-align: center;
        padding: 10px 0;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 2px;
        border-top: 1px solid rgba(0, 242, 255, 0.2);
        backdrop-filter: blur(5px);
        z-index: 999;
    ">
        © 2026 • ARYASATYA KEANDRE - DAVIN PRIMA • ENGLISH CLUB • SMAN 1 DEPOK
    </div>
    <div style="margin-bottom: 80px;"></div>
""", unsafe_allow_html=True)
