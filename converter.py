#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VIDEO ASCII - RENDU OPTIMAL + EXPORT MP4 RAPIDE
Utilise des masques Numpy pour un export haute vitesse.
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

# ============================================================
# PALETTE OPTIMISÉE
# ============================================================

PALETTE_OPTIMALE = [
    '_', '█', '▓', '▒', '░', '@', '&', '#', 'f', 'u', 't', 'u', 'r', 'c', 'r', 'e', 'w', '9', '7', '4', '_'
]

PALETTE_ETENDUE = [
    '_', '█', '▓', '▒', '░', '@', '&', '#', '%', '$', 'B', 'M', 'W', '8', '0',
    'f', 'u', 't', 'r', 'c', 'e', 'w', '9', '7', '4', '3', '2', '1', '0', ' '
]

PALETTES = {
    'optimale': PALETTE_OPTIMALE,
    'etendue': PALETTE_ETENDUE,
}

# Recherche de police
FONT_PATH = None
for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:\\Windows\\Fonts\\consola.ttf", "/System/Library/Fonts/Menlo.ttc"]:
    if os.path.exists(fp):
        FONT_PATH = fp
        break

# ============================================================
# FONCTIONS
# ============================================================

def get_video_info(video_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', video_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(json.loads(result.stdout)['format']['duration'])
    except: pass
    return None

def get_terminal_size():
    try: return shutil.get_terminal_size()
    except: return 120, 40

# ============================================================
# CONVERSION TERMINAL (ANSI)
# ============================================================

def frame_to_ascii_optimized(frame_path, width=200, color=True, palette='optimale',
                              contrast=1.4, saturation=1.3, sharpness=1.5, gamma=0.8):
    try:
        img = Image.open(frame_path)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageEnhance.Color(img).enhance(saturation)
        img = ImageEnhance.Sharpness(img).enhance(sharpness)

        w, h = img.size
        aspect = h / w
        height = int(aspect * width * 0.45)

        term_cols, term_rows = get_terminal_size()
        max_height = term_rows - 6
        if height > max_height:
            height = max_height
            width = int(height / (aspect * 0.45))

        img = img.resize((width, height), Image.Resampling.BOX)
        chars = PALETTES.get(palette, PALETTE_OPTIMALE)
        chars_len = len(chars) - 1

        gray = np.array(img.convert('L'))
        p_min, p_max = gray.min(), gray.max()
        if p_max > p_min:
            gray = ((gray - p_min) / (p_max - p_min) * 255).astype(np.uint8)
        gray = (255 * (gray / 255) ** gamma).astype(np.uint8)
        indices = (gray / 255 * chars_len).astype(int)

        if color:
            rgb = np.array(img.convert('RGB'))
            lines = []
            for y in range(indices.shape[0]):
                row_r, row_g, row_b = rgb[y, :, 0], rgb[y, :, 1], rgb[y, :, 2]
                row_indices = indices[y]
                line_parts = []
                prev_r, prev_g, prev_b = -1, -1, -1
                for x in range(len(row_indices)):
                    r, g, b = int(row_r[x]), int(row_g[x]), int(row_b[x])
                    qr, qg, qb = r >> 2, g >> 2, b >> 2
                    if qr != prev_r or qg != prev_g or qb != prev_b:
                        line_parts.append(f'\033[38;2;{r};{g};{b}m')
                        prev_r, prev_g, prev_b = qr, qg, qb
                    line_parts.append(chars[row_indices[x]])
                lines.append("".join(line_parts) + "\033[0m")
            return "\n".join(lines)
        else:
            char_array = np.array(chars)
            mapped_chars = char_array[indices]
            return '\n'.join(["".join(row) for row in mapped_chars])
    except: return ""

# ============================================================
# LECTEUR OPTIMISÉ
# ============================================================

class LecteurOptimized:
    def __init__(self, video_path, width=200, color=True, zoom=1.0,
                 fps=24, max_frames=400, volume=100, palette='optimale',
                 contrast=1.4, saturation=1.3, sharpness=1.5, gamma=0.8, sync=True, export_path=None):
        self.video_path = video_path
        self.width = int(width * zoom)
        self.color = color
        self.fps = fps
        self.max_frames = max_frames
        self.volume = volume
        self.palette = palette
        self.contrast = contrast
        self.saturation = saturation
        self.sharpness = sharpness
        self.gamma = gamma
        self.sync = sync
        self.export_path = export_path
        self.running = True
        self.frames = []
        self.temp_dir = None
        self.term_height = 0
        self.actual_fps = 24
        self.audio_process = None
        self.start_time = 0
        self.paused = False
        self.audio_started = False
        self.duration = 0

        # Variables pour l'export rapide
        self.char_masks = {}
        self.char_w = 0
        self.char_h = 0

    def extraire_frames(self):
        self.duration = get_video_info(self.video_path)
        if not self.duration: return False

        actual_fps = min(self.fps, 30)
        total_frames = int(self.duration * actual_fps)
        if total_frames > self.max_frames:
            actual_fps = self.max_frames / self.duration
            total_frames = self.max_frames

        self.actual_fps = actual_fps
        self.total_frames = total_frames
        self.temp_dir = tempfile.mkdtemp(prefix='ascii_opt_')
        frame_pattern = os.path.join(self.temp_dir, 'frame_%06d.png')

        cmd = [
            'ffmpeg', '-i', self.video_path,
            '-vf', f'fps={actual_fps},scale={self.width * 4}:-1',
            '-vframes', str(total_frames),
            '-compression_level', '1', '-y', frame_pattern
        ]

        print(f"📥 Extraction des frames...")
        if subprocess.run(cmd, capture_output=True).returncode != 0: return False

        self.frames = sorted([os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir) if f.endswith('.png')])
        return len(self.frames) > 0

    def init_masks(self, font_size=12):
        """Pré-génère les masques de chaque caractère pour un dessin ultra rapide"""
        chars = PALETTES.get(self.palette, PALETTE_OPTIMALE)
        try:
            font = ImageFont.truetype(FONT_PATH, font_size) if FONT_PATH else ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        bbox = font.getbbox("@")
        self.char_w = bbox[2] - bbox[0] + 2
        self.char_h = bbox[3] - bbox[1] + 2

        for char in set(chars):
            img = Image.new('L', (self.char_w, self.char_h), 0)
            draw = ImageDraw.Draw(img)
            draw.text((0, 0), char, fill=255, font=font)
            # True là où il y a de l'encre
            self.char_masks[char] = np.array(img) > 128

    def frame_to_image_fast(self, frame_path):
        """Génère l'image ASCII en appliquant des masques Numpy (très rapide)"""
        img = Image.open(frame_path)
        img = ImageEnhance.Contrast(img).enhance(self.contrast)
        img = ImageEnhance.Color(img).enhance(self.saturation)
        img = ImageEnhance.Sharpness(img).enhance(self.sharpness)

        w, h = img.size
        height = int((h / w) * self.width * 0.45)
        img = img.resize((self.width, height), Image.Resampling.BOX)

        chars = PALETTES.get(self.palette, PALETTE_OPTIMALE)
        chars_len = len(chars) - 1

        gray = np.array(img.convert('L'))
        p_min, p_max = gray.min(), gray.max()
        if p_max > p_min:
            gray = ((gray - p_min) / (p_max - p_min) * 255).astype(np.uint8)
        gray = (255 * (gray / 255) ** self.gamma).astype(np.uint8)
        indices = (gray / 255 * chars_len).astype(int)
        rgb = np.array(img.convert('RGB'))

        # Création du fond noir
        img_array = np.zeros((height * self.char_h, self.width * self.char_w, 3), dtype=np.uint8)

        # Application des masques
        for y in range(height):
            for x in range(self.width):
                char = chars[indices[y, x]]
                r, g, b = int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2])
                mask = self.char_masks[char]

                y_s, y_e = y * self.char_h, (y + 1) * self.char_h
                x_s, x_e = x * self.char_w, (x + 1) * self.char_w

                # Colorie uniquement les pixels du masque
                img_array[y_s:y_e, x_s:x_e][mask] = (r, g, b)

        return Image.fromarray(img_array)

    def exporter_mp4(self):
        if not self.frames: return

        print(f"\n🎬 DÉBUT DU RENDU VIDÉO MP4 RAPIDE...")
        print(f"   Initialisation des masques de dessin...")
        self.init_masks(font_size=12)
        print(f"   Taille d'un caractère: {self.char_w}x{self.char_h} px")
        print(f"   Résolution finale: {self.width * self.char_w}x{int((9/16)*self.width)*self.char_h} px")

        video_tmp = os.path.join(self.temp_dir, "video_ascii.mp4")
        audio_tmp = os.path.join(self.temp_dir, "audio.aac")

        print("🔊 Extraction de l'audio...")
        subprocess.run(['ffmpeg', '-y', '-i', self.video_path, '-vn', '-acodec', 'aac', '-b:a', '128k', audio_tmp], capture_output=True)

        # AJOUT DE stdout et stderr à DEVNULL pour cacher les logs de FFmpeg
        cmd_video = [
            'ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'png', '-r', str(self.actual_fps),
            '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'fast', video_tmp
        ]

        process = subprocess.Popen(cmd_video, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        start_render = time.time()
        for i, frame_path in enumerate(self.frames):
            progress = int((i + 1) / len(self.frames) * 30)
            bar = '█' * progress + '░' * (30 - progress)

            # Calcul du FPS de rendu en temps réel
            elapsed = time.time() - start_render
            current_fps = (i + 1) / elapsed if elapsed > 0 else 0

            print(f"\r🎨 Rendu [{bar}] {i+1}/{len(self.frames)} ({current_fps:.1f} FPS)", end='', flush=True)

            img = self.frame_to_image_fast(frame_path)
            if img:
                img.save(process.stdin, format='PNG')

        process.stdin.close()
        process.wait()

        if process.returncode != 0:
            print("\n❌ Erreur lors de l'encodage vidéo.")
            return

        print(f"\n🔗 Fusion de la vidéo et de l'audio...")
        subprocess.run(['ffmpeg', '-y', '-i', video_tmp, '-i', audio_tmp, '-c:v', 'copy', '-c:a', 'copy', '-shortest', self.export_path], capture_output=True)

        final_size = os.path.getsize(self.export_path) / (1024 * 1024)
        print(f"\n✅ EXPORT TERMINÉ !")
        print(f"   Fichier : {self.export_path}")
        print(f"   Taille  : {final_size:.2f} Mo")

    def demarrer_audio_mpv(self):
        try:
            self.audio_process = subprocess.Popen(
                ['mpv', '--no-video', '--really-quiet', f'--volume={self.volume}', self.video_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)
            self.audio_started = True
        except: pass

    def arreter_audio(self):
        if self.audio_process:
            try: self.audio_process.terminate(); self.audio_process.wait(timeout=2)
            except: self.audio_process.kill()

    def jouer_sync(self):
        if not self.frames: return
        self.demarrer_audio_mpv()
        self.term_height = get_terminal_size()[1]

        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        self.start_time = time.time()

        try:
            while self.running:
                for i, frame_path in enumerate(self.frames):
                    if not self.running: break
                    if self.paused: time.sleep(0.1); continue

                    if self.sync:
                        target_time = i / self.actual_fps
                        current_time = time.time() - self.start_time
                        if current_time > target_time + 0.1: continue

                    ascii_frame = frame_to_ascii_optimized(
                        frame_path, self.width, self.color, self.palette,
                        self.contrast, self.saturation, self.sharpness, self.gamma
                    )

                    if ascii_frame:
                        sys.stdout.write(f"\033[H{ascii_frame}")
                        progress = int((i + 1) / len(self.frames) * 30)
                        bar = '█' * progress + '░' * (30 - progress)
                        elapsed = time.time() - self.start_time
                        time_pos = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
                        total_time = f"{int(self.duration//60)}:{int(self.duration%60):02d}"

                        sys.stdout.write(f"\033[{self.term_height};1H")
                        sys.stdout.write(f"\033[90m▶️ [{bar}] {time_pos}/{total_time}\033[0m")
                        sys.stdout.flush()

                    if self.sync:
                        wait_time = (i + 1) / self.actual_fps - (time.time() - self.start_time)
                        if wait_time > 0: time.sleep(wait_time)
                    else:
                        time.sleep(1.0 / self.actual_fps)

                    if i == len(self.frames) - 1: self.start_time = time.time()

        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[?25h\n")
            sys.stdout.flush()
            self.arreter_audio()

    def run(self):
        if not self.extraire_frames(): return

        if self.export_path:
            self.exporter_mp4()
        else:
            self.jouer_sync()

        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        import PIL
    except ImportError:
        print("📦 Installation de Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])

    if len(sys.argv) < 2:
        print("=" * 70)
        print("🎬 VIDEO ASCII - RENDU OPTIMAL + EXPORT MP4")
        print("=" * 70)
        print("\n📖 UTILISATION:")
        print("  python converter.py Futurcrew.mp4")
        print("  python converter.py Futurcrew.mp4 --export resultat.mp4")
        print("=" * 70)
        sys.exit(1)

    video = sys.argv[1]
    kwargs = {
        'video_path': video, 'width': 200, 'color': True, 'zoom': 1.0,
        'fps': 24, 'max_frames': 400, 'volume': 100, 'palette': 'optimale',
        'contrast': 1.4, 'saturation': 1.3, 'sharpness': 1.5, 'gamma': 0.8,
        'sync': True, 'export_path': None
    }

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--export' and i + 1 < len(sys.argv):
            kwargs['export_path'] = sys.argv[i + 1]
            i += 2
        elif arg in ['--width', '--fps', '--frames', '--volume'] and i + 1 < len(sys.argv):
            kwargs[arg[2:]] = int(sys.argv[i + 1]); i += 2
        elif arg in ['--contrast', '--saturation', '--sharpness', '--gamma', '--zoom'] and i + 1 < len(sys.argv):
            kwargs[arg[2:]] = float(sys.argv[i + 1]); i += 2
        elif arg == '--palette' and i + 1 < len(sys.argv):
            kwargs['palette'] = sys.argv[i + 1]; i += 2
        elif arg == '--no-color': kwargs['color'] = False; i += 1
        elif arg == '--no-sync': kwargs['sync'] = False; i += 1
        else: i += 1

    if not os.path.exists(video):
        print(f"❌ Vidéo non trouvée: {video}"); sys.exit(1)

    if shutil.which('mpv') is None and not kwargs['export_path']:
        kwargs['sync'] = False

    lecteur = LecteurOptimized(**kwargs)
    lecteur.run()
