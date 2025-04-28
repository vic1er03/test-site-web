import streamlit as st
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from pydub import AudioSegment
import io

# --- CONFIGURATION ---
SECRET_CODE = "TON_CODE_SECRET"
CATEGORIES = ["rap", "afro", "rnb"]
MAX_FILE_SIZE_MB = 50
EXTRACT_DURATION_SEC = 30  # 30 secondes d'extrait gratuit

# --- GOOGLE DRIVE CONNECTION ---
@st.cache_resource
def connect_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

drive = connect_drive()

# --- FONCTIONS ---

# Vérifier extension
def allowed_file(filename):
    return filename.split('.')[-1].lower() in ['mp3', 'wav', 'zip', 'flac']

# Vérifier la taille
def file_size_ok(file):
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb <= MAX_FILE_SIZE_MB

# Extraire extrait audio
def extract_audio(file_path, duration_sec=EXTRACT_DURATION_SEC):
    sound = AudioSegment.from_file(file_path)
    extract = sound[:duration_sec * 1000]  # en millisecondes
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# Cherche un dossier existant sinon le crée
def get_or_create_folder(name):
    folder_list = drive.ListFile({'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folder_list:
        if folder['title'].lower() == name.lower():
            return folder['id']
    
    # Sinon créer
    folder_metadata = {
        'title': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

# Upload vers Drive
def upload_to_drive(file, filename, category):
    folder_id = get_or_create_folder(category)
    gfile = drive.CreateFile({'parents': [{'id': folder_id}], 'title': filename})
    gfile.SetContentString(file.read().decode('latin1'))
    gfile.Upload()
    return gfile['id']

# Lister les fichiers
def list_drive_files(folder_id):
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    return file_list

# --- STREAMLIT APP ---

st.set_page_config(page_title="Plateforme Beats", page_icon=":musical_note:")

# Sidebar Navigation
menu = st.sidebar.selectbox("Menu", ["Accueil", "Uploader", "À propos"])

st.image("https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4", use_column_width=True)

# Accueil
if menu == "Accueil":
    st.title("🎵 Bienvenue sur la Plateforme Beats")
    st.subheader("Écoutez un extrait et achetez vos beats préférés !")

    for category in CATEGORIES:
        st.header(f"🎶 Catégorie : {category.capitalize()}")
        folder_id = get_or_create_folder(category)
        files = list_drive_files(folder_id)

        if not files:
            st.info("Aucun fichier disponible.")
        else:
            for f in files:
                filename = f['title']
                file_id = f['id']
                
                st.markdown(f"**{filename}**")
                download_url = f"https://drive.google.com/uc?id={file_id}"

                if st.button(f"▶️ Écouter extrait : {filename}", key=f"play_{file_id}"):
                    st.audio(download_url)

                st.markdown(f"[⬇️ Télécharger {filename}](https://drive.google.com/uc?id={file_id})", unsafe_allow_html=True)

# Uploader
elif menu == "Uploader":
    st.title("🚀 Uploader un nouveau Beat")
    code = st.text_input("Entrez votre code secret", type="password")

    if code == SECRET_CODE:
        uploaded_file = st.file_uploader("Choisissez un fichier", type=["mp3", "wav", "zip", "flac"])
        category = st.selectbox("Catégorie", options=CATEGORIES)

        if uploaded_file:
            if not file_size_ok(uploaded_file):
                st.error(f"Le fichier dépasse {MAX_FILE_SIZE_MB}MB.")
            else:
                if allowed_file(uploaded_file.name):
                    upload_to_drive(uploaded_file, uploaded_file.name, category)
                    st.success(f"✅ Fichier {uploaded_file.name} uploadé avec succès dans {category} !")
                else:
                    st.error("Type de fichier non autorisé.")
    elif code:
        st.error("❌ Code incorrect.")

# A propos
elif menu == "À propos":
    st.title("📞 À propos")
    st.write("""
    - **Créé par** : Azaria
    - **Contact** : +237 6XX XX XX XX
    - **Email** : azariazaria473@gmail.com
    """)
    st.image("https://images.unsplash.com/photo-1546443046-ed1ce6ffd1a9", use_column_width=True)

