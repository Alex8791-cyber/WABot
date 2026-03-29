from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from models import Lead
from storage import load_services, save_lead

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


@router.post("/lead", status_code=201)
def create_lead(lead: Lead):
    if not any(s["id"] == lead.service_id for s in load_services()):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    entry = {"service_id": lead.service_id, "responses": lead.responses}
    save_lead(entry)
    return {"message": "Lead received", "lead": entry}
