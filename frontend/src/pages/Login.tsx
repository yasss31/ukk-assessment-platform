import React, { useState } from 'react';
import { Cloud, Lock, User as UserIcon, AlertCircle, ArrowRight } from 'lucide-react';
import { api } from '../api';
import { User } from '../types';

interface Props {
  onLoginSuccess: (user: User, token: string) => void;
}

export const Login: React.FC<Props> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('adminukk2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const form = new URLSearchParams();
      form.append('username', username);
      form.append('password', password);

      const res = await api.login(form);
      localStorage.setItem('ukk_token', res.access_token);
      localStorage.setItem('ukk_user', JSON.stringify(res.user));
      onLoginSuccess(res.user, res.access_token);
    } catch (err: any) {
      setError(err.message || 'Gagal masuk. Periksa kembali username dan password Anda.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        {/* Ambient lighting glow */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col items-center text-center mb-8">
          <div className="p-3.5 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white shadow-xl shadow-indigo-600/25 mb-4">
            <Cloud size={32} className="stroke-[2.5]" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">UKK Assessment Platform</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">
            Portal Penilaian Otomatis UKK Cloud Engineer SMK Negeri 1 Banyumas
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start space-x-2.5 text-xs text-rose-300">
            <AlertCircle size={16} className="shrink-0 mt-0.5 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Username</label>
            <div className="relative">
              <UserIcon size={16} className="absolute left-3.5 top-3 text-slate-500" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Masukkan username penilai"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (
              <span>Memverifikasi Sesi...</span>
            ) : (
              <>
                <span>Masuk ke Portal Penilaian</span>
                <ArrowRight size={14} />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800/80 text-center">
          <p className="text-[11px] text-slate-500">
            Akun bawaan sistem: <span className="text-slate-300 font-mono">admin</span> / <span className="text-slate-300 font-mono">adminukk2026</span>
          </p>
        </div>
      </div>
    </div>
  );
};
