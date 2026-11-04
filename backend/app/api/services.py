"""Services CRUD API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_storage
from app.core.auth import verify_dashboard_auth
from app.models.schemas import Service, ServiceCreate, ServiceUpdate
from app.storage.base import BaseRepository

router = APIRouter(
    prefix="/api/services",
    tags=["services"],
    dependencies=[Depends(verify_dashboard_auth)],
)


@router.get("", response_model=List[Service])
def list_services(storage: BaseRepository = Depends(get_storage)) -> List[Service]:
    """List monitored services with current health status and autonomy level."""
    return storage.list_services()


@router.post("", response_model=Service, status_code=status.HTTP_201_CREATED)
def register_service(
    service_in: ServiceCreate,
    storage: BaseRepository = Depends(get_storage),
) -> Service:
    """Register a new service to be monitored by Nightwatch."""
    return storage.create_service(service_in)


@router.get("/{service_id}", response_model=Service)
def get_service(
    service_id: str,
    storage: BaseRepository = Depends(get_storage),
) -> Service:
    """Get service details by ID."""
    service = storage.get_service(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )
    return service


@router.patch("/{service_id}", response_model=Service)
def update_service(
    service_id: str,
    update_in: ServiceUpdate,
    storage: BaseRepository = Depends(get_storage),
) -> Service:
    """Edit service configuration, autonomy level, or pause/resume sweeps."""
    updated = storage.update_service(service_id, update_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )
    return updated


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    storage: BaseRepository = Depends(get_storage),
) -> None:
    """Remove a service from Nightwatch monitoring."""
    deleted = storage.delete_service(service_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )
