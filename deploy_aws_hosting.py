"""
deploy_aws_hosting.py - AWS EC2 Hosting Deployment Engine
UKK Assessment Platform - SMKN 1 Banyumas

Menyediakan automated provisioning untuk hosting aplikasi UKK Assessment Platform
pada satu EC2 Ubuntu 24.04 LTS di AWS Academy Learner Lab.

Usage:
  python deploy_aws_hosting.py --plan
  python deploy_aws_hosting.py --apply [--token <CLOUDFLARE_TUNNEL_TOKEN>]
"""

import argparse
import base64
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Konstanta Konfigurasi
REGION = "us-east-1"
INSTANCE_NAME = "ukk-assessment-hosting-server"
SG_NAME = "ukk-assessment-hosting-sg"
PROJECT_TAG = "UKK-Assessment-Platform"
INSTANCE_TYPE = "t3.small"
FALLBACK_INSTANCE_TYPE = "t3.micro"
ROOT_VOLUME_SIZE_GB = 25  # 25 GB gp3
IAM_PROFILE_NAME = "LabInstanceProfile"
KEY_PAIR_NAME = "vockey"
REPO_URL = "https://github.com/yasss31/ukk-assessment-platform.git"


def get_ubuntu_2404_ami(ec2_client, ssm_client) -> str:
    """Mendapatkan AMI ID terbaru Ubuntu 24.04 LTS (Noble) gp3 di region target."""
    try:
        param = ssm_client.get_parameter(
            Name="/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
        )
        return param["Parameter"]["Value"]
    except Exception:
        # Fallback query via describe_images
        resp = ec2_client.describe_images(
            Owners=["099720109477"],
            Filters=[
                {"Name": "name", "Values": ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]},
                {"Name": "state", "Values": ["available"]}
            ]
        )
        imgs = sorted(resp["Images"], key=lambda x: x["CreationDate"], reverse=True)
        if imgs:
            return imgs[0]["ImageId"]
        return "ami-08b275ac6cc5dbefb"  # Fixed verified noble ami


def generate_user_data() -> str:
    """Menghasilkan user-data bootstrap script untuk Ubuntu 24.04 tanpa secret token."""
    script = f"""#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "=== [1/5] MEMULAI BOOTSTRAP HOSTING UKK ASSESSMENT PLATFORM ==="
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release git

echo "=== [2/5] INSTALL DOCKER & DOCKER COMPOSE ==="
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

echo "=== [3/5] CLONE REPOSITORY APLIKASI ==="
mkdir -p /opt/ukk-assessment-platform
cd /opt

if [ -d "/opt/ukk-assessment-platform/.git" ]; then
    echo "Repo already exists. Pulling latest main..."
    cd /opt/ukk-assessment-platform
    git pull origin main || true
else
    git clone {REPO_URL} /opt/ukk-assessment-platform
    cd /opt/ukk-assessment-platform
fi

chown -R ubuntu:ubuntu /opt/ukk-assessment-platform

echo "=== [4/5] KONFIGURASI ENVIRONMENT SECRETS ==="
mkdir -p /opt/ukk-assessment-platform/backend/local_storage
chown -R ubuntu:ubuntu /opt/ukk-assessment-platform/backend/local_storage

# Tulis file .env di root dengan token kosong (diisi terpisah oleh admin)
cat << 'EOF' > /opt/ukk-assessment-platform/.env
APP_NAME=UKK Assessment Platform
HOST=0.0.0.0
PORT=8000
DEBUG=false
SECRET_KEY=ukk-production-session-key-$(openssl rand -hex 16)
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=adminukk2026
GOOGLE_SPREADSHEET_ID=1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8
CORS_ORIGINS=*
CLOUDFLARE_TUNNEL_TOKEN=
EOF

chown ubuntu:ubuntu /opt/ukk-assessment-platform/.env
chmod 600 /opt/ukk-assessment-platform/.env

echo "=== [5/5] BUILD DAN JALANKAN CONTAINER DOCKER COMPOSE ==="
cd /opt/ukk-assessment-platform
docker compose up -d --build

echo "=== BOOTSTRAP SELESAI PADA $(date) ==="
"""
    return script


