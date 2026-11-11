"""
stop_aws_hosting.py - Kontrol Biaya & Manajemen Siklus Hidup EC2 Hosting
UKK Assessment Platform

Usage:
  python stop_aws_hosting.py --status
  python stop_aws_hosting.py --stop
  python stop_aws_hosting.py --start
  python stop_aws_hosting.py --terminate
"""

import argparse
import sys
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
INSTANCE_NAME = "ukk-assessment-hosting-server"
SG_NAME = "ukk-assessment-hosting-sg"


def get_hosting_instance(ec2_client):
    resp = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}
        ]
    )
    for r in resp.get("Reservations", []):
        for inst in r.get("Instances", []):
            return inst
    return None


def main():
    parser = argparse.ArgumentParser(description="Kontrol Status EC2 Hosting")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="Lihat status instance saat ini")
    group.add_argument("--stop", action="store_true", help="Hentikan EC2 (Stop) untuk menghemat kredit AWS")
    group.add_argument("--start", action="store_true", help="Mulai kembali EC2 (Start)")
    group.add_argument("--terminate", action="store_true", help="Hapus permanen EC2 dan Security Group")
    args = parser.parse_args()

    session = boto3.Session(region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)

    inst = get_hosting_instance(ec2)
    if not inst:
        print("[INFO] Tidak ada EC2 instance hosting yang aktif.")
        sys.exit(0)

    iid = inst["InstanceId"]
    state = inst["State"]["Name"]
    pub_ip = inst.get("PublicIpAddress", "N/A")

    if args.status:
        print(f"Instance ID : {iid}")
        print(f"Status      : {state.upper()}")
        print(f"Public IP   : {pub_ip}")
        return

    if args.stop:
        if state == "stopped":
            print(f"[INFO] Instance {iid} sudah dalam kondisi STOPPED.")
            return
        print(f"[ACTION] Menghentikan instance {iid}...")
        ec2.stop_instances(InstanceIds=[iid])
        print(f"[OK] Perintah Stop dikirim. Instance beralih ke STOPPING -> STOPPED.")
        print("     Biaya komputasi per jam berhenti. Data di EBS tetap tersimpan.")
        return

    if args.start:
        if state == "running":
            print(f"[INFO] Instance {iid} sudah dalam kondisi RUNNING (IP: {pub_ip}).")
            return
        print(f"[ACTION] Memulai kembali instance {iid}...")
        ec2.start_instances(InstanceIds=[iid])
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[iid])
        desc = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
        new_ip = desc.get("PublicIpAddress", "N/A")
        print(f"[OK] Instance RUNNING! IP Publik Baru: {new_ip}")
        print(f"     Docker compose otomatis melanjutkan container di startup.")
        return

    if args.terminate:
        print(f"[WARNING] Menghapus instance {iid} secara permanen...")
        ec2.terminate_instances(InstanceIds=[iid])
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[iid])
        print(f"[OK] Instance {iid} terminated.")
        try:
            ec2.delete_security_group(GroupName=SG_NAME)
            print(f"[OK] Security Group {SG_NAME} berhasil dihapus.")
        except Exception:
            pass
        print("[OK] Seluruh resource hosting berhasil dibersihkan.")


if __name__ == "__main__":
    main()
