import os
import json
import logging
import platform
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Header, File, UploadFile
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
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

def refresh_token():
    """Refresh the Google service account token."""
    request = GoogleRequest()
    try:
        credentials.refresh(request)
        logger.info("Access token refreshed successfully.")
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}")

async def refresh_token_background():
    """Background task to refresh the token periodically."""
    while True:
        if credentials.expiry:
            now = datetime.utcnow()
            time_to_expiry = (credentials.expiry - now).total_seconds()
            sleep_time = max(0, time_to_expiry - 300)  # Refresh 5 minutes before expiry
        else:
            sleep_time = 1200  # Default to 20 minutes if no expiry is set
        await asyncio.sleep(sleep_time)
        refresh_token()

async def lifespan(app: FastAPI):
    """Run tasks at application startup and shutdown."""
    refresh_token()  # Refresh the token on startup
    background_task = asyncio.create_task(refresh_token_background())  # Start the background task
    yield
    background_task.cancel()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    """Root endpoint, publicly accessible."""
    return {"message": "API is live!"}

@app.get("/get_access_token")
def get_access_token(api_key: str = Header(...)):
    """Secured endpoint to get the access token."""
    if api_key != api_key_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