def get_default_vpc_and_subnet(ec2_client) -> Tuple[str, str]:
    """Mendapatkan Default VPC dan salah satu subnet public di dalamnya."""
    vpcs = ec2_client.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    if not vpcs:
        raise RuntimeError("Default VPC tidak ditemukan pada akun ini.")
    vpc_id = vpcs[0]["VpcId"]

    subnets = ec2_client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    if not subnets:
        raise RuntimeError(f"Tidak ada subnet ditemukan di default VPC {vpc_id}")
    
    # Pilih subnet di us-east-1a jika ada, atau subnet pertama
    chosen = next((s["SubnetId"] for s in subnets if s.get("AvailabilityZone") == "us-east-1a"), subnets[0]["SubnetId"])
    return vpc_id, chosen


def ensure_security_group(ec2_client, vpc_id: str, dry_run: bool = False) -> str:
    """Membuat atau menggunakan Security Group minimal untuk EC2 hosting."""
    try:
        sgs = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [SG_NAME]}, {"Name": "vpc-id", "Values": [vpc_id]}]
        )["SecurityGroups"]
        if sgs:
            return sgs[0]["GroupId"]
    except Exception:
        pass

    if dry_run:
        return "sg-dry-run-placeholder"

    # Buat Security Group baru
    resp = ec2_client.create_security_group(
        GroupName=SG_NAME,
        Description="Security Group untuk hosting UKK Assessment Platform (SSH, HTTP, Cloudflare)",
        VpcId=vpc_id,
        TagSpecifications=[{
            "ResourceType": "security-group",
            "Tags": [
                {"Key": "Name", "Value": SG_NAME},
                {"Key": "Project", "Value": PROJECT_TAG}
            ]
        }]
    )
    sg_id = resp["GroupId"]

    # Rule Inbound: SSH (22) dan HTTP (80)
    # Port 8000 TIDAK dibuka ke publik (least privilege: hanya internal docker/tunnel)
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH Admin (vockey key)"}]
            },
            {
                "IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP Frontend Direct"}]
            }
        ]
    )
    return sg_id


