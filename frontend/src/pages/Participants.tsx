import React, { useState, useEffect } from 'react';
import { Users, Plus, Trash2, Search, CheckCircle2, AlertCircle, School } from 'lucide-react';
import { api } from '../api';
import { Participant } from '../types';

export const Participants: React.FC = () => {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPart, setNewPart] = useState({
    name: '',
    participant_number: '',
    student_class: 'XII TKJ 1',
    school: 'SMK Negeri 1 Banyumas',
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchParticipants = async () => {
    try {
      const data = await api.listParticipants();
      setParticipants(data);
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParticipants();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      await api.createParticipant(newPart);
      setShowAddModal(false);
      setNewPart({
        name: '',
        participant_number: '',
        student_class: 'XII TKJ 1',
        school: 'SMK Negeri 1 Banyumas',
      });
      await fetchParticipants();
      setMsg({ type: 'success', text: 'Peserta berhasil ditambahkan!' });
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Yakin ingin menghapus data peserta "${name}"?`)) return;
    try {
      await api.deleteParticipant(id);
      await fetchParticipants();
      setMsg({ type: 'success', text: `Peserta "${name}" berhasil dihapus.` });
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message });
    }
  };

  const filtered = participants.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.participant_number.toLowerCase().includes(search.toLowerCase()) ||
    p.student_class.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="text-purple-400" />
            Data Peserta Uji Kompetensi Keahlian
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Kelola daftar siswa peserta ujian Cloud Engineer.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center space-x-2 shadow-lg shadow-indigo-600/30 transition"
        >
          <Plus size={16} />
          <span>Tambah Peserta</span>
        </button>
      </div>

      {msg && (
        <div className={`p-4 rounded-2xl border text-xs flex items-center space-x-2 ${
          msg.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
        }`}>
          {msg.type === 'success' ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertCircle size={16} className="text-rose-400" />}
          <span>{msg.text}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari nama, nomor ujian, atau kelas..."
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div className="text-xs text-slate-400">
          Total: <span className="text-white font-bold">{participants.length}</span> peserta
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Memuat data peserta...</div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">Belum ada data peserta yang cocok.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Nomor Ujian</th>
                  <th className="py-3 px-4 font-semibold">Nama Lengkap Siswa</th>
                  <th className="py-3 px-4 font-semibold">Kelas</th>
                  <th className="py-3 px-4 font-semibold">Asal Sekolah</th>
                  <th className="py-3 px-4 font-semibold text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filtered.map(p => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-indigo-400">{p.participant_number}</td>
                    <td className="py-3.5 px-4 font-semibold text-white">{p.name}</td>
                    <td className="py-3.5 px-4 text-slate-300">{p.student_class}</td>
                    <td className="py-3.5 px-4 text-slate-400">{p.school}</td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDelete(p.id, p.name)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                        title="Hapus"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Plus size={16} className="text-indigo-400" />
              Pendaftaran Peserta UKK Baru
            </h3>

            <form onSubmit={handleAdd} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Nomor Peserta UKK</label>
                <input
                  type="text"
                  required
                  value={newPart.participant_number}
                  onChange={(e) => setNewPart({ ...newPart, participant_number: e.target.value })}
                  placeholder="UKK-CE-2627-003"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Nama Lengkap Siswa</label>
                <input
                  type="text"
                  required
                  value={newPart.name}
                  onChange={(e) => setNewPart({ ...newPart, name: e.target.value })}
                  placeholder="Ahmad Fauzi"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Kelas</label>
                <input
                  type="text"
                  required
                  value={newPart.student_class}
                  onChange={(e) => setNewPart({ ...newPart, student_class: e.target.value })}
                  placeholder="XII TKJ 1"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Sekolah</label>
                <input
                  type="text"
                  required
                  value={newPart.school}
                  onChange={(e) => setNewPart({ ...newPart, school: e.target.value })}
                  placeholder="SMK Negeri 1 Banyumas"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs hover:bg-slate-700"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-xl text-xs hover:bg-indigo-500"
                >
                  {saving ? 'Menyimpan...' : 'Simpan Peserta'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

