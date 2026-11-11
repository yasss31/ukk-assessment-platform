import React, { useState } from 'react';
import { Cloud, LogOut, User as UserIcon, ShieldCheck, Key, CheckCircle2, AlertCircle } from 'lucide-react';
import type { User } from '../types';
import { api } from '../api';

interface Props {
  user: User | null;
  onLogout: () => void;
}

export const Navbar: React.FC<Props> = ({ user, onLogout }) => {
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [pwdMsg, setPwdMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPassword(true);
    setPwdMsg(null);
    try {
      await api.changePassword(currentPassword, newPassword);
      setPwdMsg({ type: 'success', text: 'Kata sandi berhasil diperbarui!' });
      setCurrentPassword('');
      setNewPassword('');
      setTimeout(() => setShowPasswordModal(false), 1500);
    } catch (err: any) {
      setPwdMsg({ type: 'error', text: err.message || 'Gagal mengubah kata sandi' });
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white shadow-lg shadow-indigo-500/20">
          <Cloud size={24} className="stroke-[2.5]" />
        </div>
        <div>
          <h1 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
            UKK Assessment Platform
            <span className="text-[10px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full">
              Cloud Engineer 2026/2027
            </span>
          </h1>
          <p className="text-xs text-slate-400">SMK Negeri 1 Banyumas — Program Makan Bergizi Gratis (MBG)</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {user && (
          <div className="flex items-center space-x-3 bg-slate-800/80 border border-slate-700/60 rounded-xl px-3 py-1.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300">
              {user.role === 'super_admin' ? <ShieldCheck size={16} /> : <UserIcon size={16} />}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-semibold text-white leading-tight">{user.full_name}</div>
              <div className="text-[10px] text-slate-400 capitalize">{user.role.replace('_', ' ')}</div>
            </div>
            <button
              onClick={() => setShowPasswordModal(true)}
              title="Ganti Kata Sandi"
              className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors ml-1"
            >
              <Key size={15} />
            </button>
            <button
              onClick={onLogout}
              title="Keluar"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-sm shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Key size={16} className="text-indigo-400" />
              Ganti Kata Sandi Penguji
            </h3>
            <p className="text-xs text-slate-400">
              Ubah kata sandi akun default untuk meningkatkan keamanan portal penilaian.
            </p>

            {pwdMsg && (
              <div className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
                pwdMsg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              }`}>
                {pwdMsg.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                <span>{pwdMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Kata Sandi Saat Ini</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="adminukk2026"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Kata Sandi Baru (Min. 6 Karakter)</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  className="px-3.5 py-1.5 bg-slate-800 text-slate-300 rounded-xl text-xs hover:bg-slate-700"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={savingPassword}
                  className="px-3.5 py-1.5 bg-indigo-600 text-white font-semibold rounded-xl text-xs hover:bg-indigo-500 disabled:opacity-50"
                >
                  {savingPassword ? 'Menyimpan...' : 'Perbarui Kata Sandi'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
