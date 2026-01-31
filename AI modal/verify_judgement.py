
import requests
import json
import time
import sys

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Default URLs
LOCALHOST_URL = "http://localhost:8000/aibattle"
# Updated with user's specific URL
NGROK_URL = "https://1006a1bdf8d3.ngrok-free.app/aibattle"

def get_api_url():
    print(f"{CYAN}Select API Endpoint:{RESET}")
    print(f"1. Localhost ({LOCALHOST_URL})")
    print(f"2. Ngrok ({NGROK_URL})")
    print(f"3. Custom Ngrok URL (Enter manually)")
    
    choice = input(f"{YELLOW}Enter choice (1/2/3) [Default: 2]: {RESET}").strip()
    
    if choice == "1":
        return LOCALHOST_URL
    elif choice == "3":
        url = input(f"{YELLOW}Paste your Ngrok URL (e.g. https://xyz.ngrok-free.app): {RESET}").strip()
        # Remove trailing slash if present
        if url.endswith("/"):
            url = url[:-1]
        # Attach /aibattle if not present
        if not url.endswith("aibattle"):
            url = f"{url}/aibattle"
        return url
    else:
        # Default to Ngrok as requested
        return NGROK_URL

def verify_api():
    app_url = get_api_url()
    print(f"\n{YELLOW}Starting Judge Verification for: {app_url}{RESET}\n")

    # 1. Test Data (matches example from images)
    payload = {
        "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "questions": [
            "What is the content of this document?",
            "Who is the author?",
            "Is this a dummy PDF?"
        ]
    }

    print(f"DTO Payload:\n{json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    # 2. Timing Request
    start_time = time.time()
    try:
        print("Sending request... (May take time for first model load)")
        response = requests.post(app_url, json=payload, timeout=120)
        response_time_ms = (time.time() - start_time) * 1000
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ CONNECTION ERROR: Could not connect to {app_url}{RESET}")
        print("Make sure your server is running (python backend/app.py)")
        if "ngrok" in app_url:
            print("If using Ngrok, make sure to run: ngrok http 8000")
        return
    except Exception as e:
        print(f"{RED}❌ REQUEST FAILED: {str(e)}{RESET}")
        return

    # 3. Status Check
    if response.status_code != 200:
        print(f"{RED}❌ FAILED Status Code: {response.status_code}{RESET}")
        print(f"Response Body: {response.text}")
        return
    else:
        print(f"{GREEN}✅ HTTP 200 OK{RESET}")

    # 4. JSON Validation
    try:
        data = response.json()
        print(f"Response Body:\n{json.dumps(data, indent=2)}")
    except json.JSONDecodeError:
        print(f"{RED}❌ MALFORMED JSON: Response is not valid JSON{RESET}")
        return

    # 5. Schema Validation (Strict)
    # Rule: Output must only contain "answers" which is a List[str]
    
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Root response must be a JSON object (dict)")
    else:
        keys = list(data.keys())
        if "answers" not in keys:
             errors.append("Missing required key: 'answers'")
        elif len(keys) > 1:
            print(f"{YELLOW}⚠️ WARNING: Extra keys found: {keys} (Rules say 'Only include JSON response', schema implies strictness){RESET}")
            
        if "answers" in data:
            answers = data["answers"]
            if not isinstance(answers, list):
                errors.append("'answers' must be a list/array")
            else:
                if len(answers) != len(payload["questions"]):
                    errors.append(f"Mismatch in count. Questions: {len(payload['questions'])}, Answers: {len(answers)}")
                
                for i, ans in enumerate(answers):
                    if not isinstance(ans, str):
                        errors.append(f"Answer at index {i} is not a string (Type: {type(ans)})")

    # 6. Report
    print("-" * 50)
    if errors:
        print(f"{RED}❌ FAILED JUDGING CRITERIA{RESET}")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"{GREEN}✅ PASSED ALL CHECKS{RESET}")
        print(f"  - Format Correctness: 100%")
        print(f"  - Response Time: {response_time_ms:.2f} ms")
        
        # Calculate Mock Score
        # Speed Score = max(0, 100 - response_time_ms / 100)
        speed_score = max(0, 100 - (response_time_ms / 100))
        print(f"  - Speed Score (Approx): {speed_score:.2f} / 100")
        
        print(f"\n{GREEN}Ready for Submission!{RESET}")

if __name__ == "__main__":
    verify_api()
