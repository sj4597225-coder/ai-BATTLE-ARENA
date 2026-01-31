# AI PDF Question Answering System

**Pure JSON API** for answering questions from PDF documents using DeepSeek AI model via Ollama.

## 🚀 Features

- ✅ Accept PDF URLs and extract text automatically
- ✅ Process multiple questions (1-20) in a single request
- ✅ Strict JSON input/output format
- ✅ Local AI processing using DeepSeek via Ollama
- ✅ Comprehensive error handling
- ✅ Auto-generated API documentation
- ✅ Health check endpoints

## 📋 Requirements

- Python 3.8+
- Ollama installed and running
- DeepSeek model pulled in Ollama

## 🛠️ Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install and Setup Ollama

Download Ollama from: https://ollama.ai

Pull DeepSeek model:
```bash
ollama pull deepseek-r1:latest
```

Verify Ollama is running:
```bash
ollama list
```

### 3. Start the Server

```bash
cd backend
uvicorn app:app --reload --port 8000
```

Server will start at: `http://localhost:8000`

## 📖 API Documentation

### Interactive Docs
Visit `http://localhost:8000/docs` for Swagger UI with interactive testing.

### Endpoints

#### `POST /api/answer`
Main endpoint for PDF question answering.

**Request:**
```json
{
  "pdf_url": "https://example.com/document.pdf",
  "questions": [
    "What is the main topic of this document?",
    "Who are the authors?",
    "What are the key findings?"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total_questions": 3,
  "answers": [
    {
      "question_number": 1,
      "question": "What is the main topic of this document?",
      "answer": "The document discusses artificial intelligence and machine learning techniques...",
      "status": "success"
    },
    {
      "question_number": 2,
      "question": "Who are the authors?",
      "answer": "The authors are John Doe and Jane Smith from MIT.",
      "status": "success"
    },
    {
      "question_number": 3,
      "question": "What are the key findings?",
      "answer": "The key findings include improved accuracy of 95% and reduced processing time...",
      "status": "success"
    }
  ],
  "model_used": "deepseek-r1:latest",
  "pdf_processed": true
}
```

#### `GET /api/health`
Check system health and model availability.

**Response:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "model": "deepseek-r1:latest",
  "model_available": true,
  "message": "System operational"
}
```

#### `GET /api/models`
List available Ollama models.

## 💻 Usage Examples

### Using cURL

```bash
curl -X POST http://localhost:8000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf",
    "questions": [
      "What is the title of this paper?",
      "What methodology is used?"
    ]
  }'
```

### Using Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/answer',
    json={
        'pdf_url': 'https://example.com/document.pdf',
        'questions': [
            'What is this document about?',
            'What are the main conclusions?'
        ]
    }
)

result = response.json()
print(result)
```

### Using Postman

1. Create a new POST request to `http://localhost:8000/api/answer`
2. Set header: `Content-Type: application/json`
3. Add JSON body with `pdf_url` and `questions`
4. Send request and view JSON response

## ⚙️ Configuration

### Model Selection

To use a different Ollama model, edit `backend/ai_handler.py`:

```python
ai_handler = AIHandler(model_name="your-model-name")
```

### PDF Size Limit

Default: 50MB. To change, edit `backend/app.py`:

```python
pdf_processor = PDFProcessor(max_size_mb=100, timeout=60)
```

### Question Limits

Default: 1-20 questions. To change, edit the `QuestionRequest` model in `backend/app.py`.

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Test with Sample PDF
```bash
curl -X POST http://localhost:8000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "questions": ["What is this document?"]
  }'
```

## 🐛 Troubleshooting

### "Model not available" error
- Ensure Ollama is running: `ollama list`
- Pull the model: `ollama pull deepseek-r1:latest`
- Check model name matches in `ai_handler.py`

### "Failed to download PDF" error
- Verify PDF URL is accessible
- Check internet connection
- Ensure URL points to a valid PDF file
- Check if PDF size is under limit (default 50MB)

### "Failed to extract text" error
- PDF may be image-based (scanned document)
- PDF may be encrypted or password-protected
- Try a different PDF

### Connection refused
- Ensure backend server is running
- Check port 8000 is not in use
- Verify firewall settings

## 📁 Project Structure

```
E:\AI modal\
├── backend/
│   ├── app.py              # Main FastAPI application
│   ├── pdf_processor.py    # PDF download and text extraction
│   ├── ai_handler.py       # DeepSeek AI integration
│   └── requirements.txt    # Python dependencies
├── README.md               # This file
└── .gitignore             # Git ignore patterns
```

## 🔒 Security Notes

- This is a development setup. For production:
  - Add authentication/authorization
  - Implement rate limiting
  - Use environment variables for configuration
  - Add input sanitization
  - Configure CORS properly
  - Use HTTPS

## 📝 License

MIT License - Feel free to use and modify.

## 🤝 Contributing

Contributions welcome! Please test thoroughly before submitting PRs.

---

**Built with FastAPI, pdfplumber, and Ollama DeepSeek** 🚀
