import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from fastapi import FastAPI, HTTPException, status, Header

# Retrieve secrets and keys from environment variables
creds_json = os.environ.get("CREDS_JSON")
secret_pass = os.environ.get("SECRET_PASS")

creds_dict = json.loads(creds_json)
scopes = ["https://www.googleapis.com/auth/drive"]
credentials = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=scopes
)
 
# Initialize FastAPI app
app = FastAPI()

@app.head("/")
@app.get("/")
async def root():
    """Root endpoint, publicly accessible."""
    return "API is live!"

@app.post("/access-token")
async def access_token(password: str = Header(...)):
    """Secured endpoint to get the access token."""
    if password != secret_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Password",
        )
    print(credentials.expired)
    if credentials.expired or not credentials.token:
        credentials.refresh(Request())
    return {"access_token": credentials.token}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
