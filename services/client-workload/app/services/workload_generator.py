import asyncio
import time
import httpx
import logging
from typing import List, Optional, Dict
from collections import defaultdict
import statistics

from app.schemas.workload import WorkloadRequest, RequestMetrics, WorkloadMetrics, WorkloadPattern
from app.utils.config import SERVICE_NAME, LOAD_BALANCER_URL, SERVICE_DISCOVERY_URL

logger = logging.getLogger(SERVICE_NAME)


class WorkloadGenerator:
    """Generates HTTP load against services"""
    
    def __init__(self):
        self.active_tests: Dict[str, asyncio.Task] = {}
        self.test_metrics: Dict[str, List[RequestMetrics]] = {}
        self.test_configs: Dict[str, WorkloadRequest] = {}
        self.test_status: Dict[str, str] = {}  # running, completed, stopped
        self.test_start_times: Dict[str, float] = {}
    
    async def get_available_services(self) -> List[str]:
        """Get list of available website URLs from Service Discovery"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{SERVICE_DISCOVERY_URL}/services/healthy"
                )
                if response.status_code == 200:
                    data = response.json()
                    services = data.get("services", [])
                    # Extract unique website_urls
                    website_urls = set()
                    for service in services:
                        if service.get("website_url"):
                            website_urls.add(service["website_url"])
                    return list(website_urls)
                else:
                    logger.warning(f"Failed to get services: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []
    
    async def _make_request_and_collect(
        self,
        test_id: str,
        website_url: str,
        use_load_balancer: bool
    ):
        """Make a request and collect metrics"""
        try:
            metrics = await self.make_request(website_url, use_load_balancer)
            self.test_metrics[test_id].append(metrics)
        except Exception as e:
            logger.error(f"Error making request: {e}")
            # Create error metrics
            error_metrics = RequestMetrics(
                timestamp=time.time(),
                website_url=website_url,
                status_code=None,
                latency_ms=0,
                error=str(e)
            )
            self.test_metrics[test_id].append(error_metrics)
    
    async def make_request(
        self,
        website_url: str,
        use_load_balancer: bool = True
    ) -> RequestMetrics:
        """Make a single HTTP request"""
        start_time = time.time()
        status_code = None
        error = None
        
        try:
            if use_load_balancer:
                # Use Load Balancer
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # First, get routing info from Load Balancer
                    route_response = await client.post(
                        f"{LOAD_BALANCER_URL}/route",
                        json={"website_url": website_url}
                    )
                    
                    if route_response.status_code == 200:
                        route_data = route_response.json()
                        target_host = route_data.get("target_host")
                        target_port = route_data.get("target_port")
                        
                        # Make actual request to container
                        container_url = f"http://{target_host}:{target_port}"
                        response = await client.get(container_url, timeout=5.0)
                        status_code = response.status_code
                    else:
                        error = f"Load balancer error: {route_response.status_code}"
            else:
                # Direct container access (would need to get container info first)
                # For now, use Load Balancer
                async with httpx.AsyncClient(timeout=10.0) as client:
                    route_response = await client.post(
                        f"{LOAD_BALANCER_URL}/route",
                        json={"website_url": website_url}
                    )
                    if route_response.status_code == 200:
                        route_data = route_response.json()
                        target_host = route_data.get("target_host")
                        target_port = route_data.get("target_port")
                        container_url = f"http://{target_host}:{target_port}"
                        response = await client.get(container_url, timeout=5.0)
                        status_code = response.status_code
                    else:
                        error = f"Load balancer error: {route_response.status_code}"
        
        except httpx.TimeoutException:
            error = "Request timeout"
        except Exception as e:
            error = str(e)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return RequestMetrics(
            timestamp=start_time,
            website_url=website_url,
            status_code=status_code,
            latency_ms=latency_ms,
            error=error
        )
    
    def calculate_rps_for_pattern(
        self,
        pattern: WorkloadPattern,
        base_rps: int,
        elapsed_seconds: float,
        total_duration: int
    ) -> float:
        """Calculate current RPS based on pattern"""
        if pattern == WorkloadPattern.CONSTANT:
            return base_rps
        elif pattern == WorkloadPattern.SPIKE:
            # Spike in the middle
            if elapsed_seconds < total_duration / 2:
                return base_rps * (1 + elapsed_seconds / (total_duration / 2))
            else:
                return base_rps * (2 - elapsed_seconds / (total_duration / 2))
        elif pattern == WorkloadPattern.GRADUAL:
            # Gradual increase from 0 to base_rps
            return base_rps * (elapsed_seconds / total_duration)
        elif pattern == WorkloadPattern.WAVE:
            # Wave pattern
            import math
            return base_rps * (1 + 0.5 * math.sin(2 * math.pi * elapsed_seconds / 10))
        return base_rps
    
    async def run_workload(self, test_id: str, config: WorkloadRequest):
        """Run a workload test"""
        self.test_status[test_id] = "running"
        self.test_start_times[test_id] = time.time()
        self.test_metrics[test_id] = []
        self.test_configs[test_id] = config
        
        # Get website URLs to test
        if config.website_urls:
            website_urls = config.website_urls
        else:
            website_urls = await self.get_available_services()
            if not website_urls:
                logger.warning("No services available for testing")
                self.test_status[test_id] = "failed"
                return
        
        logger.info(f"Starting workload test {test_id} with {len(website_urls)} URLs")
        
        start_time = time.time()
        end_time = start_time + config.duration_seconds
        request_count = 0
        last_second_start = start_time
        
        try:
            while time.time() < end_time and self.test_status[test_id] == "running":
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check if we've entered a new second
                if current_time - last_second_start >= 1.0:
                    last_second_start = current_time
                
                current_rps = self.calculate_rps_for_pattern(
                    config.pattern,
                    config.rps,
                    elapsed,
                    config.duration_seconds
                )
                
                # Calculate interval between requests
                if current_rps > 0:
                    interval = 1.0 / current_rps
                else:
                    interval = 0.1
                
                # Make a single request
                website_url = website_urls[request_count % len(website_urls)]
                await self._make_request_and_collect(
                    test_id,
                    website_url,
                    config.use_load_balancer
                )
                request_count += 1
                
                # Sleep to maintain RPS
                await asyncio.sleep(min(interval, 0.01))  # Minimum 10ms sleep
        
        except asyncio.CancelledError:
            logger.info(f"Workload test {test_id} was cancelled")
            self.test_status[test_id] = "stopped"
        except Exception as e:
            logger.error(f"Error in workload test {test_id}: {e}")
            self.test_status[test_id] = "failed"
        finally:
            if self.test_status[test_id] == "running":
                self.test_status[test_id] = "completed"
    
    def get_metrics(self, test_id: str) -> Optional[WorkloadMetrics]:
        """Calculate aggregated metrics for a test"""
        if test_id not in self.test_metrics:
            return None
        
        metrics_list = self.test_metrics[test_id]
        if not metrics_list:
            return None
        
        config = self.test_configs[test_id]
        start_time = self.test_start_times.get(test_id, 0)
        end_time = time.time() if self.test_status[test_id] == "running" else start_time + config.duration_seconds
        
        successful = [m for m in metrics_list if m.status_code and 200 <= m.status_code < 400]
        failed = [m for m in metrics_list if m.error or (m.status_code and m.status_code >= 400)]
        
        latencies = [m.latency_ms for m in metrics_list]
        latencies_sorted = sorted(latencies)
        
        # Status code distribution
        status_codes = defaultdict(int)
        for m in metrics_list:
            if m.status_code:
                status_codes[m.status_code] += 1
        
        # Website URLs used
        website_urls = list(set(m.website_url for m in metrics_list))
        
        duration = end_time - start_time
        rps = len(metrics_list) / duration if duration > 0 else 0
        
        return WorkloadMetrics(
            test_id=test_id,
            status=self.test_status.get(test_id, "unknown"),
            total_requests=len(metrics_list),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            p95_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0,
            p99_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.99)] if latencies_sorted else 0,
            requests_per_second=rps,
            error_rate=len(failed) / len(metrics_list) if metrics_list else 0,
            start_time=start_time,
            end_time=end_time if self.test_status[test_id] != "running" else None,
            duration_seconds=duration,
            website_urls=website_urls,
            status_code_distribution=dict(status_codes)
        )
    
    async def start_test(self, test_id: str, config: WorkloadRequest) -> str:
        """Start a new workload test"""
        task = asyncio.create_task(self.run_workload(test_id, config))
        self.active_tests[test_id] = task
        return test_id
    
    async def stop_test(self, test_id: str):
        """Stop a running test"""
        if test_id in self.active_tests:
            self.active_tests[test_id].cancel()
            self.test_status[test_id] = "stopped"
            try:
                await self.active_tests[test_id]
            except asyncio.CancelledError:
                pass
            del self.active_tests[test_id]
    
    def list_tests(self) -> List[str]:
        """List all test IDs"""
        return list(self.test_metrics.keys())

