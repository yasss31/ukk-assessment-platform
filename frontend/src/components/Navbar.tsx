import React from 'react';
import { Cloud, LogOut, User as UserIcon, ShieldCheck } from 'lucide-react';
import { User } from '../types';

interface Props {
  user: User | null;
  onLogout: () => void;
}

export const Navbar: React.FC<Props> = ({ user, onLogout }) => {
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
              onClick={onLogout}
              title="Keluar"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors ml-2"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
