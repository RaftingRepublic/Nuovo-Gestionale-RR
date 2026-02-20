from __future__ import annotations
import os
import re
import time
import logging
import threading
import numpy as np
from datetime import datetime
from PIL import Image
from pathlib import Path

# Importiamo la Knowledge Base
from app.services.document_specs import DOCUMENT_SPECS, GENERIC_DATE_REGEX

# --- CONFIGURAZIONE AMBIENTALE ---
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_mkldnn"] = "0"
os.environ["GLOG_minloglevel"] = "2"
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

# POLICY DI RITENZIONE IMMAGINI (GDPR COMPLIANCE)
ID_IMAGE_RETENTION = os.getenv("ID_IMAGE_RETENTION", "NONE")

logger = logging.getLogger("vision_service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- IMPORT MODULI AI ---
try:
    import paddle
    from paddleocr import PaddleOCR
    paddle.set_device('cpu') 
    PADDLE_AVAILABLE = True
except ImportError as e:
    PADDLE_AVAILABLE = False
    logger.error(f"PaddleOCR non disponibile: {e}")

# GLiNER rimosso per ottimizzazione RAM
GLINER_AVAILABLE = False

from app.services.image_utils import (
    isolate_document_yolo, 
    pil_to_cv2, 
    save_raw_dataset_image
)

# --- CONFIGURAZIONE SCHEMI DI ESTRAZIONE ---
STANDARD_SCHEMA = {
    "cognome": {"labels": ["Cognome", "Surname", "Last Name"], "threshold": 0.40, "type": "text"},
    "nome": {"labels": ["Nome", "Name", "Given Names"], "threshold": 0.40, "type": "text"},
    "data_nascita": {"labels": ["Data di nascita", "Birth Date", "Nato il"], "threshold": 0.30, "type": "date"},
    "comune_nascita": {"labels": ["Luogo di nascita", "Comune di nascita", "Place of Birth", "Nato a"], "threshold": 0.25, "type": "text"},
    "comune_residenza": {"labels": ["Comune di residenza", "Città", "Residenza", "Abitazione", "Living in"], "threshold": 0.20, "type": "text"},
    "codice_fiscale": {"labels": ["Codice Fiscale", "Tax Code", "CF"], "threshold": 0.35, "type": "alphanum"},
    "numero_documento": {"labels": ["Numero Documento", "Card Number", "Document No"], "threshold": 0.30, "type": "alphanum"},
    "scadenza_documento": {"labels": ["Scadenza", "Valid until", "Expiry Date"], "threshold": 0.30, "type": "date"},
    "cittadinanza": {"labels": ["Cittadinanza", "Nationality"], "threshold": 0.45, "type": "text"}
}

PATENTE_SCHEMA = {
    "cognome": {"labels": ["1.", "1 ", "Cognome"], "threshold": 0.25, "type": "text"},
    "nome": {"labels": ["2.", "2 ", "Nome"], "threshold": 0.25, "type": "text"},
    "data_nascita": {"labels": ["3.", "3 ", "Data di nascita"], "threshold": 0.25, "type": "date"},
    "comune_nascita": {"labels": ["3.", "3 ", "Luogo di nascita"], "threshold": 0.25, "type": "text"},
    "data_rilascio": {"labels": ["4a", "4a.", "4 a", "Rilascio"], "threshold": 0.25, "type": "date"},
    "scadenza_documento": {"labels": ["4b", "4b.", "46", "4 b", "Scadenza"], "threshold": 0.25, "type": "date"},
    "numero_documento": {"labels": ["5.", "5 ", "Numero Patente"], "threshold": 0.30, "type": "alphanum"},
    "ente_rilascio": {"labels": ["4c", "4c.", "Rilasciato da"], "threshold": 0.20, "type": "text"}
}

PASSPORT_VISUAL_SCHEMA = {
    "cognome": {"labels": ["Surname", "Nom", "Cognome"], "threshold": 0.35, "type": "text"},
    "nome": {"labels": ["Given Names", "Prenoms", "Nome"], "threshold": 0.35, "type": "text"},
    "data_nascita": {"labels": ["Date of birth", "Date de naissance"], "threshold": 0.35, "type": "date"},
    "numero_documento": {"labels": ["Passport No", "Passeport N", "Document No"], "threshold": 0.40, "type": "alphanum"},
    "scadenza_documento": {"labels": ["Date of expiry", "Date d'expiration"], "threshold": 0.35, "type": "date"},
    "cittadinanza": {"labels": ["Nationality", "Nationalite", "Cittadinanza"], "threshold": 0.40, "type": "text"},
    "stato_nascita": {"labels": ["Place of birth", "Lieu de naissance", "Luogo di nascita"], "threshold": 0.25, "type": "text"}
}

BLACKLIST_VALUES = [
    "COGNOME", "NOME", "NATO", "IL", "RESIDENZA", "CITTADINANZA", 
    "LUOGO", "COMUNE", "VIA", "PIAZZA", "SCADENZA", "RILASCIO", "EMISSIONE", 
    "SURNAME", "NAME", "DATE", "BIRTH", "PLACE", "ADDRESS", "SEX", "F", "M",
    "REPUBBLICA", "ITALIANA", "MINISTERO", "INTERNO", "FISCAL", "CODE",
    "DRIVING", "LICENSE", "PERMESSO", "SOGGIORNO", "PASSPORT"
]

FRONT_ONLY_KEYS = ["nome", "cognome", "data_nascita", "comune_nascita", "numero_documento", "scadenza_documento", "cittadinanza"]
BACK_ONLY_KEYS = ["comune_residenza", "codice_fiscale"]

BROAD_DATE_REGEX = re.compile(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](?:19|20)?(\d{2})\b")

# -------------------------
# BACKEND CLASSES
# -------------------------
class PaddleBackend:
    _instance = None
    _lock = threading.Lock()
    model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not PADDLE_AVAILABLE: return
        logger.info("⚡ Init PaddleOCR...")
        try:
            # Re-inizializza il modello se necessario
            self.model = PaddleOCR(use_angle_cls=True, lang='it', enable_mkldnn=False, show_log=False, use_gpu=False)
            # Warmup
            self.model.ocr(np.zeros((100, 100, 3), dtype=np.uint8), cls=True)
            logger.info("✅ PaddleOCR Pronto.")
        except Exception as e:
            logger.critical(f"❌ Errore Init PaddleOCR: {e}")
            self.model = None

    def infer(self, img_array: np.ndarray):
        if not self.model: return None
        with self._lock: 
            try:
                return self.model.ocr(img_array, cls=True)
            except Exception as e:
                logger.error(f"Paddle Inference Crash: {e}")
                return None

    @classmethod
    def release_instance(cls):
        with cls._lock:
            if cls._instance:
                if cls._instance.model:
                    del cls._instance.model
                cls._instance = None
                import gc
                gc.collect()
                logger.info("🗑️ [CLEANUP] PaddleOCR scaricato dalla RAM.")

# Class GlinerBackend rimossa

# -------------------------
# HELPERS
# -------------------------
def _resize_if_needed(img: Image.Image, max_dim: int = 1500) -> Image.Image:
    if not img: return None
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        print(f"   📉 Downscaling Input: {w}x{h} -> {new_w}x{new_h}")
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return img


def _mrz_char_value(c):
    if '0' <= c <= '9': return int(c)
    if 'A' <= c <= 'Z': return ord(c) - 55
    return 0

def _calculate_mrz_checksum(value_str):
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(value_str):
        val = _mrz_char_value(char)
        weight = weights[i % 3]
        total += val * weight
    return total % 10

def _validate_and_fix_mrz_field(raw_value, expected_check_digit):
    if not raw_value or not expected_check_digit.isdigit():
        return None, False
    if str(_calculate_mrz_checksum(raw_value)) == expected_check_digit:
        return raw_value, True
    corrections = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'D': '0'}
    fixed_val = list(raw_value)
    for i, char in enumerate(fixed_val):
        if char in corrections: fixed_val[i] = corrections[char]
    fixed_str = "".join(fixed_val)
    if str(_calculate_mrz_checksum(fixed_str)) == expected_check_digit:
        print(f"      🔧 MRZ Checksum Fix: {raw_value} -> {fixed_str}")
        return fixed_str, True
    return raw_value, False

