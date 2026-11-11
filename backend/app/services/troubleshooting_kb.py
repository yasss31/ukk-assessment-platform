"""
app/services/troubleshooting_kb.py - Smart Feedback & Troubleshooting Knowledge Base
Katalog Solusi Cerdas & Panduan Perbaikan Mandiri untuk Peserta UKK Cloud Engineer
"""
from typing import Optional, Dict, Any, List
from app.models.schemas import TroubleshootingGuide, ErrorSeverity


class TroubleshootingKB:
    """
    Katalog rule-based troubleshooting untuk 17 Aspek Arsitektur UKK Cloud Engineer.
    Memberikan tutorial langkah demi langkah ramah siswa SMK, lokasi menu AWS Console,
    dampak teknis, dan perintah verifikasi.
    """

    KB: Dict[str, Dict[str, Any]] = {
        "01.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "VPC 'mbg-vpc' belum dibuat atau blok IP (CIDR) tidak sesuai spesifikasi 10.20.0.0/16.",
            "why_wrong": "VPC adalah fondasi jaringan cloud tempat seluruh server, database, dan load balancer berada.",
            "impact": "Seluruh subnet, EC2, RDS, dan EFS tidak dapat terhubung atau akan terjadi benturan alamat IP.",
            "fix_location": "AWS Console -> VPC -> Your VPCs",
            "how_to_fix": [
                "Buka AWS Console dan masuk ke layanan 'VPC'.",
                "Pilih menu 'Your VPCs' di sidebar sebelah kiri.",
                "Cek apakah ada VPC bernama 'mbg-vpc'. Jika belum ada, klik 'Create VPC'.",
                "Pilih 'VPC only', beri nama 'mbg-vpc', dan isi IPv4 CIDR block: 10.20.0.0/16.",
                "Klik 'Create VPC'. Pastikan Enable DNS hostnames dan Enable DNS resolution diaktifkan pada Edit VPC settings."
            ],
            "how_to_verify": [
                "Buka menu Your VPCs, pastikan mbg-vpc memiliki IPv4 CIDR: 10.20.0.0/16 dan status 'Available'."
            ]
        },
        "01.02": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Subnet Public ALB di AZ 1a dan 1b belum lengkap atau Auto-assign Public IPv4 belum aktif.",
            "why_wrong": "ALB (Application Load Balancer) membutuhkan 2 subnet publik di 2 Availability Zone berbeda untuk menerima akses internet.",
            "impact": "ALB tidak dapat dibuat atau website MBG tidak bisa diakses oleh masyarakat dari internet.",
            "fix_location": "AWS Console -> VPC -> Subnets",
            "how_to_fix": [
                "Buka AWS Console -> VPC -> Subnets.",
                "Buat Subnet 1: Nama 'mbg-subnet-public-alb-1a', VPC 'mbg-vpc', AZ 'us-east-1a', CIDR '10.20.1.0/24'.",
                "Buat Subnet 2: Nama 'mbg-subnet-public-alb-1b', VPC 'mbg-vpc', AZ 'us-east-1b', CIDR '10.20.2.0/24'.",
                "Pilih masing-masing subnet, klik 'Actions' -> 'Edit subnet settings', centang 'Enable auto-assign public IPv4 address', lalu Simpan."
            ],
            "how_to_verify": [
                "Pastikan kedua subnet memiliki Auto-assign public IPv4 = Yes dan terasosiasi ke mbg-vpc."
            ]
        },
        "01.03": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Subnet Private Frontend di AZ 1a dan 1b belum dibuat atau Auto-assign Public IP keliru diaktifkan.",
            "why_wrong": "Server Frontend harus terisolasi di subnet private untuk mencegah akses langsung tanpa melalui ALB.",
            "impact": "Auto Scaling Group Frontend tidak dapat menempatkan instance secara seimbang di dua AZ private.",
            "fix_location": "AWS Console -> VPC -> Subnets",
            "how_to_fix": [
                "Buka VPC -> Subnets.",
                "Buat Subnet 'mbg-subnet-private-fe-1a' (CIDR: 10.20.10.0/24) di AZ us-east-1a.",
                "Buat Subnet 'mbg-subnet-private-fe-1b' (CIDR: 10.20.11.0/24) di AZ us-east-1b.",
                "Pastikan opsi 'Enable auto-assign public IPv4 address' TIDAK dicentang (harus bernilai False)."
            ],
            "how_to_verify": [
                "Pastikan kedua subnet private FE berada di mbg-vpc dengan Auto-assign IP = No."
            ]
        },
        "02.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Internet Gateway 'mbg-igw' belum dibuat atau belum di-attach ke 'mbg-vpc'.",
            "why_wrong": "Internet Gateway adalah pintu keluar masuk lalu lintas internet untuk seluruh resource di dalam VPC.",
            "impact": "ALB, NAT Gateway, dan server tidak dapat berkomunikasi ke internet sama sekali.",
            "fix_location": "AWS Console -> VPC -> Internet Gateways",
            "how_to_fix": [
                "Buka VPC -> Internet Gateways.",
                "Klik 'Create internet gateway', beri nama 'mbg-igw', lalu klik Create.",
                "Pilih 'mbg-igw', klik 'Actions' -> 'Attach to VPC'.",
                "Pilih 'mbg-vpc' dan klik 'Attach internet gateway'."
            ],
            "how_to_verify": [
                "Pastikan status mbg-igw berubah menjadi 'Attached' ke mbg-vpc."
            ]
        },
        "02.02": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "NAT Gateway 'mbg-natgw-1a' tidak ditemukan, tidak berada di Subnet Public 1a, atau belum Available.",
            "why_wrong": "Instance EC2 di subnet private membutuhkan NAT Gateway untuk mengunduh paket Linux (yum/dnf, apache, php, efs-utils).",
            "impact": "EC2 Back End dan EC2 Front End gagal mengunduh aplikasi dan dependensi, sehingga server gagal booting.",
            "fix_location": "AWS Console -> VPC -> NAT Gateways",
            "how_to_fix": [
                "Buka VPC -> NAT Gateways -> Klik 'Create NAT gateway'.",
                "Beri nama 'mbg-natgw-1a'.",
                "Pilih Subnet: 'mbg-subnet-public-alb-1a' (WAJIB di subnet public, BUKAN private).",
                "Klik 'Allocate Elastic IP' untuk menghubungkan IP publik statis.",
                "Klik 'Create NAT gateway' dan tunggu hingga status berubah dari 'pending' menjadi 'available'."
            ],
            "how_to_verify": [
                "Pastikan mbg-natgw-1a berstatus 'available' dan berada di subnet public 1a."
            ]
        },
        "02.03": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Tabel rute (Route Table) Public belum mengarah ke IGW atau Private belum mengarah ke NAT GW.",
            "why_wrong": "Paket data dari subnet private tidak tahu ke mana harus dikirim jika rute 0.0.0.0/0 belum diarahkan ke NAT Gateway.",
            "impact": "Koneksi keluar dari server private terputus total.",
            "fix_location": "AWS Console -> VPC -> Route Tables",
            "how_to_fix": [
                "Buka VPC -> Route Tables.",
                "Pada 'mbg-rt-public', edit routes: tambahkan '0.0.0.0/0' -> Target 'Internet Gateway' (mbg-igw). Asosiasikan ke 2 subnet public.",
                "Pada 'mbg-rt-private', edit routes: tambahkan '0.0.0.0/0' -> Target 'NAT Gateway' (mbg-natgw-1a). Asosiasikan ke subnet private FE & BE.",
                "Pada 'mbg-rt-db', pastikan HANYA ada rute lokal VPC (tanpa 0.0.0.0/0) untuk isolasi database."
            ],
            "how_to_verify": [
                "Cek tab 'Routes' dan 'Subnet Associations' pada masing-masing Route Table."
            ]
        },
        "03.01": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Satu atau lebih dari 5 Security Group wajib belum dibuat (mbg-sg-alb, mbg-sg-fe, mbg-sg-be, mbg-sg-rds, mbg-sg-efs).",
            "why_wrong": "Setiap tier arsitektur membutuhkan firewall virtual terpisah sesuai prinsip Least Privilege.",
            "impact": "Komponen tidak dapat dipasang atau aturan keamanan tidak dapat saling merujuk.",
            "fix_location": "AWS Console -> EC2 -> Security Groups",
            "how_to_fix": [
                "Buka EC2 -> Security Groups -> Create security group.",
                "Pastikan seluruh Security Group dibuat di dalam 'mbg-vpc':",
                "1. mbg-sg-alb (Inbound HTTP 80 dari 0.0.0.0/0)",
                "2. mbg-sg-fe (Inbound HTTP 80 dari mbg-sg-alb)",
                "3. mbg-sg-be (Inbound HTTP 8000 dari mbg-sg-fe)",
                "4. mbg-sg-rds (Inbound MySQL 3306 dari mbg-sg-be)",
                "5. mbg-sg-efs (Inbound NFS 2049 dari mbg-sg-fe)"
            ],
            "how_to_verify": [
                "Cari filter 'mbg-sg-*' di daftar Security Group mbg-vpc dan pastikan kelima SG terdaftar."
            ]
        },
        "03.02": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Inbound Rules Security Group EFS ('mbg-sg-efs') belum mengizinkan port NFS 2049 dari sumber 'mbg-sg-fe'.",
            "why_wrong": "Frontend EC2 membutuhkan akses NFS (port 2049) ke EFS untuk membaca dan menulis session PHP bersama.",
            "impact": "PHP gagal me-mount EFS session, menyebabkan login pengguna terus logout saat berpindah server di belakang ALB.",
            "fix_location": "AWS Console -> EC2 -> Security Groups -> mbg-sg-efs",
            "how_to_fix": [
                "Buka AWS Console -> EC2 -> Security Groups.",
                "Cari dan klik 'mbg-sg-efs'.",
                "Pilih tab 'Inbound rules', lalu klik 'Edit inbound rules'.",
                "Hapus aturan 0.0.0.0/0 jika ada.",
                "Klik 'Add rule': Type: 'NFS', Port Range: '2049', Source: Custom -> pilih Security Group ID 'mbg-sg-fe'.",
                "Klik 'Save rules'."
            ],
            "how_to_verify": [
                "Cek Inbound Rules mbg-sg-efs, pastikan hanya ada port 2049 dengan Source mengarah ke ID mbg-sg-fe."
            ]
        },
        "04.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "RDS MySQL 'mbg-rds-mysql' belum dibuat, belum berstatus 'available', atau Publicly Accessible bernilai True.",
            "why_wrong": "Database MySQL adalah tempat penyimpanan seluruh data tabel MBG dan WAJIB berada di jaringan private.",
            "impact": "Back End tidak dapat menyimpan data laporan dan aduan, atau database rentan diserang jika terekspos publik.",
            "fix_location": "AWS Console -> RDS -> Databases",
            "how_to_fix": [
                "Buka RDS -> Databases -> Create database.",
                "Pilih Standard create -> MySQL -> Free Tier (db.t3.micro).",
                "DB instance identifier: 'mbg-rds-mysql', Master username: 'mbgadmin', Master password sesuai ketentuan.",
                "Pada bagian Connectivity, pilih VPC: 'mbg-vpc', DB Subnet Group: 'mbg-db-subnet-group'.",
                "Public access: Pilih 'No'.",
                "VPC security group: Pilih 'mbg-sg-rds' (hapus default).",
                "Initial database name: 'mbg_db'. Klik Create database dan tunggu hingga status 'Available'."
            ],
            "how_to_verify": [
                "Cek RDS console, pastikan status 'Available', Publicly Accessible: 'No', dan VPC 'mbg-vpc'."
            ]
        },
        "05.01": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Bucket S3 belum dibuat atau fitur 'Block Public Access' belum 100% aktif (keempat opsi True).",
            "why_wrong": "Bucket S3 digunakan untuk menyimpan foto bukti aduan masyarakat dan laporan penyaluran MBG secara aman.",
            "impact": "Potensi kebocoran data privasi foto aduan jika bucket tidak diproteksi penuh.",
            "fix_location": "AWS Console -> S3 -> Buckets",
            "how_to_fix": [
                "Buka layanan S3 di AWS Console.",
                "Buat bucket baru bernama 'mbg-uploads-<nomor-peserta>-<random>' (harus unik global).",
                "Pada bagian 'Block Public Access settings for this bucket', pastikan centang 'Block all public access' (seluruh 4 checkbox tercentang).",
                "Klik 'Create bucket'."
            ],
            "how_to_verify": [
                "Buka tab Permissions bucket S3, pastikan tertulis 'Block public access (bucket settings): On'."
            ]
        },
        "06.02": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Subscription email pada SNS Topic 'mbg-sns-notifikasi' masih berstatus 'PendingConfirmation'.",
            "why_wrong": "AWS SNS mewajibkan penerima email mengklik link konfirmasi sebelum notifikasi dapat terkirim.",
            "impact": "Notifikasi email aduan masyarakat darurat tidak akan pernah terkirim ke petugas BGN.",
            "fix_location": "Kotak Masuk Email Peserta / AWS Console -> SNS -> Subscriptions",
            "how_to_fix": [
                "Buka kotak masuk (Inbox atau Spam) email yang didaftarkan pada subscription SNS.",
                "Cari email dari 'AWS Notifications' dengan subjek 'AWS Notification - Subscription Confirmation'.",
                "Klik tautan 'Confirm subscription' di dalam email tersebut.",
                "Jika email tidak ditemukan, buka AWS SNS -> Subscriptions, pilih subscription tersebut, klik 'Request confirmation', lalu periksa kembali email Anda."
            ],
            "how_to_verify": [
                "Refresh AWS SNS console, pastikan status Subscription berubah dari 'PendingConfirmation' menjadi 'Confirmed'."
            ]
        },
        "07.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "EC2 Back End 'mbg-ec2-be' tidak berstatus running, tidak berada di private subnet, atau memiliki IP Publik.",
            "why_wrong": "Server Back End API harus berjalan di subnet private terisolasi dan hanya diakses oleh Frontend.",
            "impact": "Aplikasi Frontend tidak dapat memanggil REST API MBG (menu laporan & aduan gagal memuat data).",
            "fix_location": "AWS Console -> EC2 -> Instances",
            "how_to_fix": [
                "Buka EC2 -> Instances.",
                "Pastikan instance 'mbg-ec2-be' berjalan (running) dengan tipe t3.micro.",
                "Pastikan Subnet berada di 'mbg-subnet-private-be' dan Public IPv4 address bernilai kosong/none.",
                "Pastikan IAM Role LabInstanceProfile terpasang pada instance.",
                "Pastikan service backend berjalan di port 8000."
            ],
            "how_to_verify": [
                "Cek instance details di EC2 console: State: running, Public IPv4: None, Subnet: mbg-subnet-private-be."
            ]
        },
        "08.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Launch Template 'mbg-lt-fe' tidak menggunakan Custom AMI buatan sendiri ('mbg-ami-fe') sesuai Soal Revisi 1.",
            "why_wrong": "Soal UKK Revisi 1 mewajibkan pembuatan Custom AMI dari EC2 frontend sementara (mbg-ec2-fe-temp) agar autoscaling cepat.",
            "impact": "ASG akan meluncurkan instance kosong tanpa aplikasi, sehingga website error HTTP 502/404.",
            "fix_location": "AWS Console -> EC2 -> Launch Templates",
            "how_to_fix": [
                "Pastikan Anda telah membuat Custom AMI dari server template 'mbg-ec2-fe-temp' dengan nama 'mbg-ami-fe'.",
                "Buka EC2 -> Launch Templates -> pilih 'mbg-lt-fe' -> 'Actions' -> 'Modify template (Create new version)'.",
                "Ganti AMI ID dengan AMI kustom Anda ('mbg-ami-fe' di tab My AMIs).",
                "Pastikan versi baru tersebut dijadikan 'Default Version'."
            ],
            "how_to_verify": [
                "Cek Launch Template mbg-lt-fe: AMI ID harus merupakan AMI kustom Anda, bukan AMI publik standar Amazon Linux."
            ]
        },
        "09.02": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Jumlah instance FE berstatus 'InService' di Auto Scaling Group kurang dari 2.",
            "why_wrong": "Arsitektur High Availability (HA) MBG mewajibkan minimal 2 server frontend aktif di 2 Availability Zone berbeda.",
            "impact": "Kelebihan beban lalu lintas, kegagalan saat ada 1 instance down, dan hilangnya redundansi.",
            "fix_location": "AWS Console -> EC2 -> Auto Scaling groups -> mbg-asg-fe",
            "how_to_fix": [
                "Buka EC2 -> Auto Scaling groups -> pilih 'mbg-asg-fe'.",
                "Periksa tab 'Instance management': jika ada instance 'Unhealthy' atau gagal diluncurkan, cek tab 'Activity'.",
                "Pastikan Desired Capacity = 2, Minimum = 2, Maximum = 4.",
                "Periksa apakah Target Group mengembalikan status 'Healthy' untuk health check /health.php."
            ],
            "how_to_verify": [
                "Di tab Instance management, pastikan minimal 2 instance memiliki Health status: 'Healthy' dan Lifecycle: 'InService'."
            ]
        },
        "10.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Target Group 'mbg-tg-fe' tidak memiliki minimal 2 target berstatus 'Healthy' pada path '/health.php'.",
            "why_wrong": "ALB hanya akan meneruskan lalu lintas ke server yang lolos health check HTTP 200 pada file /health.php.",
            "impact": "ALB akan mengembalikan error '502 Bad Gateway' atau '503 Service Temporarily Unavailable' kepada pengunjung.",
            "fix_location": "AWS Console -> EC2 -> Target Groups -> mbg-tg-fe",
            "how_to_fix": [
                "Buka EC2 -> Target Groups -> pilih 'mbg-tg-fe'.",
                "Periksa tab 'Targets'. Jika target berstatus 'Unhealthy', periksa error code (misal: 404 Not Found atau Connection Timed Out).",
                "Pastikan Apache (httpd) dan PHP berjalan di instance FE.",
                "Pastikan file '/var/www/html/health.php' ada dan merespons HTTP 200.",
                "Pastikan Security Group mbg-sg-fe mengizinkan HTTP port 80 dari mbg-sg-alb."
            ],
            "how_to_verify": [
                "Di tab Targets mbg-tg-fe, pastikan minimal 2 instance berstatus 'Healthy'."
            ]
        },
        "11.02": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "DNS Endpoint Application Load Balancer ('mbg-alb-fe') tidak merespons HTTP 200 (Website MBG tidak dapat diakses).",
            "why_wrong": "ALB adalah pintu masuk utama seluruh pengguna untuk mengakses antarmuka web MBG.",
            "impact": "Penguji, guru, maupun masyarakat umum tidak dapat membuka halaman aplikasi monitoring MBG.",
            "fix_location": "AWS Console -> EC2 -> Load Balancers -> mbg-alb-fe",
            "how_to_fix": [
                "Buka EC2 -> Load Balancers -> mbg-alb-fe.",
                "Pastikan State berstatus 'Active'.",
                "Periksa tab 'Listeners and rules': pastikan ada listener HTTP:80 yang mengarah ke target group 'mbg-tg-fe'.",
                "Pastikan Security Group mbg-sg-alb mengizinkan Inbound HTTP:80 dari 0.0.0.0/0.",
                "Pastikan Target Group memiliki target Healthy."
            ],
            "how_to_verify": [
                "Buka URL DNS ALB di browser: http://<DNS-ALB>/ dan pastikan halaman login/dashboard MBG tampil sempurna."
            ]
        },
        "14.01": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Target Tracking Dynamic Scaling Policy dengan metrik CPUUtilization 50% belum terpasang pada ASG.",
            "why_wrong": "Auto scaling dinamis diperlukan agar jumlah server otomatis bertambah saat beban lonjakan aduan masyarakat meningkat.",
            "impact": "Server dapat crash atau lambat saat terjadi lonjakan kunjungan karena jumlah instance tidak dapat bertambah secara otomatis.",
            "fix_location": "AWS Console -> EC2 -> Auto Scaling groups -> mbg-asg-fe -> Automatic scaling",
            "how_to_fix": [
                "Buka EC2 -> Auto Scaling groups -> pilih 'mbg-asg-fe'.",
                "Pilih tab 'Automatic scaling' -> klik 'Create dynamic scaling policy'.",
                "Policy type: 'Target tracking scaling', Metric type: 'Average CPU utilization', Target value: '50'.",
                "Instance warmup: '300' seconds.",
                "Klik 'Create'."
            ],
            "how_to_verify": [
                "Di tab Automatic scaling, pastikan terdaftar policy 'TargetTracking-AverageCPUUtilization-50%'."
            ]
        },
        "15.02": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "EFS belum ter-mount ke '/mnt/efs/mbg-session' atau konfigurasi php.ini session.save_path belum diarahkan ke EFS.",
            "why_wrong": "PHP secara default menyimpan session di folder lokal instance (/var/lib/php/session).",
            "impact": "Pengguna yang login di Server A akan ter-logout otomatis saat request berikutnya diarahkan ALB ke Server B.",
            "fix_location": "Instance EC2 Frontend -> /etc/php.ini & /etc/fstab",
            "how_to_fix": [
                "Masuk via SSH/SSM ke instance FE:",
                "1. Pastikan direktori mount ada: sudo mkdir -p /mnt/efs/mbg-session",
                "2. Mount EFS ke folder: sudo mount -t efs <EFS_ID>:/ /mnt/efs/mbg-session",
                "3. Atur permission: sudo chown -R apache:apache /mnt/efs/mbg-session && sudo chmod 770 /mnt/efs/mbg-session",
                "4. Tambahkan ke /etc/fstab agar persisten saat reboot:",
                "   <EFS_ID>:/ /mnt/efs/mbg-session efs _netdev,tls 0 0",
                "5. Edit /etc/php.ini: ubah session.save_path = \"/mnt/efs/mbg-session\"",
                "6. Restart webserver: sudo systemctl restart httpd"
            ],
            "how_to_verify": [
                "Jalankan: php -r 'echo session_save_path();' -> Harus menghasilkan '/mnt/efs/mbg-session'.",
                "Jalankan: df -h -> Harus menampilkan filesystem EFS ter-mount pada /mnt/efs/mbg-session."
            ]
        },
        "16.01": {
            "severity": ErrorSeverity.CRITICAL,
            "what_is_wrong": "Pengujian multi-instance session sharing gagal (pengguna ter-logout saat request disebar lintas server FE).",
            "why_wrong": "Session token PHP tidak tersinkronisasi antar server frontend di belakang Application Load Balancer.",
            "impact": "Siswa gagal menunjukkan kemampuan arsitektur Stateless Web Tier.",
            "fix_location": "EFS & PHP Session Configuration",
            "how_to_fix": [
                "Pastikan EFS ter-mount di SELURUH instance Front End pada direktori /mnt/efs/mbg-session.",
                "Pastikan UserData pada Launch Template mengeksekusi 'mount -a' saat instance baru diluncurkan oleh ASG.",
                "Pastikan AMI 'mbg-ami-fe' sudah memiliki konfigurasi /etc/php.ini yang benar sebelum AMI dibuat."
            ],
            "how_to_verify": [
                "Lakukan login ke dashboard MBG, lalu refresh halaman sebanyak 20-30 kali. Pastikan sesi login tidak pernah terputus."
            ]
        },
        "17.01": {
            "severity": ErrorSeverity.MAJOR,
            "what_is_wrong": "Pengujian alur End-to-End aplikasi MBG (Login 3 role, submit aduan, upload bukti S3) mengalami kegagalan.",
            "why_wrong": "Ada keterputusan integrasi antara Frontend, Backend, Database MySQL, atau S3 API.",
            "impact": "Aplikasi MBG tidak siap pakai untuk proses operasional nyata.",
            "fix_location": "Aplikasi MBG / Database Connection",
            "how_to_fix": [
                "Buka file konfigurasi koneksi database pada Backend dan pastikan DB_HOST, DB_USER, DB_PASSWORD sesuai dengan RDS.",
                "Pastikan bucket S3 mengizinkan instance profile mengunggah file (s3:PutObject).",
                "Cek log error aplikasi di instance: /var/log/httpd/error_log dan log backend di port 8000."
            ],
            "how_to_verify": [
                "Lakukan login dengan akun: bgn / bgn123, sppg1 / sppg123, masy1 / masy123, lalu coba submit 1 aduan dengan upload foto."
            ]
        }
    }

    @classmethod
    def get_guide(cls, code: str, expected: str, actual: str, error_message: Optional[str] = None) -> TroubleshootingGuide:
        """Mengambil atau menggenerasi panduan perbaikan terarah untuk indikator yang gagal."""
        kb_entry = cls.KB.get(code)
        if not kb_entry:
            # Fallback cerdas jika ada kode variasi
            category_guess = "General"
            severity = ErrorSeverity.MAJOR
            what_is_wrong = f"Kriteria pemeriksaan '{code}' belum terpenuhi."
            why_wrong = "Konfigurasi aktual di cloud belum sesuai dengan spesifikasi rubrik penilaian."
            impact = "Dapat mempengaruhi fungsionalitas dan mengurangi perolehan skor kompetensi siswa."
            fix_location = "AWS Management Console"
            how_to_fix = [
                f"Periksa konfigurasi resource terkait {code} di AWS Console.",
                f"Pastikan nilai yang diatur sesuai dengan yang diharapkan: '{expected}'.",
                f"Kondisi saat ini yang ditemukan sistem: '{actual}'."
            ]
            how_to_verify = [
                "Periksa kembali status resource dan klik 'Periksa Ulang' pada indikator ini."
            ]
        else:
            severity = kb_entry["severity"]
            what_is_wrong = kb_entry["what_is_wrong"]
            why_wrong = kb_entry["why_wrong"]
            impact = kb_entry["impact"]
            fix_location = kb_entry["fix_location"]
            how_to_fix = kb_entry["how_to_fix"]
            how_to_verify = kb_entry["how_to_verify"]

        if error_message and "tidak ditemukan" in error_message.lower():
            what_is_wrong = f"{what_is_wrong} (Catatan: {error_message})"

        return TroubleshootingGuide(
            severity=severity,
            what_is_wrong=what_is_wrong,
            actual_found=actual or "Tidak ditemukan / Belum terkonfigurasi",
            expected_config=expected,
            why_wrong=why_wrong,
            impact=impact,
            fix_location=fix_location,
            how_to_fix=how_to_fix,
            how_to_verify=how_to_verify,
            cli_guide=None
        )

