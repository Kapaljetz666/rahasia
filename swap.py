import base64
import os
import time
import requests
from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from ftplib import FTP
import qrcode
import traceback
from werkzeug.utils import secure_filename
import uuid
from PIL import Image # Import Pillow

app = Flask(__name__) # Ini yang benar

# Flask configuration
app.config['SERVER_NAME'] = '127.0.0.1:5000'
app.config['PREFERRED_URL_SCHEME'] = 'http'

input_folder = 'watch_input'
output_folder = 'output'
model_path = r'C:\Users\X\Desktop\sd\webui\models\roop\inswapper_128.onnx' # SESUAIKAN PATH MODEL ANDA
frame_folder = 'frames' # Folder untuk menyimpan frame
FRAME_FILENAME = 'your_frame.png' # NAMA FILE FRAME ANDA DI SINI

# === KONFIGURASI FTP DAN DOMAIN ANDA ===
# PERINGATAN: Untuk keamanan yang lebih baik di lingkungan produksi,
# sangat disarankan untuk menggunakan variabel lingkungan (seperti dengan file .env)
# atau sistem manajemen secret lainnya.
FTP_HOST = "ftp.lecithiideatama.com"
FTP_USER = "lecp6655"
FTP_PASS = "NE7TcHuPjtEQ31"
REMOTE_BASE_FOLDER = "public_html/ai_results"
PUBLIC_BASE_URL = "https://lecithiideatama.com/ai_results/"
# =====================================

