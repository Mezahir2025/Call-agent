import requests
import json
import base64

def test_chat():
    url = "http://localhost:8080/chat"
    payload = {
        "prompt": "Salam, necəsən? Bu gün hava necədir?"
    }
    
    print(f"Sending request to {url}: {payload}")
    response = None
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "audio" in data:
            print("Success! Received audio data.")
            audio_bytes = base64.b64decode(data["audio"])
            print(f"Audio size: {len(audio_bytes)} bytes")
            
            # Save to file to verify
            with open("response.pcm", "wb") as f:
                f.write(audio_bytes)
            print("Saved audio to response.pcm (Raw PCM)")
        else:
            print("Response received but no audio field:", data)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if response is not None:
             print(f"Status Code: {response.status_code}")
             print(f"Response: {response.text}")

if __name__ == "__main__":
    test_chat()
