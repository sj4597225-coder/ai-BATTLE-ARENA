import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api"
PDF_URL = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

def test_chat_flow():
    session_id = f"test-{uuid.uuid4()}"
    print(f"Testing with Session ID: {session_id}")
    
    # 1. First question (Initialize context)
    print("Sending first question...")
    response = requests.post(
        f"{BASE_URL}/chat/pdf",
        json={
            "session_id": session_id,
            "pdf_url": PDF_URL,
            "message": "What is the content of this document?"
        }
    )
    
    if response.status_code == 200:
        print("Response 1:", response.json()['message'])
    else:
        print("Error 1:", response.text)
        return

    # 2. Second question (Conversational context)
    print("\nSending second question (follow-up)...")
    response = requests.post(
        f"{BASE_URL}/chat/pdf",
        json={
            "session_id": session_id,
            "pdf_url": PDF_URL,
            "message": "Can you summarize that in one sentence?"
        }
    )
    
    if response.status_code == 200:
        print("Response 2:", response.json()['message'])
        history_len = response.json().get('conversation_length', 0)
        print(f"Conversation Length: {history_len} (Expected: >2)")
    else:
        print("Error 2:", response.text)

if __name__ == "__main__":
    try:
        test_chat_flow()
    except Exception as e:
        print(f"Verification failed: {e}")
