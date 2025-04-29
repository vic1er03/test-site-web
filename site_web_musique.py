# --- Importations ---
import streamlit as st
import os
import io
from pydub import AudioSegment
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Connexion à Google Drive via compte de service ---
def connect_drive():
    SERVICE_ACCOUNT_FILE = 'credentials.json'  # Fichier de clés du compte de service
    SCOPES = ['https://www.googleapis.com/auth/drive.file']  # Scope pour l'accès au fichier Drive

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        # Créer un service Google Drive
        service = build('drive', 'v3', credentials=credentials)
        return service
    except HttpError as error:
        st.error(f"Une erreur s'est produite lors de la connexion à Google Drive : {error}")
        return None

# --- Initialiser Google Drive ---
service = connect_drive()

# --- Vérifier ou créer dossier "beats" ---
def get_or_create_folder(service, folder_name):
    # Liste des fichiers dans Drive pour chercher le dossier
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{folder_name}'"
    results = service.files().list(q=query).execute()
    items = results.get('files', [])

    if items:
        # Dossier trouvé, on retourne son ID
        return items[0]['id']
    else:
        # Dossier non trouvé, on crée un nouveau dossier
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder['id']

FOLDER_NAME = "beats"
FOLDER_ID = get_or_create_folder(service, FOLDER_NAME)

# --- Lister les beats dans Google Drive ---
def list_beats():
    try:
        query = f"'{FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(q=query).execute()
        files = results.get('files', [])
        return files
    except HttpError as error:
        st.error(f"Une erreur s'est produite lors de la récupération des beats : {error}")
        return []

# --- Uploader un beat ---
def upload_beat(file):
    try:
        # Sauvegarder le fichier temporairement pour l'upload
        temp_file_path = f"temp_{file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(file.getbuffer())

        file_metadata = {'name': file.name, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(temp_file_path, mimetype='audio/mpeg')
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        os.remove(temp_file_path)  # Supprimer le fichier temporaire
        st.success(f"✅ Fichier {file.name} uploadé avec succès dans Google Drive !")
    except HttpError as error:
        st.error(f"Une erreur s'est produite lors de l'upload du beat : {error}")

# --- Extraire un extrait de 30 secondes ---
def extract_audio(file_path_or_buffer, duration_sec=30):
    sound = AudioSegment.from_file(file_path_or_buffer)
    extract = sound[:duration_sec * 1000]  # Extraire les 30 premières secondes
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# --- Interface Streamlit ---

st.set_page_config(page_title="Plateforme Beats", page_icon="🎵")

# Code secret pour uploader
SECRET_CODE = "Josue2006"  # <-- Tu peux changer ici

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
            st.subheader(beat['name'])

            # Télécharger temporairement l'extrait
            temp_file_path = f"temp_{beat['name']}"
            request = service.files().get_media(fileId=beat['id'])
            with open(temp_file_path, "wb") as f:
                f.write(request.execute())

            # Lire l'extrait
            audio_extract = extract_audio(temp_file_path)
            st.audio(audio_extract, format='audio/mp3')

            # Bouton de téléchargement
            with open(temp_file_path, "rb") as full_file:
                st.download_button(
                    label=f"📥 Télécharger {beat['name']}",
                    data=full_file,
                    file_name=beat['name'],
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
    elif code:
        st.error("❌ Code incorrect. Vous ne pouvez pas uploader.")

elif menu == "À propos":
    st.title("ℹ️ À propos")

    st.image("https://cdn-icons-png.flaticon.com/512/4059/4059920.png", width=200)

    st.markdown("""
    ### Développeurs :
    - 📞 **KABORE Wend-Waoga Azaria** : +237 6 59 35 12 77
    - 📞 **KABORE Josué Esli** : +226 51 61 70 14
    - 📧 Email : azariazaria473@gmail.com

    ### Fonctionnalités :
    - 🎵 Uploader vos beats avec un code secret
    - 🎧 Écouter un extrait de 30 secondes avant achat
    - 📥 Télécharger vos beats préférés

    Plateforme propulsée par **Streamlit** et **Google Drive API** 🚀
    """)
