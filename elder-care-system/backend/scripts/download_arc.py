import urllib.request
import zipfile
import os
import sys

def download_and_extract():
    url = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
    dest_dir = "C:/elder_care_models/buffalo_l"
    zip_path = "C:/elder_care_models/buffalo_l.zip"
    
    os.makedirs(dest_dir, exist_ok=True)
    
    if os.path.exists(os.path.join(dest_dir, "w600k_r50.onnx")):
        print("Model already exists.")
        return

    print("Downloading buffalo_l.zip (342MB)...")
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"Download error: {e}")
        sys.exit(1)
        
    print("Extracting...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_dir)
        print("Done extraction.")
        os.remove(zip_path)
    except Exception as e:
        print(f"Extraction error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_and_extract()
