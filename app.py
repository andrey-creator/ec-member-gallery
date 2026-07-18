import streamlit as st
import os
import base64
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

    /* ==== GRID FOTO — pengganti st.columns ==== */
    .roster-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 140px));
        justify-content: center;
        gap: 24px 20px;
        margin-top: 10px;
    }
    .roster-card {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .roster-card img {
        width: 140px;
        height: 180px;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid rgba(0, 242, 255, 0.3);
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.15);
    }
    .img-label {
        text-align: center;
        font-family: 'Rajdhani', sans-serif;
        color: #00f2ff;
        font-size: 0.85rem;
        margin-top: 8px;
        letter-spacing: 1px;
        font-weight: 600;
        line-height: 1.3;
    }

    @media (max-width: 768px) {
        .glow-text { font-size: 1.6rem; }
        .sub-text { font-size: 0.8rem; letter-spacing: 1px; }
        .roster-grid { grid-template-columns: repeat(auto-fill, minmax(120px, 120px)); gap: 20px 14px; }
        .roster-card img { width: 120px; height: 155px; }
        .img-label { font-size: 0.75rem; }
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=2)
def muat_foto_member(target_path):
    """
    Mengembalikan list of dict: [{"src": <url atau data-uri>, "nama": <str>}, ...]
    """
    hasil = []

    lokal_dir = os.path.join("photos", target_path)
    if os.path.exists(lokal_dir):
        try:
            files = sorted(os.listdir(lokal_dir))
            for f in files:
                if f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                    full_path = os.path.join(lokal_dir, f)
                    with open(full_path, "rb") as img_file:
                        b64 = base64.b64encode(img_file.read()).decode()
                    ext = f.split(".")[-1].lower()
                    mime = "jpeg" if ext == "jpg" else ext
                    src = f"data:image/{mime};base64,{b64}"
                    nama = unquote(f.split(".")[0]).replace("-", " ").replace("_", " ").upper()
                    hasil.append({"src": src, "nama": nama})
        except Exception:
            return []
        return hasil

    # Fallback: ambil dari GitHub
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
                for file in files:
                    if file['name'].lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                        nama = unquote(file['name'].split(".")[0]).replace("-", " ").replace("_", " ").upper()
                        hasil.append({"src": file['download_url'], "nama": nama})
    except Exception:
        return []

    return hasil


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
    cards_html = ""
    for foto in daftar_foto:
        cards_html += f"""
        <div class="roster-card">
            <img src="{foto['src']}" alt="{foto['nama']}">
            <div class="img-label">{foto['nama']}</div>
        </div>
        """
    st.markdown(f'<div class="roster-grid">{cards_html}</div>', unsafe_allow_html=True)
else:
    st.info(
        f"Belum ada data member untuk "
        f"{pilihan_batch.replace('-', ' ').upper()} - "
        f"{pilihan_kelas.replace('-', ' ').upper()}."
    )

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
    <div style="margin-bottom: 140px;"></div>
""", unsafe_allow_html=True)