# Prompts
prompts = {
    "A": " <lora:cybepunk:1>2 people, 1girl, 1boy, geralt and ciri, trousers, white t-shirt, cyberware, bionic limbs, metalic ribs, (cyberpunk:1.2), futuristic, dystopia, bare shoulders, masterpiece, best quality, sitting, alcohol, facing each other, dust, light particles, indoors, destroyed bar, face close up shot, hard lines, drawn, illustration",
    "B": " <lora:cybepunk:1>Cyberpunk,solo,rain,looking at viewer,blurry,black hair,long hair, black jacket, blurry background,upper body,neon lights,lips,depth of field,earrings,bangs,wet,nose,from side,jewelry,tank top,realistic,outdoors,looking to the side,closed mouth,bare shoulders,wet hair,ponytail",
    "default": "young ginger woman in white furry sweater, (worlds most beautiful face), portrait, ultra realistic cinematic photo, natural lighting, soft shadows, shallow depth of field, high detail, sharp focus, 50mm photography, realistic skin texture, accurate anatomy, lifelike expression, natural environment, clean background, highly detailed textures in clothing, hair, and lighting"
}
neg_prompts = {
    "A": "woman, girl,porn, nudity, sexy, erotic, cleavage, naked, undressed, bare, exposed, NSFW, explicit, suggestive, vulgar, hentai, topless, bottomless, see-through, intimate, alluring, seductive, sexualized, sensuous, suggestive pose, provocative, obscene, adult content, R-rated, X-rated, genitals, pubic, private parts, nipple, butt crack, anus, vagina, penis, controversial, disturbing, violent, gore, blood, grotesque, dark fantasy, horror, (worst quality:2), (low quality:2), bad anatomy",
    "B": "boy, man, porn, nudity, sexy, erotic, cleavage, naked, undressed, bare, exposed, NSFW, explicit, suggestive, vulgar, hentai, topless, bottomless, see-through, intimate, alluring, seductive, sexualized, sensuous, suggestive pose, provocative, obscene, adult content, R-rated, X-rated, genitals, pubic, private parts, nipple, butt crack, anus, vagina, penis, controversial, disturbing, violent, gore, blood, grotesque, dark fantasy, horror, (worst quality, low quality, normal quality:1.4), (lowres, low resolution:1.4), (blurry, distorted, grainy, noisy:1.3), (monochrome, grayscale:1.2), (semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), abstract art, conceptual art, surrealist painting, collage, text, logo, watermark, artist name, letter, childish, fat, asian, low detailed skin, plastic skin, waxy skin, skin blemishes, skin spots, acne, age spots, poorly drawn, ugly, disfigured, deformed, mutated, disgusting, malformed limbs, extra limbs, missing limbs, floating limbs, disconnected limbs, cloned face, duplicate face, ugly face, asymmetrical face, bad anatomy, wrong anatomy, bad proportions, bad eyes, mutated hands and fingers, deformed iris, deformed pupils, amputation, bad detailed background, unclear architectural outline, floating objects, missing reflections, incorrect perspective, inconsistent lighting, fake depth of field, infinite void, holding, block the chest, clothing clipping, impossible folds, inconsistent fabric, melted clothes, unnatural smile, lifeless eyes, blank stare, uncanny valley, emotionless face, twisted posture, collapsed shoulders, neck too long, overexposed, underexposed, oversaturated, shadow artifacts, chromatic aberration, halos, lens flare, motion blur, weird angle, weird crop, brush strokes, posterization, canvas texture, outline, stylized shading, illustration style, oil painting, airbrush, man, boy, boys, porn, nudity, sexy, erotic, cleavage, naked, undressed, bare, exposed, NSFW, explicit, suggestive, vulgar, hentai, topless, bottomless, see-through, intimate, alluring, seductive, sexualized, sensuous, suggestive pose, provocative, obscene, adult content, R-rated, X-rated, genitals, pubic, private parts, nipple, butt crack, anus, vagina, penis, controversial, disturbing, violent, gore, blood, grotesque, dark fantasy, horror, (worst quality:2), (low quality:2), grayscale",
    "default": " (worst quality, low quality, normal quality:1.4), (lowres, low resolution:1.4), (blurry, distorted, grainy, noisy:1.3), (monochrome, grayscale:1.2), (semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), abstract art, conceptual art, surrealist painting, collage, text, logo, watermark, artist name, letter, childish, fat, asian, low detailed skin, plastic skin, waxy skin, skin blemishes, skin spots, acne, age spots, poorly drawn, ugly, disfigured, deformed, mutated, disgusting, malformed limbs, extra limbs, missing limbs, floating limbs, disconnected limbs, cloned face, duplicate face, ugly face, asymmetrical face, bad anatomy, wrong anatomy, bad proportions, bad eyes, mutated hands and fingers, deformed iris, deformed pupils, amputation, bad detailed background, unclear architectural outline, floating objects, missing reflections, incorrect perspective, inconsistent lighting, fake depth of field, infinite void, holding, block the chest, clothing clipping, impossible folds, inconsistent fabric, melted clothes, unnatural smile, lifeless eyes, blank stare, uncanny valley, emotionless face, twisted posture, collapsed shoulders, neck too long, overexposed, underexposed, oversaturated, shadow artifacts, chromatic aberration, halos, lens flare, motion blur, weird angle, weird crop, brush strokes, posterization, canvas texture, outline, stylized shading, illustration style, oil painting, airbrush, man, boy, boys, porn, nudity, sexy, erotic, cleavage, naked, undressed, bare, exposed, NSFW, explicit, suggestive, vulgar, hentai, topless, bottomless, see-through, intimate, alluring, seductive, sexualized, sensuous, suggestive pose, provocative, obscene, adult content, R-rated, X-rated, genitals, pubic, private parts, nipple, butt crack, anus, vagina, penis, controversial, disturbing, violent, gore, blood, grotesque, dark fantasy, horror, (worst quality:2), (low quality:2), grayscale"
}

selected_template = "default"


# --- VAR GLOBAL BARU UNTUK STATUS PROSES ---
global_processing_status = "idle" # Bisa "idle", "processing", "ready", "error"
global_current_job_id = None
global_processed_results = {} # Cache hasil untuk job_id saat ini
global_status_lock = threading.Lock() # Lock untuk mengamankan akses ke variabel global
# ------------------------------------------

# Fungsi untuk mengunggah file ke FTP
def upload_to_ftp(local_path, remote_file_name):
    """Mengunggah file dari local_path ke remote_file_name di server FTP."""
    print(f"   [FTP] Mencoba mengunggah: {os.path.basename(local_path)} ke {REMOTE_BASE_FOLDER}/{remote_file_name}")
    try:
        with FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            
            # Navigasi langsung ke REMOTE_BASE_FOLDER
            ftp.cwd(REMOTE_BASE_FOLDER) 
            
            # Unggah file langsung ke REMOTE_BASE_FOLDER
            with open(local_path, 'rb') as file:
                ftp.storbinary(f'STOR {remote_file_name}', file)
        print(f"   ✅ [FTP] Berhasil mengunggah: {os.path.basename(local_path)}")
    except Exception as e:
        print(f"   ❌ [FTP] Gagal mengunggah {os.path.basename(local_path)}: {e}")
        traceback.print_exc()
        raise

