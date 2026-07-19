import streamlit as st
import os
import base64
import io
import html
import requests
from urllib.parse import unquote
from PIL import Image

TARGET_W, TARGET_H = 280, 360 

DEFAULT_BATCH = ["batch-2025-2026", "batch-2026-2027"]
DEFAULT_KELAS = ["kelas-x", "kelas-xi"]

PHOTOS_ROOT = "photos"
GITHUB_USERNAME = "andrey-creator"
GITHUB_REPO = "ec-member-gallery"

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


def _github_headers():
    """FIX #2: akses st.secrets dibungkus try/except supaya tidak crash
    kalau file secrets.toml sama sekali tidak ada di environment."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        if "GITHUB_TOKEN" in st.secrets:
            headers["Authorization"] = f"token {st.secrets['GITHUB_TOKEN']}"
    except Exception:
        pass
    return headers


@st.cache_data(ttl=3600, show_spinner=False)
def daftar_opsi_batch_kelas():
    """FIX #5: scan folder photos/ (atau GitHub) untuk dapatkan daftar batch
    & kelas secara otomatis, dengan fallback ke daftar default kalau gagal."""
    batch_list, kelas_set = [], set()


    if os.path.isdir(PHOTOS_ROOT):
        try:
            for b in sorted(os.listdir(PHOTOS_ROOT)):
                b_path = os.path.join(PHOTOS_ROOT, b)
                if os.path.isdir(b_path):
                    batch_list.append(b)
                    for k in os.listdir(b_path):
                        if os.path.isdir(os.path.join(b_path, k)):
                            kelas_set.add(k)
            if batch_list:
                return sorted(batch_list), sorted(kelas_set), None
        except Exception as e:
            return DEFAULT_BATCH, DEFAULT_KELAS, f"Gagal membaca folder lokal: {e}"

    # 2) Fallback: coba scan root repo GitHub
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list):
                for item in items:
                    if item.get("type") == "dir":
                        batch_list.append(item["name"])
            if batch_list:
                return sorted(batch_list), DEFAULT_KELAS, None
        elif resp.status_code == 403:
            return DEFAULT_BATCH, DEFAULT_KELAS, "GitHub API rate limit tercapai, memakai daftar default."
        elif resp.status_code == 404:
            return DEFAULT_BATCH, DEFAULT_KELAS, None 
        else:
            return DEFAULT_BATCH, DEFAULT_KELAS, f"GitHub API mengembalikan status {resp.status_code}, memakai daftar default."
    except requests.exceptions.RequestException as e:
        return DEFAULT_BATCH, DEFAULT_KELAS, f"Tidak bisa menghubungi GitHub: {e}"

    return DEFAULT_BATCH, DEFAULT_KELAS, None


@st.cache_data(ttl=3600, show_spinner=False)
def muat_foto_member(target_path):
    """
    Mengembalikan tuple: (list of {"src":..., "nama":...}, pesan_error_atau_None)
    FIX #3: error dibedakan (rate limit / not found / error lain) alih-alih
            selalu disamaratakan jadi "belum ada data".
    """
    hasil = []

    lokal_dir = os.path.join(PHOTOS_ROOT, target_path)
    if os.path.exists(lokal_dir):
        try:
            files = sorted(os.listdir(lokal_dir))
            for f in files:
                if f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                    full_path = os.path.join(lokal_dir, f)
                    try:
                        img = Image.open(full_path)
                        img = img.convert("RGB")
                        # crop-to-fill supaya rasio pas sebelum resize, hindari distorsi
                        src_ratio = img.width / img.height
                        target_ratio = TARGET_W / TARGET_H
                        if src_ratio > target_ratio:
                            new_w = int(img.height * target_ratio)
                            left = (img.width - new_w) // 2
                            img = img.crop((left, 0, left + new_w, img.height))
                        else:
                            new_h = int(img.width / target_ratio)
                            top = (img.height - new_h) // 2
                            img = img.crop((0, top, img.width, top + new_h))
                        img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80, optimize=True)
                        b64 = base64.b64encode(buf.getvalue()).decode()
                        src = f"data:image/jpeg;base64,{b64}"
                    except Exception:
                        continue

                    nama_file, _ = os.path.splitext(f)
                    nama = unquote(nama_file).replace("-", " ").replace("_", " ").upper()
                    hasil.append({"src": src, "nama": nama})
        except Exception as e:
            return [], f"Gagal membaca folder lokal '{lokal_dir}': {e}"

        hasil.sort(key=lambda x: x["nama"])
        return hasil, None


    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{target_path}"

    try:
        response = requests.get(url, headers=_github_headers(), timeout=10)

        if response.status_code == 200:
            files = response.json()
            if isinstance(files, list):
                for file in files:
                    if file['name'].lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                        nama_file, _ = os.path.splitext(file['name'])
                        nama = unquote(nama_file).replace("-", " ").replace("_", " ").upper()
                        hasil.append({"src": file['download_url'], "nama": nama})
            hasil.sort(key=lambda x: x["nama"])
            return hasil, None

        elif response.status_code == 404:

            return [], None

        elif response.status_code == 403:
            return [], "GitHub API rate limit tercapai. Coba lagi beberapa saat lagi, atau tambahkan GITHUB_TOKEN di secrets."

        else:
            return [], f"GitHub API mengembalikan status {response.status_code}."

    except requests.exceptions.Timeout:
        return [], "Permintaan ke GitHub timeout. Coba refresh lagi."
    except requests.exceptions.RequestException as e:
        return [], f"Gagal menghubungi GitHub: {e}"


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


daftar_batch, daftar_kelas, pesan_opsi = daftar_opsi_batch_kelas()
if pesan_opsi:
    st.warning(pesan_opsi)

col_filter1, col_filter2, col_refresh = st.columns([2, 2, 1])
with col_filter1:
    pilihan_batch = st.selectbox("CHOOSE BATCH / ANGKATAN", daftar_batch)
with col_filter2:
    pilihan_kelas = st.selectbox("CHOOSE CLASS / TINGKATAN", daftar_kelas)
with col_refresh:
    st.write("") 
    st.write("")
    if st.button("🔄 Refresh"):
        muat_foto_member.clear()
        daftar_opsi_batch_kelas.clear()
        st.rerun()

path_pencarian = f"{pilihan_batch}/{pilihan_kelas}"

st.write("---")

with st.spinner("Retrieving Roster..."):
    daftar_foto, pesan_error = muat_foto_member(path_pencarian)

if pesan_error:
    st.warning(pesan_error)

if daftar_foto:
    cards = []
    for foto in daftar_foto:

        nama_aman = html.escape(foto['nama'])
        cards.append(
            '<div class="roster-card">'
            f'<img src="{foto["src"]}" alt="{nama_aman}">'
            f'<div class="img-label">{nama_aman}</div>'
            '</div>'
        )
    grid_html = '<div class="roster-grid">' + "".join(cards) + '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)
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
