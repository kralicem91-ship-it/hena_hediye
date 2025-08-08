from flask import Flask, request, redirect, url_for, jsonify, Response, send_file, abort
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from io import BytesIO

app = Flask(__name__)

# Cloudinary ayarları - kendi bilgilerinle değiştir
cloudinary.config(
    cloud_name='dw05usul3',
    api_key='415741124466735',
    api_secret='ksAtJX1AnWnAYxePPZMCHyzl08Q',
    secure=True
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_gallery_items():
    gallery = []
    try:
        # Videoları çek
        videos_res = cloudinary.api.resources(type='upload', resource_type='video', prefix='wedding2025/', max_results=100)
        videos = videos_res.get('resources', [])
        for v in videos:
            gallery.append({
                'url': v['secure_url'],
                'ext': v['format'].lower(),
                'public_id': v['public_id'],
                'resource_type': 'video'
            })

        # Fotoğrafları çek
        images_res = cloudinary.api.resources(type='upload', resource_type='image', prefix='wedding2025/', max_results=100)
        images = images_res.get('resources', [])
        for i in images:
            gallery.append({
                'url': i['secure_url'],
                'ext': i['format'].lower(),
                'public_id': i['public_id'],
                'resource_type': 'image'
            })
    except Exception as e:
        print("Cloudinary API hatası:", e)

    return gallery

def generate_index_html(gallery, message=''):
    gallery_items = ''
    if gallery:
        for file in gallery:
            url = file['url']
            ext = file['ext']
            public_id = file['public_id']
            resource_type = file['resource_type']
            if resource_type == 'video' or ext in ('mp4', 'mov', 'avi', 'webm'):
                # Video küçük önizleme, onclick ile tam ekran modal açılır
                gallery_items += f'''
                <div class="gallery-item">
                    <video src="{url}" muted preload="metadata" onclick="openModal('{url}', 'video')" ></video>
                    <button class="delete-btn" onclick="deleteMedia('{public_id}', '{resource_type}')">Sil</button>
                </div>
                '''
            else:
                # Resim küçük önizleme, onclick ile tam ekran modal açılır
                gallery_items += f'''
                <div class="gallery-item">
                    <img src="{url}" alt="Fotoğraf" onclick="openModal('{url}', 'image')" />
                    <button class="delete-btn" onclick="deleteMedia('{public_id}', '{resource_type}')">Sil</button>
                </div>
                '''
    else:
        gallery_items = '<p>Henüz yüklenmiş bir fotoğraf veya video yok.</p>'

    html = f'''
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Düğünümüze Hoş Geldiniz</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display&display=swap" rel="stylesheet" />
  <style>
    * {{
      margin: 0; padding: 0; box-sizing: border-box;
      font-family: 'Playfair Display', serif;
    }}
    body {{
      background: linear-gradient(135deg, #fdf6f0, #fcefe8);
      color: #5a3e36;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
    }}
    section {{
      max-width: 700px;
      background: white;
      padding: 40px 30px;
      margin-bottom: 30px;
      border-radius: 16px;
      box-shadow: 0 8px 24px rgba(197, 135, 94, 0.3);
      text-align: center;
    }}
    h1 {{
      font-size: 3rem;
      margin-bottom: 15px;
      color: #b85c38;
    }}
    h2 {{
      font-size: 2rem;
      margin-bottom: 15px;
      color: #a04a2f;
    }}
    p {{
      font-size: 1.125rem;
      line-height: 1.6;
      color: #6e4b3b;
    }}
    .upload-form {{
      max-width: 400px;
      margin: 0 auto;
      border: 2px dashed #b85c38;
      padding: 20px;
      border-radius: 16px;
      background-color: #fff7f2;
    }}
    .upload-form input[type="file"] {{
      width: 100%;
      padding: 10px;
      border: 2px solid #b85c38;
      border-radius: 8px;
      background: #fff;
      cursor: pointer;
    }}
    .upload-form button {{
      background-color: #b85c38;
      border: none;
      padding: 14px 30px;
      border-radius: 8px;
      color: white;
      font-weight: 700;
      cursor: pointer;
      font-size: 1.1rem;
      margin-top: 15px;
      transition: background-color 0.3s ease;
    }}
    .upload-form button:hover {{
      background-color: #a04a2f;
    }}
    #uploadStatus {{
      margin-top: 12px;
      font-style: italic;
      color: #7b5038;
      min-height: 1.2em;
    }}
    .gallery {{
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      justify-content: center;
    }}
    .gallery-item {{
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .gallery img, .gallery video {{
      width: 150px;
      height: 150px;
      border-radius: 12px;
      object-fit: cover;
      box-shadow: 0 6px 14px rgba(184, 92, 56, 0.5);
      transition: transform 0.3s ease;
      cursor: pointer;
    }}
    .gallery img:hover, .gallery video:hover {{
      transform: scale(1.05);
    }}
    .delete-btn {{
      margin-top: 5px;
      padding: 5px 10px;
      font-size: 0.9rem;
      background-color: #c94f3f;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
    }}

    /* Modal */
    .modal {{
      display: none;
      position: fixed;
      z-index: 999;
      top: 0; left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(0, 0, 0, 0.85);
      justify-content: center;
      align-items: center;
      flex-direction: column;
      padding: 20px;
    }}
    .modal.open {{
      display: flex;
    }}
    .modal-content {{
      max-width: 95vw;
      max-height: 85vh;
      border-radius: 12px;
      margin-bottom: 20px;
      box-shadow: 0 0 20px rgba(0,0,0,0.8);
    }}
    .modal-content video, .modal-content img {{
      max-width: 95vw;
      max-height: 85vh;
      border-radius: 12px;
    }}
    .modal button, .modal a button {{
      background-color: #b85c38;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      margin: 5px;
    }}
    .modal a {{
      text-decoration: none;
    }}

    @media (max-width: 480px) {{
      h1 {{ font-size: 2rem; }}
      h2 {{ font-size: 1.5rem; }}
      section {{ padding: 30px 20px; }}
      .gallery img, .gallery video {{ width: 100px; height: 100px; }}
    }}
  </style>
</head>
<body>

  <section class="welcome">
    <h1>Düğünümüze Hoş Geldiniz</h1>
    <p>Elif & Burak - 12 Temmuz 2025<br>Bu sayfadan bize anılarınızı bırakabilirsiniz 💍✨</p>
  </section>

  <section class="intro">
    <h2>Tanıtım</h2>
    <p>Bu sayfa sayesinde çektiğiniz fotoğraf ve videoları bize yükleyebilir, hep birlikte bu özel günün anılarını biriktirebiliriz!</p>
  </section>

  <section class="upload">
    <h2>Fotoğraf veya Video Gönder</h2>
    <div class="upload-form">
      <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/*,video/*" multiple required />
        <button type="submit">Gönder</button>
      </form>
      <p id="uploadStatus">{message}</p>
    </div>
  </section>

  <section class="gallery-section">
    <h2>Anılar</h2>
    <div class="gallery" id="galleryGrid">
      {gallery_items}
    </div>
  </section>

  <!-- Modal -->
  <div id="mediaModal" class="modal" onclick="if(event.target===this) closeModal()">
    <div id="modalContentWrapper" class="modal-content"></div>
    <a id="downloadBtn" download target="_blank" style="display:none;">
      <button>İndir</button>
    </a>
    <button onclick="closeModal()">Kapat</button>
  </div>

  <script>
    const modal = document.getElementById('mediaModal');
    const modalContentWrapper = document.getElementById('modalContentWrapper');
    const downloadBtn = document.getElementById('downloadBtn');

    function openModal(src, type) {{
      modalContentWrapper.innerHTML = '';
      let modalMedia;

      if (type === 'image') {{
        modalMedia = document.createElement('img');
        downloadBtn.style.display = "inline-block";
        downloadBtn.href = '/download?url=' + encodeURIComponent(src);
        let ext = src.split('.').pop().split(/#|\\?/)[0];
        downloadBtn.download = "indirilen_fotograf." + ext;
      }} else if (type === 'video') {{
        modalMedia = document.createElement('video');
        modalMedia.controls = true;
        modalMedia.autoplay = true;
        downloadBtn.style.display = "inline-block";
        downloadBtn.href = '/download?url=' + encodeURIComponent(src);
        let ext = src.split('.').pop().split(/#|\\?/)[0];
        downloadBtn.download = "indirilen_video." + ext;
      }} else {{
        downloadBtn.style.display = "none";
        modalContentWrapper.innerHTML = "<p>Bu medya türü görüntülenemiyor.</p>";
        modal.classList.add('open');
        return;
      }}

      modalMedia.src = src;
      modalContentWrapper.appendChild(modalMedia);
      modal.classList.add('open');
    }}

    function closeModal() {{
      modal.classList.remove('open');
      modalContentWrapper.innerHTML = '';
      const video = modalContentWrapper.querySelector('video');
      if(video) {{
        video.pause();
        video.currentTime = 0;
      }}
    }}

    function deleteMedia(public_id, resource_type) {{
      const password = prompt("Silmek için şifreyi giriniz:");
      if (!password) return;

      fetch('/delete', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json'
        }},
        body: JSON.stringify({{ public_id, resource_type, password }})
      }})
      .then(res => res.json())
      .then(data => {{
        if(data.success) {{
          alert('Dosya başarıyla silindi.');
          window.location.reload();
        }} else {{
          alert(data.message || 'Silme işlemi başarısız.');
        }}
      }})
      .catch(() => alert("Bir hata oluştu."));
    }}
  </script>

</body>
</html>
    '''
    return html

@app.route('/download')
def download_file():
    file_url = request.args.get('url')
    if not file_url:
        abort(400, "Dosya URL'si belirtilmedi.")

    try:
        # Cloudinary dosyasını getiriyoruz
        r = requests.get(file_url, stream=True)
        r.raise_for_status()

        # Dosya adı için url'den son kısmı al
        filename = file_url.split('/')[-1].split('?')[0]

        # BytesIO objesi oluştur
        file_data = BytesIO(r.content)

        # Dosyayı "attachment" olarak gönder (indir)
        return send_file(
            file_data,
            as_attachment=True,
            download_name=filename,
            mimetype=r.headers.get('Content-Type', 'application/octet-stream')
        )
    except Exception as e:
        print("Dosya indirme hatası:", e)
        abort(500, "Dosya indirilemiyor.")

@app.route('/')
def index():
    gallery = get_gallery_items()
    html = generate_index_html(gallery)
    return Response(html, mimetype='text/html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return redirect(url_for('index'))

    upload_errors = []
    for file in files:
        if file and allowed_file(file.filename):
            try:
                cloudinary.uploader.upload(
                    file,
                    resource_type="auto",
                    folder="wedding2025"
                )
            except Exception as e:
                print(f"Cloudinary yükleme hatası: {e}")
                upload_errors.append(file.filename)

    message = "Bazı dosyalar yüklenemedi: " + ", ".join(upload_errors) if upload_errors else "Dosyalar başarıyla yüklendi."

    gallery = get_gallery_items()
    html = generate_index_html(gallery, message=message)
    return Response(html, mimetype='text/html')

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Geçersiz veri!'}), 400

    public_id = data.get('public_id')
    password = data.get('password')
    resource_type = data.get('resource_type', 'image')

    if not password:
        return jsonify({'success': False, 'message': 'Şifre gerekli!'}), 400

    if password != '1234':  # Burada şifreyi istediğin gibi değiştirebilirsin
        return jsonify({'success': False, 'message': 'Şifre hatalı!'}), 403

    if not public_id:
        return jsonify({'success': False, 'message': 'Silinecek dosya belirtilmedi!'}), 400

    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Silme hatası: {e}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
