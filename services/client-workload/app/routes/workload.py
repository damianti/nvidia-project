from fastapi import APIRouter, HTTPException
import logging
import uuid
from typing import List

from app.schemas.workload import WorkloadRequest, WorkloadStatus, WorkloadMetrics
from app.services.workload_generator import WorkloadGenerator
from app.utils.config import SERVICE_NAME

logger = logging.getLogger(SERVICE_NAME)
router = APIRouter(prefix="/workload", tags=["workload"])

# Global workload generator instance
workload_generator = WorkloadGenerator()


@router.post("/start", response_model=WorkloadStatus)
async def start_workload(config: WorkloadRequest):
    """Start a new workload test"""
    test_id = str(uuid.uuid4())
    
    try:
        await workload_generator.start_test(test_id, config)
        metrics = workload_generator.get_metrics(test_id)
        
        return WorkloadStatus(
            test_id=test_id,
            status="running",
            config=config,
            metrics=metrics
        )
    except Exception as e:
        logger.error(f"Error starting workload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{test_id}")
async def stop_workload(test_id: str):
    """Stop a running workload test"""
    if test_id not in workload_generator.list_tests():
        raise HTTPException(status_code=404, detail="Test not found")
    
    await workload_generator.stop_test(test_id)
    return {"message": f"Test {test_id} stopped", "test_id": test_id}


@router.get("/status/{test_id}", response_model=WorkloadStatus)
async def get_workload_status(test_id: str):
    """Get status and metrics for a workload test"""
    if test_id not in workload_generator.list_tests():
        raise HTTPException(status_code=404, detail="Test not found")
    
    config = workload_generator.test_configs.get(test_id)
    status = workload_generator.test_status.get(test_id, "unknown")
    metrics = workload_generator.get_metrics(test_id)
    
    return WorkloadStatus(
        test_id=test_id,
        status=status,
        config=config,
        metrics=metrics
    )


@router.get("/list", response_model=List[str])
async def list_workloads():
    """List all workload test IDs"""
    return workload_generator.list_tests()


@router.get("/metrics/{test_id}", response_model=WorkloadMetrics)
async def get_workload_metrics(test_id: str):
    """Get detailed metrics for a workload test"""
    if test_id not in workload_generator.list_tests():
        raise HTTPException(status_code=404, detail="Test not found")
    
    metrics = workload_generator.get_metrics(test_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not available")
    
    return metrics


@router.get("/available-services")
async def get_available_services():
    """Get list of available website URLs from Service Discovery"""
    services = await workload_generator.get_available_services()
    return {
        "services": services,
        "count": len(services)
    }

