import React from 'react';
import { motion } from 'framer-motion';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Shield, Code2, Package, FlaskConical, FileText, Layers, AlertTriangle, Info, AlertOctagon, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

interface CategoryBadgeProps {
  type: 'severity' | 'category';
  value: string;
}

const severityConfig: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
  critical: { className: 'bg-red-500/15 text-red-400 border-red-500/20', icon: <AlertOctagon className="w-3 h-3 mr-1" />, label: 'Critical' },
  warning: { className: 'bg-orange-500/15 text-orange-400 border-orange-500/20', icon: <AlertTriangle className="w-3 h-3 mr-1" />, label: 'Warning' },
  improvement: { className: 'bg-amber-500/15 text-amber-400 border-amber-500/20', icon: <AlertCircle className="w-3 h-3 mr-1" />, label: 'Improvement' },
  info: { className: 'bg-blue-500/15 text-blue-400 border-blue-500/20', icon: <Info className="w-3 h-3 mr-1" />, label: 'Info' },
};

const categoryConfig: Record<string, { className: string; icon: React.ReactNode; label: string }> = {
  security: { className: 'bg-purple-500/15 text-purple-400 border-purple-500/20', icon: <Shield className="w-3 h-3 mr-1" />, label: 'Security' },
  code_quality: { className: 'bg-violet-500/15 text-violet-400 border-violet-500/20', icon: <Code2 className="w-3 h-3 mr-1" />, label: 'Code Quality' },
  dependencies: { className: 'bg-pink-500/15 text-pink-400 border-pink-500/20', icon: <Package className="w-3 h-3 mr-1" />, label: 'Dependencies' },
  testing: { className: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20', icon: <FlaskConical className="w-3 h-3 mr-1" />, label: 'Testing' },
  documentation: { className: 'bg-slate-500/15 text-slate-400 border-slate-500/20', icon: <FileText className="w-3 h-3 mr-1" />, label: 'Documentation' },
  architecture: { className: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20', icon: <Layers className="w-3 h-3 mr-1" />, label: 'Architecture' },
};

export function CategoryBadge({ type, value }: CategoryBadgeProps) {
  const normalizedValue = value.toLowerCase();
  let config = type === 'severity' 
    ? severityConfig[normalizedValue] || severityConfig.info
    : categoryConfig[normalizedValue] || categoryConfig.code_quality;

  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={cn(
              "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border cursor-default",
              config.className
            )}
          >
            {config.icon}
            {config.label}
          </motion.div>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className="bg-slate-800 text-white text-xs px-2 py-1 rounded shadow-lg z-50 animate-in fade-in zoom-in"
            sideOffset={4}
          >
            {type === 'severity' ? 'Severity: ' : 'Category: '} {config.label}
            <Tooltip.Arrow className="fill-slate-800" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
