from pathlib import Path
from PIL import Image
import zipfile
import requests

""" Generate image thumbnails and compress session locally """

SERVER_URL = "http://your-server-ip:5000/api/sessions/upload"

def process_and_upload_session(session_id: int, local_session_dir: Path):
    thumbnails_dir = local_session_dir / "thumbnails"
    thumbnails_dir.mkdir(exist_ok=True)
    
    zip_path = local_session_dir.parent / f"session_{session_id}.zip"
    
    thumbnail_files = []
    
    # Compress raw images into a zip and generate thumbnails locally
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for img_path in local_session_dir.glob("*.jpg"):
            # zip 
            zf.write(img_path, arcname=img_path.name)
            
            # 960x540 thumbnail 
            with Image.open(img_path) as img:
                img_thumb = img.resize((960, 540), Image.Resampling.LANCZOS)
                thumb_path = thumbnails_dir / f"thumb_{img_path.name}"
                img_thumb.save(thumb_path, "JPEG", quality=85)
                thumbnail_files.append(thumb_path)

    #  Upload thumbnails & session zip one HTTP request
    files = {"archive": open(zip_path, "rb")}
    for t_path in thumbnail_files:
        files.add(("thumbnails", open(t_path, "rb")))
        
    data = {"session_id": session_id}
    response = requests.post(SERVER_URL, data=data, files=files)
    
    if response.status_code == 201:
        print("Upload successful! Clearing local Pi staging directory...")
        for img_path in local_session_dir.glob("*.jpg"):
            img_path.unlink()