
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session
import pytest

from app.core.config import settings
from app.utils import filter_openai_response
from unittest.mock import patch

# Test with success req and res
def test_post_query_openai(
        client: TestClient, superuser_token_headers: dict[str,str]
) -> None:
    data ={"query": "who is president of russia ?","context" : "i want to study geography "}
    response = client.post(
        f"{settings.API_V1_STR}/openai/query/",
        headers= superuser_token_headers,
        json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["query"] == data["query"]
    assert "response" in content

# Text post without context
def test_post_query_without_context(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"query": "Who is the president of Russia?","context": ""}  

    response = client.post(
        f"{settings.API_V1_STR}/openai/query/",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code in [200, 400]
    content = response.json()
    assert "query" in content or "detail" in content 

# Test post without query
def test_post_query_without_query(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"query": "","context": "I want to study geography"} 

    response = client.post(
        f"{settings.API_V1_STR}/openai/query/",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 400 
    content = response.json()
    assert "detail" in content

# Test with long query
def test_long_query(client: TestClient, superuser_token_headers: dict[str, str]):
    long_query = "a" * 10_000  # Query dengan 10.000 karakter
    data = {"query": long_query, "context": "Testing long input"}
    
    response = client.post(
        f"{settings.API_V1_STR}/openai/query/",
        headers=superuser_token_headers,
        json=data
    )
    
    assert response.status_code in [200, 400, 413]
    assert "query" in response.json() or "detail" in response.json()

@patch("httpx.AsyncClient.post")
def test_openai_api_timeout(mock_post, client: TestClient, superuser_token_headers: dict[str, str]):
    mock_post.side_effect = Exception("Timeout error")

    data = {"query": "Tell me a joke", "context": "funny"}
    response = client.post(
        f"{settings.API_V1_STR}/openai/query/",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 500

    try:
        content = response.json()
    except ValueError:
        pytest.fail(f"Invalid JSON response: {response.text}")

    # Allow both possible responses for better coverage
    assert "status" in content or "detail" in content, f"Unexpected response: {content}"

    if "status" in content:
        assert content["status"] == "error"
        assert "message" in content, f"Missing 'message' key in response: {content}"
    else:
        assert content["detail"] == "Internal Server Error"

# valid response from filter
def test_valid_response():
    response = {
        "choices": [
            {"message": {"content": "Hello, how can I assist you?"}}
        ]
    }
    result = filter_openai_response(response)
    assert result["status"] == "success"
    assert "Hello, how can I assist you?" in result["response"]
    assert "timestamp" in result

def test_empty_choices():
    response = {"choices": []} 
    result = filter_openai_response(response)
    assert result["status"] == "error"
    assert result["message"] == "Error: No response from OpenAI"

def test_missing_message():
    response = {"choices": [{}]}
    result = filter_openai_response(response)
    assert result["status"] == "error"
    assert result["message"] == "Error: Invalid message format from OpenAI"

def test_empty_content():
    response = {"choices": [{"message": {"content": ""}}]}  
    result = filter_openai_response(response)
    assert result["status"] == "error"
    assert result["message"] == "Error: Empty response from OpenAI"

def test_invalid_response_type():
    response = "not a dict" 
    result = filter_openai_response(response)
    assert result["status"] == "error"
    assert result["message"] == "Error: Invalid response format from OpenAI"
