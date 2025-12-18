import logging
import httpx
from typing import Optional
from urllib.parse import urlencode
from app.utils.logger import correlation_id_var

logger = logging.getLogger("api-gateway")

class OrchestratorClient:
    def __init__(self, base_url: str, 
        http_client: Optional[httpx.AsyncClient] = None,
        timeout_s: float = 30.0
    ) -> None:
        
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or httpx.AsyncClient(follow_redirects=True)
        self.timeout_s = timeout_s

    def _build_headers(self) -> dict:
        """Adds X-Correlation-ID reading correlation_id_var"""
        corr_id = correlation_id_var.get()
        return {"X-Correlation-ID": corr_id} if corr_id else {}
    
    async def proxy_request(
        self,
        method: str, 
        path: str, 
        query_params: Optional[dict] = None,
        headers: Optional[dict] = None,
        body: Optional[bytes] = None
    ) -> httpx.Response:
        """Proxy request to the Orchestrator API"""

        url = f"{self.base_url}{path}"
        if query_params:    
            query_string = urlencode(query_params)
            url = f"{url}?{query_string}"
        
        base_headers = self._build_headers()
        if headers:
            base_headers.update(headers)
        
        try:
            # For multipart/form-data, we need to use content=body to preserve the raw encoding
            # httpx will use the Content-Type header we provide
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=base_headers,
                content=body if body else None,
                timeout=self.timeout_s
            )
            
            logger.info(
                "orchestrator.proxy.request",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except httpx.TimeoutException:
            logger.error(
                "orchestrator.proxy.timeout",
                extra={
                    "method": method,
                    "path": path,
                    "timeout_s": self.timeout_s
                }
            )
            raise
        except Exception as e:
            logger.error(
                "orchestrator.proxy.error",
                extra={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise