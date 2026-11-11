# Panduan Deployment UKK Assessment Platform

Dokumen ini menyediakan opsi deployment untuk menjalankan UKK Assessment Platform dalam berbagai lingkungan.

---

## Opsi 1: Single VPS dengan Docker Compose (Sangat Direkomendasikan)
Menjalankan frontend dan backend dalam satu container stack di VPS Linux (Ubuntu / Debian / CentOS).

```bash
git clone https://github.com/yasss31/ukk-assessment-platform.git
cd ukk-assessment-platform
docker compose up -d --build
```

**Port:**
- `80`: Frontend Web (Nginx reverse proxy ke backend)
- `8000`: Backend FastAPI (Internal/Direct)

---

## Opsi 2: Split Deployment (Vercel Frontend + Render/VPS Backend)

Jika ingin memisahkan frontend ke serverless CDN:
1. **Frontend:** Deploy folder `frontend/` ke [Vercel](https://vercel.com) dengan build command `npm run build` dan output directory `dist`.
   - Set environment variable: `VITE_API_URL=https://api-ukk.domainanda.com`
2. **Backend:** Deploy folder `backend/` ke VPS atau [Render.com](https://render.com) sebagai web service Docker / Python.
   - Set environment variable `CORS_ORIGINS=https://ukk.vercel.app,https://ukk.domainanda.com`

---

## Opsi 3: Pengujian Manual Bare-Metal (Tanpa Docker)

### Backend (FastAPI):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend (Vite):
```bash
cd frontend
npm install
npm run build
npm run preview -- --port 80 --host
```
