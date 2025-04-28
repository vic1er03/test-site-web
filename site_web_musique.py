import streamlit as st
import os
import io
from pydub import AudioSegment
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# --- CONFIGURATION ---
SECRET_CODE = "2003"
MAX_FILE_SIZE_MB = 50
EXTRACT_DURATION_SEC = 30
CATEGORIES = ["rap", "afro", "rnb"]
GOOGLE_DRIVE_FOLDER_ID = "TON_ID_DOSSIER"  # <- ID du dossier 'beat'

CONTACT_PHONE = "+237 6 59 35 12 77 / +226 51 61 70 14 "
CONTACT_EMAIL = "azariazaria473@gmail.com"

# --- GOOGLE DRIVE CONNECTION ---
@st.cache_resource
def connect_to_drive():
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

# --- LISTER FICHIERS DU DOSSIER BEAT ---
def list_beats(drive_service):
    results = drive_service.files().list(
        q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    return items

# --- EXTRAIRE UN EXTRAIT AUDIO ---
def extract_audio(file_bytes, duration_sec=EXTRACT_DURATION_SEC):
    sound = AudioSegment.from_file(file_bytes)
    extract = sound[:duration_sec * 1000]
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# --- TÉLÉCHARGER UN FICHIER DE GOOGLE DRIVE ---
def download_file(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# --- UPLOADER UN FICHIER VERS DRIVE ---
def upload_to_drive(file, filename, folder_id):
    drive_service = connect_to_drive()
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(file, mimetype='application/octet-stream')
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded_file.get('id')

# --- PAGES STREAMLIT ---
def accueil():
    st.title("🎶 Bienvenue sur la Plateforme Beats 🎶")
    st.write("Écoutez les extraits et téléchargez vos beats préférés !")
    st.success(f"Contactez-nous : 📞 {CONTACT_PHONE} | 📩 {CONTACT_EMAIL}")

def ecouter_acheter():
    st.title("🎧 Écouter / Acheter Beats")

    drive_service = connect_to_drive()
    beats = list_beats(drive_service)

    if not beats:
        st.info("Aucun beat disponible pour l'instant.")
    else:
        for beat in beats:
            st.subheader(beat['name'])
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"▶️ Play Extrait - {beat['name']}", key=f"play_{beat['id']}"):
                    file_bytes = download_file(drive_service, beat['id'])
                    extract = extract_audio(file_bytes)
                    st.audio(extract, format="audio/mp3")

            with col2:
                full_file = download_file(drive_service, beat['id'])
                st.download_button(
                    label=f"⬇️ Télécharger {beat['name']}",
                    data=full_file,
                    file_name=beat['name'],
                    mime="application/octet-stream"
                )

def uploader():
    st.title("📤 Uploader votre Beat")

    code = st.text_input("Entrez votre code secret", type="password")
    if code == SECRET_CODE:
        uploaded_file = st.file_uploader("Choisissez un beat", type=["mp3", "wav", "zip", "flac"])
        category = st.selectbox("Choisissez une catégorie", options=CATEGORIES)

        if uploaded_file:
            size_mb = uploaded_file.size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                st.error(f"Le fichier dépasse {MAX_FILE_SIZE_MB} MB.")
            else:
                if st.button("Uploader sur Google Drive"):
                    uploaded_file.seek(0)
                    file_id = upload_to_drive(io.BytesIO(uploaded_file.getvalue()), uploaded_file.name, GOOGLE_DRIVE_FOLDER_ID)
                    st.success(f"✅ Upload réussi ! [Voir dans Drive](https://drive.google.com/file/d/{file_id}/view)")
    elif code != "":
        st.error("Code incorrect.")

def apropos():
    st.title("ℹ️ À propos")
    st.write("""
    Cette plateforme permet aux artistes de partager, vendre et écouter des beats facilement.

    📞 Téléphone : +237 6 59 35 12 77 / +226 51 61 70 14 
    📩 Email : azariazaria473@gmail.com  
    """)

# --- MAIN STREAMLIT ---
def main():
    st.sidebar.title("Menu")
    choice = st.sidebar.selectbox("Navigation", ["Accueil", "Écouter / Acheter", "Uploader", "À propos"])

    if choice == "Accueil":
        accueil()
    elif choice == "Écouter / Acheter":
        ecouter_acheter()
    elif choice == "Uploader":
        uploader()
    elif choice == "À propos":
        apropos()

if __name__ == "__main__":
    main()
