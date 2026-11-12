"""
app/services/official_rubric_kb.py - Knowledge Base Pemetaan Resmi
Single Source of Truth: Soal_UKK Cloud Engineer_2627-Rev1.pdf
"""
from typing import Dict, Any, List
from app.models.schemas import ErrorSeverity

OFFICIAL_ASPEK_METADATA: Dict[str, Dict[str, Any]] = {
    "01": {
        "title": "VPC & Subnet (public hanya utk ALB, private utk FE/BE)",
        "weight": 6.0,
        "category": "Networking",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.1, Bab D.1, Bab E.1",
        "doc_pages": "Halaman 2-3, 5-6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.1 (Langkah 1-7)",
        "expected_condition": "VPC 'mbg-vpc' (10.20.0.0/16), 7 Subnet (2 public ALB, 2 private FE, 1 private BE, 2 DB). Auto-assign Public IP HANYA pada 2 subnet public ALB. Subnet private tanpa IP publik.",
        "troubleshooting_steps": [
            "Buka AWS Console -> VPC -> Subnets.",
            "Periksa apakah ke-7 subnet ada dan CIDR serta AZ sesuai tabel C.1.",
            "Pilih mbg-subnet-public-alb-1a dan 1b -> Actions -> Edit subnet settings -> Pastikan 'Enable auto-assign public IPv4 address' AKTIF.",
            "Pilih seluruh subnet private (FE, BE, DB) -> Pastikan auto-assign public IPv4 NONAKTIF.",
            "Periksa Route Table: subnet public terasosiasi ke mbg-rt-public (IGW), subnet private ke mbg-rt-private (NAT), subnet DB tanpa default route."
        ],
        "verification_steps": [
            "aws ec2 describe-vpcs --filters Name=tag:Name,Values=mbg-vpc",
            "aws ec2 describe-subnets --filters Name=vpc-id,<vpc-id>"
        ],
        "cli_command": "aws ec2 describe-subnets --filters \"Name=tag:Name,Values=mbg-subnet-*\" --query \"Subnets[*].{Name:Tags[?Key=='Name']|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch}\" --output table",
        "expected_output": "7 subnet terdaftar, public=True hanya pada mbg-subnet-public-alb-1a/1b"
    },
    "02": {
        "title": "Internet Gateway, NAT Gateway & Route Table",
        "weight": 6.0,
        "category": "Networking",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.2, Bab D.1, Bab E.2",
        "doc_pages": "Halaman 2-3, 5-6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.1 (Langkah 3-6)",
        "expected_condition": "IGW mbg-igw attached ke mbg-vpc. NAT Gateway mbg-natgw-1a berstatus available di mbg-subnet-public-alb-1a dengan 1 Elastic IP. Route Table public -> IGW, Route Table private -> NAT Gateway. Akses internet outbound dari EC2 private berhasil.",
        "troubleshooting_steps": [
            "Buka VPC -> Internet Gateways -> Pastikan mbg-igw ada dan status 'Attached' ke mbg-vpc.",
            "Buka VPC -> NAT Gateways -> Pastikan mbg-natgw-1a ada di mbg-subnet-public-alb-1a, status 'Available', memiliki 1 Elastic IP.",
            "Buka VPC -> Route Tables -> mbg-rt-public: route 0.0.0.0/0 -> mbg-igw, asosiasi hanya ke 2 subnet public ALB.",
            "Buka VPC -> Route Tables -> mbg-rt-private: route 0.0.0.0/0 -> mbg-natgw-1a, asosiasi ke private-fe-1a, private-fe-1b, private-be.",
            "Masuk ke EC2 private via Session Manager, uji curl https://aws.amazon.com untuk memastikan NAT berfungsi."
        ],
        "verification_steps": [
            "aws ec2 describe-nat-gateways --filter Name=tag:Name,Values=mbg-natgw-1a",
            "aws ec2 describe-route-tables --filter Name=tag:Name,Values=mbg-rt-*"
        ],
        "cli_command": "aws ec2 describe-nat-gateways --filter \"Name=tag:Name,Values=mbg-natgw-1a\" --query \"NatGateways[*].{ID:NatGatewayId,State:State,Subnet:SubnetId}\" --output table",
        "expected_output": "State = available, SubnetId = subnet public alb 1a"
    },
    "03": {
        "title": "Security Group & inbound rule",
        "weight": 6.0,
        "category": "Security",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.3, Bab D.2, Bab E.3",
        "doc_pages": "Halaman 3, 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.2 (Langkah 1)",
        "expected_condition": "5 Security Group: mbg-sg-alb (TCP 80), mbg-sg-fe (TCP 22, 80), mbg-sg-be (TCP 22, 80), mbg-sg-rds (TCP 3306), mbg-sg-efs (TCP 2049 dari mbg-sg-fe atau 0.0.0.0/0).",
        "troubleshooting_steps": [
            "Buka EC2 -> Security Groups.",
            "Periksa 5 SG: mbg-sg-alb, mbg-sg-fe, mbg-sg-be, mbg-sg-rds, mbg-sg-efs.",
            "Pastikan mbg-sg-efs memiliki Inbound Rule: NFS (TCP 2049) dengan source Security Group mbg-sg-fe.",
            "Pastikan mbg-sg-rds mengizinkan TCP 3306.",
            "Pastikan mbg-sg-alb mengizinkan TCP 80 dari 0.0.0.0/0."
        ],
        "verification_steps": [
            "aws ec2 describe-security-groups --filters Name=group-name,Values=mbg-sg-*"
        ],
        "cli_command": "aws ec2 describe-security-groups --filters \"Name=group-name,Values=mbg-sg-*\" --query \"SecurityGroups[*].{Name:GroupName,Rules:IpPermissions[*].{Proto:IpProtocol,Port:FromPort}}\" --output table",
        "expected_output": "Kelima security group terkonfigurasi dengan port 80, 22, 3306, 2049"
    },
    "04": {
        "title": "RDS MySQL",
        "weight": 6.0,
        "category": "Database",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.4, Bab D.3, Bab E.4",
        "doc_pages": "Halaman 3, 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.3 (Langkah 1-2)",
        "expected_condition": "RDS 'mbg-rds-mysql' MySQL Free Tier db.t3.micro, Single-AZ us-east-1a, master user 'admin', DB subnet group 'mbg-db-subnet-group' (subnet-db-1a & 1b), mbg-sg-rds, PubliclyAccessible=false.",
        "troubleshooting_steps": [
            "Buka RDS -> Databases -> Pilih mbg-rds-mysql.",
            "Pastikan status 'Available', class db.t3.micro, Public access 'No'.",
            "Periksa Subnet Group: mbg-db-subnet-group harus berisi 2 subnet DB (1a dan 1b).",
            "Periksa VPC Security Groups: terpasang mbg-sg-rds.",
            "Catat Endpoint RDS untuk digunakan di config.php Back End."
        ],
        "verification_steps": [
            "aws rds describe-db-instances --db-instance-identifier mbg-rds-mysql"
        ],
        "cli_command": "aws rds describe-db-instances --db-instance-identifier mbg-rds-mysql --query \"DBInstances[0].{Status:DBInstanceStatus,Class:DBInstanceClass,Public:PubliclyAccessible,SubnetGrp:DBSubnetGroup.DBSubnetGroupName}\" --output table",
        "expected_output": "Status = available, Class = db.t3.micro, Public = False"
    },
    "05": {
        "title": "S3 Bucket",
        "weight": 5.0,
        "category": "Storage",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.5, Bab D.4, Bab E.5",
        "doc_pages": "Halaman 3, 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.4 (Langkah 1)",
        "expected_condition": "Bucket 'mbg-uploads-<akun>-us-east-1-an' di region us-east-1, Block Public Access aktif (ke-4 opsi true), prefix folder 'aduan/' dan 'laporan/' tersedia.",
        "troubleshooting_steps": [
            "Buka S3 -> Buckets -> Cari bucket dengan pola mbg-uploads-<account-id>-us-east-1-an.",
            "Buka tab Permissions -> Block public access (bucket settings) -> Klik Edit -> Centang 'Block all public access' (seluruh 4 opsi aktif).",
            "Buka tab Objects -> Buat folder bernama 'aduan/' dan 'laporan/' jika belum ada."
        ],
        "verification_steps": [
            "aws s3api get-public-access-block --bucket <bucket-name>",
            "aws s3 ls s3://<bucket-name>/"
        ],
        "cli_command": "aws s3 ls | grep mbg-uploads",
        "expected_output": "Bucket berawalan mbg-uploads- terdaftar di us-east-1"
    },
    "06": {
        "title": "SNS Topic & Subscription Email",
        "weight": 5.0,
        "category": "Messaging",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.6, Bab D.5, Bab E.6",
        "doc_pages": "Halaman 4, 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.5 (Langkah 1-3)",
        "expected_condition": "SNS Topic 'mbg-sns-notifikasi' tipe Standard, Subscription protocol Email ke 'ukkce2627@smkn1bms.sch.id', status Confirmed.",
        "troubleshooting_steps": [
            "Buka Amazon SNS -> Topics -> Pastikan topic mbg-sns-notifikasi ada (Standard, bukan FIFO).",
            "Buka Subscriptions -> Pastikan ada subscription email ke ukkce2627@smkn1bms.sch.id.",
            "Jika status masih 'PendingConfirmation', buka inbox email tersebut dan klik tautan 'Confirm subscription'.",
            "Salin Topic ARN untuk dicantumkan di config.php Back End."
        ],
        "verification_steps": [
            "aws sns list-topics",
            "aws sns list-subscriptions-by-topic --topic-arn <topic-arn>"
        ],
        "cli_command": "aws sns list-subscriptions --query \"Subscriptions[?Endpoint=='ukkce2627@smkn1bms.sch.id'].{Topic:TopicArn,Status:SubscriptionArn}\" --output table",
        "expected_output": "Status bukan 'PendingConfirmation' (berisi ARN lengkap)"
    },
    "07": {
        "title": "EC2 Back End (mbg-ec2-be) di subnet private",
        "weight": 6.0,
        "category": "Compute",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.8, Bab D.6, Bab E.7",
        "doc_pages": "Halaman 4, 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.6 (Langkah 1-6)",
        "expected_condition": "EC2 instance running bernama 'mbg-ec2-be', type t3.micro, AMI Amazon Linux 2023, key pair vockey, subnet mbg-subnet-private-be, tanpa IP publik, SG mbg-sg-be, IAM Profile LabInstanceProfile.",
        "troubleshooting_steps": [
            "Buka EC2 -> Instances -> Cari mbg-ec2-be.",
            "Pastikan State 'Running', Instance Type 't3.micro', AMI Amazon Linux 2023.",
            "Pastikan SubnetId mengarah ke mbg-subnet-private-be dan Public IP kosong (Disabled).",
            "Pastikan IAM Instance Profile terpasang 'LabInstanceProfile' agar SSM Session Manager aktif.",
            "Masuk via Systems Manager Session Manager untuk mengelola server."
        ],
        "verification_steps": [
            "aws ec2 describe-instances --filters Name=tag:Name,Values=mbg-ec2-be"
        ],
        "cli_command": "aws ec2 describe-instances --filters \"Name=tag:Name,Values=mbg-ec2-be\" --query \"Reservations[0].Instances[0].{State:State.Name,Type:InstanceType,Subnet:SubnetId,PublicIP:PublicIpAddress,Profile:IamInstanceProfile.Arn}\" --output table",
        "expected_output": "State = running, PublicIP = None, Profile berisi LabInstanceProfile"
    },
    "08": {
        "title": "Launch Template mbg-lt-fe",
        "weight": 6.0,
        "category": "Compute",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.10, Bab D.7, Bab E.8",
        "doc_pages": "Halaman 5, 6-7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.7 (Langkah 6-7)",
        "expected_condition": "Launch Template 'mbg-lt-fe' ada, versi default = versi terbaru, instance type t3.micro, key pair vockey, LabInstanceProfile, auto-assign public IP = Disabled, SG mbg-sg-fe, tag Name mbg-ec2-fe, AMI mbg-ami-fe, user-data mount EFS ke /mnt/efs/mbg-session dan start httpd.",
        "troubleshooting_steps": [
            "Buka EC2 -> Launch Templates -> Pilih mbg-lt-fe.",
            "Pastikan Default version sama dengan Latest version.",
            "Periksa template data: AMI mbg-ami-fe, t3.micro, LabInstanceProfile, mbg-sg-fe, Auto-assign public IP: Disable.",
            "Periksa User Data: harus berisi perintah mount EFS persisten (/mnt/efs/mbg-session) dan systemctl enable --now httpd.",
            "Jika ada perubahan, buat versi baru dan set sebagai default version."
        ],
        "verification_steps": [
            "aws ec2 describe-launch-templates --launch-template-names mbg-lt-fe"
        ],
        "cli_command": "aws ec2 describe-launch-templates --launch-template-names mbg-lt-fe --query \"LaunchTemplates[0].{Name:LaunchTemplateName,Default:DefaultVersionNumber,Latest:LatestVersionNumber}\" --output table",
        "expected_output": "DefaultVersionNumber == LatestVersionNumber"
    },
    "09": {
        "title": "Auto Scaling Group mbg-asg-fe (subnet private, multi-AZ)",
        "weight": 7.0,
        "category": "Compute",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.10, Bab D.8, Bab E.9",
        "doc_pages": "Halaman 5, 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.8 (Langkah 3-4)",
        "expected_condition": "ASG 'mbg-asg-fe' aktif, Min/Desired/Max = 2/2/4, memakai mbg-lt-fe, subnet private-fe-1a & 1b (2 AZ), terhubung ke Target Group mbg-tg-fe, minimal 2 instance InService di 2 AZ berbeda, Scaling Policy Target Tracking CPU 60%.",
        "troubleshooting_steps": [
            "Buka EC2 -> Auto Scaling Groups -> Pilih mbg-asg-fe.",
            "Pastikan Launch Template: mbg-lt-fe.",
            "Pastikan Group size: Min=2, Desired=2, Max=4.",
            "Pastikan Network: mbg-subnet-private-fe-1a dan mbg-subnet-private-fe-1b (2 AZ).",
            "Pastikan Target Groups: terpasang mbg-tg-fe.",
            "Buka tab Automatic scaling -> Scaling policies -> Pastikan policy Target Tracking CPU target value = 60%."
        ],
        "verification_steps": [
            "aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names mbg-asg-fe"
        ],
        "cli_command": "aws autoscaling describe-policies --auto-scaling-group-name mbg-asg-fe --query \"ScalingPolicies[*].{Type:PolicyType,Target:TargetTrackingConfiguration.TargetValue}\" --output table",
        "expected_output": "PolicyType = TargetTrackingScaling, TargetValue = 60.0"
    },
    "10": {
        "title": "Target Group mbg-tg-fe",
        "weight": 5.0,
        "category": "Load Balancing",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.10, Bab D.8, Bab E.10",
        "doc_pages": "Halaman 5, 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.8 (Langkah 1, 5)",
        "expected_condition": "Target Group 'mbg-tg-fe', protokol HTTP:80, Target type instance, Health check path /health.php, VPC mbg-vpc, seluruh target berstatus healthy (>= 2 target).",
        "troubleshooting_steps": [
            "Buka EC2 -> Target Groups -> Pilih mbg-tg-fe.",
            "Periksa Health check settings: Protocol HTTP, Port 80, Path /health.php.",
            "Buka tab Targets: periksa status seluruh instance registered.",
            "Jika unhealthy: masuk ke EC2 via Session Manager, periksa apakah Apache berjalan (sudo systemctl status httpd).",
            "Uji endpoint lokal: curl -i http://localhost/health.php (harus membalas HTTP 200 {\"status\":\"ok\"}).",
            "Periksa Security Group mbg-sg-fe mengizinkan TCP 80 dari mbg-sg-alb."
        ],
        "verification_steps": [
            "aws elbv2 describe-target-health --target-group-arn <tg-arn>"
        ],
        "cli_command": "aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names mbg-tg-fe --query 'TargetGroups[0].TargetGroupArn' --output text) --query \"TargetHealthDescriptions[*].{ID:Target.Id,State:TargetHealth.State,Reason:TargetHealth.Reason}\" --output table",
        "expected_output": "Minimal 2 target berstatus 'healthy'"
    },
    "11": {
        "title": "Application Load Balancer mbg-alb-fe",
        "weight": 6.0,
        "category": "Load Balancing",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.10, Bab D.8, Bab E.11",
        "doc_pages": "Halaman 5, 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.8 (Langkah 2) & D.9 (Langkah 1)",
        "expected_condition": "ALB 'mbg-alb-fe' aktif, internet-facing, subnet public-alb-1a & 1b (saja), SG mbg-sg-alb, Listener HTTP:80 forward ke mbg-tg-fe. curl http://<alb-dns>/ membalas HTTP 200, endpoint /health.php = 200.",
        "troubleshooting_steps": [
            "Buka EC2 -> Load Balancers -> Pilih mbg-alb-fe.",
            "Pastikan State 'active', Scheme 'internet-facing'.",
            "Pastikan Subnets terpasang hanya 2 subnet public ALB (1a dan 1b).",
            "Pastikan Security Groups terpasang mbg-sg-alb (port 80 open 0.0.0.0/0).",
            "Pastikan Listener HTTP:80 memiliki default action forward to mbg-tg-fe.",
            "Uji via browser atau curl http://<alb-dns>/ (harus HTTP 200)."
        ],
        "verification_steps": [
            "aws elbv2 describe-load-balancers --names mbg-alb-fe",
            "curl -i http://<alb-dns>/"
        ],
        "cli_command": "curl -s -o /dev/null -w \"HTTP %{http_code}\\n\" http://$(aws elbv2 describe-load-balancers --names mbg-alb-fe --query 'LoadBalancers[0].DNSName' --output text)/health.php",
        "expected_output": "HTTP 200"
    },
    "12": {
        "title": "Back End berjalan & auto-migration database (via SSM)",
        "weight": 5.0,
        "category": "Application",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab D.6, Bab E.12",
        "doc_pages": "Halaman 6, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.6 (Langkah 2-4)",
        "expected_condition": "Apache (httpd) aktif di BE, endpoint /health membalas status ok & DB connected, S3 connected, SNS connected. Auto-migration tabel users, sppg, laporan, aduan terbentuk di RDS. Database menunjuk endpoint RDS. Data seed awal terisi.",
        "troubleshooting_steps": [
            "Masuk ke mbg-ec2-be via Systems Manager Session Manager.",
            "Periksa layanan Apache: sudo systemctl status httpd.",
            "Periksa /var/www/html/config.php: pastikan endpoint RDS, nama bucket S3, SNS ARN, dan API key terisi benar.",
            "Uji endpoint lokal: curl -s http://localhost/health (harus membalas status ok dan db/s3/sns connected).",
            "Periksa tabel database: php -r '$c=require \"config.php\";$p=new PDO(...);print_r($p->query(\"SHOW TABLES\")->fetchAll());'."
        ],
        "verification_steps": [
            "curl -s http://<be-private-ip>/health"
        ],
        "cli_command": "curl -s http://localhost/health",
        "expected_output": "{\"status\":\"ok\",\"db\":\"connected\",\"s3\":{\"status\":\"connected\"},\"sns\":{\"status\":\"connected\"}}"
    },
    "13": {
        "title": "Notifikasi email SNS saat aduan/laporan baru",
        "weight": 6.0,
        "category": "Messaging",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.6, Bab D.5, Bab D.9, Bab E.13",
        "doc_pages": "Halaman 4, 6, 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.5 (Langkah 1-3) & D.9 (Langkah 3)",
        "expected_condition": "Saat ada aduan atau laporan baru dibuat, Back End memanggil Publish ke topic SNS. CloudWatch mencatat pesan published >= 2 dan delivered >= 2. Log BE tidak mencatat error SNS.",
        "troubleshooting_steps": [
            "Pastikan ARN topic mbg-sns-notifikasi dicantumkan di config.php Back End.",
            "Pastikan IAM role EC2 BE memiliki izin sns:Publish (LabInstanceProfile bawaan lab sudah mencakup ini).",
            "Buat 1 aduan baru dan 1 laporan baru dari web dashboard atau via API.",
            "Periksa error log Apache di BE: tail -n 50 /var/log/httpd/error_log (pastikan tidak ada 'SNS publish gagal').",
            "Periksa metrik CloudWatch SNS: NumberOfMessagesPublished dan NumberOfNotificationsDelivered."
        ],
        "verification_steps": [
            "aws cloudwatch get-metric-statistics --namespace AWS/SNS --metric-name NumberOfMessagesPublished ..."
        ],
        "cli_command": "aws sns get-topic-attributes --topic-arn $(aws sns list-topics --query \"Topics[?contains(TopicArn,'mbg-sns-notifikasi')].TopicArn|[0]\" --output text)",
        "expected_output": "Topic terkonfigurasi dengan Attributes valid"
    },
    "14": {
        "title": "Uji ketahanan Auto Scaling (terminate 1 instance FE)",
        "weight": 6.0,
        "category": "Compute",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab D.9, Bab E.14",
        "doc_pages": "Halaman 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.9 (Langkah 4)",
        "expected_condition": "Ketika salah satu instance FE di-terminate secara manual, Auto Scaling Group secara otomatis meluncurkan instance pengganti di subnet private FE dan Target Group kembali Healthy dalam < 5 menit.",
        "troubleshooting_steps": [
            "Buka EC2 -> Auto Scaling Groups -> mbg-asg-fe -> Tab Instance management.",
            "Pilih salah satu instance FE, klik Actions -> Terminate.",
            "Pantau ASG Activity history: ASG akan mendeteksi kapasitas berkurang dan menjalankan Launching a new EC2 instance.",
            "Tunggu hingga instance pengganti berstatus InService dan Target Group mbg-tg-fe berstatus Healthy.",
            "Catatan: Pengujian ini bersifat destruktif dan memakan waktu sekitar 3-5 menit."
        ],
        "verification_steps": [
            "aws autoscaling describe-scaling-activities --auto-scaling-group-name mbg-asg-fe"
        ],
        "cli_command": "aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names mbg-asg-fe --query \"AutoScalingGroups[0].Instances[*].{ID:InstanceId,Status:LifecycleState,AZ:AvailabilityZone}\" --output table",
        "expected_output": "Jumlah instance kembali 2, status InService di 2 AZ berbeda"
    },
    "15": {
        "title": "EFS mbg-efs-fe-session & mount di instance FE",
        "weight": 6.0,
        "category": "Storage",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.7, Bab C.9, Bab D.7, Bab E.15",
        "doc_pages": "Halaman 4, 5, 6-7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.7 (Langkah 1, 4, 7)",
        "expected_condition": "EFS 'mbg-efs-fe-session' regional available, General Purpose, Bursting. Mount target available di kedua subnet private FE (1a dan 1b) dengan SG mbg-sg-efs. /mnt/efs/mbg-session ter-mount via NFS, persisten di /etc/fstab, session.save_path PHP diarahkan ke /mnt/efs/mbg-session, Apache aktif.",
        "troubleshooting_steps": [
            "Buka EFS -> File systems -> Pilih mbg-efs-fe-session.",
            "Pastikan status Available, Regional, dan memiliki Mount Target di kedua subnet private FE dengan security group mbg-sg-efs.",
            "Masuk ke instance FE via Session Manager.",
            "Periksa mount: mountpoint /mnt/efs/mbg-session (harus ter-mount NFS).",
            "Periksa /etc/fstab: harus memuat baris mount EFS persisten.",
            "Periksa PHP session.save_path: php -r 'echo ini_get(\"session.save_path\");' (harus /mnt/efs/mbg-session).",
            "Pastikan permission direktori: sudo chown -R apache:apache /mnt/efs/mbg-session && sudo chmod 777 /mnt/efs/mbg-session."
        ],
        "verification_steps": [
            "php -r 'echo ini_get(\"session.save_path\");'",
            "mountpoint -q /mnt/efs/mbg-session && echo yes"
        ],
        "cli_command": "php -r 'echo ini_get(\"session.save_path\");'",
        "expected_output": "/mnt/efs/mbg-session"
    },
    "16": {
        "title": "Session shared antar instance FE (bukti fungsi EFS)",
        "weight": 7.0,
        "category": "Storage",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab C.7, Bab D.7, Bab E.16",
        "doc_pages": "Halaman 4, 7, 8",
        "doc_procedure": "Petunjuk Pelaksanaan D.7 (Langkah 4) & E.16",
        "expected_condition": "Login masyarakat/petugas lewat ALB tetap aktif saat request didistribusikan ke >= 2 instance FE berbeda (30 request beruntun tanpa logout). File session sess_<id> tersimpan di EFS dan cookie yang sama diterima oleh instance peer.",
        "troubleshooting_steps": [
            "Pastikan session.save_path di /etc/php.d/99-mbg-session.ini mengarah ke /mnt/efs/mbg-session di seluruh instance FE.",
            "Pastikan direktori /mnt/efs/mbg-session memiliki izin tulis bagi user apache.",
            "Login via ALB di browser, lakukan refresh berulang kali, periksa apakah user tetap berada di dashboard tanpa terlempar ke halaman login.",
            "Masuk ke salah satu instance FE via Session Manager, periksa berkas session di EFS: ls -la /mnt/efs/mbg-session/sess_*."
        ],
        "verification_steps": [
            "ls -la /mnt/efs/mbg-session/sess_*"
        ],
        "cli_command": "ls /mnt/efs/mbg-session | grep -c '^sess_'",
        "expected_output": "Angka > 0 (menandakan file session tersimpan di EFS)"
    },
    "17": {
        "title": "Alur aplikasi end-to-end lewat ALB (login 3 role, aduan, upload S3, tanggapan, laporan, monitoring)",
        "weight": 6.0,
        "category": "Application",
        "doc_name": "Soal_UKK Cloud Engineer_2627-Rev1.pdf",
        "doc_revision": "Revisi 1",
        "doc_chapter": "Bab D.9, Bab E.17",
        "doc_pages": "Halaman 7, 9",
        "doc_procedure": "Petunjuk Pelaksanaan D.9 (Langkah 1-3)",
        "expected_condition": "Login sukses untuk 3 role (BGN: bgn, SPPG: sppg1, masyarakat: masy1; password seed 123) lewat DNS ALB. Dashboard publik tampil. Masyarakat membuat aduan + foto lampiran -> tersimpan di S3 prefix aduan/ dan presigned URL dapat dibuka. SPPG melihat aduan dan mengirim tanggapan. SPPG membuat laporan + file ke S3 prefix laporan/. Dashboard monitoring BGN menampilkan data riil.",
        "troubleshooting_steps": [
            "Buka http://<alb-dns>/ di browser.",
            "Uji login peran BGN (username: bgn, password: 123) -> Masuk ke /views/bgn/dashboard.php.",
            "Uji login peran SPPG (username: sppg1, password: 123) -> Masuk ke /views/sppg/dashboard.php.",
            "Uji login peran Masyarakat (username: masy1, password: 123) -> Buat aduan baru beserta foto lampiran.",
            "Login kembali sebagai SPPG -> Berikan tanggapan atas aduan tersebut dan submit 1 laporan kegiatan.",
            "Periksa S3 bucket: objek baru harus muncul pada prefix aduan/ dan laporan/."
        ],
        "verification_steps": [
            "curl -sL http://<alb-dns>/views/auth/login.php",
            "aws s3 ls s3://<bucket-name>/aduan/",
            "aws s3 ls s3://<bucket-name>/laporan/"
        ],
        "cli_command": "curl -s -o /dev/null -w \"HTTP %{http_code}\\n\" http://$(aws elbv2 describe-load-balancers --names mbg-alb-fe --query 'LoadBalancers[0].DNSName' --output text)/",
        "expected_output": "HTTP 200"
    }
}

