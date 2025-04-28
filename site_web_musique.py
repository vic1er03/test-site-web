import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydub import AudioSegment
import io

# --- CONFIGURATION ---
SECRET_CODE = "2003"  # <-- Change ici
CATEGORIES = ["rap", "afro", "rnb"]
UPLOAD_FOLDER = "uploads"
SUGGESTION_FILE = "suggestions.txt"
MAX_FILE_SIZE_MB = 50
EXTRACT_DURATION_SEC = 30  # Durée de l'extrait gratuit en secondes

# Email settings
SENDER_EMAIL = "azariaazaria473@gmail.com"  # <-- ton email ici
SENDER_PASSWORD = "Azaria2003"  # mot de passe spécial application
RECEIVER_EMAIL = "azariaazaria473@gmail.com"  # email pour notifications

# --- FONCTIONS ---

# Créer les dossiers
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

for category in CATEGORIES:
    os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)

# Vérifier extensions autorisées
def allowed_file(filename):
    return filename.split('.')[-1].lower() in ['mp3', 'wav', 'zip', 'flac']

# Vérifier taille du fichier
def file_size_ok(file):
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb <= MAX_FILE_SIZE_MB

# Lister les fichiers par catégorie
def list_files():
    files_per_category = {}
    for cat in CATEGORIES:
        path = os.path.join(UPLOAD_FOLDER, cat)
        files = os.listdir(path)
        files_per_category[cat] = files
    return files_per_category

# Envoyer un email de notification
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
        st.error(f"Erreur lors de l'envoi d'email : {e}")

# Extraire un extrait audio
def extract_audio(file_path, duration_sec=EXTRACT_DURATION_SEC):
    sound = AudioSegment.from_file(file_path)
    extract = sound[:duration_sec * 1000]  # pydub utilise les millisecondes
    buf = io.BytesIO()
    extract.export(buf, format="mp3")
    buf.seek(0)
    return buf

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Plateforme Beats", page_icon=":musical_note:")

st.title("🎵 Plateforme de Musiques & Beats")

tab1, tab2, tab3 = st.tabs(["Écouter / Acheter", "Uploader", "Suggérer Catégorie"])

# --- Onglet Écouter / Acheter ---
with tab1:
    st.header("🎧 Écouter un extrait ou acheter un Beat")

    files = list_files()
    for category, filelist in files.items():
        st.subheader(category.capitalize())
        if filelist:
            for idx, filename in enumerate(filelist):
                file_path = os.path.join(UPLOAD_FOLDER, category, filename)
                st.markdown(f"**{filename}**")

                # Jouer l'extrait
                extract_audio_file = extract_audio(file_path)
                st.audio(extract_audio_file, format='audio/mp3')

                # Simuler l'achat
                if st.button(f"🎼 Télécharger Complet ({filename})", key=f"download_{category}_{idx}"):
                    st.warning("Veuillez payer pour débloquer le téléchargement :")
                    st.info("Envoyez le paiement par Orange Money au numéro +237 6XX XX XX XX")

                    if st.button(f"✅ J'ai payé ({filename})", key=f"paid_{category}_{idx}"):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Télécharger {filename}",
                                data=f,
                                file_name=filename,
                                mime="application/octet-stream"
                            )
        else:
            st.info(f"Aucun fichier dans {category.capitalize()}.")

# --- Onglet Uploader ---
with tab2:
    st.header("📤 Uploader un Beat")

    code = st.text_input("Entrez votre code secret", type="password")

    if code == SECRET_CODE:
        uploaded_file = st.file_uploader("Choisissez un fichier", type=["mp3", "wav", "zip", "flac"])
        category = st.selectbox("Choisissez une catégorie existante", options=CATEGORIES)

        if uploaded_file:
            if not file_size_ok(uploaded_file):
                st.error(f"Le fichier dépasse {MAX_FILE_SIZE_MB} MB.")
            elif not allowed_file(uploaded_file.name):
                st.error("Type de fichier non autorisé.")
            else:
                save_path = os.path.join(UPLOAD_FOLDER, category, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Fichier {uploaded_file.name} uploadé dans {category} avec succès !")

                # Envoyer une notification par email
                subject = "Nouveau Beat Uploadé"
                body = f"Le fichier '{uploaded_file.name}' a été uploadé dans la catégorie '{category}'."
                send_email(subject, body, RECEIVER_EMAIL)
                st.info("Notification envoyée par email.")
    elif code:
        st.error("Code incorrect.")

# --- Onglet Suggérer Catégorie ---
with tab3:
    st.header("💡 Suggérer une nouvelle catégorie")

    suggested_category = st.text_input("Votre suggestion de catégorie")
    if st.button("Envoyer ma suggestion"):
        if suggested_category:
            with open(SUGGESTION_FILE, "a") as f:
                f.write(f"{suggested_category}\n")
            st.success("Merci pour votre suggestion !")
        else:
            st.error("Veuillez entrer une suggestion.")
