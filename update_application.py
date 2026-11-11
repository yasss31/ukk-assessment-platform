"""
update_application.py - Pembaruan Otomatis Aplikasi di AWS EC2
UKK Assessment Platform

Melakukan git pull dan docker compose up -d --build di EC2 hosting
menggunakan AWS Systems Manager (SSM) Run Command tanpa perlu SSH.
"""

import argparse
import sys
import time
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
INSTANCE_NAME = "ukk-assessment-hosting-server"


def get_instance_id(ec2_client):
    resp = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["running"]}
        ]
    )
    for r in resp.get("Reservations", []):
        for i in r.get("Instances", []):
            return i["InstanceId"], i.get("PublicIpAddress")
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Update Aplikasi di EC2 Hosting")
    parser.add_argument("--branch", default="main", help="Git branch target (default: main)")
    args = parser.parse_args()

    print("=============================================================================")
    print("  UPDATE APLIKASI DI AWS EC2 HOSTING")
    print("=============================================================================\n")

    session = boto3.Session(region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)
    ssm = session.client("ssm", region_name=REGION)

    iid, pub_ip = get_instance_id(ec2)
    if not iid:
        print("[ERROR] Instance EC2 hosting running tidak ditemukan!")
        sys.exit(1)

    print(f"[INFO] Target Instance: {iid} ({pub_ip})")
    print(f"[INFO] Branch Target  : {args.branch}")

    commands = [
        "export HOME=/root",
        "git config --system --add safe.directory /opt/ukk-assessment-platform || true",
        "cd /opt/ukk-assessment-platform",
        f"git fetch origin && git checkout {args.branch} && git pull origin {args.branch}",
        "docker compose up -d --build",
        "docker compose ps"
    ]

    print("[INFO] Mengirim SSM Run Command ke EC2...")
    try:
        resp = ssm.send_command(
            InstanceIds=[iid],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands},
            Comment="Update UKK Assessment Platform via Git Pull & Docker Rebuild"
        )
        cmd_id = resp["Command"]["CommandId"]
        print(f"[OK] Command ID: {cmd_id}")
        print("[WAIT] Menunggu eksekusi update selesai di EC2...")

        # Poll status SSM
        for _ in range(60):
            time.sleep(5)
            inv = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=iid)
            st = inv["Status"]
            if st in ["Success", "Failed", "Cancelled", "TimedOut"]:
                print(f"\n[HASIL UPDATE] Status: {st}")
                print("--- Output Konsol ---")
                print(inv.get("StandardOutputContent", "(Tidak ada output)"))
                if inv.get("StandardErrorContent"):
                    print("--- Error Konsol ---")
                    print(inv.get("StandardErrorContent"))
                break
            print(".", end="", flush=True)

    except ClientError as e:
        print(f"[WARNING] SSM Run Command belum siap atau gagal: {e}")
        print("\nFallback Manual via SSH:")
        print(f"  ssh -i vockey.pem ubuntu@{pub_ip}")
        print("  cd /opt/ukk-assessment-platform && git pull origin main && docker compose up -d --build")


if __name__ == "__main__":
    main()