# Fungsi untuk membuat QR code
def generate_qr_code(target_url, qr_path):
    """Membuat gambar QR code dari target_url dan menyimpannya di qr_path."""
    print(f"   [QR] Membuat QR code untuk URL: {target_url}")
    try:
        img = qrcode.make(target_url)
        img.save(qr_path)
        print(f"   ✅ [QR] QR code disimpan di: {qr_path}")
    except Exception as e:
        print(f"   ❌ [QR] Gagal membuat QR code: {e}")
        traceback.print_exc()
        raise

# Fungsi untuk membuat payload Stable Diffusion
def generate_payload(image_path):
    """Membaca gambar input dan membuat payload JSON untuk Stable Diffusion API."""
    print(f"   [AI] Membangun payload untuk: {os.path.basename(image_path)}")
    try:
        prompt = prompts.get(selected_template, prompts["default"])
        neg = neg_prompts.get(selected_template, neg_prompts["default"])

        with open(image_path, 'rb') as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        print(f"   ✅ [AI] Payload berhasil dibuat.")
        return {
            "prompt": prompt,
            "negative_prompt": neg,
            "seed": -1,
            "sampler_name": "DPM++ 2M",
            "steps": 10,
            "cfg_scale": 2,
            "width": 512,
            "height": 768,
            "restore_faces": True,
            "batch_size": 2, # <-- Mengatur Stable Diffusion untuk menghasilkan 2 gambar
            "alwayson_scripts": {
                "roop": {
                    "args": [img_b64, True, '0', model_path, 'CodeFormer', 1, None, 1, 'None', False, True]
                }
            }
        }
    except Exception as e:
        print(f"   ❌ [AI] Gagal membangun payload: {e}")
        traceback.print_exc()
        raise

# Fungsi untuk mengirim request ke Stable Diffusion API
def send_request(payload):
    """Mengirim payload ke Stable Diffusion API dan mengembalikan respons JSON."""
    url = "http://localhost:7860/sdapi/v1/txt2img"
    print(f"   [API] Mengirim request ke Stable Diffusion API: {url}")
    try:
        res = requests.post(url, json=payload, timeout=300)
        res.raise_for_status()
        print(f"   ✅ [API] Request berhasil. Status: {res.status_code}")
        return res.json()
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ [API] Gagal koneksi ke Stable Diffusion API. Pastikan webui berjalan di {url}. Error: {e}")
        raise
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ [API] HTTP Error dari Stable Diffusion API: {e}. Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"   ❌ [API] Error tak terduga saat mengirim request: {e}")
        traceback.print_exc()
        raise

def clean_old_files():
    """Menghapus semua file yang saat ini ada di output_folder."""
    print(f"   [Clean] Membersihkan folder output: {output_folder}")
    for f in os.listdir(output_folder):
        file_path = os.path.join(output_folder, f)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"     > Dihapus file lama: {file_path}")
        except OSError as e:
            print(f"     Error menghapus file lama {file_path}: {e}")

# Fungsi baru untuk overlay frame
def overlay_frame(base_image_path, frame_image_path, output_image_path):
    """
    Menumpuk frame pada gambar dasar.
    Asumsi: Ukuran frame sama dengan ukuran gambar dasar.
    """
    try:
        base_img = Image.open(base_image_path).convert("RGBA") # Pastikan RGBA untuk alpha channel
        frame_img = Image.open(frame_image_path).convert("RGBA")

        # Pastikan ukuran frame sama dengan gambar dasar
        if base_img.size != frame_img.size:
            print(f"   ⚠️ [Frame] Ukuran gambar dasar ({base_img.size}) tidak sama dengan ukuran frame ({frame_img.size}). Mengubah ukuran frame agar sesuai.")
            frame_img = frame_img.resize(base_img.size, Image.Resampling.LANCZOS) # Ubah ukuran frame jika tidak sama

        # Menggabungkan gambar dasar dengan frame
        # Parameter kedua (mask=frame_img) penting jika frame memiliki transparansi
        combined_img = Image.alpha_composite(base_img, frame_img)
        combined_img.save(output_image_path)
        print(f"   ✅ [Frame] Gambar dengan frame disimpan di: {output_image_path}")
        return True
    except FileNotFoundError:
        print(f"   ❌ [Frame] File frame tidak ditemukan: {frame_image_path}")
        return False
    except Exception as e:
        print(f"   ❌ [Frame] Gagal menggabungkan frame: {e}")
        traceback.print_exc()
        return False

