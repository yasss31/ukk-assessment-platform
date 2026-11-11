import React, { useState, useEffect } from 'react';
import { FileBarChart, Download, Printer, Filter, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../api';
import { AssessmentSession } from '../types';

export const Reports: React.FC = () => {
  const [assessments, setAssessments] = useState<AssessmentSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.listAssessments();
        setAssessments(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const completed = assessments.filter(a => a.status === 'COMPLETED');
  const avgScore = completed.length > 0
    ? completed.reduce((sum, a) => sum + a.total_score, 0) / completed.length
    : 0;

  const passedCount = completed.filter(a => a.total_score >= 75).length;
  const passRate = completed.length > 0 ? (passedCount / completed.length) * 100 : 0;

  // Breakdown per kelas
  const classBreakdown = completed.reduce((acc, a) => {
    const cls = a.participant.student_class || 'Umum';
    if (!acc[cls]) acc[cls] = { total: 0, passed: 0, scores: [] };
    acc[cls].total += 1;
    if (a.total_score >= 75) acc[cls].passed += 1;
    acc[cls].scores.push(a.total_score);
    return acc;
  }, {} as Record<string, { total: number; passed: number; scores: number[] }>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileBarChart className="text-indigo-400" />
          Laporan Analisis & Ekspor Rekap Nilai
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Rekapitulasi pencapaian kompetensi seluruh peserta Uji Kompetensi Keahlian Cloud Engineer.
        </p>
      </div>

      {/* Top Aggregated Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs text-slate-400">Total Uji Terevaluasi</div>
          <div className="text-2xl font-bold text-white mt-1">{completed.length} siswa</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Dari total {assessments.length} sesi</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs text-slate-400">Rata-Rata Nilai Akhir</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{avgScore.toFixed(1)} / 100</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Batas kompetensi: 75.0</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs text-slate-400">Tingkat Kelulusan (≥ 75)</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1">{passRate.toFixed(0)}%</div>
          <div className="text-[11px] text-slate-500 mt-0.5">{passedCount} siswa dinyatakan Kompeten</div>
        </div>
      </div>

      {/* Breakdown per Class Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4">Rekapitulasi Pencapaian Per Kelas</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Kelas</th>
                <th className="py-2.5 px-3 font-semibold">Jumlah Peserta</th>
                <th className="py-2.5 px-3 font-semibold">Rata-Rata Nilai</th>
                <th className="py-2.5 px-3 font-semibold">Kompeten (Lulus)</th>
                <th className="py-2.5 px-3 font-semibold">Persentase</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {Object.keys(classBreakdown).length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    Belum ada data penilaian yang selesai.
                  </td>
                </tr>
              ) : (
                Object.entries(classBreakdown).map(([cls, data]) => {
                  const cAvg = data.scores.reduce((a, b) => a + b, 0) / data.scores.length;
                  const cPct = (data.passed / data.total) * 100;
                  return (
                    <tr key={cls} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-semibold text-white">{cls}</td>
                      <td className="py-3 px-3 text-slate-300">{data.total} siswa</td>
                      <td className="py-3 px-3 font-bold text-white">{cAvg.toFixed(1)}</td>
                      <td className="py-3 px-3 text-emerald-400 font-semibold">{data.passed} siswa</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          cPct >= 75 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                        }`}>
                          {cPct.toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

