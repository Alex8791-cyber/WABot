# service_bot_backend/routes/services.py
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from models import Lead
from auth import require_admin
from storage import load_services, save_services, save_lead

router = APIRouter()


@router.get("/services", response_model=List[Dict[str, Any]])
def get_services():
    return load_services()


@router.get("/services/{service_id}")
def get_service(service_id: str):
    for s in load_services():
        if s["id"] == service_id:
            return s
    raise HTTPException(status_code=404, detail="Service not found")


@router.post("/services", dependencies=[Depends(require_admin)])
def update_services_catalog(services: List[Dict[str, Any]]):
    """Replace the entire services catalog (admin only)."""
    save_services(services)
    return {"message": "Services catalog updated", "count": len(services)}


@router.put("/services/{service_id}", dependencies=[Depends(require_admin)])
def update_service(service_id: str, service: Dict[str, Any]):
    """Update a single service by ID (admin only)."""
    services = load_services()
    for i, s in enumerate(services):
        if s["id"] == service_id:
            service["id"] = service_id  # preserve ID
            services[i] = service
            save_services(services)
            return service
    raise HTTPException(status_code=404, detail="Service not found")


@router.delete("/services/{service_id}", dependencies=[Depends(require_admin)])
def delete_service(service_id: str):
    """Delete a service by ID (admin only)."""
    services = load_services()
    original_len = len(services)
    services = [s for s in services if s["id"] != service_id]
    if len(services) == original_len:
        raise HTTPException(status_code=404, detail="Service not found")
    save_services(services)
    return {"message": "Service deleted", "id": service_id}


@router.post("/lead", status_code=201)
def create_lead(lead: Lead):
    if not any(s["id"] == lead.service_id for s in load_services()):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    entry = {"service_id": lead.service_id, "responses": lead.responses}
    save_lead(entry)
    return {"message": "Lead received", "lead": entry}
