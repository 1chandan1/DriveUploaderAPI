# Google Drive API Token Generator

## Introduction
This repository hosts a FastAPI application designed to generate and refresh access tokens for the Google Drive API. The API is secured and only accessible using a predefined API key. It's built with automatic token refreshing, request logging, and CORS support for ease of integration.

## Prerequisites
- Python 3.6+
- FastAPI
- Uvicorn or any ASGI server
- A Google Cloud Platform account with a configured service account
- The service account JSON key

## Installation
1. Clone the repository:
git clone https://github.com/1chandan1/DriveUploaderAPI.git

2. Navigate to the project directory:
cd DriveUploaderAPI

3. Install required Python packages:
pip install fastapi uvicorn google-auth

## Configuration
Set the following environment variables:
- `CREDS_JSON`: Your Google service account JSON key.
- `API_KEY`: A secret key to secure your API.

## Running the Application
1. Start the server:
uvicorn main:app --reload
Replace `main` with the name of your Python file if different.

## Usage
- Access the root endpoint at `GET /` to verify if the API is live.
- To view the access logs, visit `GET /logs`.
- For the access token, use `GET /get_access_token` with the API key set in the request header.
- Dashboard available at `GET /dashboard`.

## Security
The `/get_access_token` endpoint is secured with an API key. Ensure to keep your `API_KEY` environment variable secret.

## Contributing
This project is personal and not intended for public contribution. However, suggestions and feedback are welcome.

## License
This project is open-sourced under the MIT License.

## Acknowledgements
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google OAuth2 Client Library](https://google-auth.readthedocs.io/en/latest/)
