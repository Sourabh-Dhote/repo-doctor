import { useState } from 'react';
import { motion } from 'framer-motion';
import * as Tabs from '@radix-ui/react-tabs';
import { CheckCircle2 } from 'lucide-react';
import { IssueCard } from './IssueCard';
import type { Issue } from '../types';

interface IssueListProps {
  issues: Issue[];
  repoUrl: string;
}

const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'security', label: 'Security' },
  { id: 'code_quality', label: 'Code Quality' },
  { id: 'dependencies', label: 'Dependencies' },
  { id: 'testing', label: 'Testing' },
  { id: 'documentation', label: 'Documentation' },
  { id: 'architecture', label: 'Architecture' }
];

const SEVERITY_ORDER: Record<string, number> = {
  critical: 4,
  warning: 3,
  improvement: 2,
  info: 1
};

export function IssueList({ issues, repoUrl }: IssueListProps) {
  const [activeTab, setActiveTab] = useState('all');

  const getFilteredAndSortedIssues = (category: string) => {
    let filtered = issues;
    if (category !== 'all') {
      filtered = issues.filter(i => i.category.toLowerCase() === category);
    }
    return filtered.sort((a, b) => {
      const aScore = SEVERITY_ORDER[a.severity.toLowerCase()] || 0;
      const bScore = SEVERITY_ORDER[b.severity.toLowerCase()] || 0;
      return bScore - aScore;
    });
  };

  const getCategoryCount = (category: string) => {
    if (category === 'all') return issues.length;
    return issues.filter(i => i.category.toLowerCase() === category).length;
  };

  return (
    <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="w-full">
      <Tabs.List className="flex overflow-x-auto no-scrollbar border-b border-white/10 mb-6 pb-px">
        {CATEGORIES.map((cat) => {
          const count = getCategoryCount(cat.id);
          const isActive = activeTab === cat.id;
          
          return (
            <Tabs.Trigger
              key={cat.id}
              value={cat.id}
              className={`relative px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-2 outline-none
                ${isActive ? 'text-white' : 'text-slate-400 hover:text-slate-200'}
              `}
            >
              {cat.label}
              <span className={`inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs rounded-full transition-colors
                ${isActive ? 'bg-violet-500/20 text-violet-400' : 'bg-white/5 text-slate-400'}
              `}>
                {count}
              </span>
              {isActive && (
                <motion.div
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-violet-500"
                  layoutId="activeTab"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </Tabs.Trigger>
          );
        })}
      </Tabs.List>

      <div className="relative min-h-[200px]">
        {CATEGORIES.map((cat) => (
          <Tabs.Content key={cat.id} value={cat.id} className="outline-none">
            <div className="flex flex-col gap-4">
              {getFilteredAndSortedIssues(cat.id).length > 0 ? (
                getFilteredAndSortedIssues(cat.id).map((issue, index) => (
                  <IssueCard 
                    key={issue.id || `${issue.title}-${index}`} 
                    issue={issue} 
                    repoUrl={repoUrl} 
                    index={index} 
                  />
                ))
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-center justify-center py-12 text-slate-400 glass-card rounded-xl"
                >
                  <CheckCircle2 className="w-12 h-12 text-violet-500/50 mb-3" />
                  <p className="text-lg">No issues found — looking good!</p>
                </motion.div>
              )}
            </div>
          </Tabs.Content>
        ))}
      </div>
    </Tabs.Root>
  );
}