def _extract_mrz_data(text_blob: str, label: str = "GENERIC") -> dict:
    """
    Estrae dati MRZ (Machine Readable Zone).
    FIX 8.1: Aggiunto filtro per evitare "hallucination" su testi tipo "FIRMA DEL TITOLARE"
    che venivano scambiati per codici MRZ.
    """
    if not text_blob or len(text_blob) < 30: return {}

    print(f"\n   🕵️ [MRZ SCANNER - {label}] Analisi e Ricostruzione...")
    schema = {}
    
    compact_text = text_blob.replace(" ", "").replace("\n", "").upper()
    fuzzy_mrz = re.sub(r"[K«\(\{\[\£]", "<", compact_text)
    
    # 1. Numeri e Date
    # Pattern esteso per supportare ID-1 e ID-3
    # Cerchiamo l'ancora ITA. 
    ita_anchor = re.search(r"([ACIPV]<|[ACIPV])([A-Z]{3})", fuzzy_mrz)
    
    if ita_anchor:
        start_idx = ita_anchor.start()
        country_code = ita_anchor.group(2) 
        
        # [FIX] Anti-Hallucination: Se il country code non è ITA e non siamo sicuri, 
        # potrebbe essere "FIRMA" -> "RMA". Se il documento è CIE, deve esserci ITA.
        # "RMA" non è un country code valido per CIE italiane.
        is_suspicious = False
        if country_code not in ["ITA", "DEU", "FRA", "ESP", "USA", "GBR"]:
             # Controllo euristico: se è "RMA" probabilmente è "FIRMA"
             if "RMA" in country_code or "DEL" in country_code:
                 print(f"      🚫 [MRZ] Ignorato falso positivo MRZ (Country: {country_code} sospetto)")
                 is_suspicious = True

        if not is_suspicious:
            stream = fuzzy_mrz[start_idx:]
            anchor_len = len(ita_anchor.group(0))
            
            schema["stato_emittente"] = country_code
            
            raw_doc_num = stream[anchor_len : anchor_len+9]
            doc_check = stream[anchor_len+9 : anchor_len+10]
            
            # [FIX] Check Garbarge nel numero documento
            # Se contiene 'DEL', 'TIT', 'FIRM' è sicuramente spazzatura
            if any(bad in raw_doc_num for bad in ["DEL", "TIT", "FIRM", "MA", "OLA"]):
                print(f"      🚫 [MRZ] Scartato Num Doc invalido: {raw_doc_num}")
            else:
                val_doc, ok_doc = _validate_and_fix_mrz_field(raw_doc_num, doc_check)
                if ok_doc:
                    schema["numero_documento"] = val_doc
                    first_char = ita_anchor.group(0)[0]
                    if first_char in ['C', 'I']: schema["tipo_documento"] = "CIE" if country_code == 'ITA' else "ID_CARD"
                    elif first_char == 'P': schema["tipo_documento"] = "PASSAPORTO"
                    print(f"      ✅ DOC NUM VALIDATO: {val_doc}")
                elif re.match(r"^[A-Z0-9]{9}$", raw_doc_num):
                    # Accettiamo anche se checksum fallisce ma il formato è solido
                    schema["numero_documento"] = raw_doc_num

            # Date: Nascita e Scadenza
            date_candidates = re.finditer(r"(\d{6})(\d)([MF<X])(\d{6})(\d)", stream)
            for match in date_candidates:
                birth_raw, birth_check, sex, expiry_raw, expiry_check = match.groups()
                
                # Data Nascita
                v_birth, ok_birth = _validate_and_fix_mrz_field(birth_raw, birth_check)
                if ok_birth:
                    try:
                        yy, mm, dd = int(v_birth[:2]), int(v_birth[2:4]), int(v_birth[4:])
                        if 1 <= mm <= 12 and 1 <= dd <= 31:
                            curr_yy = int(datetime.now().strftime("%y"))
                            prefix = "19" if yy > (curr_yy + 5) else "20"
                            schema["data_nascita"] = f"{dd:02d}/{mm:02d}/{prefix}{yy:02d}"
                    except: pass

                # Scadenza
                v_exp, ok_exp = _validate_and_fix_mrz_field(expiry_raw, expiry_check)
                candidate_exp = v_exp if ok_exp else expiry_raw
                
                try:
                    yy, mm, dd = int(candidate_exp[:2]), int(candidate_exp[2:4]), int(candidate_exp[4:])
                    if 1 <= mm <= 12 and 1 <= dd <= 31:
                        full_year = 2000 + yy
                        if full_year >= datetime.now().year - 5:
                            schema["scadenza_documento"] = f"{dd:02d}/{mm:02d}/{full_year}"
                except: pass
                    
                if sex in ['M', 'F']:
                    schema['sesso'] = sex

    # 2. NOMI DA MRZ
    name_match = re.search(r"([A-Z]+(?:<[A-Z]+)*)<<([A-Z]+(?:<[A-Z]+)*)", fuzzy_mrz)
    if name_match:
        raw_sur = name_match.group(1).replace("<", " ").strip()
        raw_names = name_match.group(2).replace("<", " ").strip()
        
        # Filtra parole chiave comuni che finiscono nell'MRZ
        if "ITA" not in raw_sur and "REPUBBLICA" not in raw_sur and len(raw_sur) > 1: 
            schema["cognome"] = raw_sur.title()
            schema["nome"] = raw_names.title()
            print(f"      ✅ NOMI MRZ: {schema['cognome']} {schema['nome']}")

    return schema

