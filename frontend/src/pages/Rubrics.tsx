import React, { useState, useEffect } from 'react';
import { BookOpen, Copy, Trash2, CheckCircle2, AlertTriangle, Plus, Save, Layers } from 'lucide-react';
import { api } from '../api';
import { RubricProfile, RubricIndicator } from '../types';

export const Rubrics: React.FC = () => {
  const [rubrics, setRubrics] = useState<RubricProfile[]>([]);
  const [selectedRubric, setSelectedRubric] = useState<RubricProfile | null>(null);
  const [indicators, setIndicators] = useState<RubricIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchRubrics = async () => {
    try {
      const data = await api.listRubrics();
      setRubrics(data);
      if (data.length > 0) {
        const active = selectedRubric ? (data.find(r => r.id === selectedRubric.id) || data[0]) : data[0];
        setSelectedRubric(active);
        setIndicators(active.indicators);
      }
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRubrics();
  }, []);

  const handleSelectRubric = (r: RubricProfile) => {
    setSelectedRubric(r);
    setIndicators(r.indicators);
    setSuccessMsg(null);
    setErrorMsg(null);
  };

  const handleDuplicate = async (id: string) => {
    try {
      setSaving(true);
      const cloned = await api.duplicateRubric(id);
      await fetchRubrics();
      setSelectedRubric(cloned);
      setIndicators(cloned.indicators);
      setSuccessMsg(`Profil rubrik berhasil disalin: ${cloned.name}`);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleWeightChange = (index: number, newWeight: number) => {
    const updated = [...indicators];
    updated[index].weight = Math.max(0, newWeight);
    setIndicators(updated);
  };

  const handleToggleActive = (index: number) => {
    const updated = [...indicators];
    updated[index].is_active = !updated[index].is_active;
    setIndicators(updated);
  };

  const handleSaveProfile = async () => {
    if (!selectedRubric) return;
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const updated = await api.updateRubric(selectedRubric.id, {
        name: selectedRubric.name,
        version: selectedRubric.version,
        description: selectedRubric.description,
        indicators: indicators,
      });
      setSelectedRubric(updated);
      setIndicators(updated.indicators);
      await fetchRubrics();
      setSuccessMsg('Perubahan bobot dan indikator rubrik berhasil disimpan!');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setSaving(false);
    }
  };

  const totalCurrentWeight = indicators
    .filter(i => i.is_active)
    .reduce((sum, i) => sum + (Number(i.weight) || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <BookOpen className="text-purple-400" />
          Manajemen Rubrik Penilaian Dinamis
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Kustomisasi bobot, indikator aktif, dan kriteria penilaian. Penguji dapat membuat variasi rubrik berbeda untuk tiap batch siswa.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center space-x-2 text-xs text-emerald-300">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center space-x-2 text-xs text-rose-300">
          <AlertTriangle size={16} className="text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Profile Selector & Quick Action Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto">
          {rubrics.map(r => (
            <button
              key={r.id}
              onClick={() => handleSelectRubric(r)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                selectedRubric?.id === r.id
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {r.name}
            </button>
          ))}
        </div>

        {selectedRubric && (
          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            <button
              onClick={() => handleDuplicate(selectedRubric.id)}
              disabled={saving}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium px-3 py-2 rounded-xl flex items-center space-x-1.5 transition"
            >
              <Copy size={14} />
              <span>Duplikasi Profil</span>
            </button>
            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-1.5 shadow-md shadow-purple-600/25 transition disabled:opacity-50"
            >
              <Save size={14} />
              <span>{saving ? 'Menyimpan...' : 'Simpan Rubrik'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Selected Rubric Info & Weight Summary */}
      {selectedRubric && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white">{selectedRubric.name}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{selectedRubric.description}</p>
            </div>
            <div className={`px-4 py-2 rounded-xl border text-xs font-bold flex items-center gap-2 ${
              Math.abs(totalCurrentWeight - 100) < 0.1
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              <span>Total Bobot Aktif:</span>
              <span className="text-sm font-mono">{totalCurrentWeight.toFixed(1)} / 100</span>
              {Math.abs(totalCurrentWeight - 100) >= 0.1 && (
                <span className="text-[10px] font-normal text-amber-300">(Disarankan tepat 100)</span>
              )}
            </div>
          </div>

          {/* Indicator Table */}
          <div className="overflow-x-auto pt-2">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold w-12 text-center">Aktif</th>
                  <th className="py-2.5 px-3 font-semibold w-20">Kode</th>
                  <th className="py-2.5 px-3 font-semibold">Nama Indikator Aspek</th>
                  <th className="py-2.5 px-3 font-semibold">Kategori</th>
                  <th className="py-2.5 px-3 font-semibold">Kriteria Diharapkan</th>
                  <th className="py-2.5 px-3 font-semibold w-24 text-center">Bobot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {indicators.map((ind, idx) => (
                  <tr key={ind.id} className={`hover:bg-slate-800/30 transition-colors ${!ind.is_active ? 'opacity-40' : ''}`}>
                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={ind.is_active}
                        onChange={() => handleToggleActive(idx)}
                        className="w-4 h-4 rounded text-purple-600 focus:ring-0 bg-slate-800 border-slate-600 cursor-pointer"
                      />
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-purple-300">{ind.code}</td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-white">{ind.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">Metode: {ind.check_method}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      <span className="bg-slate-800 border border-slate-700/80 px-2 py-0.5 rounded text-[10px]">
                        {ind.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">{ind.expected_value}</td>
                    <td className="py-3 px-3 text-center">
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        max="50"
                        value={ind.weight}
                        onChange={(e) => handleWeightChange(idx, parseFloat(e.target.value) || 0)}
                        className="w-16 bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-center font-bold text-white text-xs focus:outline-none focus:border-purple-500"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

