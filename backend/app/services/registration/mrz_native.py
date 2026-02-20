# backend/app/services/registration/mrz_native.py
from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MrzParsed:
    format: str
    doc_type: str
    issuer: str
    nationality: str
    surname: str
    given_names: str
    document_number: str
    birth_date: str   # YYMMDD
    sex: str
    expiry_date: str  # YYMMDD


class MrzNative:
    def __init__(self):
        dll_path = os.getenv("MRZ_DLL_PATH", os.path.join("backend", "native", "mrz", "build", "mrz.dll"))
        self.dll_path = os.path.abspath(dll_path)
        self.lib = None

        if os.path.exists(self.dll_path):
            try:
                self.lib = ctypes.CDLL(self.dll_path)
                self.lib.mrz_parse_td3.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
                self.lib.mrz_parse_td3.restype = ctypes.c_int
                self.lib.mrz_parse_td1.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
                self.lib.mrz_parse_td1.restype = ctypes.c_int
            except Exception:
                self.lib = None

    def parse_td3(self, line1: str, line2: str) -> Optional[dict]:
        if not self.lib:
            return None
        out = ctypes.create_string_buffer(2048)
        ok = self.lib.mrz_parse_td3(line1.encode("utf-8"), line2.encode("utf-8"), out, ctypes.sizeof(out))
        if ok != 1:
            return None
        import json
        return json.loads(out.value.decode("utf-8"))

    def parse_td1(self, line1: str, line2: str, line3: str) -> Optional[dict]:
        if not self.lib:
            return None
        out = ctypes.create_string_buffer(2048)
        ok = self.lib.mrz_parse_td1(line1.encode("utf-8"), line2.encode("utf-8"), line3.encode("utf-8"), out, ctypes.sizeof(out))
        if ok != 1:
            return None
        import json
        return json.loads(out.value.decode("utf-8"))