def _inject_spaces_in_address(text: str) -> str:
    patterns = [
        (r'(?i)(VIA|PIAZZA|CORSO|L\.GO|LARGO|V\.LE|VIALE|STRADA)(?=[A-Z0-9])', r'\1 '),
        (r'(?i)(N\.|NUM\.)(?=[0-9])', r'\1 '), 
        (r'(?i)([a-z])(N\.|NUM\.)', r'\1 \2'),
    ]
    for p, r in patterns:
        text = re.sub(p, r, text)
    
    text = re.sub(r'(\d+)([A-Z]{3,})', r'\1 \2', text) 
    text = re.sub(r'([A-Z]{3,})(\d+)', r'\1 \2', text)
    
    return text

def _clean_text_blob(ocr_result, label="UNK") -> str:
    print(f"\n   📝 [OCR RAW {label}] Analisi righe grezze (FULL):")
    if not ocr_result: return ""
    raw_lines = ocr_result[0] if isinstance(ocr_result, list) and len(ocr_result) > 0 else []
    if not raw_lines: return ""

    sorted_lines = sorted(raw_lines, key=lambda line: sum([p[1] for p in line[0]]) / 4)
    text_parts = []
    
    for i, line in enumerate(sorted_lines):
        txt = line[1][0].strip()
        if len(txt) > 1:
            txt_fixed = _inject_spaces_in_address(txt)
            text_parts.append(txt_fixed)
            print(f"      Line {i:02d}: {txt} -> {txt_fixed}")
            
    return "\n".join(text_parts)

