# Video-to-Ascii
Video to ascii rendering . on terminal and export .mp4 .

# ===================================================
# Dépendances pour VIDEO ASCII - RENDU OPTIMAL + EXPORT MP4
# ===================================================

# Traitement d'images
Pillow>=10.0.0

# Calculs vectoriels (déjà inclus avec Pillow)
numpy>=1.24.0

# Pour l'extraction des métadonnées vidéo (via ffprobe)
# ffmpeg-python est une alternative, mais nous utilisons subprocess
# donc pas de dépendance Python directe.

# ==================================================
# DÉPENDANCES SYSTÈME (à installer séparément)
# ==================================================

# ffmpeg (nécessaire pour l'extraction des frames et l'encodage)
# Installation:
#   Ubuntu/Debian: sudo apt install ffmpeg
#   MacOS: brew install ffmpeg
#   Windows: télécharger depuis https://ffmpeg.org/

# mpv (pour la lecture audio en arrière-plan)
# Installation:
#   Ubuntu/Debian: sudo apt install mpv
#   MacOS: brew install mpv
#   Windows: télécharger depuis https://mpv.io/

________________________________________________________


# CREER UN ENVIRONEMENT VIRTUEL PYTHON

    python -m venv vid

# ACTIVER L'ENVIRONEMENT VIRTUEL

    source vid/bin/activate

# INSTALLER LES DEPENDENCES 

    pip install -r requirements.txt 

# Installer ffmpeg et mpv (système)

    sudo apt install ffmpeg mpv

# RUN COMMANDE ON TERMINAL 

    python converter.py video.mp4 --width 220 --palette optimale --contrast 1.2 --sharpness 1.3 --gamma 0.7

OU avec export .mp4
    
    python converter.py video.mp4 --width 220 --palette optimale --contrast 1.2 --sharpness 1.3 --gamma 0.7 --export nom_de_video.mp4

## 🎬 Démonstration


<img width="2096" height="940" alt="dem" src="https://github.com/user-attachments/assets/7d9c3774-cdad-4af0-bfd3-320a5e6ec8ff" />




By Gleaphe 2026 .


