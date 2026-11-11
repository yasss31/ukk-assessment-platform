import React, { useState } from 'react';
import {
  X, AlertTriangle, AlertCircle, Wrench, CheckCircle2,
  ExternalLink, Sparkles, RefreshCw, Compass, BookOpen, Terminal
} from 'lucide-react';
import { IndicatorResult, TroubleshootingGuide, ErrorSeverity } from '../types';
import { api } from '../api';

interface Props {
  sessionId: string;
  indicator: IndicatorResult;
  onClose: () => void;
  onReassessRequest?: (indicatorId: string) => void;
}

export const TroubleshootingModal: React.FC<Props> = ({
  sessionId,
  indicator,
  onClose,
  onReassessRequest
}) => {
  const [loadingAi, setLoadingAi] = useState(false);
  const [aiResponse, setAiResponse] = useState<any>(null);

  const guide = indicator.troubleshooting;

  const handleAskAi = async () => {
    setLoadingAi(true);
    try {
      const res = await api.getAiExplanation(sessionId, indicator.code);
      setAiResponse(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAi(false);
    }
  };

  const getSeverityBadge = (severity?: ErrorSeverity) => {
    switch (severity) {
      case 'Critical':
        return <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1"><AlertCircle size={14} /> Tingkat: Critical</span>;
      case 'Major':
        return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1"><AlertTriangle size={14} /> Tingkat: Major</span>;
      case 'Minor':
        return <span className="bg-yellow-500/10 text-yellow-300 border border-yellow-500/30 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1"><AlertTriangle size={14} /> Tingkat: Minor</span>;
      default:
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1"><Compass size={14} /> Informational</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl relative overflow-hidden my-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/40">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="bg-indigo-600/20 text-indigo-300 font-mono font-bold text-xs px-2.5 py-1 rounded-lg border border-indigo-500/30">
                {indicator.code}
              </span>
              {getSeverityBadge(guide?.severity || indicator.severity)}
            </div>
            <h3 className="text-base font-bold text-white pt-1">{indicator.name}</h3>
            <p className="text-xs text-slate-400">Smart Troubleshooting & Asisten Panduan Perbaikan Siswa</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          {/* Apa yang salah */}
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4 space-y-1.5">
            <div className="font-bold text-rose-400 flex items-center gap-2">
              <AlertCircle size={16} />
              <span>Apa yang salah?</span>
            </div>
            <p className="text-rose-200/90 leading-relaxed">
              {guide?.what_is_wrong || indicator.actual}
            </p>
          </div>

          {/* Actual vs Expected Comparison */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-3.5 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Kondisi Aktual yang Ditemukan (AWS)
              </span>
              <div className="font-mono text-rose-400 text-xs break-all">
                {guide?.actual_found || indicator.actual}
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-3.5 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Kondisi yang Seharusnya (Rubrik)
              </span>
              <div className="font-mono text-emerald-400 text-xs break-all">
                {guide?.expected_config || indicator.expected}
              </div>
            </div>
          </div>

          {/* Mengapa bermasalah & Dampak */}
          {guide && (
            <div className="bg-slate-800/30 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div>
                <span className="font-semibold text-indigo-300 block mb-0.5">Mengapa ini bermasalah?</span>
                <p className="text-slate-300 leading-relaxed">{guide.why_wrong}</p>
              </div>
              <div className="pt-2 border-t border-slate-800/80">
                <span className="font-semibold text-amber-300 block mb-0.5">Dampak Nyata:</span>
                <p className="text-slate-300 leading-relaxed">{guide.impact}</p>
              </div>
            </div>
          )}

          {/* Lokasi Menu & Langkah Perbaikan */}
          {guide && (
            <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <Wrench size={16} className="text-indigo-400" />
                  Tutorial Langkah demi Langkah Perbaikan
                </span>
                <span className="bg-slate-700/60 text-slate-300 px-2.5 py-0.5 rounded-lg text-[11px] font-mono">
                  {guide.fix_location}
                </span>
              </div>

              <ol className="space-y-2 pl-4 list-decimal text-slate-200">
                {guide.how_to_fix.map((step, idx) => (
                  <li key={idx} className="leading-relaxed pl-1">
                    {step}
                  </li>
                ))}
              </ol>

              {/* Cara Verifikasi */}
              <div className="pt-3 border-t border-slate-700/60 space-y-1.5">
                <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 size={14} />
                  Cara Memastikan Sudah Benar:
                </span>
                <ul className="list-disc pl-4 space-y-1 text-slate-300 text-[11px]">
                  {guide.how_to_verify.map((v, i) => (
                    <li key={i}>{v}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* AI-Assisted Explanation Section */}
          <div className="bg-gradient-to-r from-purple-950/30 to-indigo-950/30 border border-purple-500/20 rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles size={16} className="text-purple-400" />
                <span className="font-bold text-white">Asisten Penjelasan AI (Interaktif)</span>
              </div>
              {!aiResponse && (
                <button
                  onClick={handleAskAi}
                  disabled={loadingAi}
                  className="bg-purple-600 hover:bg-purple-500 text-white font-semibold px-3 py-1.5 rounded-xl text-xs flex items-center space-x-1.5 transition shadow-sm"
                >
                  {loadingAi ? <RefreshCw size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  <span>{loadingAi ? 'Menganalisis...' : 'Sederhanakan Penjelasan'}</span>
                </button>
              )}
            </div>

            {aiResponse && (
              <div className="space-y-2.5 pt-1 text-xs text-purple-200/90 leading-relaxed bg-black/30 p-3.5 rounded-xl border border-purple-500/20">
                <div className="font-semibold text-white">{aiResponse.ringkasan_ramah_siswa}</div>
                <div>💡 <span className="font-medium text-purple-300">Tips Sukses:</span> {aiResponse.tips_sukses}</div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs transition"
          >
            Tutup
          </button>

          {onReassessRequest && (
            <button
              onClick={() => {
                onClose();
                onReassessRequest(indicator.indicator_id);
              }}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center space-x-1.5 shadow-md shadow-emerald-600/30 transition"
            >
              <RefreshCw size={14} />
              <span>Periksa Ulang Aspek Ini</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

