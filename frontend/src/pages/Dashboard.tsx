import React, { useEffect, useState } from 'react';
import {
  FileCheck2, Users, BookOpen, Timer, CheckCircle,
  AlertTriangle, ArrowUpRight, PlayCircle, RefreshCw, Database
} from 'lucide-react';
import { api } from '../api';
import { DashboardStats } from '../types';
import { StatusBadge } from '../components/StatusBadge';

interface Props {
  onNavigate: (tab: string, param?: any) => void;
}

export const Dashboard: React.FC<Props> = ({ onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-xs text-slate-400">
        <RefreshCw size={20} className="animate-spin mr-2 text-indigo-400" />
        Memuat statistik penilaian...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Dashboard Ringkasan Penilaian</h2>
          <p className="text-xs text-slate-400 mt-1">
            Uji Kompetensi Keahlian Cloud Engineer — Sistem Monitoring & Pelaporan MBG
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 rounded-xl border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-white hover:bg-slate-700 transition"
            title="Segarkan Data"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin text-indigo-400' : ''} />
          </button>
          <button
            onClick={() => onNavigate('new-assessment')}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-600/30 transition"
          >
            <PlayCircle size={16} />
            <span>Mulai Penilaian Siswa</span>
          </button>
        </div>
      </div>

      {/* Connection Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Google Sheets Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-xl ${stats?.google_sheets.is_connected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
              <Database size={20} />
            </div>
            <div>
              <div className="text-xs font-semibold text-white flex items-center gap-2">
                Google Sheets Sync
                <StatusBadge status={stats?.google_sheets.is_connected ? 'CONNECTED' : 'LOCAL_STORAGE'} size="sm" />
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5 font-mono truncate max-w-xs">
                Spreadsheet: {stats?.google_sheets.spreadsheet_id || 'Belum dihubungkan'}
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigate('settings')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
          >
            Konfigurasi <ArrowUpRight size={14} />
          </button>
        </div>

        {/* AWS Auto Play Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-xl ${stats?.auto_play.is_enabled ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-700/30 text-slate-400 border border-slate-700'}`}>
              <Timer size={20} />
            </div>
            <div>
              <div className="text-xs font-semibold text-white flex items-center gap-2">
                AWS Auto Play Manager
                <StatusBadge status={stats?.auto_play.is_enabled ? 'ACTIVE' : 'DISABLED'} size="sm" />
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Interval: {stats?.auto_play.interval_minutes} menit • Status: {stats?.auto_play.last_status}
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigate('autoplay')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
          >
            Atur <ArrowUpRight size={14} />
          </button>
        </div>
      </div>

      {/* Core KPI Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Uji Selesai</span>
            <FileCheck2 size={16} className="text-indigo-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {stats?.completed_assessments || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">/ {stats?.total_assessments || 0} total</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Rata-Rata Nilai</span>
            <CheckCircle size={16} className="text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {stats?.average_score ? stats.average_score.toFixed(1) : '0.0'}
            <span className="text-xs font-normal text-slate-500 ml-1.5">/ 100</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Tingkat Kelulusan</span>
            <AlertTriangle size={16} className="text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {stats?.pass_rate ? stats.pass_rate.toFixed(0) : 0}%
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Peserta Terdaftar</span>
            <Users size={16} className="text-purple-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {stats?.total_participants || 0}
            <span className="text-xs font-normal text-slate-500 ml-1.5">siswa</span>
          </div>
        </div>
      </div>

      {/* Recent Assessment Sessions */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Aktivitas Penilaian Terakhir</h3>
          <button
            onClick={() => onNavigate('assessments')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
          >
            Lihat Semua <ArrowUpRight size={14} />
          </button>
        </div>

        {(!stats?.recent_assessments || stats.recent_assessments.length === 0) ? (
          <div className="text-center py-10 text-xs text-slate-500">
            Belum ada riwayat penilaian. Klik tombol <span className="text-indigo-400 font-semibold">Mulai Penilaian Siswa</span> untuk memulai sesi perdana.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/40 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Peserta</th>
                  <th className="py-2.5 px-3 font-semibold">Profil Rubrik</th>
                  <th className="py-2.5 px-3 font-semibold">Nilai</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                  <th className="py-2.5 px-3 font-semibold">Waktu Uji</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {stats.recent_assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-semibold text-white">{a.participant.name}</div>
                      <div className="text-[11px] text-slate-400">{a.participant.participant_number} • {a.participant.student_class}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-300">{a.rubric_name}</td>
                    <td className="py-3 px-3 font-bold text-white">
                      {a.total_score.toFixed(1)} / {a.max_score}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={a.status} size="sm" />
                    </td>
                    <td className="py-3 px-3 text-slate-400 text-[11px]">
                      {new Date(a.started_at).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => onNavigate('assessment-detail', a.id)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Detail Hasil
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

