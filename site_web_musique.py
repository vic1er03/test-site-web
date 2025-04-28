# --- Importations ---
import streamlit as st
import os
import io
from pydub import AudioSegment
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# --- Connexion à Google Drive ---
def connect_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("credentials.json")
    return GoogleDrive(gauth)

# --- Initialiser Drive ---
drive = connect_drive()

# --- Vérifier ou créer dossier "beats" ---
def get_or_create_folder(drive, folder_name):
    file_list = drive.ListFile({'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for file in file_list:
        if file['title'] == folder_name:
            return file['id']

    # Dossier non trouvé => créer
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

FOLDER_NAME = "beats"
FOLDER_ID = get_or_create_folder(drive, FOLDER_NAME)

# --- Lister les beats dans le Drive ---
def list_beats():
    query = f"'{FOLDER_ID}' in parents and trashed=false"
    files = drive.ListFile({'q': query}).GetList()
    return files

# --- Uploader un beat ---
def upload_beat(file):
    temp_file_path = f"temp_{file.name}"
    with open(temp_file_path, "wb") as f:
        f.write(file.getbuffer())

    beat_file = drive.CreateFile({'title': file.name, 'parents': [{'id': FOLDER_ID}]})
    beat_file.SetContentFile(temp_file_path)
    beat_file.Upload()
    os.remove(temp_file_path)

# --- Extraire un extrait de 30 secondes ---
def extract_audio(file_path_or_buffer, duration_sec=30):
    sound = AudioSegment.from_file(file_path_or_buffer)
    extract = sound[:duration_sec * 1000]
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# --- Interface Streamlit ---

st.set_page_config(page_title="Plateforme Beats", page_icon="🎵")

# Code secret pour uploader
SECRET_CODE = "2003"  # <-- Tu peux changer ici

# Sidebar navigation
menu = st.sidebar.selectbox("Navigation", ["Accueil", "Uploader un Beat", "À propos"])

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/727/727240.png", width=150)

if menu == "Accueil":
    st.title("🎵 Beats disponibles")

    beats = list_beats()

    if not beats:
        st.info("Aucun beat disponible pour le moment.")
    else:
        for beat in beats:
            st.subheader(beat['title'])

            # Télécharger temporairement l'extrait
            temp_file_path = f"temp_{beat['title']}"
            beat.GetContentFile(temp_file_path)

            # Lire l'extrait
            audio_extract = extract_audio(temp_file_path)
            st.audio(audio_extract, format='audio/mp3')

            # Bouton de téléchargement
            with open(temp_file_path, "rb") as full_file:
                st.download_button(
                    label=f"📥 Télécharger {beat['title']}",
                    data=full_file,
                    file_name=beat['title'],
                    mime='audio/mpeg'
                )

            os.remove(temp_file_path)

elif menu == "Uploader un Beat":
    st.title("⬆️ Uploader votre Beat")

    code = st.text_input("Entrez votre code secret pour uploader :", type="password")

    if code == SECRET_CODE:
        uploaded_file = st.file_uploader("Choisissez un fichier audio", type=["mp3", "wav", "zip", "flac"])

        if uploaded_file is not None:
            upload_beat(uploaded_file)
            st.success(f"✅ Fichier {uploaded_file.name} uploadé avec succès dans le Drive !")
    elif code:
        st.error("❌ Code incorrect. Vous ne pouvez pas uploader.")

elif menu == "À propos":
    st.title("ℹ️ À propos")

    st.image("https://cdn-icons-png.flaticon.com/512/4059/4059920.png", width=200)

    st.markdown("""
    ### Développeurs :
    - 📞 **KABORE Wend-Waoga Azaria** : +237 6 59 35 12 77
    - 📞 **Josué** : +226 6 51 61 70 14
    - 📧 Email : azariazaria473@gmail.com

    ### Fonctionnalités :
    - 🎵 Uploader vos beats avec un code secret
    - 🎧 Écouter un extrait de 30 secondes avant achat
    - 📥 Télécharger vos beats préférés

    Plateforme propulsée par **Streamlit** et **Google Drive API** 🚀
    """)

