"""
PDF Processing Module
Handles PDF download from URLs and text extraction
"""
import os
import tempfile
import requests
import pdfplumber
from typing import Optional
from pathlib import Path


class PDFProcessor:
    """Handles PDF downloading and text extraction"""
    
    def __init__(self, max_size_mb: int = 50, timeout: int = 30):
        """
        Initialize PDF processor
        
        Args:
            max_size_mb: Maximum PDF file size in MB
            timeout: Request timeout in seconds
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.timeout = timeout
        
    def download_pdf(self, url: str) -> str:
        """
        Download PDF from URL to temporary file
        
        Args:
            url: PDF URL to download
            
        Returns:
            Path to downloaded PDF file
            
        Raises:
            ValueError: If URL is invalid or file is too large
            requests.RequestException: If download fails
        """
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL: must start with http:// or https://")

        # Handle Google Drive URLs
        if 'drive.google.com' in url and '/view' in url:
            file_id = url.split('/d/')[1].split('/')[0]
            url = f'https://drive.google.com/uc?export=download&id={file_id}'

        
        # Send HEAD request to check file size
        try:
            head_response = requests.head(url, timeout=self.timeout, allow_redirects=True)
            content_length = head_response.headers.get('content-length')
            
            if content_length and int(content_length) > self.max_size_bytes:
                raise ValueError(f"PDF file too large: {int(content_length) / (1024*1024):.2f} MB")
        except requests.RequestException as e:
            # If HEAD fails, continue with GET (some servers don't support HEAD)
            pass
        
        # Download PDF
        response = requests.get(url, timeout=self.timeout, stream=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
            raise ValueError(f"URL does not point to a PDF file (content-type: {content_type})")
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        total_size = 0
        
        try:
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size > self.max_size_bytes:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    raise ValueError(f"PDF file too large: exceeded {self.max_size_bytes / (1024*1024):.2f} MB")
                temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF cannot be read or is empty
        """
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF file not found: {pdf_path}")
        
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF file is empty (no pages)")
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                raise ValueError("PDF contains no extractable text")
            
            return full_text
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def process_pdf_url(self, url: str) -> tuple[str, str]:
        """
        Download PDF from URL and extract text
        
        Args:
            url: PDF URL
            
        Returns:
            Tuple of (pdf_path, extracted_text)
        """
        pdf_path = self.download_pdf(url)
        
        try:
            text = self.extract_text(pdf_path)
            return pdf_path, text
        except Exception as e:
            # Clean up downloaded file on error
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
            raise
    
    @staticmethod
    def cleanup(pdf_path: str):
        """
        Delete temporary PDF file
        
        Args:
            pdf_path: Path to PDF file to delete
        """
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except Exception:
                pass  # Ignore cleanup errors
