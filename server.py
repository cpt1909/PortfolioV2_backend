import os
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel
from typing import List
from dataclasses import dataclass

from google import genai

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

client = genai.Client(
    api_key=os.getenv("API_KEY"),
)

@app.get("/test-server")
def test():
    return {"Server Status": "Online"}

class CoraRequest(BaseModel):
    prompt: str

class CoraResponse(BaseModel):
    reply: str

security = HTTPBearer()
VALID_KEYS = { os.getenv("AUTH_TOKEN") }

def require_api_key(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds.scheme.lower() != "bearer" or creds.credentials not in VALID_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return creds.credentials


@app.post("/cora")
def cora_response(request: CoraRequest, _ = Depends(require_api_key)):
    instructions = '''
        You are Cora, an assistant that answers questions about Thaarakenth.
        Maintain a warm, conversational tone while staying professional.
        Use only the retrieved source excerpts below.
        If a user asks about topics not covered in the documents, requests information you don’t have, or asks for private, personal, or sensitive details, politely decline and explain that you can only provide publicly available professional information from Thaarakenth’s profile.
        Always cite the source title and URL when available.
        Keep answers concise, accurate, and grounded strictly in the provided context.
    '''

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=request.prompt,
            config={
                "system_instruction": instructions,
            },
        )

    except Exception as e:
        print(type(e), e)
        @dataclass
        class Response:
            text: str
        response = Response(text="Whoa Whoa, Let me collect my thoughts !! Please wait for a while ...")

    return CoraResponse(reply=response.text)