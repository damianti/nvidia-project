from fastapi import HTTPException
import httpx
from typing import Optional
import logging
from app.utils.logger import correlation_id_var
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)

class AuthClient:
    def __init__(self, base_url: str, http_client: Optional[httpx.AsyncClient] = None, timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or httpx.AsyncClient(follow_redirects=True)
        self.timeout_s = timeout_s

    def _build_headers(self) -> dict:
        """Adds X-Correlation-ID reading correlation_id_var"""
        corr_id = correlation_id_var.get()
        return {"X-Correlation-ID": corr_id} if corr_id else {}

    async def login(self, login_data: dict) -> httpx.Response:
        try:
            response = await self.http_client.request(
                method="POST",
                url=f"{self.base_url}/auth/login",
                headers=self._build_headers(),
                json=login_data,
                timeout=self.timeout_s
            )
            logger.info(
                "auth.client.request",
                extra={
                    "status_code": response.status_code,
                    "method": "POST",
                    "path": "/auth/login"
                }
            )
            
            return response

        except httpx.TimeoutException:
            logger.error(
                "auth.proxy.timeout",
                extra={
                    "timeout_s": self.timeout_s
                }
            )
            raise
        except Exception as e:
            logger.error(
                "auth.proxy.error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    async def signup(self,signup_data: dict) -> httpx.Response:
        try:
            response = await self.http_client.request(
                method="POST",
                url=f"{self.base_url}/auth/signup",
                headers=self._build_headers(),
                json=signup_data,
                timeout=self.timeout_s
            )
            logger.info(
                "auth.client.request",
                extra={
                    "status_code": response.status_code,
                    "method": "POST",
                    "path": "/auth/signup"
                }
            )
            
            return response

        except httpx.TimeoutException:
            logger.error(
                "auth.proxy.timeout",
                extra={
                    "timeout_s": self.timeout_s
                }
            )
            raise
        except Exception as e:
            logger.error(
                "auth.proxy.error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
        
    
    async def get_current_user(self, authorization_header: str, cookies: Optional[dict] = None) -> httpx.Response:
        try:
            headers = {"Authorization": authorization_header}
            headers.update(self._build_headers())
            
            # Build cookies string if provided
            cookies_dict = {}
            if cookies:
                cookies_dict = cookies
            
            response = await self.http_client.request(
                method="GET",
                url=f"{self.base_url}/auth/me",
                headers=headers,
                cookies=cookies_dict,
                timeout=self.timeout_s
            )
            logger.info(
                "auth.client.request",
                extra={
                    "status_code": response.status_code,
                    "method": "GET",
                    "path": "/auth/me"
                }
            )
            
            return response

        except httpx.TimeoutException:
            logger.error(
                "auth.proxy.timeout",
                extra={
                    "timeout_s": self.timeout_s
                }
            )
            raise
        except Exception as e:
            logger.error(
                "auth.proxy.error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise

    async def verify_token(self):
        pass
    
    async def logout(self, token: str, cookies: Optional[dict] = None) -> httpx.Response:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            headers.update(self._build_headers())
            
            cookies_dict = {}
            if cookies:
                cookies_dict = cookies
            
            response = await self.http_client.request(
                method="POST",
                url=f"{self.base_url}/auth/logout",
                headers=headers,
                cookies=cookies_dict,
                timeout=self.timeout_s
            )
            logger.info(
                "auth.client.request",
                extra={
                    "status_code": response.status_code,
                    "method": "POST",
                    "path": "/auth/logout"
                }
            )
            
            return response

        except httpx.TimeoutException:
            logger.error(
                "auth.proxy.timeout",
                extra={
                    "timeout_s": self.timeout_s
                }
            )
            raise
        except Exception as e:
            logger.error(
                "auth.proxy.error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
