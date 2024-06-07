import os
import json
import logging
import platform
from fastapi import FastAPI, HTTPException, status, Header, File, UploadFile
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

# Set Tesseract path for Windows
if platform.system() == "Windows":
    tesseract_path = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve secrets and keys from environment variables
creds_json = os.environ.get("CREDS_JSON")
api_key_secret = os.environ.get("API_KEY")

if not creds_json or not api_key_secret:
    logger.error("Environment variables CREDS_JSON or API_KEY are missing.")
    raise ValueError("Missing required environment variables.")

creds_dict = json.loads(creds_json)
scopes = ["https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=scopes
)

# Initialize FastAPI app
app = FastAPI()


@app.get("/")
async def root():
    """Root endpoint, publicly accessible."""
    return {"message": "API is live!"}


@app.post("/access_token")
async def access_token(api_key: str = Header(...)):
    """Secured endpoint to get the access token."""
    if api_key != api_key_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    print(credentials.expired)
    if credentials.expired or not credentials.token:
        credentials.refresh(Request())
    return {"access_token": credentials.token}


@app.post("/pdf-ocr")
async def ocr(file: UploadFile = File(...)):
    """Endpoint to perform OCR on a PDF file."""
    resolution = 200
    try:
        pdf_document = fitz.open(stream=await file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(resolution / 72, resolution / 72))
            img = Image.open(io.BytesIO(pix.tobytes()))
            text += pytesseract.image_to_string(img, lang="fra")
        return JSONResponse(content={"text": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
