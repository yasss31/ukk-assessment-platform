import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon, Database, ExternalLink, RefreshCw,
  CheckCircle2, AlertTriangle, ShieldCheck, Terminal, Globe, Server
} from 'lucide-react';
import { api } from '../api';
import { StatusBadge } from '../components/StatusBadge';

export const Settings: React.FC = () => {
  const [sheetsStatus, setSheetsStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [savingJson, setSavingJson] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getSheetsStatus();
      setSheetsStatus(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTestConnection = async () => {
    setTesting(true);
    setMsg(null);
    try {
      const res = await api.testSheetsConnection();
      await fetchStatus();
      if (res.success) {
        setMsg({ type: 'success', text: `${res.message} Lembar ditemukan: ${(res.available_sheets || []).join(', ') || 'Baru'}` });
      } else {
        setMsg({ type: 'error', text: res.message || 'Koneksi gagal.' });
      }
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveServiceAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingJson(true);
    setMsg(null);
    try {
      const res = await api.configureSheets(jsonInput);
      await fetchStatus();
      if (res.success) {
        setMsg({ type: 'success', text: res.message });
        setJsonInput('');
      } else {
        setMsg({ type: 'error', text: res.error || res.message });
      }
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setSavingJson(false);
    }
  };

  const handleSyncNow = async () => {
    setSyncing(true);
    setMsg(null);
    try {
      const res = await api.syncSheets();
      setMsg({ type: 'success', text: res.message });
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="text-indigo-400" />
          Pengaturan Integrasi & Konfigurasi Cloud
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Konfigurasi Google Sheets API, sinkronisasi data peserta, dan panduan domain Cloudflare Tunnel VPS.
        </p>
      </div>

      {msg && (
        <div className={`p-4 rounded-2xl border text-xs flex items-center space-x-2 ${
          msg.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
        }`}>
          {msg.type === 'success' ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-rose-400" />}
          <span>{msg.text}</span>
        </div>
      )}

      {/* Google Sheets Settings */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Database size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Google Sheets Live Sync</h3>
              <p className="text-xs text-slate-400">Sinkronisasi hasil penilaian ke spreadsheet secara otomatis</p>
            </div>
          </div>
          <StatusBadge status={sheetsStatus?.is_connected ? 'CONNECTED' : 'LOCAL_FALLBACK'} />
        </div>

        <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-800 space-y-2 text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <span className="text-slate-400 font-medium">Target Spreadsheet ID:</span>
            <a
              href={`https://docs.google.com/spreadsheets/d/${sheetsStatus?.spreadsheet_id || '1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8'}/edit`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
            >
              <span>{sheetsStatus?.spreadsheet_id || '1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8'}</span>
              <ExternalLink size={12} />
            </a>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Mode Penyimpanan:</span>
            <span className="text-white font-medium">
              {sheetsStatus?.is_connected ? 'Dual Sync (Sheets + Local JSON)' : 'Local JSON Fallback (Aman & Portabel)'}
            </span>
          </div>
          {sheetsStatus?.error && (
            <div className="text-amber-400 text-[11px] pt-1">
              Catatan: {sheetsStatus.error}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 pt-1">
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition"
          >
            <RefreshCw size={14} className={testing ? 'animate-spin text-indigo-400' : ''} />
            <span>Uji Ulang Koneksi Google Sheets</span>
          </button>
          {sheetsStatus?.is_connected && (
            <button
              onClick={handleSyncNow}
              disabled={syncing}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 transition"
            >
              <span>{syncing ? 'Sinkronisasi...' : 'Sinkronkan Data Sekarang'}</span>
            </button>
          )}
        </div>

        {/* Service Account JSON Input */}
        <form onSubmit={handleSaveServiceAccount} className="pt-4 border-t border-slate-800 space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Konfigurasi Kredensial Service Account Google Cloud (JSON)
            </label>
            <p className="text-[11px] text-slate-500 mb-2">
              Paste isi file <code className="bg-slate-800 px-1 py-0.5 rounded text-slate-300">service_account.json</code> dari Google Cloud Console. Pastikan email service account sudah diundang sebagai <strong>Editor</strong> pada Google Spreadsheet di atas.
            </p>
            <textarea
              rows={4}
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder='{ "type": "service_account", "project_id": "...", "private_key": "...", "client_email": "..." }'
              className="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={savingJson || !jsonInput.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-xl transition disabled:opacity-50"
          >
            {savingJson ? 'Menyimpan & Menghubungkan...' : 'Terapkan Service Account'}
          </button>
        </form>
      </div>

      {/* Cloudflared Tunnel & VPS Deployment Instructions */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-orange-500/10 text-orange-400 border border-orange-500/20">
            <Globe size={20} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Panduan Domain Publik & Cloudflare Tunnel (VPS)</h3>
            <p className="text-xs text-slate-400">Jalankan platform di VPS Anda dan sambungkan domain tanpa membuka port router</p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-300 bg-slate-800/40 p-4 rounded-xl border border-slate-800 font-mono">
          <div># 1. Jalankan aplikasi di VPS dengan Docker Compose:</div>
          <div className="text-indigo-300 bg-black/40 p-2 rounded-lg">docker compose up -d --build</div>

          <div className="pt-2"># 2. Hubungkan domain menggunakan Cloudflare Tunnel:</div>
          <div className="text-indigo-300 bg-black/40 p-2 rounded-lg">
            cloudflared tunnel route dns &lt;TUNNEL_NAME&gt; ukk.domainanda.com<br />
            cloudflared tunnel run --url http://localhost:80 &lt;TUNNEL_NAME&gt;
          </div>

          <div className="pt-2"># 3. Atau gunakan quick tunnel Cloudflare seketika tanpa login:</div>
          <div className="text-indigo-300 bg-black/40 p-2 rounded-lg">cloudflared tunnel --url http://localhost:80</div>
        </div>
      </div>
    </div>
  );
};

