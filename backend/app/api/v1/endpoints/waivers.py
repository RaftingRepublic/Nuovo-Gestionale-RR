from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import FileResponse

from app.services.waiver_service import (
    WaiverService,
    WaiverDraftRequest,
    WaiverDraftResponse,
    WaiverFinalizeRequest,
    WaiverFinalizeResponse,
)

router = APIRouter()


def _public_base_url(request: Request) -> str:
    # Se sei dietro reverse proxy, in produzione metteremo header forward.
    # Per ora ok così in locale.
    return str(request.base_url).rstrip("/")


@router.post("/waivers/draft", response_model=WaiverDraftResponse)
def create_draft(req: WaiverDraftRequest, request: Request):
    try:
        svc = WaiverService()
        return svc.create_draft(req=req, public_base_url=_public_base_url(request))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore draft: {e}")


@router.post("/waivers/{waiver_id}/finalize", response_model=WaiverFinalizeResponse)
def finalize(waiver_id: str, req: WaiverFinalizeRequest, request: Request):
    try:
        svc = WaiverService()
        return svc.finalize(waiver_id=waiver_id, req=req, public_base_url=_public_base_url(request))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="waiver_id non trovato")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore finalize: {e}")


@router.get("/waivers/{waiver_id}/pdf")
def get_pdf(waiver_id: str, which: str = Query(default="final", pattern="^(draft|final)$")):
    # Nota: in produzione potresti voler mettere auth o token temporanei
    from pathlib import Path
    base = Path(__file__).resolve().parents[3] / "storage" / "waivers" / waiver_id
    pdf = base / ("draft.pdf" if which == "draft" else "final.pdf")
    if not pdf.exists():
        raise HTTPException(status_code=404, detail="PDF non trovato")
    return FileResponse(path=str(pdf), media_type="application/pdf", filename=f"{waiver_id}_{which}.pdf")
