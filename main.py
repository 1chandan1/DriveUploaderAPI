import asyncio
import base64
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from google.oauth2 import service_account
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
from google.auth.transport.requests import Request
from fastapi import FastAPI, HTTPException, status, Header, File, UploadFile
from PIL import Image
import fitz  # PyMuPDF
import io

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

# Retrieve secrets and keys from environment variables
creds_json = os.environ.get("CREDS_JSON")
api_key_secret = os.environ.get("API_KEY")
gpt_key = os.environ.get("GPT_KEY")
openai_client = OpenAI(api_key=gpt_key)


creds_dict = json.loads(creds_json)
scopes = ["https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=scopes
)

# Initialize FastAPI app
app = FastAPI()

# Initialize ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)


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


def get_image_result(base64_image):
    prompt = """
    get dob and dod from the deah cirtificate
    if not found then ""
    json
    {
        "dob": (dd/mm/yyyy),
        "dod": (dd/mm/yyyy)
    }
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )
    result = eval(response.choices[0].message.content)
    return result


def get_dates_with_gpt(file_data: bytes, resolution: int = 200) -> str:
    try:
        pdf_document = fitz.open(stream=file_data, filetype="pdf")
        page = pdf_document.load_page(0)  # Process only the first page
        pix = page.get_pixmap(matrix=fitz.Matrix(resolution / 72, resolution / 72))
        img = Image.open(io.BytesIO(pix.tobytes()))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        response = get_image_result(img_str)
        return response
    except Exception as e:
        raise


@app.post("/pdf-ocr-gpt")
async def ocr(file: UploadFile = File(...)):
    """Endpoint to perform OCR on a PDF file and extract DOB and DOD."""
    file_data = await file.read()
    try:
        loop = asyncio.get_running_loop()
        dates = await loop.run_in_executor(None, get_dates_with_gpt, file_data)
        return JSONResponse(content=dates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
