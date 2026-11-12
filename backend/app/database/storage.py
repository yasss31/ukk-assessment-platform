"""
app/database/storage.py - Unified Storage Layer (Local Persistence + Google Sheets Sync)
"""
import os
import json
import threading
from typing import List, Dict, Optional, Any
from pathlib import Path
from app.config import LOCAL_DATA_DIR, GOOGLE_SPREADSHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SERVICE_ACCOUNT_BASE64, STORAGE_MODE
from app.database.sheets_service import GoogleSheetsService
from app.models.schemas import (
    Participant, RubricProfile, RubricIndicator, AssessmentSession,
    AutoPlayConfig, AutoPlayLog, IndicatorStatus, AssessmentStatus
)

_LOCK = threading.Lock()


class DataStorage:
    def __init__(self):
        self.sheets_service = GoogleSheetsService(
            spreadsheet_id=GOOGLE_SPREADSHEET_ID,
            credentials_json_path=GOOGLE_SERVICE_ACCOUNT_JSON,
            credentials_base64=GOOGLE_SERVICE_ACCOUNT_BASE64
        )
        self.sheets = self.sheets_service

        self.participants_file = LOCAL_DATA_DIR / "participants.json"
        self.rubrics_file = LOCAL_DATA_DIR / "rubric_profiles.json"
        self.assessments_file = LOCAL_DATA_DIR / "assessments.json"
        self.autoplay_file = LOCAL_DATA_DIR / "autoplay_config.json"
        self.logs_file = LOCAL_DATA_DIR / "logs.json"

        self._init_local_data()

    def _load_json(self, file_path: Path, default_val: Any) -> Any:
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_val
        return default_val

    def _save_json(self, file_path: Path, data: Any):
        temp_file = file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(file_path)

    def _init_local_data(self):
        with _LOCK:
            # 1. Inisialisasi Peserta Contoh jika kosong
            if not self.participants_file.is_file():
                initial_participants = [
                    {
                        "id": "part-01",
                        "name": "Peserta Uji 1",
                        "participant_number": "UKK-CE-2627-001",
                        "student_class": "XII TKJ 1",
                        "school": "SMK Negeri 1 Banyumas",
                        "created_at": "2026-11-06T08:00:00"
                    },
                    {
                        "id": "part-02",
                        "name": "Peserta Uji 2",
                        "participant_number": "UKK-CE-2627-002",
                        "student_class": "XII TKJ 1",
                        "school": "SMK Negeri 1 Banyumas",
                        "created_at": "2026-11-06T08:00:00"
                    }
                ]
                self._save_json(self.participants_file, initial_participants)

            # 2. Inisialisasi Profil Rubrik Default: UKK Cloud Engineer 2026/2027 - MBG
            if not self.rubrics_file.is_file():
                default_profile = self._get_default_ukk_profile()
                self._save_json(self.rubrics_file, [default_profile])

            # 3. Inisialisasi Auto Play Config jika kosong
            if not self.autoplay_file.is_file():
                initial_autoplay = {
                    "is_enabled": False,
                    "interval_minutes": 180,
                    "max_retries": 3,
                    "target_instances": [],
                    "last_run": None,
                    "next_run": None,
                    "last_status": "IDLE",
                    "last_error": None,
                    "updated_at": "2026-11-06T08:00:00"
                }
                self._save_json(self.autoplay_file, initial_autoplay)

    def _get_default_ukk_profile(self) -> Dict:
        """Profil Penilaian Resmi UKK Cloud Engineer 2026/2027 (Program MBG)"""
        indicators = [
            # 01. VPC & Subnets (Bobot 6)
            {"id": "IND-01-01", "code": "01.01", "name": "Keberadaan & CIDR mbg-vpc (10.20.0.0/16)", "category": "Network", "expected_value": "10.20.0.0/16", "weight": 1.0, "check_method": "aws_vpc_cidr"},
            {"id": "IND-01-02", "code": "01.02", "name": "Subnet Public ALB 1a & 1b (Auto-assign IP = True)", "category": "Network", "expected_value": "2 subnets / Public", "weight": 1.5, "check_method": "aws_public_subnets"},
            {"id": "IND-01-03", "code": "01.03", "name": "Subnet Private FE 1a & 1b (Auto-assign IP = False)", "category": "Network", "expected_value": "2 subnets / Private", "weight": 1.5, "check_method": "aws_private_fe_subnets"},
            {"id": "IND-01-04", "code": "01.04", "name": "Subnet Private BE (Auto-assign IP = False)", "category": "Network", "expected_value": "1 subnet / Private", "weight": 1.0, "check_method": "aws_private_be_subnet"},
            {"id": "IND-01-05", "code": "01.05", "name": "Subnet Database 1a & 1b (Isolasi tanpa default route)", "category": "Network", "expected_value": "2 subnets / No default route", "weight": 1.0, "check_method": "aws_db_subnets"},
            
            # 02. IGW, NAT GW & Routing (Bobot 6)
            {"id": "IND-02-01", "code": "02.01", "name": "Internet Gateway mbg-igw attached ke mbg-vpc", "category": "Network", "expected_value": "Attached to mbg-vpc", "weight": 1.5, "check_method": "aws_igw_attached"},
            {"id": "IND-02-02", "code": "02.02", "name": "NAT Gateway mbg-natgw-1a di Subnet Public 1a (Available)", "category": "Network", "expected_value": "Available with Elastic IP", "weight": 2.5, "check_method": "aws_nat_gateway"},
            {"id": "IND-02-03", "code": "02.03", "name": "Route Tables Public (-> IGW) dan Private (-> NAT GW)", "category": "Network", "expected_value": "Routing associations valid", "weight": 2.0, "check_method": "aws_route_tables"},

            # 03. Security Groups (Bobot 6)
            {"id": "IND-03-01", "code": "03.01", "name": "5 Security Groups MBG terkonfigurasi (ALB, FE, BE, RDS, EFS)", "category": "Security", "expected_value": "5 SGs present", "weight": 3.0, "check_method": "aws_security_groups_list"},
            {"id": "IND-03-02", "code": "03.02", "name": "Inbound Rules SG (EFS hanya menerima port 2049 dari mbg-sg-fe)", "category": "Security", "expected_value": "mbg-sg-efs source: mbg-sg-fe", "weight": 3.0, "check_method": "aws_sg_inbound_rules"},

            # 04. RDS MySQL (Bobot 6)
            {"id": "IND-04-01", "code": "04.01", "name": "RDS mbg-rds-mysql (db.t3.micro, status: available, Private)", "category": "Database", "expected_value": "available / PubliclyAccessible: False", "weight": 4.0, "check_method": "aws_rds_status"},
            {"id": "IND-04-02", "code": "04.02", "name": "DB Subnet Group mbg-db-subnet-group multi-AZ", "category": "Database", "expected_value": "2 AZs (us-east-1a, 1b)", "weight": 2.0, "check_method": "aws_db_subnet_group"},

            # 05. S3 Bucket (Bobot 5)
            {"id": "IND-05-01", "code": "05.01", "name": "S3 Bucket Regional Namespace (mbg-uploads-*), Block Public Access 100%", "category": "Storage", "expected_value": "All 4 BPA flags True", "weight": 3.0, "check_method": "aws_s3_bucket"},
            {"id": "IND-05-02", "code": "05.02", "name": "Prefix S3 aduan/ dan laporan/ terkonfigurasi", "category": "Storage", "expected_value": "aduan/ and laporan/ exist", "weight": 2.0, "check_method": "aws_s3_prefixes"},

            # 06. SNS Notifikasi (Bobot 5)
            {"id": "IND-06-01", "code": "06.01", "name": "Topic mbg-sns-notifikasi ada", "category": "Notification", "expected_value": "Standard Topic active", "weight": 2.0, "check_method": "aws_sns_topic"},
            {"id": "IND-06-02", "code": "06.02", "name": "Subscription email BGN terkonfirmasi (Confirmed)", "category": "Notification", "expected_value": "Confirmed (Not PendingConfirmation)", "weight": 3.0, "check_method": "aws_sns_subscription_confirmed"},

            # 07. EC2 Back End (Bobot 6)
            {"id": "IND-07-01", "code": "07.01", "name": "EC2 mbg-ec2-be (t3.micro, subnet private be, tanpa IP publik)", "category": "Compute", "expected_value": "running / No Public IP", "weight": 6.0, "check_method": "aws_ec2_be_specs"},

            # 08. Launch Template FE (Bobot 6)
            {"id": "IND-08-01", "code": "08.01", "name": "Launch Template mbg-lt-fe menggunakan Custom AMI mbg-ami-fe (Revisi 1)", "category": "Compute", "expected_value": "ImageId = mbg-ami-fe", "weight": 4.0, "check_method": "aws_lt_fe_ami"},
            {"id": "IND-08-02", "code": "08.02", "name": "UserData mbg-lt-fe auto-mount EFS persisten dan start Apache", "category": "Compute", "expected_value": "Contains mount -a & httpd", "weight": 2.0, "check_method": "aws_lt_fe_userdata"},

            # 09. Auto Scaling Group (Bobot 7)
            {"id": "IND-OFFICIAL-09", "code": "ASPEK-09", "name": "Auto Scaling Group mbg-asg-fe (subnet private, multi-AZ & CPU 60%)", "category": "Compute", "expected_value": "Min/Desired/Max 2/2/4, multi-AZ, Target Tracking CPU 60%", "weight": 7.0, "check_method": "official_grader_asg"},

            # 10. Target Group (Bobot 5)
            {"id": "IND-OFFICIAL-10", "code": "ASPEK-10", "name": "Target Group mbg-tg-fe", "category": "Load Balancing", "expected_value": "HTTP:80, health path /health.php, >=2 healthy", "weight": 5.0, "check_method": "official_grader_tg"},

            # 11. Application Load Balancer (Bobot 6)
            {"id": "IND-OFFICIAL-11", "code": "ASPEK-11", "name": "Application Load Balancer mbg-alb-fe", "category": "Load Balancing", "expected_value": "internet-facing, public ALB 1a/1b, HTTP 200", "weight": 6.0, "check_method": "official_grader_alb"},

            # 12. Back End Database & Auto-migration (Bobot 5)
            {"id": "IND-OFFICIAL-12", "code": "ASPEK-12", "name": "Back End berjalan & auto-migration database (via SSM)", "category": "Application", "expected_value": "status: ok, db/s3/sns connected, tables exist, seeded", "weight": 5.0, "check_method": "official_grader_be"},

            # 13. SNS Email Delivery Metric (Bobot 6)
            {"id": "IND-OFFICIAL-13", "code": "ASPEK-13", "name": "Notifikasi email SNS saat aduan/laporan baru", "category": "Notification", "expected_value": "Published & Delivered >= 2, no error log", "weight": 6.0, "check_method": "official_grader_sns"},

            # 14. Uji Ketahanan Auto Scaling (Bobot 6 - Opsional / Default SKIP)
            {"id": "IND-OFFICIAL-14", "code": "ASPEK-14", "name": "Uji ketahanan Auto Scaling (terminate 1 instance FE)", "category": "Compute", "expected_value": "ASG launch replacement in < 5 mins (Opsional: SKIP)", "weight": 6.0, "check_method": "official_grader_asg_resilience"},

            # 15. Shared Session EFS (Bobot 6)
            {"id": "IND-OFFICIAL-15", "code": "ASPEK-15", "name": "EFS mbg-efs-fe-session & mount di instance FE", "category": "Storage", "expected_value": "Available, mount /mnt/efs/mbg-session, session.save_path OK", "weight": 6.0, "check_method": "official_grader_efs"},

            # 16. Multi-instance Session Sharing (Bobot 7)
            {"id": "IND-OFFICIAL-16", "code": "ASPEK-16", "name": "Session shared antar instance FE (bukti fungsi EFS)", "category": "Application", "expected_value": "No logout across FE instances, 30 requests consistent", "weight": 7.0, "check_method": "official_grader_session_sharing"},

            # 17. End-to-End Application Workflow (Bobot 6)
            {"id": "IND-OFFICIAL-17", "code": "ASPEK-17", "name": "Alur aplikasi end-to-end lewat ALB (login 3 role, aduan, upload S3)", "category": "Application", "expected_value": "Login 3 role, create aduan, upload S3, tanggapan, laporan", "weight": 6.0, "check_method": "official_grader_e2e"},
        ]
        total_w = sum(i["weight"] for i in indicators)
        return {
            "id": "default-ukk-mbg-rev1",
            "name": "UKK Cloud Engineer 2026/2027 - MBG (Revisi 1)",
            "version": "1.0",
            "description": "Profil penilaian resmi UKK Cloud Engineer SMK Negeri 1 Banyumas — Proyek Sistem Monitoring & Pelaporan MBG dengan AWS Academy Learner Lab (Revisi 1).",
            "indicators": indicators,
            "total_weight": total_w,
            "created_at": "2026-11-06T08:00:00",
            "updated_at": "2026-11-06T08:00:00"
        }

    # ==================== PARTICIPANTS CRUD ====================
    def list_participants(self) -> List[Any]:
        with _LOCK:
            data = self._load_json(self.participants_file, [])
            return [Participant(**p) if isinstance(p, dict) else p for p in data]

    def get_participant(self, participant_id: str) -> Optional[Participant]:
        for p in self.list_participants():
            if (p.id if hasattr(p, "id") else p["id"]) == participant_id:
                return p
        return None

    def add_participant(self, participant: Any) -> Participant:
        p_dict = participant.model_dump() if hasattr(participant, "model_dump") else (participant.dict() if hasattr(participant, "dict") else participant)
        with _LOCK:
            raw = self._load_json(self.participants_file, [])
            raw.append(p_dict)
            self._save_json(self.participants_file, raw)
            
            # Sync to Google Sheets if connected
            if self.sheets_service.is_connected:
                self.sheets_service.append_row("Peserta", [
                    p_dict["id"],
                    p_dict["name"],
                    p_dict["participant_number"],
                    p_dict["student_class"],
                    p_dict.get("school", ""),
                    p_dict.get("created_at", "")
                ])
        return Participant(**p_dict)

    def save_participant(self, participant: Any) -> Participant:
        return self.add_participant(participant)

    def delete_participant(self, participant_id: str) -> bool:
        with _LOCK:
            raw = self._load_json(self.participants_file, [])
            filtered = [p for p in raw if p["id"] != participant_id]
            if len(filtered) < len(raw):
                self._save_json(self.participants_file, filtered)
                return True
            return False

    # ==================== RUBRIC CRUD ====================
    def list_rubric_profiles(self) -> List[RubricProfile]:
        with _LOCK:
            data = self._load_json(self.rubrics_file, [])
            return [RubricProfile(**r) if isinstance(r, dict) else r for r in data]

    def list_rubrics(self) -> List[RubricProfile]:
        return self.list_rubric_profiles()

    def get_rubric_profile(self, profile_id: str) -> Optional[RubricProfile]:
        profiles = self.list_rubric_profiles()
        for r in profiles:
            if r.id == profile_id:
                return r
        # Fallback alias pencarian rubrik bawaan
        if profile_id in ["default-ukk-mbg-rev1", "prof-ukk-cloud-2026", "default"] and profiles:
            return profiles[0]
        return None


    def get_rubric(self, profile_id: str) -> Optional[RubricProfile]:
        return self.get_rubric_profile(profile_id)

    def save_rubric_profile(self, profile: Any) -> RubricProfile:
        r_dict = profile.model_dump() if hasattr(profile, "model_dump") else (profile.dict() if hasattr(profile, "dict") else profile)
        with _LOCK:
            raw = self._load_json(self.rubrics_file, [])
            idx = next((i for i, r in enumerate(raw) if r["id"] == r_dict["id"]), None)
            if idx is not None:
                raw[idx] = r_dict
            else:
                raw.append(r_dict)
            self._save_json(self.rubrics_file, raw)
            return RubricProfile(**r_dict)

    def save_rubric(self, profile: Any) -> RubricProfile:
        return self.save_rubric_profile(profile)

    def delete_rubric(self, profile_id: str) -> bool:
        with _LOCK:
            raw = self._load_json(self.rubrics_file, [])
            filtered = [r for r in raw if r["id"] != profile_id]
            if len(filtered) < len(raw):
                self._save_json(self.rubrics_file, filtered)
                return True
            return False

    # ==================== ASSESSMENTS CRUD ====================
    def list_assessments(self) -> List[Dict]:
        with _LOCK:
            return self._load_json(self.assessments_file, [])

    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        for a in self.list_assessments():
            if a["id"] == assessment_id:
                return a
        return None

    def save_assessment(self, session_data: Any) -> Dict:
        s_dict = session_data.model_dump() if hasattr(session_data, "model_dump") else (session_data.dict() if hasattr(session_data, "dict") else session_data)
        with _LOCK:
            data = self._load_json(self.assessments_file, [])
            idx = next((i for i, a in enumerate(data) if a["id"] == s_dict["id"]), None)
            if idx is not None:
                data[idx] = s_dict
            else:
                data.append(s_dict)
            self._save_json(self.assessments_file, data)

            # Sync to Google Sheets if completed and connected
            if s_dict.get("status") in [AssessmentStatus.COMPLETED, AssessmentStatus.FAILED]:
                if self.sheets_service.is_connected:
                    part = s_dict.get("participant", {})
                    self.sheets_service.append_row("Penilaian", [
                        s_dict["id"],
                        part.get("participant_number", ""),
                        part.get("name", ""),
                        s_dict.get("rubric_name", ""),
                        s_dict.get("total_score", 0.0),
                        s_dict.get("max_score", 100.0),
                        f"{s_dict.get('completion_percentage', 0)}%",
                        s_dict.get("status", ""),
                        s_dict.get("pass_count", 0),
                        s_dict.get("fail_count", 0),
                        s_dict.get("completed_at", "")
                    ])
            return s_dict

    # ==================== AUTOPLAY CRUD ====================
    def get_autoplay_config(self) -> Dict:
        with _LOCK:
            return self._load_json(self.autoplay_file, {
                "is_enabled": False,
                "interval_minutes": 180,
                "max_retries": 3,
                "target_instances": [],
                "last_run": None,
                "next_run": None,
                "last_status": "IDLE"
            })

    def save_autoplay_config(self, config_data: Dict) -> Dict:
        with _LOCK:
            self._save_json(self.autoplay_file, config_data)
            return config_data

    def add_autoplay_log(self, log_entry: Dict):
        with _LOCK:
            logs = self._load_json(self.logs_file, [])
            logs.insert(0, log_entry)  # newest first
            self._save_json(self.logs_file, logs[:200])  # keep last 200 logs

    def get_autoplay_logs(self, limit: int = 50) -> List[Dict]:
        with _LOCK:
            logs = self._load_json(self.logs_file, [])
            return logs[:limit]



storage = DataStorage()
