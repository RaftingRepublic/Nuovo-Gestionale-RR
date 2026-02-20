from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image
import io

# --- IMPORT CONDIZIONALE AI ---
try:
    from app.services.local_vision_service import analyze_documents_locally
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"⚠️ AI Vision non disponibile: {e}")

router = APIRouter()


@router.post("/analyze")
async def analyze_document(
    front: UploadFile = File(...),
    back: UploadFile = File(None),
    doc_type: str = Form("AUTO"),  # default più sensato
    use_local: bool = Form(True),  # compat
):
    """
    Riceve le immagini e un hint opzionale sul tipo di documento.
    """
    # --- CHECK AI DISPONIBILITÀ ---
    if not AI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Servizio AI Vision non disponibile su questo server. "
                   "Le librerie AI (PaddleOCR, YOLO) non sono installate."
        )

    # 1. Leggi fronte
    try:
        f_content = await front.read()
        front_image = Image.open(io.BytesIO(f_content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Immagine Fronte non valida")

    # 2. Leggi retro (se c'è)
    back_image = None
    if back:
        try:
            b_content = await back.read()
            back_image = Image.open(io.BytesIO(b_content)).convert("RGB")
        except Exception:
            back_image = None

    hint = (doc_type or "AUTO").strip()
    print(f"🧠 Analisi Vision avviata. Hint: {hint}")

    # ✅ Passaggio POSIZIONALE (anti 'unexpected keyword argument' se cambiano i nomi)
    result = analyze_documents_locally(front_image, back_image, hint)

    return result
