import React, { useEffect, useState } from 'react';
import {
  FileText, Download, Printer, ArrowLeft, RefreshCw,
  CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronUp,
  Search, ExternalLink, ShieldCheck, Clock
} from 'lucide-react';
import { api } from '../api';
import { AssessmentSession, IndicatorResult } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ScoreRing } from '../components/ScoreRing';

interface Props {
  sessionId: string;
  onBack: () => void;
}

export const AssessmentDetail: React.FC<Props> = ({ sessionId, onBack }) => {
  const [session, setSession] = useState<AssessmentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

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
    // Jika status masih RUNNING, polling setiap 3 detik
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

  // Filter indikator berdasarkan kategori dan pencarian
  const categories = ['ALL', ...Array.from(new Set(session.results.map(r => r.category)))];
  const filteredResults = session.results.filter(r => {
    const matchCat = selectedCategory === 'ALL' || r.category === selectedCategory;
    const matchSearch = r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        r.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        r.expected.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSearch;
  });

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

        {/* Export / Print Buttons */}
        <div className="flex items-center space-x-2">
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

      {/* Main Score & Summary Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Score Ring */}
        <div className="flex justify-center border-b md:border-b-0 md:border-r border-slate-800 pb-6 md:pb-0">
          <ScoreRing score={session.total_score} maxScore={session.max_score} size={140} />
        </div>

        {/* Indicator Counts */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-300">Ringkasan Validasi Aspek</h4>
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
          {session.duration_seconds && (
            <div className="flex justify-between text-slate-400">
              <span>Durasi Audit:</span>
              <span className="text-slate-200">{session.duration_seconds.toFixed(1)} detik</span>
            </div>
          )}
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-4">
        {/* Category Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              {cat === 'ALL' ? 'Semua Kategori' : cat}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Cari indikator atau aspek..."
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Indicators List */}
      <div className="space-y-3">
        {filteredResults.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-xs text-slate-500">
            Tidak ada indikator yang sesuai dengan filter.
          </div>
        ) : (
          filteredResults.map((ind) => {
            const isExpanded = !!expandedCards[ind.indicator_id];
            const isPass = ind.status === 'PASS';
            const isFail = ind.status === 'FAIL';

            return (
              <div
                key={ind.indicator_id}
                className={`bg-slate-900 border rounded-2xl p-4 transition-colors ${
                  isPass
                    ? 'border-emerald-500/20 bg-gradient-to-r from-slate-900 to-emerald-950/10'
                    : isFail
                    ? 'border-rose-500/20 bg-gradient-to-r from-slate-900 to-rose-950/10'
                    : 'border-slate-800'
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
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] font-mono font-bold bg-slate-800 px-2 py-0.5 rounded text-indigo-300">
                          {ind.code}
                        </span>
                        <h4 className="text-xs font-semibold text-white">{ind.name}</h4>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{ind.category}</span>
                      </div>

                      {/* Expected vs Actual */}
                      <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Nilai Diharapkan (Rubrik):</span>
                          <span className="font-mono text-slate-300 text-[11px]">{ind.expected}</span>
                        </div>
                        <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Kondisi Aktual (AWS):</span>
                          <span className={`font-mono text-[11px] ${isPass ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {ind.actual}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Score & Expand */}
                  <div className="flex flex-col items-end space-y-2 shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-bold text-white">
                        {ind.score.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">/ {ind.weight}</span>
                      </div>
                      <div className="text-[10px] text-slate-500">Bobot {ind.weight}</div>
                    </div>
                    <button
                      onClick={() => toggleExpand(ind.indicator_id)}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center space-x-0.5"
                    >
                      <span>{isExpanded ? 'Tutup Bukti' : 'Lihat Bukti'}</span>
                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Evidence & Technical Dump */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-800 text-xs">
                    <div className="text-[11px] font-semibold text-slate-400 mb-1">Bukti Audit & Respons API AWS:</div>
                    <pre className="bg-black/50 border border-slate-800 rounded-xl p-3 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      {ind.evidence || ind.error_message || 'Tidak ada detail data tambahan.'}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
