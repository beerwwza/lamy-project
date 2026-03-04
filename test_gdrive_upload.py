import urllib.request
import json
import base64

def test_upload():
    url = "https://script.google.com/macros/s/AKfycbxKah-cN1vkOIJyT8CJ0QRVUJQEgpkPGKyh7xBla1rdpCsPbarPIQlc_lpKaYEPlNJ6gw/exec"
    
    # Create a dummy text file content
    dummy_text = "Hello, this is a test file from backend simulation."
    base64_data = base64.b64encode(dummy_text.encode('utf-8')).decode('utf-8')
    
    payload = {
        "filename": "test_upload_script.txt",
        "mimeType": "text/plain",
        "fileData": base64_data
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        print("Sending request to Google Apps Script...")
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"Status Code: {response.getcode()}")
            print(f"Response: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload()
