from __future__ import annotations

import os
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps

from app.schemas.registration import (
    DocumentScanResponse,
    RegistrationPayload,
    RegistrationSubmitResponse,
)


def _stitch_images_vertical(front_bytes: bytes, back_bytes: bytes) -> bytes:
    """
    Unisce fronte e retro in un'unica immagine verticale (fronte in alto, retro sotto).
    Usa ImageOps.exif_transpose() per gestire foto scattate da cellulare.
    Tutto in RAM – nessun salvataggio su disco (GDPR).
    Restituisce i bytes JPEG dell'immagine combinata.
    """
    front_img = Image.open(BytesIO(front_bytes)).convert("RGB")
    front_img = ImageOps.exif_transpose(front_img)

    back_img = Image.open(BytesIO(back_bytes)).convert("RGB")
    back_img = ImageOps.exif_transpose(back_img)

    # Salva dimensioni prima di qualsiasi operazione
    fw, fh = front_img.width, front_img.height
    bw, bh = back_img.width, back_img.height

    # Larghezza massima tra le due, altezza = somma
    max_width = max(fw, bw)
    total_height = fh + bh

    # Crea canvas bianco e incolla le due immagini
    stitched = Image.new("RGB", (max_width, total_height), (255, 255, 255))
    stitched.paste(front_img, (0, 0))
    stitched.paste(back_img, (0, fh))

    # Salva in buffer JPEG in memoria
    buffer = BytesIO()
    stitched.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    combined_bytes = buffer.getvalue()

    # Libera memoria PIL
    front_img.close()
    back_img.close()
    stitched.close()
    buffer.close()

    print(f"📐 Stitching completato: {fw}x{fh} + {bw}x{bh} → "
          f"{max_width}x{total_height} ({len(combined_bytes) / 1024:.0f} KB)")

    return combined_bytes

# --- IMPORT CONDIZIONALE: Azure Document Intelligence (PRIMARIO) ---
try:
    from app.services.azure_document_service import analyze_with_azure
    AZURE_AVAILABLE = True
except ImportError as e:
    AZURE_AVAILABLE = False
    analyze_with_azure = None
    print(f"⚠️ Azure Document Intelligence non disponibile: {e}")

# --- IMPORT CONDIZIONALE: AI Locale (FALLBACK) ---
try:
    from app.services.local_vision_service import analyze_documents_locally
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    analyze_documents_locally = None
    print(f"⚠️ AI Vision locale non disponibile in registration: {e}")

from app.services.registration.registration_service import RegistrationService

router = APIRouter(prefix="/registration", tags=["registration"])
service = RegistrationService()