def find_existing_instance(ec2_client) -> Optional[Dict[str, Any]]:
    """Mencari instance hosting yang sudah ada."""
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
    parser = argparse.ArgumentParser(description="AWS EC2 Hosting Deployment Script")
    parser.add_argument("--plan", action="store_true", help="Tampilkan rencana deployment tanpa membuat resource")
    parser.add_argument("--apply", action="store_true", help="Eksekusi pembuatan/pembaruan EC2 instance di AWS")
    args = parser.parse_args()

    if not args.plan and not args.apply:
        print("[INFO] Jalankan dengan --plan untuk simulasi atau --apply untuk eksekusi.")
        sys.exit(0)

    print("=============================================================================")
    print("  UKK ASSESSMENT PLATFORM - AWS EC2 HOSTING DEPLOYMENT")
    print("  Region: us-east-1 | OS: Ubuntu 24.04 LTS | Runtime: Docker Compose")
    print("=============================================================================\n")

    # 1. Autentikasi STS
    try:
        session = boto3.Session(region_name=REGION)
        sts = session.client("sts")
        caller = sts.get_caller_identity()
        account_id = caller.get("Account")
        print(f"[AUTH OK] Terhubung ke AWS Account: {account_id}")
        print(f"          Caller ARN: {caller.get('Arn')}")
    except Exception as e:
        print(f"[ERROR] Gagal verifikasi kredensial AWS STS: {e}")
        sys.exit(1)

    ec2 = session.client("ec2", region_name=REGION)
    ssm = session.client("ssm", region_name=REGION)

    # 2. Cek apakah instance sudah ada (Idempotensi)
    existing_instance = find_existing_instance(ec2)
    if existing_instance:
        iid = existing_instance["InstanceId"]
        state = existing_instance["State"]["Name"]
        pub_ip = existing_instance.get("PublicIpAddress", "Belum ada (Stopped)")
        print(f"\n[INFO] Ditemukan instance hosting eksisting: {iid}")
        print(f"       Status: {state.upper()} | Public IP: {pub_ip}")
        if state == "stopped":
            print(f"       Instance sedang stopped. Anda dapat menjalankannya dengan:")
            print(f"       python stop_aws_hosting.py --start")
        elif state == "running":
            print(f"       Instance sudah running. Untuk update aplikasi gunakan:")
            print(f"       python update_application.py")
        return

    # 3. Kumpulkan informasi target
    vpc_id, subnet_id = get_default_vpc_and_subnet(ec2)
    ami_id = get_ubuntu_2404_ami(ec2, ssm)

    print(f"\n[TARGET AWS]")
    print(f"  VPC (Default) : {vpc_id}")
    print(f"  Subnet Public : {subnet_id}")
    print(f"  AMI Target    : {ami_id} (Ubuntu Server 24.04 LTS)")
    print(f"  Instance Type : {INSTANCE_TYPE} (Fallback: {FALLBACK_INSTANCE_TYPE})")
    print(f"  Root Storage  : {ROOT_VOLUME_SIZE_GB} GB gp3")
    print(f"  IAM Profile   : {IAM_PROFILE_NAME}")
    print(f"  Key Pair      : {KEY_PAIR_NAME}")

    print("\n[ESTIMASI BIAYA AWS ACADEMY]")
    print("  - EC2 t3.small       : ~$0.0208 / jam (~$0.08 per 4 jam sesi)")
    print(f"  - EBS gp3 {ROOT_VOLUME_SIZE_GB} GB      : ~$1.60 / bulan (~$0.002 per jam)")
    print("  - Cloudflare Tunnel  : $0.00 (Free)")
    print("  - NAT Gateway        : $0.00 (TIDAK DIGUNAKAN)")
    print("  - ALB / RDS / EFS    : $0.00 (TIDAK DIGUNAKAN)")
    print("  - TOTAL PER SESI     : < $0.10 dari saldo $100 AWS Academy")

    if args.plan:
        print("\n=============================================================================")
        print("  [PLAN MODE SELESAI] Tidak ada resource yang dibuat.")
        print("  Untuk mulai provisioning EC2 hosting, jalankan:")
        print("  python deploy_aws_hosting.py --apply [--token <CLOUDFLARE_TUNNEL_TOKEN>]")
        print("=============================================================================")
        return

    # Mode APPLY
    print("\n[APPLY] Memulai pembuatan Security Group & EC2 Instance...")
    sg_id = ensure_security_group(ec2, vpc_id, dry_run=False)
    print(f"  [OK] Security Group siap: {sg_id}")

    user_data_script = generate_user_data()

    try:
        run_args = {
            "ImageId": ami_id,
            "InstanceType": INSTANCE_TYPE,
            "KeyName": KEY_PAIR_NAME,
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": [sg_id],
            "SubnetId": subnet_id,
            "IamInstanceProfile": {"Name": IAM_PROFILE_NAME},
            "UserData": user_data_script,
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {
                        "VolumeSize": ROOT_VOLUME_SIZE_GB,
                        "VolumeType": "gp3",
                        "DeleteOnTermination": True
                    }
                }
            ],
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": INSTANCE_NAME},
                        {"Key": "Project", "Value": PROJECT_TAG},
                        {"Key": "Role", "Value": "UKK-Assessment-Hosting"}
                    ]
                }
            ]
        }
        res = ec2.run_instances(**run_args)
        instance = res["Instances"][0]
        instance_id = instance["InstanceId"]
        print(f"  [LAUNCH OK] EC2 Instance berhasil di-launch: {instance_id}")

        print("  [WAIT] Menunggu instance mencapai status RUNNING...")
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

        # Fetch IP publik
        desc = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
        pub_ip = desc.get("PublicIpAddress", "N/A")
        priv_ip = desc.get("PrivateIpAddress", "N/A")

        print(f"\n=============================================================================")
        print(f"  PROVISIONING EC2 SELESAI!")
        print(f"  Instance ID : {instance_id}")
        print(f"  Public IP   : {pub_ip}")
        print(f"  Private IP  : {priv_ip}")
        print(f"  Frontend    : http://{pub_ip}/")
        print(f"  Backend API : http://{pub_ip}:8000/docs")
        print(f"  SSH Command : ssh -i vockey.pem ubuntu@{pub_ip}")
        print("=============================================================================")
        print("  Catatan Bootstrap:")
        print("  Docker & Docker Compose sedang melakukan build & startup otomatis.")
        print("  Proses ini membutuhkan ~2-3 menit pada boot pertama.")
        print("  Jalankan 'python verify_aws_hosting.py' untuk memeriksa kesiapan server.")

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ["Unsupported", "InstanceLimitExceeded", "InsufficientInstanceCapacity"]:
            print(f"\n[WARNING] Instance type {INSTANCE_TYPE} terkendala ({code}). Mencoba fallback {FALLBACK_INSTANCE_TYPE}...")
            run_args["InstanceType"] = FALLBACK_INSTANCE_TYPE
            res = ec2.run_instances(**run_args)
            instance_id = res["Instances"][0]["InstanceId"]
            print(f"  [LAUNCH OK with fallback] Instance: {instance_id}")
        else:
            print(f"[ERROR] Gagal membuat EC2 Instance: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
