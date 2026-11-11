import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, AlertCircle, Clock, PlayCircle } from 'lucide-react';

interface Props {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<Props> = ({ status, size = 'md' }) => {
  const s = (status || '').toUpperCase();

  const getStyle = () => {
    switch (s) {
      case 'PASS':
      case 'COMPLETED':
      case 'SUCCESS':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'FAIL':
      case 'FAILED':
      case 'ERROR':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'WARNING':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'RUNNING':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse';
      case 'SCHEDULED':
      case 'IDLE':
      case 'PENDING':
      case 'SKIP':
      default:
        return 'bg-slate-700/30 text-slate-400 border-slate-700';
    }
  };

  const getIcon = () => {
    const iconSize = size === 'sm' ? 12 : 14;
    switch (s) {
      case 'PASS':
      case 'COMPLETED':
      case 'SUCCESS':
        return <CheckCircle2 size={iconSize} className="mr-1" />;
      case 'FAIL':
      case 'FAILED':
      case 'ERROR':
        return <XCircle size={iconSize} className="mr-1" />;
      case 'WARNING':
        return <AlertTriangle size={iconSize} className="mr-1" />;
      case 'RUNNING':
        return <PlayCircle size={iconSize} className="mr-1 animate-spin" />;
      default:
        return <Clock size={iconSize} className="mr-1" />;
    }
  };

  const sizeCls = size === 'sm' ? 'px-2 py-0.5 text-xs' : size === 'lg' ? 'px-3 py-1.5 text-sm font-semibold' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center rounded-full border ${getStyle()} ${sizeCls}`}>
      {getIcon()}
      {status}
    </span>
  );
};