def _smart_clean_field(raw_value: str, field_type: str, regex_pattern: re.Pattern | None = None) -> str | None:
    if not raw_value: return None
    val = raw_value.strip()
    
    # 1. VALIDAZIONE REGEX RIGIDA
    if regex_pattern:
        match = regex_pattern.search(val)
        if match:
            if match.groups():
                for g in match.groups():
                    if g: return g
            return match.group(0)
        else:
            val_nospace = val.replace(" ", "")
            match = regex_pattern.search(val_nospace)
            if match: return match.group(0)
            return None
    
    # 2. Pulizia standard per altri campi
    if field_type == "text":
        headers = ["CITTADINANZA", "LUOGO", "NASCITA", "NATA A", "TARTAA", "COMUNE", "RESIDENZA", "DI", "RILASCIATO", "DA"]
        for h in headers:
            val = re.sub(f"(?i){h}", "", val)
        val = re.sub(r"[^a-zA-ZàèéìòùÀÈÉÌÒÙ\s'\(\)-]", "", val) 
        return val.title().strip()
    
    elif field_type == "alphanum":
        return val.upper().replace(" ", "").replace(".", "").replace("-", "")
    
    elif field_type == "date":
        val = val.replace("-", "/").replace(".", "/").replace("\\", "/")
        date_match = BROAD_DATE_REGEX.search(val)
        if date_match:
            d, m, y_part = date_match.group(1), date_match.group(2), date_match.group(3)
            if len(y_part) == 4:
                final_year = y_part
            elif len(y_part) == 2:
                y_val = int(y_part)
                prefix = "19" if y_val > 50 else "20"
                final_year = f"{prefix}{y_part}"
            else:
                return None
            return f"{d}/{m}/{final_year}"
        return None
    
    elif field_type == "address":
        val = re.sub(r"\s+", " ", val)
        val = re.sub(r"^(RESIDENZA|ABITAZIONE|INDIRIZZO)\s*", "", val, flags=re.IGNORECASE)
        return val.strip()
    return val

# _run_gliner_extraction function removed

def _extract_and_repair_cf(text: str) -> str | None:
    digit_sim = r"[0-9OQILZASGB]"
    fuzzy_pattern = r"([A-Z]{6})(" + digit_sim + r"{2})([A-Z])(" + digit_sim + r"{2})([A-Z])(" + digit_sim + r"{3})([A-Z])"
    match = re.search(fuzzy_pattern, text.upper())
    if match:
        groups = list(match.groups())
        rep_map = {'O': '0', 'Q': '0', 'I': '1', 'L': '1', 'Z': '2', 'A': '4', 'S': '5', 'G': '6', 'B': '8'}
        for i in [1, 3, 5]:
            fixed = ""
            for char in groups[i]: fixed += rep_map.get(char, char)
            groups[i] = fixed
        final_cf = "".join(groups)
        print(f"      🔧 CF REPAIR: {match.group(0)} -> {final_cf}")
        return final_cf
    return None

def _extract_all_dates(text_blob: str) -> list[str]:
    found = []
    matches = BROAD_DATE_REGEX.findall(text_blob)
    for m in matches:
        d, month, y = m
        if len(y) == 2:
            y_val = int(y)
            prefix = "19" if y_val > 50 else "20"
            y = f"{prefix}{y}"
        normalized = f"{d}/{month}/{y}"
        found.append(normalized)
    return found