# Modifikasi process_image untuk menerima job_id
def process_image(image_path, job_id):
    """
    Memproses gambar input: mengirim ke AI, menambahkan frame, menyimpan gambar individu secara lokal
    dan mengunggahnya langsung ke folder dasar di FTP, membuat QR code yang mengarah langsung ke gambar di FTP,
    lalu memperbarui cache hasil untuk review.html.
    """
    global global_processing_status, global_processed_results

    print(f"🔄 Memulai pemrosesan gambar: {os.path.basename(image_path)} untuk Job ID: {job_id}")
    try:
        if not os.path.exists(image_path):
            print(f"   ❌ File input tidak ditemukan: {image_path}. Mungkin sudah dipindahkan atau dihapus.")
            with global_status_lock:
                if global_current_job_id == job_id:
                    global_processing_status = "error"
            return

        # Hapus file lama sebelum memproses gambar baru - ini harusnya sudah dilakukan di upload_image
        # clean_old_files() # Hapus baris ini

        payload = generate_payload(image_path)
        result = send_request(payload)
        images_b64 = result['images'][:2] # Mengambil hingga 2 gambar pertama yang dihasilkan AI

        current_local_image_urls = []
        public_image_urls_on_ftp = []

        # Tentukan path lengkap ke file frame
        frame_full_path = os.path.join(app.root_path, frame_folder, FRAME_FILENAME)
        if not os.path.exists(frame_full_path):
            print(f"   ❌ [ERROR] File frame tidak ditemukan di: {frame_full_path}. Gambar akan disimpan tanpa frame.")
            frame_full_path = None # Set ke None agar tidak mencoba overlay

        
        if images_b64:
            for i, img_b64 in enumerate(images_b64):
                img_data = base64.b64decode(img_b64)
                
                # Simpan gambar AI asli sementara sebelum di-frame
                temp_ai_image_path = os.path.join(output_folder, f"temp_ai_{job_id}_{i+1}.png")
                with open(temp_ai_image_path, 'wb') as f:
                    f.write(img_data)

                # Tentukan nama file akhir (dengan frame)
                # Nama file unik untuk FTP dan juga untuk URL publik
                remote_img_filename = f"ai_photo_{job_id}_{i+1}.png" 
                # Nama file unik untuk penyimpanan lokal agar Flask bisa melayani
                local_temp_filename_for_flask = f"local_{remote_img_filename}" 
                final_local_img_path = os.path.join(output_folder, local_temp_filename_for_flask)

                # Jika frame tersedia, lakukan overlay
                if frame_full_path:
                    print(f"   [Frame] Menerapkan frame ke gambar AI #{i+1}...")
                    overlay_successful = overlay_frame(temp_ai_image_path, frame_full_path, final_local_img_path)
                    if not overlay_successful:
                        # Jika overlay gagal, gunakan gambar AI asli tanpa frame
                        os.rename(temp_ai_image_path, final_local_img_path)
                        print(f"   ⚠️ [Frame] Gagal overlay, menggunakan gambar AI asli tanpa frame: {final_local_img_path}")
                else:
                    # Jika tidak ada frame, langsung gunakan gambar AI asli
                    os.rename(temp_ai_image_path, final_local_img_path)
                    print(f"   [Frame] Tidak ada frame yang ditentukan atau ditemukan, menggunakan gambar AI asli: {final_local_img_path}")

                # Hapus file AI asli sementara
                if os.path.exists(temp_ai_image_path):
                    os.remove(temp_ai_image_path)
                
                # Unggah gambar yang sudah diframe (atau gambar asli jika tanpa frame) ke FTP
                upload_to_ftp(final_local_img_path, remote_img_filename)

                with app.app_context():
                    flask_local_img_url = url_for('serve_output', filename=local_temp_filename_for_flask, _external=False)
                current_local_image_urls.append(flask_local_img_url)
                public_image_urls_on_ftp.append(f"{PUBLIC_BASE_URL}{remote_img_filename}")
                
                print(f"   > Gambar AI #{i+1} (dengan/tanpa frame) disimpan lokal: {final_local_img_path}, URL Flask: {flask_local_img_url}")
                print(f"   [FILE] URL gambar #{i+1} di FTP: {public_image_urls_on_ftp[-1]}")

            with global_status_lock:
                if global_current_job_id == job_id: # Hanya update jika ini masih job yang sama
                    global_processed_results = {
                        "images": current_local_image_urls,
                        "public_ftp_urls": public_image_urls_on_ftp
                    }
                    global_processing_status = "ready"
            
            print(f"✅ Proses Selesai! Hasil disimpan dalam cache untuk Job ID {job_id}.")
            
        else:
            print("   ⚠️ Tidak ada gambar yang dihasilkan oleh Stable Diffusion.")
            with global_status_lock:
                if global_current_job_id == job_id:
                    global_processing_status = "error" # Atau "no_images"

    except Exception as e:
        print(f"❌ Gagal memproses {os.path.basename(image_path)} secara keseluruhan untuk Job ID {job_id}: {e}")
        traceback.print_exc()
        with global_status_lock:
            if global_current_job_id == job_id:
                global_processing_status = "error"