def _open_image_bytes(content: bytes, filename: str) -> Image.Image:
    try:
        return Image.open(BytesIO(content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail=f"Immagine non valida: {filename}")


@router.post("/scan", response_model=DocumentScanResponse)
async def scan_document(
    front: UploadFile = File(...),
    back: Optional[UploadFile] = File(None),
    doc_type: str = Form("AUTO"),
):
    """
    Endpoint di scansione documenti d'identità.
    
    Strategia:
      1. Se Azure è configurato → usa Azure Document Intelligence (cloud, più accurato)
      2. Altrimenti fallback su AI locale (PaddleOCR + YOLO)
      3. Se nessuno è disponibile → errore 503
    """
    print("\n>>> [API] RICEVUTA FOTO DAL FRONTEND <<<")
    print(f">>> [API] front.filename={front.filename}, back={'SI' if back else 'NO'}, doc_type={doc_type}")
    print(f">>> [API] AZURE_AVAILABLE={AZURE_AVAILABLE}, AZURE_ENDPOINT={os.getenv('AZURE_DOCUMENT_ENDPOINT', 'NONE')}")
    f_content = await front.read()
    print(f">>> [API] Foto letta: {len(f_content)} bytes")
    b_content = None
    if back:
        b_content = await back.read()

    # --- STRATEGIA 1: Azure Document Intelligence ---
    if AZURE_AVAILABLE and os.getenv("AZURE_DOCUMENT_ENDPOINT"):
        print("🔵 Scansione documento via Azure Document Intelligence...")

        # Image Stitching: se c'è anche il retro, unisci in una sola immagine
        # → Azure fattura 1 pagina invece di 2 (dimezza i costi!)
        if b_content:
            try:
                azure_bytes = _stitch_images_vertical(f_content, b_content)
                print("📐 Fronte + Retro uniti in singola immagine per Azure")
            except Exception as e:
                print(f"⚠️ Stitching fallito ({e}), invio solo fronte")
                azure_bytes = f_content
        else:
            azure_bytes = f_content

        extracted = analyze_with_azure(azure_bytes, doc_type_hint=doc_type)

        if "error" in extracted:
            print(f"⚠️ Azure ha restituito errore: {extracted['error']}")
            # Se Azure fallisce, proviamo il fallback locale
            if AI_AVAILABLE:
                print("🟡 Fallback su AI locale...")
                front_img = _open_image_bytes(f_content, front.filename)
                back_img = None
                if b_content:
                    try:
                        back_img = _open_image_bytes(b_content, back.filename if back else "back")
                    except Exception:
                        back_img = None
                extracted = analyze_documents_locally(front_img, back_img, doc_type_hint=doc_type)
                if "error" in extracted:
                    raise HTTPException(status_code=500, detail=extracted["error"])
            else:
                raise HTTPException(status_code=500, detail=extracted["error"])

        detected = extracted.get("tipo_documento", "ALTRO")
        mrz_nat = extracted.get("cittadinanza")

        return DocumentScanResponse(
            detected_doc_type=detected,
            mrz_nationality=mrz_nat,
            extracted=extracted,
        )

    # --- STRATEGIA 2: AI Locale (PaddleOCR + YOLO) ---
    if AI_AVAILABLE:
        print("🟡 Azure non configurato. Scansione via AI locale...")
        front_img = _open_image_bytes(f_content, front.filename)
        back_img = None
        if b_content:
            try:
                back_img = _open_image_bytes(b_content, back.filename if back else "back")
            except Exception:
                back_img = None

        extracted = analyze_documents_locally(front_img, back_img, doc_type_hint=doc_type)

        if "error" in extracted:
            raise HTTPException(status_code=500, detail=extracted["error"])

        detected = extracted.get("tipo_documento", "ALTRO")
        mrz_nat = extracted.get("cittadinanza")

        return DocumentScanResponse(
            detected_doc_type=detected,
            mrz_nationality=mrz_nat,
            extracted=extracted,
        )

    # --- NESSUN PROVIDER DISPONIBILE ---
    raise HTTPException(
        status_code=503,
        detail="Nessun servizio OCR disponibile. "
               "Configura le credenziali Azure (.env) oppure installa le librerie AI locali."
    )


@router.post("/submit", response_model=RegistrationSubmitResponse)
async def submit_registration(
    payload: RegistrationPayload, 
    update_id: Optional[str] = Query(None, description="ID registrazione da aggiornare")
):
    try:
        # Passiamo update_id al service
        result = service.submit(payload, registration_id=update_id)
        return RegistrationSubmitResponse(
            registration_id=result.registration_id,
            timestamp_iso=result.timestamp_iso,
            pdf_filename=result.pdf_filename,
            emailed_to=result.emailed_to,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf_stateless(payload: RegistrationPayload):
    """
    Cantiere 3.12: Genera SOLO il PDF senza toccare il DB.
    Il Kiosk gestisce lo stato partecipanti direttamente in Supabase.
    """
    try:
        from app.services.registration.pdf_service import PdfService
        pdf_svc = PdfService()
        pdf_path = pdf_svc.generate_consent_pdf(payload.model_dump(by_alias=True))
        return {"status": "success", "pdf_path": pdf_path}
    except Exception as e:
        print(f"[PDF ERROR]: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("/details/{registration_id}")
async def get_registration_details(registration_id: str):
    """Restituisce il JSON completo per la modifica."""
    try:
        data = service.get_registration_details(registration_id)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Registrazione non trovata")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_registrations(
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filtro testuale (nome, cognome, email, id)"),
):
    items = service.list_registrations(limit=limit, offset=offset, query=q)
    return {"items": items}


@router.post("/{registration_id}/lock")
async def set_registration_lock(
    registration_id: str,
    body: dict = Body(...),
):
    locked = bool(body.get("locked", True))
    try:
        return service.set_locked(registration_id, locked)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Registrazione non trovata")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{registration_id}/pdf")
async def get_pdf(registration_id: str):
    """Cantiere 6: Download della liberatoria PDF firmata."""
    try:
        pdf_path = service.find_pdf_path(registration_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF non trovato")

    # Cerca nome/cognome nel DB per filename leggibile
    filename = f"Liberatoria_{registration_id[:8]}.pdf"
    try:
        from app.db.database import SessionLocal
        from app.models.registration import RegistrationDB
        db = SessionLocal()
        reg = db.query(RegistrationDB).filter(RegistrationDB.id == registration_id).first()
        if reg and reg.cognome:
            nome = (reg.nome or "").replace(" ", "_")
            cognome = (reg.cognome or "").replace(" ", "_")
            filename = f"Liberatoria_{nome}_{cognome}.pdf"
        db.close()
    except Exception:
        pass  # Fallback al filename generico

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename,
    )