
import requests
import json
import time
import sys

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Default URLs
LOCALHOST_URL = "http://localhost:8000/aibattle"
NGROK_URL = "https://36f95614ec93.ngrok-free.app/aibattle"

def get_api_url():
    print(f"{CYAN}Select API Endpoint:{RESET}")
    print(f"1. Localhost ({LOCALHOST_URL})")
    print(f"2. Ngrok ({NGROK_URL})")
    print(f"3. Custom URL")
    
    choice = input(f"{YELLOW}Enter choice (1/2/3) [Default: 1]: {RESET}").strip()
    
    if choice == "2":
        return NGROK_URL
    elif choice == "3":
        return input(f"{YELLOW}Enter full API URL: {RESET}").strip()
    else:
        return LOCALHOST_URL

def get_user_input():
    print(f"{CYAN}=== Interactive AI Judge Tester ==={RESET}")
    print("Test your API with any PDF and Questions.\n")
    
    # 1. Get PDF URL
    while True:
        pdf_url = input(f"{YELLOW}Enter PDF URL (or press Enter for default dummy PDF): {RESET}").strip()
        if not pdf_url:
            pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            print(f"Using default: {pdf_url}")
        
        if pdf_url.startswith("http"):
            break
        print(f"{RED}Invalid URL. Must start with http:// or https://{RESET}")

    # 2. Get Questions
    questions = []
    print(f"\n{YELLOW}Enter Questions (Press Enter without typing to finish):{RESET}")
    while True:
        q = input(f"Question {len(questions) + 1}: ").strip()
        if not q:
            if not questions:
                print(f"{RED}You must enter at least one question!{RESET}")
                continue
            break
        questions.append(q)

    return pdf_url, questions

def run_test():
    app_url = get_api_url()
    pdf_url, questions = get_user_input()
    
    payload = {
        "pdf_url": pdf_url,
        "questions": questions
    }
    
    print("\n" + "-" * 50)
    print(f"{CYAN}Sending Payload to Judge (API)...{RESET}")
    print(json.dumps(payload, indent=2))
    print("-" * 50)

    start_time = time.time()
    try:
        print("Waiting for response... (Timeout: 120s)")
        response = requests.post(app_url, json=payload, timeout=120)
        response_time_ms = (time.time() - start_time) * 1000
    except Exception as e:
        print(f"{RED}❌ REQUEST FAILED: {str(e)}{RESET}")
        return

    # Results Analysis
    print("\n" + "-" * 50)
    print(f"{CYAN}JUDGE VERIFICATION REPORT{RESET}")
    print("-" * 50)

    # 1. Status Check
    if response.status_code != 200:
        print(f"{RED}❌ FAILED Status Code: {response.status_code}{RESET}")
        print(f"Response: {response.text}")
        return
    else:
        print(f"{GREEN}✅ HTTP 200 OK{RESET}")

    # 2. JSON & Schema Check
    try:
        data = response.json()
        print(f"\n{CYAN}Received Response:{RESET}")
        print(json.dumps(data, indent=2))
        
        errors = []
        if not isinstance(data, dict) or "answers" not in data:
            errors.append("Missing 'answers' key or root is not dict")
        elif not isinstance(data["answers"], list):
            errors.append("'answers' is not a list")
        elif len(data["answers"]) != len(questions):
            errors.append(f"Answer count mismatch (Expected {len(questions)}, Got {len(data['answers'])})")
        else:
            for i, ans in enumerate(data["answers"]):
                if not isinstance(ans, str):
                    errors.append(f"Answer [{i}] is not a string")

        if errors:
            print(f"\n{RED}❌ JUDGING CRITERIA FAILED:{RESET}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"\n{GREEN}✅ ALL CHECKS PASSED{RESET}")
            print(f"  - Response Time: {response_time_ms:.2f} ms")
            
            # Show QA Pairs
            print(f"\n{YELLOW}Q&A Review:{RESET}")
            for i, (q, a) in enumerate(zip(questions, data["answers"])):
                print(f"Q{i+1}: {q}")
                print(f"A{i+1}: {a}\n")

    except json.JSONDecodeError:
        print(f"{RED}❌ RESPONSE IS NOT JSON{RESET}")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