def _solve_dates_heuristic(dates: list[str]) -> dict:
    if not dates: return {}
    
    unique_dates = list(set(dates))
    dt_objs = []
    for ds in unique_dates:
        try:
            dt = datetime.strptime(ds, "%d/%m/%Y")
            dt_objs.append((dt, ds))
        except: pass
        
    if not dt_objs: return {}
    dt_objs.sort(key=lambda x: x[0])
    sorted_dates = [x[1] for x in dt_objs]
    
    result = {}
    result["data_nascita"] = sorted_dates[0]
    
    if len(sorted_dates) >= 2:
        last_dt = dt_objs[-1][0]
        if last_dt.year > datetime.now().year - 5:
            result["scadenza_documento"] = sorted_dates[-1]
            
    if len(sorted_dates) >= 3:
        result["data_rilascio"] = sorted_dates[1]
        
    print(f"      🧠 [DATE HEURISTIC] Sorted: {sorted_dates} -> {result}")
    return result

def _extract_patente_regex(text_lines: list[str]) -> dict:
    print(f"\n   🏎️ [PATENTE LINE SCAN] Analisi posizionale su {len(text_lines)} righe...")
    data = {}
    HEADERS_BLOCKLIST = ["REPUBBLICA", "ITALIANA", "PATENTE", "GUIDA", "COMUNITA", "UNIONE", "EUROPEA", "MODEL"]

    def is_header(s):
        u = s.upper()
        return any(k in u for k in HEADERS_BLOCKLIST)

    def is_valid_person_text(s):
        if len(s) < 2: return False
        if is_header(s): return False
        if re.search(r'[\(\)\d]', s): return False
        return True

    for i, line in enumerate(text_lines):
        clean_line = line.strip()
        
        # 1. COGNOME
        match_inline = re.search(r'1\s*[\.,]?\s*([A-Z\s]+)', clean_line, re.IGNORECASE)
        if match_inline and len(match_inline.group(1)) > 2:
            candidate = match_inline.group(1).strip().title()
            if is_valid_person_text(candidate):
                data["cognome"] = candidate
                print(f"      ✅ Cognome (Inline): {data['cognome']}")
        elif re.match(r'^1\s*[\.,]?$', clean_line):
            found = False
            if i > 0:
                candidate_prev = text_lines[i-1].strip()
                if is_valid_person_text(candidate_prev):
                    data["cognome"] = candidate_prev.title()
                    print(f"      ✅ Cognome (Previous Line): {data['cognome']}")
                    found = True
            if not found and i < len(text_lines) - 1:
                candidate_next = text_lines[i+1].strip()
                if is_valid_person_text(candidate_next):
                    data["cognome"] = candidate_next.title()
                    print(f"      ✅ Cognome (Next Line): {data['cognome']}")

        # 2. NOME
        match_inline = re.search(r'2\s*[\.,]?\s*([A-Z\s]+)', clean_line, re.IGNORECASE)
        if match_inline and len(match_inline.group(1)) > 2:
            candidate = match_inline.group(1).strip().title()
            if is_valid_person_text(candidate):
                data["nome"] = candidate
                print(f"      ✅ Nome (Inline): {data['nome']}")
        elif re.match(r'^2\s*[\.,]?$', clean_line):
            found = False
            if i > 0:
                candidate_prev = text_lines[i-1].strip()
                if "1." not in candidate_prev and is_valid_person_text(candidate_prev):
                    if data.get("cognome", "").lower() != candidate_prev.lower():
                        data["nome"] = candidate_prev.title()
                        print(f"      ✅ Nome (Previous Line): {data['nome']}")
                        found = True
            if not found and i < len(text_lines) - 1:
                candidate_next = text_lines[i+1].strip()
                if is_valid_person_text(candidate_next):
                    data["nome"] = candidate_next.title()
                    print(f"      ✅ Nome (Next Line): {data['nome']}")

        # 5. NUMERO DOCUMENTO
        match_doc = DOCUMENT_SPECS["PATENTE_IT"]["doc_number_regex"].search(clean_line)
        if match_doc:
            data["numero_documento"] = match_doc.group(0)
            print(f"      ✅ Num Doc (Line Scan): {data['numero_documento']}")
        
        # COMUNE DI NASCITA
        match_comune = re.search(r'([A-Z\s\']+?)\s*\(\s*([A-Z]{2})', clean_line)
        if match_comune:
            city = match_comune.group(1).strip()
            prov = match_comune.group(2).strip()
            if len(city) > 2 and not is_header(city):
                data["comune_nascita"] = city.title()
                print(f"      ✅ Comune Nascita (Pattern): {data['comune_nascita']} [{prov}]")

    return data

