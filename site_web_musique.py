import streamlit as st
from streamlit_option_menu import option_menu
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydub import AudioSegment
import io

# --- CONFIGURATION ---
SECRET_CODE = "2003"  # <-- Change ici
CATEGORIES = ["rap", "afro", "rnb"]
UPLOAD_FOLDER = "uploads"
IMAGES_FOLDER = "images"
SUGGESTION_FILE = "suggestions.txt"
MAX_FILE_SIZE_MB = 50
EXTRACT_DURATION_SEC = 30  # Durée de l'extrait gratuit en secondes

# Liens d'images publiques fiables (exemples)
IMAGE_LINKS = {
    "accueil": "https://images.unsplash.com/photo-1511376777868-611b54f68947",
    "upload": "https://images.unsplash.com/photo-1551907234-6f3b8fb46c27",
    "about": "https://images.unsplash.com/photo-1531297484001-80022131f5a1",
    "rap": "https://images.unsplash.com/photo-1618329730972-f95cf1974209",
    "afro": "https://images.unsplash.com/photo-1598387990893-9b8b05c29746",
    "rnb": "https://images.unsplash.com/photo-1532634726-8b9fb99825c4"
}

CATEGORY_IMAGES = {
    "rap": f"{IMAGES_FOLDER}/rap.jpg",
    "afro": f"{IMAGES_FOLDER}/afro.jpg",
    "rnb": f"{IMAGES_FOLDER}/rnb.jpg"
}

# Email settings
SENDER_EMAIL = "azariaazaria473@gmail.com"  # <-- ton email ici
SENDER_PASSWORD = "TON_MOT_DE_PASSE_APP"  # mot de passe spécial application
RECEIVER_EMAIL = "azariaazaria473@gmail.com"  # email pour notifications

# --- CRÉATION DES DOSSIERS ET TÉLÉCHARGEMENT DES IMAGES ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def download_image(name, url):
    path = f"{IMAGES_FOLDER}/{name}.jpg"
    if not os.path.exists(path):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(r.content)
        except Exception as e:
            print(f"Erreur téléchargement {name}: {e}")

# Télécharger toutes les images si elles manquent
for name, url in IMAGE_LINKS.items():
    download_image(name, url)

# --- FONCTIONS UTILES ---
def allowed_file(filename):
    return filename.split('.')[-1].lower() in ['mp3', 'wav', 'zip', 'flac']

def file_size_ok(file):
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb <= MAX_FILE_SIZE_MB

def list_files():
    files_per_category = {}
    for cat in CATEGORIES:
        path = os.path.join(UPLOAD_FOLDER, cat)
        files = os.listdir(path)
        files_per_category[cat] = files
    return files_per_category

def send_email(subject, body, to_email):
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())
    except Exception as e:
        print(f"Erreur email : {e}")

def extract_audio(file_path, duration_sec=EXTRACT_DURATION_SEC):
    sound = AudioSegment.from_file(file_path)
    extract = sound[:duration_sec * 1000]
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# --- PAGE SETUP ---
st.set_page_config(page_title="Plateforme Beats", page_icon=":musical_note:", layout="wide")

# --- SIDEBAR AVEC MENU ---
with st.sidebar:
    selected = option_menu(
        menu_title="🎵 Menu Principal", 
        options=["Accueil", "Uploader", "À propos"], 
        icons=["house", "cloud-upload", "info-circle"],
        menu_icon="cast", 
        default_index=0,
        orientation="vertical"
    )

# --- ACCUEIL ---
if selected == "Accueil":
    st.title("🎶 Plateforme de Musiques & Beats")
    st.image(f"{IMAGES_FOLDER}/accueil.jpg", caption="Bienvenue sur notre plateforme !", use_column_width=True)
    
    st.header("🎧 Écouter un extrait ou acheter un Beat")
    
    simulate_pay = st.checkbox("✅ J'ai effectué mon paiement")
    
    if not simulate_pay:
        st.warning("⚠️ Vous devez effectuer un paiement pour écouter les extraits complets.")
        st.info("Envoyez le paiement par Orange Money au numéro : +237 6XX XX XX XX")
    else:
        files = list_files()
        for category, filelist in files.items():
            st.subheader(f"🎵 {category.capitalize()} Beats")
            if category in CATEGORY_IMAGES and os.path.exists(CATEGORY_IMAGES[category]):
                st.image(CATEGORY_IMAGES[category], use_column_width=True)

            if filelist:
                for filename in filelist:
                    file_path = os.path.join(UPLOAD_FOLDER, category, filename)
                    st.markdown(f"**🎶 {filename}**")
                    
                    if os.path.exists(file_path):
                        extract_audio_file = extract_audio(file_path)
                        st.audio(extract_audio_file, format='audio/mp3')

                        if st.button(f"⬇️ Télécharger {filename}", key=filename):
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"Télécharger {filename}",
                                    data=f,
                                    file_name=filename,
                                    mime="application/octet-stream"
                                )
                    else:
                        st.error(f"Le fichier {filename} n'existe pas ou a été déplacé.")
            else:
                st.info(f"Aucun fichier disponible pour {category.capitalize()}.")

# --- UPLOADER UN FICHIER ---
elif selected == "Uploader":
    st.title("📤 Uploader un Beat")
    st.image(f"{IMAGES_FOLDER}/accueil.jpg", caption="Bienvenue sur notre plateforme !", use_column_width=True)
    
    code = st.text_input("🔒 Entrez votre code secret", type="password")

    if code == SECRET_CODE:
        uploaded_file = st.file_uploader("📂 Choisissez un fichier", type=["mp3", "wav", "zip", "flac"])
        category = st.selectbox("🎼 Choisissez une catégorie existante", options=CATEGORIES)

        if uploaded_file:
            if not file_size_ok(uploaded_file):
                st.error(f"❌ Le fichier dépasse {MAX_FILE_SIZE_MB} MB.")
            else:
                if allowed_file(uploaded_file.name):
                    save_path = os.path.join(UPLOAD_FOLDER, category, uploaded_file.name)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)  # sécurité
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"✅ Fichier {uploaded_file.name} uploadé avec succès dans {category}!")

                    # Notification par email
                    subject = "🎵 Nouveau Beat Uploadé"
                    body = f"Le fichier '{uploaded_file.name}' a été uploadé dans la catégorie '{category}'."
                    send_email(subject, body, RECEIVER_EMAIL)
                    st.info("✉️ Notification envoyée par email.")
                else:
                    st.error("❌ Type de fichier non autorisé.")
    elif code and code != SECRET_CODE:
        st.error("🔒 Code incorrect.")

# --- À PROPOS ---
elif selected == "À propos":
    st.title("ℹ️ À propos de la plateforme")
    st.image(f"{IMAGES_FOLDER}/about.jpg", caption="Notre équipe de créateurs passionnés", use_column_width=True)

    st.markdown("""
    ### 📞 Contactez-nous :
    - **Téléphone Orange** : +237 6 59 35 12 77 / +226 51 61 70 14
    - **Téléphone MTN** : +237 6YY YY YY YY
    - **Email** : azariaazaria473@gamil.com

    ### 👨‍💻 Auteurs :
    - Kabore Wend-Waoga Azaria (Développeur)
    - Kabore Esli Josué WendKouni (beat-maker)

    Merci d'utiliser notre plateforme pour écouter, uploader et découvrir de nouveaux beats 🎶 !
    """)
