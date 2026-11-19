import { useEffect, useState } from 'react';
import { motion, animate } from 'framer-motion';
import { cn } from '../lib/utils';

interface HealthScoreProps {
  score: number;
}

export function HealthScore({ score }: HealthScoreProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1.5,
      ease: 'easeOut',
      onUpdate: (v) => setDisplayScore(Math.round(v)),
    });
    return controls.stop;
  }, [score]);

  const getScoreColorClass = (s: number) => {
    if (s >= 90) return 'text-green-500 glow-green';
    if (s >= 70) return 'text-yellow-500 glow-yellow';
    if (s >= 50) return 'text-orange-500 glow-orange';
    return 'text-red-500 glow-red';
  };

  const getScoreStrokeClass = (s: number) => {
    if (s >= 90) return 'stroke-green-500';
    if (s >= 70) return 'stroke-yellow-500';
    if (s >= 50) return 'stroke-orange-500';
    return 'stroke-red-500';
  };

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center justify-center w-48 h-48 mx-auto my-6">
      <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 160 160">
        {/* Background gradient ring */}
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          strokeWidth="12"
          className="stroke-slate-800/50"
        />
        
        {/* Main animated circle */}
        <motion.circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          strokeWidth="12"
          strokeLinecap="round"
          className={cn("transition-colors duration-500", getScoreStrokeClass(score))}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>
      
      <div className={cn("absolute flex flex-col items-center justify-center rounded-full w-32 h-32 bg-slate-900/40 backdrop-blur-sm border border-white/5", getScoreColorClass(score))}>
        <span className="text-4xl font-bold">
          <motion.span>{displayScore}</motion.span>
        </span>
        <motion.span 
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold"
        >
          Health
        </motion.span>
      </div>
    </div>
  );
}
