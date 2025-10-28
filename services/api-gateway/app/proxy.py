from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
import os
import httpx
from urllib.parse import urlencode

client = httpx.AsyncClient(follow_redirects=True)

load_dotenv()

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:3003")


router = APIRouter(tags=["proxy"])


@router.api_route("/api/{path:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH"])
async def proxy_api(path:str, request: Request):

    base_url = f"{ORCHESTRATOR_URL}/api/{path}"
    if request.query_params:
        query_string = urlencode(request.query_params)
        URL_destiny = f"{base_url}?{query_string}"
    else:
        URL_destiny = base_url

    method = request.method
    headers = dict (request.headers)

    headers.pop("host", None)
    headers.pop("content-length", None)

    body = await request.body()

    try:
        response = await client.request(
            method, 
            URL_destiny, 
            headers=headers, 
            content=body
            )

        return Response(
            content = response.content,
            status_code = response.status_code,
            headers = dict(response.headers)
        )
    
    except Exception as e:
        return Response (
            content = f"Proxy error: {str(e)}",
            status_code=502
        )
