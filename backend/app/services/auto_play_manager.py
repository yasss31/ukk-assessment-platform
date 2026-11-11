"""
app/services/auto_play_manager.py - Pengelola Auto Play AWS Terjadwal & Aman
"""
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from app.database.storage import storage
from app.models.schemas import AutoPlayConfig, AutoPlayLog, AWSCredentialInput


class AWSAutoPlayManager:
    @staticmethod
    def get_config() -> AutoPlayConfig:
        raw = storage.get_autoplay_config()
        return AutoPlayConfig(**raw)

    @staticmethod
    def update_config(is_enabled: bool, interval_minutes: int = 180, target_instances: List[Dict] = None) -> AutoPlayConfig:
        current = storage.get_autoplay_config()
        current["is_enabled"] = is_enabled
        current["interval_minutes"] = max(15, interval_minutes)
        if target_instances is not None:
            current["target_instances"] = target_instances
        current["updated_at"] = datetime.utcnow().isoformat()
        
        if is_enabled:
            current["last_status"] = "SCHEDULED"
            next_time = datetime.utcnow() + timedelta(minutes=current["interval_minutes"])
            current["next_run"] = next_time.isoformat()
        else:
            current["last_status"] = "DISABLED"
            current["next_run"] = None

        storage.save_autoplay_config(current)
        
        # Log aksi
        log_entry = {
            "id": f"log-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "action": "CONFIG_UPDATE",
            "status": "SUCCESS",
            "account_id": None,
            "target_instance_id": None,
            "details": f"Auto Play diubah ke: {'ENABLED' if is_enabled else 'DISABLED'}, Interval: {current['interval_minutes']} menit"
        }
        storage.add_autoplay_log(log_entry)
        return AutoPlayConfig(**current)

    @staticmethod
    def run_auto_play_cycle(creds: AWSCredentialInput) -> Dict:
        """
        Menjalankan 1 siklus Auto Play secara aman:
        1. Validasi sesi AWS Academy
        2. Periksa instance yang ada di allowlist target
        3. Mulai (StartInstances) HANYA jika instance berstatus 'stopped'
        4. Terapkan idempotensi penuh (tidak memanggil berulang jika sudah running)
        """
        cfg = storage.get_autoplay_config()
        if not cfg.get("is_enabled"):
            return {"status": "SKIPPED", "message": "Auto Play sedang nonaktif (DISABLED)"}

        region = creds.aws_region or "us-east-1"
        try:
            session = boto3.Session(
                aws_access_key_id=creds.aws_access_key_id,
                aws_secret_access_key=creds.aws_secret_access_key,
                aws_session_token=creds.aws_session_token,
                region_name=region
            )
            sts = session.client("sts")
            identity = sts.get_caller_identity()
            account_id = identity.get("Account")

            ec2 = session.client("ec2")
            allowed_targets = [
                t["instance_id"] for t in cfg.get("target_instances", [])
                if t.get("is_allowed", True)
            ]

            if not allowed_targets:
                # Jika belum ada allowlist spesifik, ambil instance ber-tag mbg-ec2-*
                insts = ec2.describe_instances(Filters=[{"Name": "tag:Name", "Values": ["mbg-ec2-*"]}])
                found_targets = []
                for r in insts["Reservations"]:
                    for i in r["Instances"]:
                        if i["State"]["Name"] != "terminated":
                            found_targets.append(i["InstanceId"])
                allowed_targets = found_targets

            if not allowed_targets:
                msg = "Tidak ada target instance EC2 yang ditemukan atau terdaftar dalam allowlist"
                AWSAutoPlayManager._record_log("DISCOVERY", "EMPTY", account_id, None, msg)
                return {"status": "SUCCESS", "message": msg, "started_count": 0}

            # Periksa status aktual instance
            desc = ec2.describe_instances(InstanceIds=allowed_targets)
            stopped_instances = []
            running_instances = []

            for r in desc["Reservations"]:
                for i in r["Instances"]:
                    iid = i["InstanceId"]
                    state_name = i["State"]["Name"]
                    if state_name == "stopped":
                        stopped_instances.append(iid)
                    elif state_name == "running":
                        running_instances.append(iid)

            started_count = 0
            if stopped_instances:
                # Idempotency: nyalakan hanya yang benar-benar berstatus stopped
                ec2.start_instances(InstanceIds=stopped_instances)
                started_count = len(stopped_instances)
                msg = f"Berhasil mengirim StartInstances untuk {started_count} instance: {', '.join(stopped_instances)}"
                AWSAutoPlayManager._record_log("START_INSTANCES", "SUCCESS", account_id, str(stopped_instances), msg)
            else:
                msg = f"Seluruh {len(running_instances)} target instance sudah berstatus RUNNING. Tidak ada tindakan diperlukan (Idempotent)."
                AWSAutoPlayManager._record_log("CHECK_ONLY", "NOOP", account_id, None, msg)

            # Update schedule
            cfg["last_run"] = datetime.utcnow().isoformat()
            cfg["next_run"] = (datetime.utcnow() + timedelta(minutes=cfg.get("interval_minutes", 180))).isoformat()
            cfg["last_status"] = "SUCCESS"
            cfg["last_error"] = None
            storage.save_autoplay_config(cfg)

            return {
                "status": "SUCCESS",
                "account_id": account_id,
                "message": msg,
                "started_count": started_count,
                "running_count": len(running_instances)
            }

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            err_msg = f"AWS ClientError ({code}): {e.response.get('Error', {}).get('Message')}"
            AWSAutoPlayManager._record_log("ERROR", "FAILED", None, None, err_msg)
            cfg["last_status"] = "ERROR"
            cfg["last_error"] = err_msg
            storage.save_autoplay_config(cfg)
            return {"status": "ERROR", "error": err_msg}
        except Exception as ex:
            err_msg = f"Kesalahan Auto Play: {str(ex)}"
            AWSAutoPlayManager._record_log("ERROR", "FAILED", None, None, err_msg)
            cfg["last_status"] = "ERROR"
            cfg["last_error"] = err_msg
            storage.save_autoplay_config(cfg)
            return {"status": "ERROR", "error": err_msg}

    @staticmethod
    def _record_log(action: str, status_str: str, account_id: Optional[str], target_iid: Optional[str], details: str):
        log_entry = {
            "id": f"log-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "status": status_str,
            "account_id": account_id,
            "target_instance_id": target_iid,
            "details": details
        }
        storage.add_autoplay_log(log_entry)
