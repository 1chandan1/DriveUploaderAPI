from fastapi import FastAPI, HTTPException, status, Request, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
import time
import json
import os
import asyncio

# Your secrets and keys
creds_json = os.environ['CREDS_JSON']
api_key_secret = os.environ['API_KEY']

creds_dict = json.loads(creds_json)
scopes = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=scopes)

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def refresh_token():
    request = GoogleRequest()
    credentials.refresh(request)

# Background task to refresh the token every hour
async def refresh_token_background():
    while True:
        await asyncio.sleep(1200)
        refresh_token()

@app.on_event("startup")
async def startup_event():
    refresh_token()  # Refresh the token on startup
    asyncio.create_task(refresh_token_background())  # Start the background task

# Default root endpoint, publicly accessible
@app.get("/")
@app.head("/")
async def root():
    return {"message": "API is live!"}

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Identify the application
    app_identifier = request.headers.get('App-Identifier', 'unknown')

    log_details = {
        "app": app_identifier,
        "path": request.url.path,
        "method": request.method,
        "duration": duration,
        "timestamp": time.time()
    }

    with open("request_logs.json", "a") as log_file:
        json.dump(log_details, log_file)
        log_file.write("\n")

    return response

# Endpoint to get the logs
@app.get("/logs")
async def get_logs():
    with open("request_logs.json", "r") as log_file:
        logs = log_file.readlines()
        return [json.loads(log) for log in logs]

# Secured endpoint to get the access token
@app.get("/get_access_token")
def get_access_token(api_key: str = Header(...)):
    if api_key != api_key_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    access_token = credentials.token
    return {"access_token": access_token}

@app.get("/dashboard")
async def dashboard():
    return FileResponse("index.html")
