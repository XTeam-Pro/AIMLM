import httpx
import os
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils import filter_openai_response
from app.api.deps import get_current_user
from app.models import User, QueryLog
from app.core.db import engine
from sqlmodel import Session
import json

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/openai", tags=["OpenAI"])

user_request_count = {}

REQUEST_LIMIT = 10 
TIME_WINDOW = 60  

class UserQueryRequest(BaseModel):
    query: str
    context: Optional[str] = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

if not OPENAI_API_KEY:
    raise ValueError("🔴 API Key OpenAI not found!")

async def call_openai_api(query: str, context: Optional[str] = None):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if context:
        messages.append({"role": "user", "content": context})
    messages.append({"role": "user", "content": query})

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.5,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                except Exception:
                    raise HTTPException(status_code=500, detail="Invalid response from OpenAI API")

                if "error" in error_data:
                    error_message = error_data["error"].get("message", "Unknown error from OpenAI API")

                    if response.status_code == 401:
                        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key.")
                    elif response.status_code == 429:
                        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
                    elif response.status_code == 500:
                        raise HTTPException(status_code=500, detail="OpenAI server error. Please try again later.")
                    else:
                        raise HTTPException(status_code=response.status_code, detail=error_message)

                raise HTTPException(status_code=response.status_code, detail="OpenAI API returned an error")

            response_data = response.json()
            if "choices" not in response_data:
                raise HTTPException(status_code=500, detail="OpenAI API response is missing choices")

            return response_data

    except httpx.HTTPStatusError as http_err:
        raise HTTPException(status_code=http_err.response.status_code, detail="OpenAI API error")

    except httpx.RequestError as req_err:
        raise HTTPException(status_code=500, detail="Request to OpenAI API failed")

    except Exception as err:
        raise HTTPException(status_code=500, detail="Internal Server Error")

def is_rate_limited(user_id: str) -> bool:
    current_time = time.time()
    if user_id not in user_request_count:
        user_request_count[user_id] = []

    user_request_count[user_id] = [
        t for t in user_request_count[user_id] if t > current_time - TIME_WINDOW
    ]

    if len(user_request_count[user_id]) >= REQUEST_LIMIT:
        return True

    user_request_count[user_id].append(current_time)
    return False

def get_db():
    with Session(engine) as session:
        yield session

@router.post("/query")
async def query_openai(
    request: UserQueryRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.query or request.query.strip() == "":
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    if len(request.query) > 500:
        raise HTTPException(status_code=400, detail="Query too long max only 500 characters.")

    user_id = str(current_user.id)
    if is_rate_limited(user_id):
        raise HTTPException(status_code=429, detail="Too much request. Please Try again later.")

    try:
        response = await call_openai_api(request.query, request.context)

        assistant_response = filter_openai_response(response)

        response_text = assistant_response.get("response", "")

        if len(response_text) > 5000:
            truncated_response = response_text[:5000] 
            warning_message = "Response too long max only 5000 characters."

            query_log = QueryLog(
                user_id=current_user.id,
                query=request.query,
                response=truncated_response,
            )
            db.add(query_log)
            db.commit()
            db.refresh(query_log)

            return {
                "query": request.query,
                "response": truncated_response,
                "warning": warning_message
            }

        query_log = QueryLog(
            user_id=current_user.id,
            query=request.query,
            response=response_text,
        )
        db.add(query_log)
        db.commit()
        db.refresh(query_log)

        return {"query": request.query, "response": response_text}

    except HTTPException as http_err:
        raise http_err  
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/history")
async def get_query_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ambil semua riwayat percakapan berdasarkan user_id
    history = db.query(QueryLog).filter(QueryLog.user_id == current_user.id).order_by(QueryLog.created_at.asc()).all()

    return [
        {
            "id": log.id,
            "query": log.query,
            "response": log.response,
            "created_at": log.created_at
        }
        for log in history
    ]