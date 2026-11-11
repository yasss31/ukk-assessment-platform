import React, { useState, useEffect } from 'react';
import {
  Key, ShieldCheck, CheckCircle2, AlertCircle, PlayCircle,
  Users, BookOpen, Sparkles, RefreshCw, Layers
} from 'lucide-react';
import { api } from '../api';
import { Participant, RubricProfile, AWSCredentialInput } from '../types';

interface Props {
  onNavigate: (tab: string, param?: any) => void;
}

export const NewAssessment: React.FC<Props> = ({ onNavigate }) => {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [rubrics, setRubrics] = useState<RubricProfile[]>([]);
  const [selectedParticipantId, setSelectedParticipantId] = useState('');
  const [selectedRubricId, setSelectedRubricId] = useState('');
  const [rawCredsBlock, setRawCredsBlock] = useState('');
  const [creds, setCreds] = useState<AWSCredentialInput>({
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_session_token: '',
    aws_region: 'us-east-1',
  });
  const [notes, setNotes] = useState('');
  const [runAppTests, setRunAppTests] = useState(true);

  const [validatingAWS, setValidatingAWS] = useState(false);
  const [awsValidationResult, setAwsValidationResult] = useState<{
    valid: boolean;
    account_id?: string;
    arn?: string;
    error?: string;
  } | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initData = async () => {
      try {
        const [parts, rlist] = await Promise.all([
          api.listParticipants(),
          api.listRubrics(),
        ]);
        setParticipants(parts);
        if (parts.length > 0) setSelectedParticipantId(parts[0].id);

        setRubrics(rlist);
        if (rlist.length > 0) {
          // Pilih default UKK jika ada
          const def = rlist.find(r => r.id.includes('default') || r.id.includes('prof-ukk')) || rlist[0];
          setSelectedRubricId(def.id);
        }
      } catch (err: any) {
        setError('Gagal memuat daftar peserta atau rubrik: ' + err.message);
      }
    };
    initData();
  }, []);

  // Handler parse otomatis jika penguji mem-paste seluruh blok AWS CLI credentials
  const handlePasteCredsBlock = (text: string) => {
    setRawCredsBlock(text);
    const keyMatch = text.match(/aws_access_key_id\s*=\s*([^\r\n\s]+)/i);
    const secretMatch = text.match(/aws_secret_access_key\s*=\s*([^\r\n\s]+)/i);
    const tokenMatch = text.match(/aws_session_token\s*=\s*([^\r\n\s]+)/i);
    const regionMatch = text.match(/region\s*=\s*([^\r\n\s]+)/i);

    if (keyMatch || secretMatch || tokenMatch) {
      setCreds({
        aws_access_key_id: keyMatch ? keyMatch[1].trim() : creds.aws_access_key_id,
        aws_secret_access_key: secretMatch ? secretMatch[1].trim() : creds.aws_secret_access_key,
        aws_session_token: tokenMatch ? tokenMatch[1].trim() : creds.aws_session_token,
        aws_region: regionMatch ? regionMatch[1].trim() : (creds.aws_region || 'us-east-1'),
      });
      setAwsValidationResult(null);
    }
  };

  const handleValidateAWS = async () => {
    setError(null);
    if (!creds.aws_access_key_id || !creds.aws_secret_access_key || !creds.aws_session_token) {
      setError('Mohon isi Access Key, Secret Key, dan Session Token AWS terlebih dahulu.');
      return;
    }

    setValidatingAWS(true);
    try {
      const res = await api.validateAWSCredentials(creds);
      if (res.is_valid) {
        setAwsValidationResult({
          valid: true,
          account_id: res.account_id,
          arn: res.arn,
        });
      } else {
        setAwsValidationResult({
          valid: false,
          error: res.error_message || 'Kredensial AWS ditolak oleh STS.',
        });
      }
    } catch (err: any) {
      setAwsValidationResult({
        valid: false,
        error: err.message || 'Gagal menghubungi AWS STS API.',
      });
    } finally {
      setValidatingAWS(false);
    }
  };

  const handleStartAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedParticipantId) {
      setError('Pilih peserta ujian terlebih dahulu.');
      return;
    }
    if (!selectedRubricId) {
      setError('Pilih profil rubrik penilaian.');
      return;
    }
    if (!creds.aws_access_key_id || !creds.aws_secret_access_key || !creds.aws_session_token) {
      setError('Kredensial AWS Academy peserta wajib diisi lengkap.');
      return;
    }

    setSubmitting(true);
    try {
      const session = await api.createAssessment({
        participant_id: selectedParticipantId,
        rubric_profile_id: selectedRubricId,
        aws_credentials: creds,
        notes,
        run_app_tests: runAppTests,
      });

      // Berhasil dibuat dan mulai dievaluasi di background, arahkan ke detail
      onNavigate('assessment-detail', session.id);
    } catch (err: any) {
      setError('Gagal memulai sesi penilaian: ' + err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <PlayCircle className="text-indigo-400" />
          Mulai Uji Penilaian Infrastruktur Cloud
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Mesin penilaian akan memeriksa 17 aspek arsitektur AWS peserta secara transparan sesuai rubrik yang dipilih.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start space-x-3 text-xs text-rose-300">
          <AlertCircle size={18} className="shrink-0 mt-0.5 text-rose-400" />
          <div>
            <div className="font-semibold text-rose-400">Terjadi Kesalahan</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      <form onSubmit={handleStartAssessment} className="space-y-6">
        {/* Step 1 & 2: Peserta dan Rubrik */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-white">
              <Users size={16} className="text-indigo-400" />
              <span>1. Pilih Peserta Ujian</span>
            </div>
            <select
              value={selectedParticipantId}
              onChange={(e) => setSelectedParticipantId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {participants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.participant_number}) — {p.student_class}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400">
              Ingin mendaftarkan siswa baru? Buka menu <button type="button" onClick={() => onNavigate('participants')} className="text-indigo-400 underline font-medium">Data Peserta</button>.
            </p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold text-white">
              <BookOpen size={16} className="text-purple-400" />
              <span>2. Pilih Profil Rubrik Penilaian</span>
            </div>
            <select
              value={selectedRubricId}
              onChange={(e) => setSelectedRubricId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {rubrics.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} (v{r.version} • {r.indicators.length} Indikator • Bobot {r.total_weight})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400">
              Rubrik dinamis dapat disesuaikan bobotnya melalui menu <button type="button" onClick={() => onNavigate('rubrics')} className="text-purple-400 underline font-medium">Rubrik Penilaian</button>.
            </p>
          </div>
        </div>

        {/* Step 3: Input Kredensial AWS Academy */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-white">
              <Key size={16} className="text-amber-400" />
              <span>3. Kredensial AWS Academy Peserta (Read-Only Audit)</span>
            </div>
            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
              Zero-Persistence: In-Memory Only
            </span>
          </div>

          {/* Quick Paste Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
              <span>Paste Otomatis AWS CLI Credentials Block</span>
              <span className="text-[11px] text-slate-500 font-normal">Dari menu AWS Details / Cloud Access di AWS Academy</span>
            </label>
            <textarea
              rows={3}
              value={rawCredsBlock}
              onChange={(e) => handlePasteCredsBlock(e.target.value)}
              placeholder="[default]&#10;aws_access_key_id=ASIA...&#10;aws_secret_access_key=...&#10;aws_session_token=IQoJb3Jp..."
              className="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Access Key ID</label>
              <input
                type="text"
                required
                value={creds.aws_access_key_id}
                onChange={(e) => setCreds({ ...creds, aws_access_key_id: e.target.value })}
                placeholder="ASIA..."
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Region</label>
              <input
                type="text"
                required
                value={creds.aws_region}
                onChange={(e) => setCreds({ ...creds, aws_region: e.target.value })}
                placeholder="us-east-1"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Secret Access Key</label>
            <input
              type="password"
              required
              value={creds.aws_secret_access_key}
              onChange={(e) => setCreds({ ...creds, aws_secret_access_key: e.target.value })}
              placeholder="••••••••••••••••••••••••••••••••"
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">AWS Session Token</label>
            <textarea
              rows={2}
              required
              value={creds.aws_session_token}
              onChange={(e) => setCreds({ ...creds, aws_session_token: e.target.value })}
              placeholder="IQoJb3Jp..."
              className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs font-mono text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Validate Button & Result */}
          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleValidateAWS}
              disabled={validatingAWS || !creds.aws_access_key_id}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-4 py-2 rounded-xl flex items-center justify-center space-x-2 transition disabled:opacity-50"
            >
              {validatingAWS ? (
                <>
                  <RefreshCw size={14} className="animate-spin text-indigo-400" />
                  <span>Memvalidasi AWS STS...</span>
                </>
              ) : (
                <>
                  <ShieldCheck size={14} className="text-emerald-400" />
                  <span>Uji Kredensial AWS Sekarang</span>
                </>
              )}
            </button>

            {awsValidationResult && (
              <div className="text-xs">
                {awsValidationResult.valid ? (
                  <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                    <CheckCircle2 size={15} />
                    Valid! Akun: {awsValidationResult.account_id}
                  </span>
                ) : (
                  <span className="text-rose-400 flex items-center gap-1 font-semibold">
                    <AlertCircle size={15} />
                    {awsValidationResult.error}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 4: Options & Notes */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-xs font-semibold text-white">
            <Layers size={16} className="text-indigo-400" />
            <span>4. Opsi Penilaian Tambahan</span>
          </div>

          <label className="flex items-center space-x-3 cursor-pointer text-xs text-slate-300 bg-slate-800/40 p-3 rounded-xl border border-slate-700/60">
            <input
              type="checkbox"
              checked={runAppTests}
              onChange={(e) => setRunAppTests(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-slate-800 border-slate-600"
            />
            <div>
              <div className="font-semibold text-white">Jalankan Pengujian Fungsional Aplikasi E2E</div>
              <div className="text-[11px] text-slate-400">
                Menguji ALB DNS publik, Auto Scaling Session Sharing (30 requests), Login 3 role MBG, dan upload bukti aduan ke S3.
              </div>
            </div>
          </label>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Catatan Tambahan Penguji (Opsional)</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Contoh: Sesi ujian gelombang 1, ruang Lab Cloud 2"
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Submit Execution */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="w-full sm:w-auto bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold py-3 px-8 rounded-xl text-xs flex items-center justify-center space-x-2.5 shadow-xl shadow-indigo-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <>
                <RefreshCw size={16} className="animate-spin text-white" />
                <span>Memulai Audit Infrastruktur...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Mulai Penilaian Otomatis</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

