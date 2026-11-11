import React from 'react';

interface Props {
  score: number;
  maxScore?: number;
  size?: number;
}

export const ScoreRing: React.FC<Props> = ({ score, maxScore = 100, size = 120 }) => {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));
  const strokeWidth = size * 0.08;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    if (percentage >= 75) return '#10b981'; // Green
    if (percentage >= 60) return '#f59e0b'; // Amber
    return '#f43f5e'; // Red
  };

  const getLabel = () => {
    if (percentage >= 85) return 'Sangat Kompeten';
    if (percentage >= 75) return 'Kompeten';
    if (percentage >= 60) return 'Cukup Kompeten';
    return 'Belum Kompeten';
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={getColor()}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold tracking-tight text-white">
            {score.toFixed(1)}
          </span>
          <span className="text-xs text-slate-400">/ {maxScore}</span>
        </div>
      </div>
      <span
        className="mt-2 text-xs font-semibold px-2 py-0.5 rounded"
        style={{ color: getColor(), backgroundColor: `${getColor()}15` }}
      >
        {getLabel()}
      </span>
    </div>
  );
};

