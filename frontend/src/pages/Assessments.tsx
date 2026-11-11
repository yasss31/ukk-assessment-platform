import React, { useState, useEffect } from 'react';
import { History, Search, ArrowRight, Printer, RefreshCw } from 'lucide-react';
import { api } from '../api';
import { AssessmentSession } from '../types';
import { StatusBadge } from '../components/StatusBadge';

interface Props {
  onNavigate: (tab: string, param?: any) => void;
}

export const Assessments: React.FC<Props> = ({ onNavigate }) => {
  const [assessments, setAssessments] = useState<AssessmentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchAssessments = async () => {
    try {
      const data = await api.listAssessments();
      setAssessments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  const filtered = assessments.filter(a => {
    const matchStatus = statusFilter === 'ALL' || a.status === statusFilter;
    const matchSearch =
      a.participant.name.toLowerCase().includes(search.toLowerCase()) ||
      a.participant.participant_number.toLowerCase().includes(search.toLowerCase()) ||
      a.participant.student_class.toLowerCase().includes(search.toLowerCase()) ||
      a.rubric_name.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="text-indigo-400" />
            Riwayat Penilaian UKK Siswa
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Daftar seluruh sesi penilaian infrastruktur AWS yang telah dievaluasi oleh sistem.
          </p>
        </div>
        <button
          onClick={() => { setLoading(true); fetchAssessments(); }}
          className="p-2.5 rounded-xl border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition"
          title="Segarkan"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin text-indigo-400' : ''} />
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center space-x-2">
          {['ALL', 'COMPLETED', 'RUNNING', 'FAILED'].map(st => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {st === 'ALL' ? 'Semua Status' : st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari nama siswa, nomor peserta, kelas..."
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs text-slate-400 flex items-center justify-center">
            <RefreshCw size={18} className="animate-spin text-indigo-400 mr-2" />
            Memuat riwayat penilaian...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            Tidak ada sesi penilaian yang cocok dengan pencarian.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Peserta Ujian</th>
                  <th className="py-3 px-4 font-semibold">Profil Rubrik</th>
                  <th className="py-3 px-4 font-semibold">Nilai Akhir</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Lolos / Gagal</th>
                  <th className="py-3 px-4 font-semibold">Tanggal & Waktu</th>
                  <th className="py-3 px-4 font-semibold text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filtered.map(a => (
                  <tr key={a.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{a.participant.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {a.participant.participant_number} • {a.participant.student_class}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div>{a.rubric_name}</div>
                      <div className="text-[10px] text-slate-500">v{a.rubric_version}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-sm font-bold text-white">
                        {a.total_score.toFixed(1)}
                      </span>
                      <span className="text-slate-500 text-[10px]"> / {a.max_score}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={a.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-emerald-400 font-semibold">{a.pass_count}</span>
                      <span className="text-slate-500"> / </span>
                      <span className="text-rose-400 font-semibold">{a.fail_count}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {new Date(a.started_at).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <a
                        href={api.getExportUrl(a.id, 'html')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 inline-block text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition"
                        title="Cetak Lembar Nilai"
                      >
                        <Printer size={15} />
                      </a>
                      <button
                        onClick={() => onNavigate('assessment-detail', a.id)}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-3 py-1.5 rounded-xl text-xs inline-flex items-center space-x-1 transition shadow-sm"
                      >
                        <span>Detail</span>
                        <ArrowRight size={12} />
                      </button>
                    </td>
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
