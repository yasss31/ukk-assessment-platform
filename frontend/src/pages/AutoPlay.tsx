import React, { useState, useEffect } from 'react';
import {
  Timer, Power, Play, AlertTriangle, ShieldCheck, RefreshCw,
  Clock, CheckCircle2, History, Info
} from 'lucide-react';
import { api } from '../api';
import { AutoPlayConfig, AutoPlayLog, AWSCredentialInput } from '../types';
import { StatusBadge } from '../components/StatusBadge';

export const AutoPlay: React.FC = () => {
  const [config, setConfig] = useState<AutoPlayConfig | null>(null);
  const [logs, setLogs] = useState<AutoPlayLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [manualCreds, setManualCreds] = useState<AWSCredentialInput>({
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_session_token: '',
    aws_region: 'us-east-1',
  });
  const [showManualModal, setShowManualModal] = useState(false);
  const [manualRunning, setManualRunning] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchData = async () => {
    try {
      const [cfg, logRes] = await Promise.all([
        api.getAutoPlayConfig(),
        api.getAutoPlayLogs(50),
      ]);
      setConfig(cfg);
      setLogs(logRes.logs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggle = async () => {
    if (!config) return;
    setUpdating(true);
    setFeedback(null);
    try {
      const updated = await api.updateAutoPlayConfig({
        is_enabled: !config.is_enabled,
        interval_minutes: config.interval_minutes,
      });
      setConfig(updated);
      await fetchData();
      setFeedback({
        type: 'success',
        text: `AWS Auto Play berhasil diubah ke: ${updated.is_enabled ? 'AKTIF (ENABLED)' : 'NONAKTIF (DISABLED)'}`,
      });
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message });
    } finally {
      setUpdating(false);
    }
  };

  const handleIntervalChange = async (newInterval: number) => {
    if (!config) return;
    setUpdating(true);
    try {
      const updated = await api.updateAutoPlayConfig({
        is_enabled: config.is_enabled,
        interval_minutes: newInterval,
      });
      setConfig(updated);
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message });
    } finally {
      setUpdating(false);
    }
  };

  const handleRunNow = async (e: React.FormEvent) => {
    e.preventDefault();
    setManualRunning(true);
    setFeedback(null);
    try {
      const res = await api.runAutoPlayNow(manualCreds);
      setShowManualModal(false);
      await fetchData();
      setFeedback({
        type: 'success',
        text: res.message || 'Siklus Auto Play berhasil dijalankan.',
      });
    } catch (err: any) {
      setFeedback({ type: 'error', text: err.message });
    } finally {
      setManualRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Timer className="text-indigo-400" />
          AWS Auto Play Manager
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Pengelola terjadwal untuk menjaga kesiapan instance EC2 siswa secara aman dan hemat biaya di AWS Academy Learner Lab.
        </p>
      </div>

      {/* Safety & Cost Guard Alert */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 flex items-start space-x-3 text-xs text-amber-300">
        <AlertTriangle size={20} className="shrink-0 text-amber-400 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold text-amber-300">Protokol Keamanan & Penghematan Biaya AWS Academy</div>
          <div className="text-[11px] leading-relaxed text-amber-300/80">
            • Auto Play <span className="font-bold underline">HANYA</span> menyalakan instance yang berstatus <code className="bg-amber-950/40 px-1 py-0.5 rounded text-amber-200">stopped</code>.<br />
            • Menerapkan <span className="font-semibold">idempotensi penuh</span>: jika instance sudah <code className="bg-amber-950/40 px-1 py-0.5 rounded text-amber-200">running</code>, sistem tidak melakukan tindakan apa pun (NOOP).<br />
            • Kredensial tidak disimpan di disk untuk mencegah penggunaan kuota tanpa izin.
          </div>
        </div>
      </div>

      {feedback && (
        <div className={`p-4 rounded-2xl border text-xs flex items-center space-x-2 ${
          feedback.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
        }`}>
          {feedback.type === 'success' ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-rose-400" />}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Toggle & Interval Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Status Penjadwalan</h3>
              <p className="text-xs text-slate-400 mt-0.5">Nyalakan/matikan siklus pengecekan otomatis</p>
            </div>
            <button
              onClick={handleToggle}
              disabled={updating || loading}
              className={`p-3 rounded-2xl flex items-center justify-center transition shadow-lg ${
                config?.is_enabled
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700'
              }`}
            >
              <Power size={20} className={updating ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="pt-2 border-t border-slate-800">
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-2">
              <span>Interval Pengecekan:</span>
              <span className="text-indigo-400 font-mono">{config?.interval_minutes || 180} menit ({((config?.interval_minutes || 180)/60).toFixed(1)} jam)</span>
            </div>
            <input
              type="range"
              min="15"
              max="360"
              step="15"
              value={config?.interval_minutes || 180}
              onChange={(e) => handleIntervalChange(parseInt(e.target.value))}
              disabled={updating}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>15 menit (cepat)</span>
              <span>180 menit (standar)</span>
              <span>360 menit (hemat)</span>
            </div>
          </div>
        </div>

        {/* Manual Trigger Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Play size={16} className="text-indigo-400" />
              Siklus Manual Seketika
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Jalankan siklus pengecekan dan start instance yang sedang berstatus <span className="text-rose-400 font-semibold">stopped</span> seketika menggunakan kredensial aktif penguji.
            </p>
          </div>

          <button
            onClick={() => setShowManualModal(true)}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/30 transition"
          >
            <Play size={14} />
            <span>Jalankan Siklus Sekarang</span>
          </button>
        </div>
      </div>

      {/* Manual Run Modal */}
      {showManualModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white">Masukkan Kredensial AWS Penguji untuk Siklus Ini</h3>
            <p className="text-xs text-slate-400">
              Kredensial hanya digunakan satu kali saat pemanggilan ini dan langsung dibuang dari memori.
            </p>

            <form onSubmit={handleRunNow} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Access Key ID</label>
                <input
                  type="text"
                  required
                  value={manualCreds.aws_access_key_id}
                  onChange={(e) => setManualCreds({ ...manualCreds, aws_access_key_id: e.target.value })}
                  placeholder="ASIA..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Secret Access Key</label>
                <input
                  type="password"
                  required
                  value={manualCreds.aws_secret_access_key}
                  onChange={(e) => setManualCreds({ ...manualCreds, aws_secret_access_key: e.target.value })}
                  placeholder="••••••••••••••"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Session Token</label>
                <textarea
                  rows={2}
                  required
                  value={manualCreds.aws_session_token}
                  onChange={(e) => setManualCreds({ ...manualCreds, aws_session_token: e.target.value })}
                  placeholder="IQoJb3Jp..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2 text-xs font-mono text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs hover:bg-slate-700"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={manualRunning}
                  className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-xl text-xs hover:bg-indigo-500 flex items-center gap-1.5"
                >
                  {manualRunning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                  <span>{manualRunning ? 'Menjalankan...' : 'Eksekusi Sekarang'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Activity Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <History size={16} className="text-slate-400" />
            Riwayat Log Aktivitas Auto Play
          </h3>
          <span className="text-xs text-slate-500">{logs.length} catatan audit</span>
        </div>

        {logs.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            Belum ada aktivitas tercatat.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/40 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Waktu</th>
                  <th className="py-2.5 px-3 font-semibold">Aksi</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                  <th className="py-2.5 px-3 font-semibold">Akun AWS</th>
                  <th className="py-2.5 px-3 font-semibold">Rincian Eksekusi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
                {logs.map(l => (
                  <tr key={l.id} className="hover:bg-slate-800/20">
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                      {new Date(l.timestamp).toLocaleString('id-ID')}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-indigo-300">{l.action}</td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={l.status} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{l.account_id || '-'}</td>
                    <td className="py-2.5 px-3 text-slate-300 font-sans text-xs">{l.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