def _extract_passport_visual(text_lines: list[str]) -> dict:
    print(f"\n    🛂 [PASSPORT VISUAL SCAN] Analisi posizionale su {len(text_lines)} righe...")
    data = {}
    
    def clean_ppt_date(txt):
        txt = txt.upper().replace("O", "0").replace("Q", "0").replace(" ", "")
        match = re.search(r"(\d{2})([A-Z]{3}).*?(\d{4})", txt)
        if match:
            d, m_str, y = match.groups()
            months = {
                'GEN': '01', 'JAN': '01', 'FEB': '02', 'FÉV': '02', 'MAR': '03', 
                'APR': '04', 'AVR': '04', 'MAG': '05', 'MAY': '05', 'MAI': '05',
                'GIU': '06', 'JUN': '06', 'JUI': '06', 'LUG': '07', 'JUL': '07',
                'AGO': '08', 'AUG': '08', 'AOÛ': '08', 'SET': '09', 'SEP': '09', 
                'OTT': '10', 'OCT': '10', 'NOV': '11', 'DIC': '12', 'DEC': '12', 'DÉC': '12'
            }
            for k, v in months.items():
                if k in m_str: return f"{d}/{v}/{y}"
        return _smart_clean_field(txt, "date")

    for i, line in enumerate(text_lines):
        clean_line = line.strip().upper()
        if "COGNOME" in clean_line or "SURNAME" in clean_line:
            if i < len(text_lines) - 1:
                val = text_lines[i+1].strip()
                if len(val) > 2 and "PASSEPORT" not in val:
                    data["cognome"] = val.title()
        if "NOME" in clean_line and ("GIVEN" in clean_line or "PRENOMS" in clean_line):
            if i < len(text_lines) - 1:
                val = text_lines[i+1].strip()
                if len(val) > 2: data["nome"] = val.title()
        if "NASCITA" in clean_line and "DATA" in clean_line:
            if i < len(text_lines) - 1:
                dt = clean_ppt_date(text_lines[i+1].strip())
                if dt: data["data_nascita"] = dt
        if "LUOGO" in clean_line and "NASCITA" in clean_line:
            candidates = []
            if i < len(text_lines) - 1: candidates.append(text_lines[i+1])
            if i < len(text_lines) - 2: candidates.append(text_lines[i+2])
            for cand in candidates:
                if len(cand.strip()) > 3 and not any(x in cand.upper() for x in ["AUTORITA", "AUTHORITY", "SESS"]):
                    data["comune_nascita"] = cand.strip().title()
                    break
        if "SCADENZA" in clean_line and "DATA" in clean_line:
            if i < len(text_lines) - 1:
                dt = clean_ppt_date(text_lines[i+1].strip())
                if dt: data["scadenza_documento"] = dt
        
    if "numero_documento" not in data:
        for k in range(min(5, len(text_lines))):
            m = re.search(r'\b([A-Z]{2}\d{7})\b', text_lines[k].upper())
            if m:
                data["numero_documento"] = m.group(1)
                print(f"      ✅ Num Doc (Header Scan): {data['numero_documento']}")
                break
    return data

def _regex_fallback(text_blob: str, context: str = "ALL", doc_specs: dict = None) -> dict:
    schema = {}
    text_upper = text_blob.upper()
    text_compact = text_upper.replace(" ", "").replace("\n", "").replace(".", "").replace("-", "")
    
    if context in ["ALL", "BACK"]:
        cf_match = re.search(r'[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]', text_compact)
        if cf_match:
            schema["codice_fiscale"] = cf_match.group(0)
            print(f"      🔧 REGEX: Trovato CF: {cf_match.group(0)}")
        else:
            repaired = _extract_and_repair_cf(text_compact)
            if repaired: schema["codice_fiscale"] = repaired

    if context in ["ALL", "FRONT"] and doc_specs:
        regex = doc_specs.get("doc_number_regex")
        if regex:
            match = regex.search(text_blob) or regex.search(text_upper)
            if match:
                val = match.group(0)
                if match.groups():
                    for g in match.groups():
                        if g: val = g; break
                schema["numero_documento"] = val.replace(" ", "")
                print(f"      🔧 REGEX SPECIFICA: Trovato Doc Num: {schema['numero_documento']}")

    return schema

def _parse_cf_to_data(cf: str) -> dict:
    if len(cf) != 16: return {}
    data = {}
    try:
        yy = int(cf[6:8])
        month_map = {'A':1, 'B':2, 'C':3, 'D':4, 'E':5, 'H':6, 'L':7, 'M':8, 'P':9, 'R':10, 'S':11, 'T':12}
        mm = month_map.get(cf[8].upper())
        dd_val = int(cf[9:11])
        sex = 'M'
        dd = dd_val
        if dd_val > 40:
            sex = 'F'
            dd = dd_val - 40
        if mm and 1 <= dd <= 31:
            curr_year = datetime.now().year % 100
            prefix = "19" if yy > curr_year else "20"
            data["data_nascita"] = f"{dd:02d}/{mm:02d}/{prefix}{yy:02d}"
            data["sesso"] = sex
    except: pass
    return data

