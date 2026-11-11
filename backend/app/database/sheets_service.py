"""
app/database/sheets_service.py - Integrasi Google Sheets API (Service Account)
Mendukung Spreadsheet ID: 1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8
"""
import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("sheets_service")

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


class GoogleSheetsService:
    def __init__(self, spreadsheet_id: str, credentials_json_path: str = "", credentials_base64: str = ""):
        self.spreadsheet_id = spreadsheet_id
        self.credentials_json_path = credentials_json_path
        self.credentials_base64 = credentials_base64
        self.service = None
        self.is_connected = False
        self.last_error = None
        self._initialize_service()

    def _initialize_service(self):
        if not GOOGLE_LIBS_AVAILABLE:
            self.last_error = "Pustaka google-api-python-client atau google-auth belum terpasang"
            self.is_connected = False
            return

        creds = None
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            
            # Prioritas 1: Base64 string dari environment
            if self.credentials_base64:
                json_str = base64.b64decode(self.credentials_base64).decode("utf-8")
                info = json.loads(json_str)
                creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
            # Prioritas 2: Path file JSON
            elif self.credentials_json_path and os.path.exists(self.credentials_json_path):
                creds = service_account.Credentials.from_service_account_file(self.credentials_json_path, scopes=scopes)
            # Prioritas 3: Cek file service_account.json di direktori kerja
            elif os.path.exists("service_account.json"):
                creds = service_account.Credentials.from_service_account_file("service_account.json", scopes=scopes)
            else:
                self.last_error = "Kredensial Service Account Google Sheets belum dikonfigurasi (NEEDS_CONFIGURATION)"
                self.is_connected = False
                return

            self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)
            # Verifikasi koneksi dengan membaca metadata spreadsheet secara aman
            sheet_meta = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            self.is_connected = True
            self.last_error = None
            logger.info(f"Google Sheets terhubung: {sheet_meta.get('properties', {}).get('title')}")
        except Exception as e:
            self.is_connected = False
            self.last_error = f"Gagal menghubungkan ke Google Sheets: {str(e)}"
            logger.warning(self.last_error)

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "spreadsheet_id": self.spreadsheet_id,
            "status": "CONNECTED" if self.is_connected else "NEEDS_CONFIGURATION",
            "error": self.last_error,
            "google_libs_available": GOOGLE_LIBS_AVAILABLE
        }

    def list_sheet_names(self) -> List[str]:
        if not self.is_connected or not self.service:
            return []
        try:
            meta = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            return [s["properties"]["title"] for s in meta.get("sheets", [])]
        except Exception as e:
            logger.error(f"Gagal mengambil nama sheet: {e}")
            return []

    def ensure_sheet_exists(self, sheet_name: str, headers: List[str]):
        """Membuat sheet baru jika belum ada dan mengisi baris header tanpa merusak data lama."""
        if not self.is_connected or not self.service:
            return False
        try:
            sheets = self.list_sheet_names()
            if sheet_name not in sheets:
                body = {
                    "requests": [{
                        "addSheet": {
                            "properties": {"title": sheet_name}
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
                # Tulis header
                self.append_row(sheet_name, headers)
            return True
        except Exception as e:
            logger.error(f"Gagal memastikan sheet {sheet_name}: {e}")
            return False

    def append_row(self, sheet_name: str, values: List[Any]) -> bool:
        if not self.is_connected or not self.service:
            return False
        try:
            body = {"values": [values]}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Gagal append row ke {sheet_name}: {e}")
            return False

    def read_sheet(self, sheet_name: str) -> List[List[Any]]:
        if not self.is_connected or not self.service:
            return []
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:Z5000"
            ).execute()
            return result.get("values", [])
        except Exception as e:
            logger.error(f"Gagal membaca sheet {sheet_name}: {e}")
            return []