# Kelas event handler untuk watchdog
class ImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"\n--- Deteksi file baru via Watchdog: {event.src_path} ---")
            time.sleep(1) # Beri sedikit waktu untuk file selesai ditulis
            # Di sini, kita tidak langsung memanggil process_image karena upload_image yang mengurusnya
            # Kecuali jika Anda ingin watchdog ini tetap menjadi jalur utama upload, maka logika status perlu di sini juga.
            # Untuk skenario saat ini, upload_image yang akan mengatur status
            pass # Biarkan upload_image yang handle

# --- Rute Flask ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture.html')
def capture():
    return render_template('capture.html')

@app.route('/review.html')
def review():
    print(f"   [Flask Render] Mengirim review.html.")
    # Reset status saat me-render review.html untuk memastikan tampilan fresh
    # Ini opsional, tapi membantu menghindari tampilan hasil lama jika langsung ke review.html
    # tanpa upload baru.
    # with global_status_lock:
    #     if global_processing_status == "ready": # Jika ada hasil, biarkan
    #         pass
    #     else: # Jika tidak ada proses atau error, set ke idle agar frontend tampil loading
    #         global_processing_status = "idle"
    return render_template('review.html')

@app.route('/api/last_results_status')
def get_last_results_status():
    """Endpoint API untuk memantau status hasil terakhir (gambar dan QR)."""
    with global_status_lock:
        status = global_processing_status
        job_id = global_current_job_id
        results = global_processed_results.copy() # Ambil salinan

    response_data = {
        "status": status,
        "job_id": job_id
    }

    if status == "ready" and job_id:
        # Pastikan results adalah hasil untuk job_id yang sedang 'ready'
        if results:
            response_data["data"] = results
        else: # Kasus edge: status ready tapi results kosong (misal gagal ambil gambar dari SD)
            response_data["status"] = "error"
            response_data["message"] = "Hasil tidak ditemukan untuk job yang selesai."
    elif status == "error":
        response_data["message"] = "Terjadi kesalahan saat memproses gambar."
    elif status == "processing":
        response_data["message"] = "AI sedang memproses gambar Anda..."
    elif status == "idle":
        response_data["message"] = "Menunggu unggahan gambar..."
    
    print(f"   [API] Mengirim status: {response_data['status']} (Job ID: {response_data['job_id']})")
    return jsonify(response_data)

@app.route('/api/generate_qr', methods=['POST'])
def generate_qr_for_selected_image():
    """
    Endpoint API untuk membuat QR code dari URL gambar yang dipilih di frontend.
    URL yang diterima adalah URL lokal Flask, perlu diubah ke URL FTP publik.
    """
    try:
        data = request.get_json()
        selected_flask_local_url = data.get('imageUrl')

        if not selected_flask_local_url:
            print("❌ [API Generate QR] Tidak ada imageUrl yang diterima.")
            return jsonify({"status": "error", "message": "Tidak ada URL gambar yang diterima."}), 400

        target_ftp_url = None
        # Perbarui dari processed_results_cache ke global_processed_results
        with global_status_lock:
            if global_processed_results:
                local_urls = global_processed_results['images']
                ftp_urls = global_processed_results['public_ftp_urls']
                
                for i, local_url in enumerate(local_urls):
                    if local_url == selected_flask_local_url:
                        target_ftp_url = ftp_urls[i]
                        break
        
        if not target_ftp_url:
            print(f"❌ [API Generate QR] URL FTP publik tidak ditemukan untuk URL lokal: {selected_flask_local_url}")
            return jsonify({"status": "error", "message": "URL gambar tidak valid atau tidak ditemukan."}), 400

        qr_filename = f"qr_{str(uuid.uuid4())}.png"
        local_qr_path = os.path.join(output_folder, qr_filename)
        
        generate_qr_code(target_ftp_url, local_qr_path)

        with app.app_context():
            flask_local_qr_url = url_for('serve_output', filename=qr_filename, _external=False)
        
        print(f"✅ [API Generate QR] QR code berhasil dibuat. URL QR lokal: {flask_local_qr_url}, Target URL FTP: {target_ftp_url}")
        return jsonify({"status": "success", "qr_code_url": flask_local_qr_url})

    except Exception as e:
        print(f"❌ [API Generate QR] Error saat membuat QR code: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Gagal membuat QR Code: {str(e)}"}), 500


