import time
from pathlib import Path
import requests
from session_helper import package_session_files

SERVER_URL = "http://192.168.1.50:5000"
DEVICE_ID = "observatory_pi_1"
is_active = False

LOCAL_STAGING_DIR = Path("/home/pi/observatory_staging/current_session")

def capture_photos(duration, interval):
    """Simulates or executes camera capture, saving raw frames locally."""
    global is_active
    is_active = True
    
    if LOCAL_STAGING_DIR.exists():
        for f in LOCAL_STAGING_DIR.glob("*"):
            if f.is_file(): f.unlink()
    LOCAL_STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting session capture: duration={duration}s, interval={interval}s")
    
    start_time = time.time()
    frame_count = 0
    try:
        while time.time() - start_time < duration:
            frame_count += 1
            frame_path = LOCAL_STAGING_DIR / f"frame_{int(time.time())}_{frame_count:03d}.jpg"
            
            # --- CAMERA CAPTURE GOES HERE ---
            from PIL import Image
            mock_img = Image.new("RGB", (3840, 2160), color=(20, 20, 40))
            mock_img.save(frame_path, "JPEG")
            # ---------------------------------
            
            print(f"Captured frame {frame_count} -> {frame_path.name}")
            time.sleep(interval)
            
    finally:
        is_active = False
        print("Session capture completed.")

def upload_session(session_id, zip_path, thumbnail_files):
    """Handles the actual network POST request to upload files to the server."""
    upload_url = f"{SERVER_URL}/api/sessions/upload"
    
    files = [
        ("archive", (zip_path.name, open(zip_path, "rb"), "application/zip"))
    ]
    
    file_handles = [files[0][1][1]]
    for t_path in thumbnail_files:
        f = open(t_path, "rb")
        file_handles.append(f)
        files.append(("thumbnails", (t_path.name, f, "image/jpeg")))
        
    data = {"session_id": session_id}
    
    try:
        print(f"Uploading session {session_id} package to server...")
        response = requests.post(upload_url, data=data, files=files, timeout=60)
        
        if response.status_code == 201:
            print("Session successfully uploaded and registered!")
            return True
        else:
            print(f"Server rejected upload: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Network error during upload: {e}")
        return False
        
    finally:
        for f in file_handles:
            f.close()

def main():
    print(f"Raspberry Pi worker started. Polling server at {SERVER_URL}...")
    
while True:
        try:
            response = requests.get(API_URL)
            data = response.json()
            
            if data.get("status") != "idle" and "id" in data:
                print(f"Starting job {data['id']}...")
                execute_imaging_session(data)
                continue 

            next_scheduled_str = data.get("next_scheduled_for")
            if next_scheduled_str:
                next_dt = datetime.fromisoformat(next_scheduled_str.replace("Z", "+00:00"))
                now_utc = datetime.now(timezone.utc)
                
                seconds_until_job = (next_dt - now_utc).total_seconds()
                
                sleep_time = max(1, min(seconds_until_job, 60))
                print(f"Next job in {int(seconds_until_job)}s. Sleeping for {int(sleep_time)}s...")
                time.sleep(sleep_time)
                continue

        except Exception as e:
            print(f"Polling error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()