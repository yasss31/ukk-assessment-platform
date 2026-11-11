import React from 'react';
import {
  LayoutDashboard, PlayCircle, History, BookOpen,
  Timer, Users, FileBarChart, Settings as SettingsIcon
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<Props> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new-assessment', label: 'Uji Penilaian Baru', icon: PlayCircle, highlight: true },
    { id: 'assessments', label: 'Riwayat Penilaian', icon: History },
    { id: 'rubrics', label: 'Rubrik Penilaian', icon: BookOpen },
    { id: 'autoplay', label: 'AWS Auto Play', icon: Timer },
    { id: 'participants', label: 'Data Peserta', icon: Users },
    { id: 'reports', label: 'Laporan & Ekspor', icon: FileBarChart },
    { id: 'settings', label: 'Pengaturan & Cloud', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/60 p-4 flex flex-col space-y-1">
      <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
        Navigasi Penilai
      </div>
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`flex items-center space-x-3 w-full px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
              isActive
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : item.highlight
                ? 'text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
            }`}
          >
            <Icon size={18} className={isActive ? 'text-white' : item.highlight ? 'text-indigo-400' : 'text-slate-400'} />
            <span>{item.label}</span>
          </button>
        );
      })}

      <div className="mt-auto pt-4 border-t border-slate-800/80">
        <div className="bg-slate-800/40 rounded-xl p-3 border border-slate-700/40 text-xs text-slate-400">
          <div className="font-semibold text-slate-300 mb-1">Status Keamanan</div>
          <div className="text-[11px] leading-relaxed">
            Kredensial AWS hanya diproses <span className="text-emerald-400 font-medium">in-memory</span>. Kunci rahasia tidak pernah disimpan di disk atau database.
          </div>
        </div>
      </div>
    </aside>
  );
};
