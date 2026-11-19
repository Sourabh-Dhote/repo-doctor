import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { GitBranch, AlertTriangle, AlertOctagon, Info } from 'lucide-react';
import { HealthScore } from './HealthScore';
import { IssueList } from './IssueList';
import type { Analysis } from '../types';

interface ReportDashboardProps {
  analysis: Analysis;
}

const COLORS = ['#8b5cf6', '#6366f1', '#a78bfa', '#c084fc', '#818cf8', '#f472b6', '#fb923c'];

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 }
};

export function ReportDashboard({ analysis }: ReportDashboardProps) {
  const languageData = Object.entries(analysis.repository?.languages || {}).map(([name, bytes]) => ({ name, value: bytes }));
  
  const issueCounts = {
    critical: analysis.issues.filter(i => i.severity === 'critical').length,
    warning: analysis.issues.filter(i => i.severity === 'warning').length,
    improvement: analysis.issues.filter(i => i.severity === 'improvement').length,
    info: analysis.issues.filter(i => i.severity === 'info').length,
  };

  const severityData = [
    { name: 'Critical', count: issueCounts.critical, fill: '#ef4444' },
    { name: 'Warning', count: issueCounts.warning, fill: '#f97316' },
    { name: 'Improvement', count: issueCounts.improvement, fill: '#f59e0b' },
    { name: 'Info', count: issueCounts.info, fill: '#3b82f6' },
  ];

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="max-w-6xl mx-auto py-8 px-4 flex flex-col gap-8"
    >
      {/* Repo Header */}
      <motion.div variants={itemVariants} className="glass-card rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <GitBranch className="w-4 h-4" />
            <span>{(analysis.repository?.url || '').split('github.com/')[1] || analysis.repository?.name}</span>
          </div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-indigo-400">
            Analysis Report
          </h1>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-300 bg-slate-800/50 px-4 py-2 rounded-lg border border-white/5">
          <div>Files: <span className="font-semibold text-white">{analysis.repository?.total_files || 0}</span></div>
          <div className="w-px h-4 bg-white/10" />
          <a href={analysis.repository?.url || ''} target="_blank" rel="noreferrer" className="text-violet-400 hover:text-violet-300 transition-colors">
            View on GitHub
          </a>
        </div>
      </motion.div>

      {/* Health Score & Summary */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center lg:col-span-1">
          <h2 className="text-lg font-medium text-white mb-2">Overall Health</h2>
          <HealthScore score={analysis.health_score ?? 0} />
        </div>
        
        <div className="glass-card rounded-2xl p-6 lg:col-span-2 flex flex-col">
          <h2 className="text-lg font-medium text-white mb-4">Executive Summary</h2>
          <div className="text-slate-300 leading-relaxed whitespace-pre-wrap flex-1 bg-slate-900/30 rounded-xl p-5 border border-white/5">
            {analysis.summary}
          </div>
        </div>
      </motion.div>

      {/* Stats Row */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-slate-800/80 rounded-lg text-slate-300">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{analysis.issues.length}</div>
            <div className="text-sm text-slate-400">Total Issues</div>
          </div>
        </div>
        <div className="glass-card rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-red-500/10 rounded-lg text-red-400">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-red-400">{issueCounts.critical}</div>
            <div className="text-sm text-slate-400">Critical</div>
          </div>
        </div>
        <div className="glass-card rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-orange-500/10 rounded-lg text-orange-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-orange-400">{issueCounts.warning}</div>
            <div className="text-sm text-slate-400">Warnings</div>
          </div>
        </div>
        <div className="glass-card rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400">
            <Info className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-400">{issueCounts.improvement}</div>
            <div className="text-sm text-slate-400">Improvements</div>
          </div>
        </div>
      </motion.div>

      {/* Charts Section */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-lg font-medium text-white mb-6">Language Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={languageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {languageData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px', color: '#cbd5e1' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-lg font-medium text-white mb-6">Issues by Severity</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                <RechartsTooltip
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>

      {/* Issues List */}
      <motion.div variants={itemVariants} className="glass-card rounded-2xl p-6 mb-12">
        <h3 className="text-xl font-semibold text-white mb-6">Detailed Findings</h3>
        <IssueList issues={analysis.issues} repoUrl={analysis.repository?.url || ''} />
      </motion.div>
    </motion.div>
  );
}
