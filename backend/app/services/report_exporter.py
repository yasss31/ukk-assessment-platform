"""
app/services/report_exporter.py - Ekspor Laporan Penilaian (CSV, JSON, HTML/PDF)
"""
import io
import csv
import json
from typing import Dict, Any


class ReportExporter:
    @staticmethod
    def to_json(session_data: Dict[str, Any]) -> str:
        return json.dumps(session_data, indent=2, ensure_ascii=False)

    @staticmethod
    def to_csv(session_data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Kode", "Nama Indikator", "Kategori", "Bobot", "Skor", "Status", "Ekspektasi", "Bukti/Hasil Aktual", "Error"])
        
        for res in session_data.get("results", []):
            writer.writerow([
                res.get("code", ""),
                res.get("name", ""),
                res.get("category", ""),
                res.get("weight", 0.0),
                res.get("score", 0.0),
                res.get("status", ""),
                res.get("expected", ""),
                res.get("actual", ""),
                res.get("error_message", "")
            ])
        return output.getvalue()

    @staticmethod
    def to_txt(session_data: Dict[str, Any]) -> str:
        part = session_data.get("participant", {})
        results = session_data.get("results", [])
        lines = []
        lines.append("=============================================================================")
        lines.append("                 LAPORAN HASIL PENILAIAN UKK CLOUD ENGINEER                  ")
        lines.append("=============================================================================")
        lines.append(f"Peserta        : {part.get('name')} ({part.get('participant_number')})")
        lines.append(f"Kelas/Sekolah  : {part.get('student_class')} - {part.get('school')}")
        lines.append(f"Rubrik Profil  : {session_data.get('rubric_name')} (v{session_data.get('rubric_version')})")
        lines.append(f"Waktu Evaluasi : {session_data.get('created_at')}")
        lines.append(f"Penguji        : {session_data.get('examiner_name')}")
        lines.append(f"Total Skor     : {session_data.get('total_score')} / {session_data.get('max_score')} ({session_data.get('score_percentage')}%)")
        lines.append(f"Ringkasan      : PASS={session_data.get('pass_count')}, FAIL={session_data.get('fail_count')}, SKIP={session_data.get('skip_count')}")
        lines.append("-----------------------------------------------------------------------------")
        for r in results:
            st = r.get("status")
            lines.append(f"[{st:4s}] {r.get('code')} - {r.get('name')} (Skor: {r.get('score')}/{r.get('weight')})")
            if r.get('actual'):
                lines.append(f"       Bukti: {r.get('actual')}")
            if r.get('error_message'):
                lines.append(f"       Catatan/Error: {r.get('error_message')}")
        lines.append("=============================================================================")
        return "\n".join(lines)

    @staticmethod
    def to_html(session_data: Dict[str, Any]) -> str:
        part = session_data.get("participant", {})
        results = session_data.get("results", [])
        
        rows_html = ""
        for r in results:
            st = r.get("status", "")
            color = "#16a34a" if st == "PASS" else ("#dc2626" if st == "FAIL" else "#d97706")
            bg = "#f0fdf4" if st == "PASS" else ("#fef2f2" if st == "FAIL" else "#fffbeb")
            rows_html += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 10px; font-weight: 600;">{r.get('code')}</td>
                <td style="padding: 10px;">
                    <div>{r.get('name')}</div>
                    <div style="font-size: 11px; color: #6b7280;">Kategori: {r.get('category')}</div>
                </td>
                <td style="padding: 10px; text-align: center;">
                    <span style="background: {bg}; color: {color}; padding: 3px 8px; border-radius: 9999px; font-weight: 700; font-size: 12px; border: 1px solid {color};">{st}</span>
                </td>
                <td style="padding: 10px; text-align: right; font-weight: 600;">{r.get('score', 0)} / {r.get('weight', 0)}</td>
                <td style="padding: 10px; font-size: 12px; font-family: monospace; max-width: 320px; word-break: break-all;">{r.get('actual', '')}</td>
            </tr>
            """

        score = session_data.get("total_score", 0)
        grade_badge = "#16a34a" if score >= 85 else ("#2563eb" if score >= 75 else "#dc2626")

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Laporan Penilaian UKK - {part.get('name', 'Peserta')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; color: #1f2937; line-height: 1.5; }}
        .header {{ text-align: center; border-bottom: 3px double #374151; padding-bottom: 15px; margin-bottom: 25px; }}
        .header h1 {{ margin: 0; font-size: 20px; text-transform: uppercase; }}
        .header h2 {{ margin: 5px 0; font-size: 16px; color: #4b5563; }}
        .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }}
        .meta-table td {{ padding: 6px; }}
        .score-box {{ background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 25px; }}
        .score-num {{ font-size: 40px; font-weight: 900; color: {grade_badge}; margin: 5px 0; }}
        table.results {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
        table.results th {{ background: #f1f5f9; padding: 10px; border-bottom: 2px solid #cbd5e1; font-weight: 700; }}
        @media print {{
            body {{ margin: 15mm; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button onclick="window.print()" style="padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">Cetak / Simpan PDF</button>
    </div>

    <div class="header">
        <h1>SMK NEGERI 1 BANYUMAS</h1>
        <h2>LEMBAR PENILAIAN UJI KOMPETENSI KEAHLIAN (UKK)</h2>
        <div style="font-size: 13px; color: #6b7280;">Konsentrasi Keahlian: Teknik Komputer dan Jaringan — Tahun Ajaran 2026/2027</div>
    </div>

    <table class="meta-table">
        <tr>
            <td style="width: 20%; font-weight: bold;">Nama Peserta:</td>
            <td style="width: 30%;">{part.get('name', '-')}</td>
            <td style="width: 20%; font-weight: bold;">Profil Rubrik:</td>
            <td style="width: 30%;">{session_data.get('rubric_name', '-')}</td>
        </tr>
        <tr>
            <td style="font-weight: bold;">No. Peserta:</td>
            <td>{part.get('participant_number', '-')}</td>
            <td style="font-weight: bold;">Penguji:</td>
            <td>{session_data.get('examiner_name', '-')}</td>
        </tr>
        <tr>
            <td style="font-weight: bold;">Kelas:</td>
            <td>{part.get('student_class', '-')}</td>
            <td style="font-weight: bold;">Waktu Penilaian:</td>
            <td>{session_data.get('completed_at', session_data.get('started_at', '-'))}</td>
        </tr>
        <tr>
            <td style="font-weight: bold;">AWS Account ID:</td>
            <td><code>{session_data.get('aws_account_id', '-')}</code></td>
            <td style="font-weight: bold;">Status Evaluasi:</td>
            <td><strong>{session_data.get('status', '-')}</strong></td>
        </tr>
    </table>

    <div class="score-box">
        <div style="font-size: 14px; font-weight: 700; color: #64748b; text-transform: uppercase;">NILAI AKHIR EVALUASI RESMI</div>
        <div class="score-num">{score} / 100.0</div>
        <div style="font-size: 13px; color: #475569;">
            Ringkasan: <strong>{session_data.get('pass_count', 0)} PASS</strong> | 
            <strong>{session_data.get('fail_count', 0)} FAIL</strong> | 
            <strong>{session_data.get('skip_count', 0)} SKIP</strong> | 
            <strong>{session_data.get('warning_count', 0)} WARNING</strong>
        </div>
    </div>

    <table class="results">
        <thead>
            <tr>
                <th style="width: 8%;">Kode</th>
                <th style="width: 35%;">Indikator Penilaian</th>
                <th style="width: 12%; text-align: center;">Hasil</th>
                <th style="width: 12%; text-align: right;">Skor</th>
                <th style="width: 33%;">Bukti / Temuan Aktual</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div style="margin-top: 40px; display: flex; justify-content: space-between; font-size: 14px;">
        <div style="text-align: center; width: 220px;">
            <div>Peserta Uji,</div>
            <div style="margin-top: 70px; border-bottom: 1px solid black; font-weight: bold;">{part.get('name', '................................')}</div>
            <div>NISN / No. Peserta</div>
        </div>
        <div style="text-align: center; width: 220px;">
            <div>Banyumas, {session_data.get('started_at', '')[:10]}</div>
            <div>Penguji UKK,</div>
            <div style="margin-top: 70px; border-bottom: 1px solid black; font-weight: bold;">{session_data.get('examiner_name', '................................')}</div>
            <div>NIP / ID Penguji</div>
        </div>
    </div>
</body>
</html>"""
        return html