def verify_document_coherence(text_blob: str, doc_type: str) -> bool:
    specs = DOCUMENT_SPECS.get(doc_type)
    if not specs or not specs["keywords"]: return True 
    text_upper = text_blob.upper()
    for kw in specs["keywords"]:
        if kw in text_upper:
            print(f"     ✅ [PROMO] Keyword trovata: {kw}")
            return True
    if specs.get("doc_number_regex") and specs["doc_number_regex"].search(text_upper):
        print(f"   ✅ [PROMO] Keyword assente ma trovato numero documento valido.")
        return True
    print(f"   ⚠️ [PROMO] Nessuna keyword per {doc_type} trovata nel testo.")
    return False

def detect_nationality_context(text_blob: str, mrz_data: dict, doc_type_hint: str) -> bool:
    if doc_type_hint == "PATENTE_IT": return True
    if mrz_data.get("stato_emittente") == "ITA" or mrz_data.get("nationality") == "ITA": return True
    text_compact = text_blob.upper().replace(" ", "")
    if "REPUBBLICAITALIANA" in text_compact or "CITTADINANZAITALIANA" in text_compact: return True
    return False

# -------------------------
# CORE PIPELINE
# -------------------------
def analyze_documents_locally(front_img: Image.Image, back_img: Image.Image | None = None, doc_type_hint: str = "AUTO") -> dict:
    debug_log = {"steps": [], "sources": {}}
    
    print("\n" + "="*80)
    print(f"🚀 AVVIO ANALISI IBRIDA V8.2 (Robustness Fix) [Time: {datetime.now().strftime('%H:%M:%S')}]")
    print(f"   Documento Dichiarato: {doc_type_hint}")
    print("="*80)
    
    final_data = {
        "source": "HYBRID_NEURAL_V8", 
        "tipo_documento": doc_type_hint if doc_type_hint != "AUTO" else "ALTRO"
    }

    try:
        if ID_IMAGE_RETENTION == "DEBUG":
            if front_img: save_raw_dataset_image(front_img, f"{doc_type_hint}_FRONT")
            if back_img: save_raw_dataset_image(back_img, f"{doc_type_hint}_BACK")
            print("   ⚠️ WARNING: Salvataggio immagini RAW attivo (ID_IMAGE_RETENTION=DEBUG).")
        else:
            print("   🔒 GDPR: Immagini trattate in RAM e non persistite su disco (ID_IMAGE_RETENTION=NONE).")

        doc_specs = DOCUMENT_SPECS.get(doc_type_hint, DOCUMENT_SPECS["ALTRO"])
        # 1. OCR Scanning (SEQUENZIALE: YOLO -> PADDLE -> CLEANUP)
        paddle_engine = None
        ocr_texts = {"FRONT": "", "BACK": ""}
        
        for side, raw_img in [("FRONT", front_img), ("BACK", back_img)]:
            if not raw_img: continue
            
            # Optimization: Resize input before any processing
            img = _resize_if_needed(raw_img)

            print(f"\n--- 📸 ELABORAZIONE LATO: {side} ---")
            try:
                # A. YOLO ISOLATION (Auto-releases memory)
                cropped = isolate_document_yolo(img, debug_prefix=side)
                target = cropped if cropped else img
                
                # B. PADDLE OCR (Load just-in-time)
                if PADDLE_AVAILABLE:
                    if not paddle_engine:
                        paddle_engine = PaddleBackend.get_instance()
                    
                    cv_img = pil_to_cv2(target)
                    res = paddle_engine.infer(cv_img)
                    text = _clean_text_blob(res, label=side)
                    ocr_texts[side] = text
                    debug_log[f"{side}_raw_ocr"] = text[:200]
                    
            except Exception as e_ocr:
                logger.error(f"❌ Errore OCR su {side}: {e_ocr}")
                debug_log[f"{side}_error"] = str(e_ocr)

        # C. PADDLE CLEANUP (Crucial for 1GB limit)
        if paddle_engine:
            PaddleBackend.release_instance()

        full_text = ocr_texts["FRONT"] + "\n" + ocr_texts["BACK"]

        # 2. PROMO Check
        if doc_type_hint not in ["AUTO", "ALTRO"]:
            is_coherent = verify_document_coherence(full_text, doc_type_hint)
            if not is_coherent:
                print("   ❌ [PROMO] Warning: Mismatch documento.")
                final_data["warning_mismatch"] = True

        # 3. MRZ Extraction
        mrz_data = {}
        if doc_type_hint == "PATENTE_IT":
            print("   🚫 [MRZ] Saltato per Patente")
        else:
            try:
                if ocr_texts["BACK"]:
                    mrz_data = _extract_mrz_data(ocr_texts["BACK"], label="BACK")
                if not mrz_data and ocr_texts["FRONT"]:
                    mrz_data = _extract_mrz_data(ocr_texts["FRONT"], label="FRONT")
            except Exception as e_mrz:
                logger.error(f"❌ Errore MRZ Extraction: {e_mrz}")

        # 4. Residence Context
        is_italian_resident = detect_nationality_context(full_text, mrz_data, doc_type_hint)
        print(f"   🌍 Contesto Residenza: {'ITALIA' if is_italian_resident else 'ESTERO'}")
        
        active_schema = PATENTE_SCHEMA if doc_type_hint == "PATENTE_IT" else STANDARD_SCHEMA
        target_front = list(FRONT_ONLY_KEYS)
        target_back = list(BACK_ONLY_KEYS)
        
        if not is_italian_resident:
            if "codice_fiscale" in target_back: target_back.remove("codice_fiscale")
            if "comune_residenza" in target_back: target_back.remove("comune_residenza")

        # 5. REGEX & HEURISTIC EXTRACTION (No GLiNER)
        ai_front_data = {}
        ai_back_data = {}

        if ocr_texts["FRONT"]:
            try:
                print("   ⚡ [EXTRACTION] Running Regex/Heuristic Engine...")
                
                # Regex Fallback Universale
                regex_data = _regex_fallback(ocr_texts["FRONT"], context="FRONT", doc_specs=doc_specs)
                ai_front_data.update(regex_data)

                # Speciale Patente
                if doc_type_hint == "PATENTE_IT":
                    lines = ocr_texts["FRONT"].split('\n')
                    regex_patente = _extract_patente_regex(lines)
                    ai_front_data.update(regex_patente)
                
                # Speciale Passaporto Visual
                elif doc_type_hint == "PASSAPORTO":
                    lines = ocr_texts["FRONT"].split('\n')
                    ppt_data = _extract_passport_visual(lines)
                    ai_front_data.update(ppt_data)

                missing_dates = [k for k in ["data_nascita", "scadenza_documento", "data_rilascio"] if k not in ai_front_data]
                if missing_dates:
                    print(f"   🧩 [HEURO] Date mancanti {missing_dates}, attivo euristica...")
                    all_dates_front = _extract_all_dates(ocr_texts["FRONT"])
                    all_dates_back = _extract_all_dates(ocr_texts["BACK"])
                    combined_dates = all_dates_front + all_dates_back
                    date_logic = _solve_dates_heuristic(combined_dates)
                    for k, v in date_logic.items():
                         if k not in ai_front_data: ai_front_data[k] = v

            except Exception as e:
                logger.error(f"❌ Extraction Frontend Error: {e}")

        if ocr_texts["BACK"]:
             # Estrazione minima retro (regex CF, etc)
             try:
                 print("   ⚡ [EXTRACTION] Running Regex on BACK...")
                 regex_data_back = _regex_fallback(ocr_texts["BACK"], context="BACK", doc_specs=doc_specs)
                 ai_back_data.update(regex_data_back)
             except Exception as e: 
                 logger.error(f"❌ Extraction Backend Error: {e}")

        # 6. MERGE & VALIDATE
        merged = {**ai_front_data, **ai_back_data}
        if mrz_data:
            print("   🧬 [MERGE] Integrazione dati MRZ...")
            # MRZ è altamente affidabile per certi campi
            if "data_nascita" in mrz_data: merged["data_nascita"] = mrz_data["data_nascita"]
            if "scadenza_documento" in mrz_data: merged["scadenza_documento"] = mrz_data["scadenza_documento"]
            if "numero_documento" in mrz_data: merged["numero_documento"] = mrz_data["numero_documento"]
            if "cittadinanza" in mrz_data: merged["cittadinanza"] = mrz_data["cittadinanza"]
            
            # Per Nome/Cognome, MRZ è spesso troncato. Usiamo AI se differenza lunghezza significativa
            for k in ["nome", "cognome"]:
                if k in mrz_data:
                    if k not in merged: merged[k] = mrz_data[k]
                    elif len(mrz_data[k]) > len(merged[k]): merged[k] = mrz_data[k] # MRZ spesso vince

        final_data.update(merged)
        final_data["debug_log"] = debug_log
        
        print(f"✅ ANALISI COMPLETATA. Campi trovati: {len(merged)}")
        return final_data

    except Exception as e:
        logger.critical(f"🔥 FATAL ERROR in analyze_documents_locally: {e}", exc_info=True)
        return {"error": "Internal Server Error during Scanning", "details": str(e)}