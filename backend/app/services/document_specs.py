from __future__ import annotations
import re

# ==============================================================================
# DOCUMENT SPECIFICATIONS & REGEX KNOWLEDGE BASE
# Reference: Configurazione Nuovi Campi Documenti Stranieri.pdf (Sez. 3, 6.1)
# ==============================================================================

# Regex universale per date (dd/mm/yyyy, dd.mm.yyyy, dd-mm-yyyy)
# Fonte: Tabella 1, Sez 6.1 [cite: 887]
GENERIC_DATE_REGEX = re.compile(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](19|20)\d{2}\b")

DOCUMENT_SPECS = {
    "CIE": {
        # Keywords per il "Promo Step" (Validazione preliminare) [cite: 726]
        "keywords": [
            "CARTA D'IDENTITA", 
            "IDENTITY CARD", 
            "REPUBBLICA ITALIANA",
            "MINISTERO DELL'INTERNO"
        ],
        # Regex Rigida CIE 3.0: Inizia con C, 1 lettera, 5 numeri, 2 lettere 
        "doc_number_regex": re.compile(r"\b[C][A-Z]\d{5}[A-Z]{2}\b"),
        "has_mrz": True,
        "required_sides": ["FRONT", "BACK"], # Retro obbligatorio per indirizzo 
        "date_format": "%d/%m/%Y",
        "description": "Carta d'Identità Elettronica Italiana"
    },

    "PATENTE_IT": {
        # Keywords identificative [cite: 773]
        "keywords": [
            "PATENTE DI GUIDA", 
            "DRIVING LICENSE", 
            "REPUBBLICA ITALIANA"
        ],
        # Regex Unificata: Formato Card (2L 7N 1L) O Formato U1 (U1 + 7+ alfanum) [cite: 781, 886]
        "doc_number_regex": re.compile(r"(?i)\b(U1[0-9A-Z]{7,}|[A-Z]{2}\d{7}[A-Z])\b"),
        "has_mrz": False,
        "required_sides": ["FRONT", "BACK"], # UPDATE: Retro reso obbligatorio per estrazione ente/indirizzo
        "date_format": "%d/%m/%Y",
        "description": "Patente di Guida Italiana"
    },

    "PASSAPORTO": {
        "keywords": [
            "PASSAPORTO", 
            "PASSPORT"
        ],
        # Standard Internazionale Generico (9 chars) o Italiano (2L 7N) 
        # Usiamo il pattern ICAO 9 chars come baseline robusta
        "doc_number_regex": re.compile(r"\b[A-Z0-9]{9}\b"),
        "has_mrz": True,
        "required_sides": ["FRONT"], # Indirizzo non affidabile su passaporto [cite: 764]
        "date_format": "%d %b %Y", # Es. 22 JAN 2026
        "description": "Passaporto Internazionale/Italiano"
    },

    "CI_CARTACEA": {
        "keywords": [
            "CARTA D'IDENTITA", 
            "REPUBBLICA ITALIANA", 
            "CONNOTATI"
        ],
        # Vecchio formato cartaceo: 2 lettere + 7 numeri (spesso con spazi)
        "doc_number_regex": re.compile(r"\b[A-Z]{2}\s?\d{7}\b"),
        "has_mrz": False,
        "required_sides": ["FRONT", "BACK"], # Dati sparsi su due lati
        "date_format": "%d/%m/%Y",
        "description": "Carta d'Identità Cartacea (Vecchio Modello)"
    },

    "PERMESSO_SOGGIORNO": {
        "keywords": [
            "PERMESSO DI SOGGIORNO", 
            "RESIDENCE PERMIT"
        ],
        # Pattern generico alphanumeric
        "doc_number_regex": re.compile(r"\b[A-Z0-9]{8,12}\b"),
        "has_mrz": True,
        "required_sides": ["FRONT", "BACK"], # UPDATE: Obbligatorio per sicurezza
        "date_format": "%d/%m/%Y",
        "description": "Permesso di Soggiorno"
    },

    "ALTRO": {
        "keywords": [],
        "doc_number_regex": None, # Nessuna validazione rigida, ci affidiamo a GLINER [cite: 892]
        "has_mrz": False,
        "required_sides": ["FRONT", "BACK"], # UPDATE: Obbligatorio per massimizzare info estratte
        "date_format": "%d/%m/%Y",
        "description": "Documento Generico / Estero non classificato"
    }
}

# Alias per CIE Europee generiche (mappate come logica light)
DOCUMENT_SPECS["CIE_EU"] = {
    "keywords": ["IDENTITY CARD", "PERSONALAUSWEIS", "CARTE D'IDENTITE"],
    "doc_number_regex": re.compile(r"\b[A-Z0-9]{8,12}\b"), # [cite: 833]
    "has_mrz": True,
    "required_sides": ["FRONT", "BACK"],
    "date_format": "%d/%m/%Y",
    "description": "Carta d'Identità UE (Non Italiana)"
}