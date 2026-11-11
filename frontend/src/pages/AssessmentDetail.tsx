import React, { useEffect, useState } from 'react';
import {
  FileText, Download, Printer, ArrowLeft, RefreshCw,
  CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronUp,
  Search, ShieldCheck, Wrench, Sparkles, Filter, History as HistoryIcon,
  Play
} from 'lucide-react';
import { api } from '../api';
import { AssessmentSession, IndicatorResult, AWSCredentialInput, ErrorSeverity } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ScoreRing } from '../components/ScoreRing';
import { TroubleshootingModal } from '../components/TroubleshootingModal';

interface Props {
  sessionId: string;
  onBack: () => void;
}

export const AssessmentDetail: React.FC<Props> = ({ sessionId, onBack }) => {
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  // Smart Troubleshooting Modal state
  const [activeTroubleshootInd, setActiveTroubleshootInd] = useState<IndicatorResult | null>(null);

  // Reassessment Modal state
  const [showReassessModal, setShowReassessModal] = useState(false);
  const [reassessIndicatorId, setReassessIndicatorId] = useState<string | null>(null);
  const [reassessCreds, setReassessCreds] = useState<AWSCredentialInput>({
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_session_token: '',
    aws_region: 'us-east-1',
  });
  const [reassessing, setReassessing] = useState(false);
  const [reassessFeedback, setReassessFeedback] = useState<string | null>(null);

  const fetchDetail = async () => {
    try {
      const data = await api.getAssessment(sessionId);
      setSession(data);
    } catch (err: any) {
      setError(err.message || 'Gagal memuat detail sesi penilaian');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    const interval = setInterval(() => {
      if (session?.status === 'RUNNING') {
        fetchDetail();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [sessionId, session?.status]);

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleTriggerReassess = async (e: React.FormEvent) => {
    e.preventDefault();
    setReassessing(true);
    setReassessFeedback(null);
    try {
      const targetIds = reassessIndicatorId ? [reassessIndicatorId] : undefined;
      const res = await api.reassess(sessionId, reassessCreds, targetIds);
      setShowReassessModal(false);
      setReassessFeedback('Pemeriksaan ulang berhasil diselesaikan! Skor diperbarui.');
      await fetchDetail();
    } catch (err: any) {
      setReassessFeedback('Gagal memeriksa ulang: ' + err.message);
    } finally {
      setReassessing(false);
    }
  };

  const openReassessDialog = (indId?: string) => {
    setReassessIndicatorId(indId || null);
    setShowReassessModal(true);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 space-y-3 text-xs text-slate-400">
        <RefreshCw size={24} className="animate-spin text-indigo-400" />
        <span>Memuat hasil evaluasi penilaian...</span>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
        <div className="text-rose-400 font-semibold text-sm">Gagal memuat penilaian</div>
        <p className="text-xs text-slate-400">{error || 'Data tidak ditemukan'}</p>
        <button
          onClick={onBack}
          className="bg-slate-800 hover:bg-slate-700 text-white text-xs px-4 py-2 rounded-xl transition"
        >
          Kembali ke Daftar
        </button>
      </div>
    );
  }

  // Filter indikator
  const categories = ['ALL', ...Array.from(new Set(session.results.map(r => r.category)))];
  const filteredResults = session.results.filter(r => {
    const matchCat = selectedCategory === 'ALL' || r.category === selectedCategory;
    const matchSeverity = severityFilter === 'ALL' || (r.severity === severityFilter) || (severityFilter === 'HAS_ISSUE' && r.status !== 'PASS');
    const matchStatus = statusFilter === 'ALL' || r.status === statusFilter;
    const matchSearch = r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        r.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        r.expected.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSeverity && matchStatus && matchSearch;
  });

  const failedCount = session.results.filter(r => r.status === 'FAIL' || r.status === 'ERROR').length;

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 transition"
            title="Kembali"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-tight">
                {session.participant.name} ({session.participant.participant_number})
              </h2>
              <StatusBadge status={session.status} size="sm" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {session.participant.student_class} • {session.participant.school} • Rubrik: {session.rubric_name}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {failedCount > 0 && (
            <button
              onClick={() => openReassessDialog()}
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3.5 py-2 rounded-xl flex items-center space-x-1.5 shadow-md shadow-emerald-600/20 transition"
            >
              <RefreshCw size={14} />
              <span>Periksa Ulang Semua Aspek Gagal</span>
            </button>
          )}
          <a
            href={api.getExportUrl(session.id, 'html')}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-2 rounded-xl flex items-center space-x-1.5 shadow-md shadow-indigo-600/20 transition"
          >
            <Printer size={14} />
            <span>Cetak Lembar Nilai</span>
          </a>
          <a
            href={api.getExportUrl(session.id, 'csv')}
            download
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-2 rounded-xl flex items-center space-x-1.5 transition"
          >
            <Download size={14} />
            <span>CSV</span>
          </a>
          <a
            href={api.getExportUrl(session.id, 'json')}
            download
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-2 rounded-xl flex items-center space-x-1.5 transition"
          >
            <FileText size={14} />
            <span>JSON</span>
          </a>
        </div>
      </div>

      {reassessFeedback && (
        <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-between text-xs text-indigo-300">
          <div className="flex items-center space-x-2">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span>{reassessFeedback}</span>
          </div>
          <button onClick={() => setReassessFeedback(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Main Score & Summary Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Score Ring */}
        <div className="flex justify-center border-b md:border-b-0 md:border-r border-slate-800 pb-6 md:pb-0">
          <ScoreRing score={session.total_score} maxScore={session.max_score} size={140} />
        </div>

        {/* Indicator Counts & Troubleshooting summary */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-300">Ringkasan Validasi Aspek</h4>
            {failedCount > 0 && (
              <span className="text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded-full font-bold">
                {failedCount} Kesalahan Terdeteksi
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-2.5 flex items-center justify-between">
              <span className="text-emerald-400 font-medium">Lolos (PASS)</span>
              <span className="font-bold text-white">{session.pass_count}</span>
            </div>
            <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-2.5 flex items-center justify-between">
              <span className="text-rose-400 font-medium">Gagal (FAIL)</span>
              <span className="font-bold text-white">{session.fail_count}</span>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-2.5 flex items-center justify-between">
              <span className="text-amber-400 font-medium">Peringatan</span>
              <span className="font-bold text-white">{session.warning_count}</span>
            </div>
            <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-2.5 flex items-center justify-between">
              <span className="text-slate-400 font-medium">Dilewati</span>
              <span className="font-bold text-white">{session.skip_count}</span>
            </div>
          </div>
        </div>

        {/* Audit Meta */}
        <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-800 space-y-2 text-xs">
          <div className="flex justify-between text-slate-400">
            <span>Akun AWS:</span>
            <span className="font-mono text-slate-200">{session.aws_account_id || '-'}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Region:</span>
            <span className="font-mono text-slate-200">{session.aws_region}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Penilai:</span>
            <span className="text-slate-200">{session.examiner_name}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Waktu Selesai:</span>
            <span className="text-slate-200">
              {session.completed_at ? new Date(session.completed_at).toLocaleTimeString('id-ID') : 'Dalam Proses'}
            </span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
        {/* Severity & Issue filter bar */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-semibold mr-1 flex items-center gap-1">
            <Filter size={12} /> Filter:
          </span>
          {[
            { id: 'ALL', label: 'Semua Status' },
            { id: 'HAS_ISSUE', label: '⚠️ Hanya Aspek Bermasalah' },
            { id: 'Critical', label: '🔴 Critical' },
            { id: 'Major', label: '🟠 Major' },
            { id: 'Minor', label: '🟡 Minor' },
            { id: 'PASS', label: '🟢 Lolos (PASS)' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => {
                if (['Critical', 'Major', 'Minor', 'HAS_ISSUE'].includes(f.id)) {
                  setSeverityFilter(f.id);
                  setStatusFilter('ALL');
                } else if (f.id === 'PASS') {
                  setStatusFilter('PASS');
                  setSeverityFilter('ALL');
                } else {
                  setSeverityFilter('ALL');
                  setStatusFilter('ALL');
                }
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                (severityFilter === f.id || (f.id === 'PASS' && statusFilter === 'PASS') || (f.id === 'ALL' && severityFilter === 'ALL' && statusFilter === 'ALL'))
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Category Pills & Search */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800">
          <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                  selectedCategory === cat
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-800/80 text-slate-400 hover:text-white'
                }`}
              >
                {cat === 'ALL' ? 'Semua Kategori' : cat}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-64">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari indikator..."
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Indicators List */}
      <div className="space-y-3">
        {filteredResults.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-xs text-slate-500">
            Tidak ada indikator yang sesuai dengan filter yang dipilih.
          </div>
        ) : (
          filteredResults.map((ind) => {
            const isExpanded = !!expandedCards[ind.indicator_id];
            const isPass = ind.status === 'PASS';
            const isFail = ind.status === 'FAIL';
            const hasGuide = !!ind.troubleshooting;

            return (
              <div
                key={ind.indicator_id}
                className={`bg-slate-900 border rounded-2xl p-4 transition-all ${
                  isPass
                    ? 'border-emerald-500/20 bg-gradient-to-r from-slate-900 to-emerald-950/10'
                    : isFail
                    ? 'border-rose-500/30 bg-gradient-to-r from-slate-900 to-rose-950/20 shadow-md shadow-rose-950/10'
                    : 'border-amber-500/20 bg-gradient-to-r from-slate-900 to-amber-950/10'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start space-x-3">
                    <div className="mt-0.5">
                      {isPass ? (
                        <CheckCircle2 size={18} className="text-emerald-400" />
                      ) : isFail ? (
                        <XCircle size={18} className="text-rose-400" />
                      ) : (
                        <AlertTriangle size={18} className="text-amber-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-mono font-bold bg-slate-800 px-2 py-0.5 rounded text-indigo-300">
                          {ind.code}
                        </span>
                        <h4 className="text-xs font-semibold text-white">{ind.name}</h4>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{ind.category}</span>
                        {ind.severity && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            ind.severity === 'Critical' ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                            ind.severity === 'Major' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                            'bg-yellow-500/10 text-yellow-300 border-yellow-500/30'
                          }`}>
                            {ind.severity}
                          </span>
                        )}
                        {ind.is_resolved && (
                          <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold">
                            Terselesaikan
                          </span>
                        )}
                      </div>

                      {/* Expected vs Actual */}
                      <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Kriteria Diharapkan:</span>
                          <span className="font-mono text-slate-300 text-[11px]">{ind.expected}</span>
                        </div>
                        <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Kondisi Aktual (AWS):</span>
                          <span className={`font-mono text-[11px] ${isPass ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {ind.actual}
                          </span>
                        </div>
                      </div>

                      {/* Riwayat Reassessment jika ada */}
                      {ind.reassessment_history && ind.reassessment_history.length > 0 && (
                        <div className="mt-2 text-[10px] text-slate-400 flex items-center gap-1">
                          <HistoryIcon size={12} className="text-indigo-400" />
                          <span>Pernah diperiksa ulang {ind.reassessment_history.length} kali (sebelumnya: {ind.reassessment_history[ind.reassessment_history.length - 1].previous_status})</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions & Score */}
                  <div className="flex flex-col items-end space-y-2 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-bold text-white">
                        {ind.score.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">/ {ind.weight}</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Bobot {ind.weight}</div>
                    </div>

                    <div className="flex items-center space-x-1.5">
                      {!isPass && hasGuide && (
                        <button
                          onClick={() => setActiveTroubleshootInd(ind)}
                          className="bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-semibold px-2.5 py-1 rounded-lg text-[11px] flex items-center space-x-1 transition shadow-sm"
                        >
                          <Wrench size={12} />
                          <span>Panduan Solusi</span>
                        </button>
                      )}

                      {!isPass && (
                        <button
                          onClick={() => openReassessDialog(ind.indicator_id)}
                          className="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 font-semibold px-2 py-1 rounded-lg text-[11px] flex items-center space-x-1 transition"
                          title="Periksa ulang aspek ini"
                        >
                          <RefreshCw size={11} />
                          <span>Uji Ulang</span>
                        </button>
                      )}

                      <button
                        onClick={() => toggleExpand(ind.indicator_id)}
                        className="text-[11px] text-slate-400 hover:text-slate-200 p-1"
                        title="Tampilkan raw evidence"
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Raw Evidence */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-800 text-xs">
                    <div className="text-[11px] font-semibold text-slate-400 mb-1">Bukti Teknis Audit:</div>
                    <pre className="bg-black/50 border border-slate-800 rounded-xl p-3 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      {ind.evidence || ind.error_message || 'Tidak ada detail log tambahan.'}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Troubleshooting Guide Drawer Modal */}
      {activeTroubleshootInd && (
        <TroubleshootingModal
          sessionId={session.id}
          indicator={activeTroubleshootInd}
          onClose={() => setActiveTroubleshootInd(null)}
          onReassessRequest={(indId) => openReassessDialog(indId)}
        />
      )}

      {/* Reassessment Modal */}
      {showReassessModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-lg shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <RefreshCw className="text-emerald-400" />
              <span>
                {reassessIndicatorId
                  ? `Pemeriksaan Ulang Aspek Terpilih (${reassessIndicatorId})`
                  : 'Pemeriksaan Ulang Seluruh Aspek yang Belum Lolos'}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Sistem akan memverifikasi konfigurasi terbaru di akun AWS peserta tanpa menghapus riwayat penilaian sebelumnya.
            </p>

            <form onSubmit={handleTriggerReassess} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Access Key ID</label>
                <input
                  type="text"
                  required
                  value={reassessCreds.aws_access_key_id}
                  onChange={(e) => setReassessCreds({ ...reassessCreds, aws_access_key_id: e.target.value })}
                  placeholder="ASIA..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Secret Access Key</label>
                <input
                  type="password"
                  required
                  value={reassessCreds.aws_secret_access_key}
                  onChange={(e) => setReassessCreds({ ...reassessCreds, aws_secret_access_key: e.target.value })}
                  placeholder="••••••••••••••"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Session Token</label>
                <textarea
                  rows={2}
                  required
                  value={reassessCreds.aws_session_token}
                  onChange={(e) => setReassessCreds({ ...reassessCreds, aws_session_token: e.target.value })}
                  placeholder="IQoJb3Jp..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2 text-xs font-mono text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReassessModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs hover:bg-slate-700"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={reassessing}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  {reassessing ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                  <span>{reassessing ? 'Memeriksa Ulang...' : 'Mulai Verifikasi'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
