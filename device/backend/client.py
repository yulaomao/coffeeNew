import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..config import config
from ..constants import HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT, MAX_RETRIES
from ..utils.time import utc_now, iso_format
from .schemas import *

class BackendClient:
    """HTTP client for communicating with management backend"""
    
    def __init__(self):
        self.base_url = config.BACKEND_BASE_URL.rstrip('/')
        self.device_id = config.DEVICE_ID
        self.device_token = config.DEVICE_TOKEN
        self.timeout = httpx.Timeout(
            connect=HTTP_CONNECT_TIMEOUT,
            read=HTTP_READ_TIMEOUT,
            write=HTTP_READ_TIMEOUT,
            pool=HTTP_READ_TIMEOUT
        )
        
        # Default headers
        self.default_headers = {
            "Content-Type": "application/json",
            "X-Device-Id": self.device_id
        }
        
        if self.device_token:
            self.default_headers["X-Device-Token"] = self.device_token
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.default_headers, params=data)
                else:
                    response = await client.request(
                        method, url, 
                        headers=self.default_headers,
                        json=data
                    )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {method} {endpoint}: {e}")
                if e.response.status_code >= 500:
                    raise  # Will be retried
                else:
                    # 4xx errors should not be retried
                    try:
                        error_data = e.response.json()
                        return error_data
                    except:
                        return {"ok": False, "error": {"code": e.response.status_code, "message": str(e)}}
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                logger.error(f"Network error for {method} {endpoint}: {e}")
                raise  # Will be retried
            
            except Exception as e:
                logger.error(f"Unexpected error for {method} {endpoint}: {e}")
                return {"ok": False, "error": {"code": "unknown", "message": str(e)}}
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def register_device(self, location: Optional[str] = None) -> DeviceRegisterResponse:
        """Register device with backend"""
        request_data = DeviceRegisterRequest(
            device_id=self.device_id,
            device_type="coffee_machine",
            firmware_version="1.0.0",
            location=location
        )
        
        response_data = await self._make_request("POST", "/devices/register", request_data.model_dump())
        return DeviceRegisterResponse(**response_data)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def post_status(self, status_data: Dict[str, Any]) -> StatusReportResponse:
        """Post device status to backend"""
        request_data = StatusReportRequest(
            device_id=self.device_id,
            timestamp=utc_now(),
            **status_data
        )
        
        endpoint = f"/devices/{self.device_id}/status"
        response_data = await self._make_request("POST", endpoint, request_data.model_dump())
        return StatusReportResponse(**response_data)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def report_materials(self, bins_data: List[Dict[str, Any]]) -> MaterialReportResponse:
        """Report material levels to backend"""
        bins = [MaterialBinReport(**bin_data) for bin_data in bins_data]
        request_data = MaterialReportRequest(
            device_id=self.device_id,
            bins=bins,
            timestamp=utc_now()
        )
        
        endpoint = f"/devices/{self.device_id}/materials/report"
        response_data = await self._make_request("POST", endpoint, request_data.model_dump())
        return MaterialReportResponse(**response_data)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def get_pending_commands(self) -> PendingCommandsResponse:
        """Get pending commands from backend"""
        endpoint = f"/devices/{self.device_id}/commands/pending"
        response_data = await self._make_request("GET", endpoint)
        return PendingCommandsResponse(**response_data)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def post_command_result(self, command_id: str, status: str, 
                                result_payload: Dict[str, Any],
                                error_message: Optional[str] = None) -> CommandResultResponse:
        """Post command execution result to backend"""
        request_data = CommandResultRequest(
            command_id=command_id,
            status=status,
            result_payload=result_payload,
            result_at=utc_now(),
            error_message=error_message
        )
        
        endpoint = f"/devices/{self.device_id}/command_result"
        response_data = await self._make_request("POST", endpoint, request_data.model_dump())
        return CommandResultResponse(**response_data)
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))
    )
    async def post_order(self, order_data: Dict[str, Any]) -> OrderCreateResponse:
        """Post order to backend"""
        request_data = OrderCreateRequest(
            device_id=self.device_id,
            created_at=utc_now(),
            **order_data
        )
        
        endpoint = f"/devices/{self.device_id}/orders/create"
        response_data = await self._make_request("POST", endpoint, request_data.model_dump())
        return OrderCreateResponse(**response_data)
    
    async def download_file(self, url: str, timeout: int = 300) -> bytes:
        """Download file from URL"""
        download_timeout = httpx.Timeout(connect=10.0, read=timeout)
        
        async with httpx.AsyncClient(timeout=download_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    
    async def test_connection(self) -> bool:
        """Test connection to backend"""
        try:
            # Try to get pending commands as a connectivity test
            response = await self.get_pending_commands()
            return response.ok
        except Exception as e:
            logger.error(f"Backend connectivity test failed: {e}")
            return False

# Global backend client instance
backend_client = BackendClient()