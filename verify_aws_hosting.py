"""
verify_aws_hosting.py - Verifikasi Kesiapan Server Hosting AWS EC2
UKK Assessment Platform

Usage:
  python verify_aws_hosting.py [--domain https://domain-anda.com]
"""

import argparse
import sys
import time
from typing import Dict, Any, Optional
import urllib.request
import urllib.error
import json
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
INSTANCE_NAME = "ukk-assessment-hosting-server"


def get_hosting_instance(ec2_client) -> Optional[Dict[str, Any]]:
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


def check_http_endpoint(url: str, timeout: int = 5) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UKK-Health-Checker"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            code = response.getcode()
            content = response.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(content)
            except Exception:
                data = None
            return {"status": "OK", "code": code, "data": data}
    except urllib.error.HTTPError as e:
        return {"status": "HTTP_ERROR", "code": e.code, "error": str(e)}
    except Exception as e:
        return {"status": "CONN_ERROR", "code": None, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Verifikasi Kesiapan Hosting EC2")
    parser.add_argument("--domain", default=None, help="Domain Cloudflare Tunnel publik yang ingin diuji")
    args = parser.parse_args()

    print("=============================================================================")
    print("  VERIFIKASI HOSTING AWS EC2 - UKK ASSESSMENT PLATFORM")
    print("=============================================================================\n")

    try:
        session = boto3.Session(region_name=REGION)
        ec2 = session.client("ec2", region_name=REGION)
    except Exception as e:
        print(f"[ERROR] AWS Session init failed: {e}")
        sys.exit(1)

    inst = get_hosting_instance(ec2)
    if not inst:
        print("[FAIL] EC2 instance hosting 'ukk-assessment-hosting-server' tidak ditemukan!")
        print("       Jalankan: python deploy_aws_hosting.py --apply")
        sys.exit(1)

    iid = inst["InstanceId"]
    state = inst["State"]["Name"]
    pub_ip = inst.get("PublicIpAddress")

    print(f"1. Status Instance EC2:")
    print(f"   - Instance ID : {iid}")
    print(f"   - State       : {state.upper()}")
    print(f"   - Public IP   : {pub_ip or 'None'}")

    if state != "running":
        print(f"\n[ALERT] Instance berstatus '{state}'. Harus 'running' agar aplikasi dapat diakses.")
        if state == "stopped":
            print("Gunakan: python stop_aws_hosting.py --start")
        sys.exit(1)

    # 2. Cek System & Instance Status Checks
    status_resp = ec2.describe_instance_status(InstanceIds=[iid])
    if status_resp.get("InstanceStatuses"):
        st = status_resp["InstanceStatuses"][0]
        sys_st = st.get("SystemStatus", {}).get("Status", "unknown")
        inst_st = st.get("InstanceStatus", {}).get("Status", "unknown")
        print(f"   - System Status Check   : {sys_st.upper()}")
        print(f"   - Instance Status Check : {inst_st.upper()}")
    else:
        print("   - Status Check : Masih dalam proses inisialisasi...")

    if not pub_ip:
        print("\n[FAIL] Tidak ada Public IP pada EC2 instance.")
        sys.exit(1)

    print(f"\n2. Menguji Akses Port & Layanan (Public IP: {pub_ip}):")

    # Frontend Check
    fe_url = f"http://{pub_ip}/"
    fe_res = check_http_endpoint(fe_url)
    if fe_res["status"] == "OK":
        print(f"   [PASS] Frontend Web: HTTP {fe_res['code']} (Aplikasi web aktif)")
    else:
        print(f"   [WAIT] Frontend Web: {fe_res['status']} ({fe_res.get('error')})")
        print("          (Jika EC2 baru di-launch, tunggu 1-2 menit hingga docker compose selesai build)")

    # Backend Health Check
    be_url = f"http://{pub_ip}:8000/health"
    be_res = check_http_endpoint(be_url)
    if be_res["status"] == "OK":
        data = be_res.get("data", {})
        sheets_info = data.get("google_sheets", {})
        print(f"   [PASS] Backend API: HTTP {be_res['code']} (FastAPI Healthy)")
        print(f"          - Mode Storage  : {data.get('storage_mode')}")
        print(f"          - Google Sheets : {sheets_info.get('status')}")
    else:
        print(f"   [WAIT] Backend API: {be_res['status']} ({be_res.get('error')})")

    # 3. Domain Check jika disediakan
    if args.domain:
        domain_url = args.domain if args.domain.startswith("http") else f"https://{args.domain}"
        print(f"\n3. Menguji Akses Domain Cloudflare Tunnel ({domain_url}):")
        dom_res = check_http_endpoint(domain_url)
        if dom_res["status"] == "OK":
            print(f"   [PASS] Domain Publik: HTTP {dom_res['code']} - Tunnel Sukses Terhubung!")
        else:
            print(f"   [FAIL] Domain Publik: {dom_res['status']} ({dom_res.get('error')})")
            print("          Pastikan container cloudflared aktif dan token tunnel sesuai.")

    print("\n=============================================================================")
    print("  VERIFIKASI SELESAI")
    print("=============================================================================")


if __name__ == "__main__":
    main()