@app.route('/set_template', methods=['POST'])
def set_template():
    global selected_template
    data = request.get_json()
    template = data.get('template')
    if template in prompts:
        selected_template = template
        print(f"   [API] Template diatur ke: {selected_template}")
        return jsonify({"status": "success", "template": selected_template})
    return jsonify({"status": "error", "message": "Invalid template"}), 400

@app.route('/upload_image', methods=['POST'])
def upload_image():
    global global_processing_status, global_current_job_id, global_processed_results

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file gambar dalam permintaan."}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "Tidak ada file yang dipilih."}), 400
    
    if file:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.png', '.jpg', '.jpeg']:
            return jsonify({"status": "error", "message": "Format file tidak didukung. Harap unggah PNG, JPG, atau JPEG."}), 400

        job_id = str(uuid.uuid4()) # ID unik untuk job ini
        unique_filename = job_id + file_extension # Gunakan job_id sebagai bagian dari filename
        filepath = os.path.join(input_folder, unique_filename)
        try:
            file.save(filepath)
            print(f"File berhasil diunggah ke {filepath}")

            # --- Perbarui status global SEBELUM memulai proses AI ---
            with global_status_lock:
                global_current_job_id = job_id
                global_processing_status = "processing"
                global_processed_results = {} # Kosongkan hasil sebelumnya
            # --------------------------------------------------------

            # Hapus semua file lama di output_folder agar review.html bersih dari hasil lama
            clean_old_files()

            # Mulai pemrosesan di thread terpisah
            threading.Thread(target=process_image, args=(filepath, job_id)).start()
            
            return jsonify({"status": "success", "message": "File berhasil diunggah. AI sedang memproses.", "filename": unique_filename, "job_id": job_id})
        except Exception as e:
            print(f"Gagal menyimpan file: {e}")
            with global_status_lock:
                if global_current_job_id == job_id: # Pastikan hanya update jika job ini yang gagal
                    global_processing_status = "error"
            return jsonify({"status": "error", "message": f"Gagal menyimpan file: {str(e)}"}), 500
    
    return jsonify({"status": "error", "message": "Kesalahan yang tidak diketahui saat mengunggah file."}), 500

@app.route('/output/<path:filename>')
def serve_output(filename):
    """Melayani file dari folder output (gambar AI dan QR code)."""
    print(f"   [Flask Serve] Melayani file dari output: {filename}")
    try:
        full_path = os.path.join(output_folder, filename)
        if not os.path.exists(full_path):
            print(f"   ❌ [Flask Serve] File tidak ditemukan di disk: {full_path}")
            return "File not found", 404
        return send_from_directory(output_folder, filename)
    except Exception as e:
        print(f"   ❌ [Flask Serve] Gagal melayani {filename}: {e}")
        traceback.print_exc()
        return "File not found", 404

def start_watcher():
    observer = Observer()
    observer.schedule(ImageHandler(), input_folder, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    # Pastikan folder ada
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(frame_folder, exist_ok=True) # Buat folder frames

    # Bersihkan folder output saat startup agar tidak ada file lama
    clean_old_files()

    threading.Thread(target=start_watcher, daemon=True).start()
    print("\n--- Flask Photobooth Aplikasi Dimulai ---")
    print(f"Memantau folder input: {input_folder}")
    print(f"""File output sementara (untuk tampilan lokal) disimpan ke: {output_folder}""") 
    print(f"Folder Frame: {frame_folder}, Nama File Frame: {FRAME_FILENAME}")
    print(f"FTP Host: {FTP_HOST}, Remote Base Folder: {REMOTE_BASE_FOLDER}")
    print(f"URL Publik Base FTP: {PUBLIC_BASE_URL}")
    print(f"Menjalankan Flask di http://127.0.0.1:5000 (dapat diakses dari PC ini)")
    print("----------------------------------------")
    app.run(debug=True, host='127.0.0.1', port=5000)