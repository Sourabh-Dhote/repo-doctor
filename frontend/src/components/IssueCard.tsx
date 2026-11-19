import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as Collapsible from '@radix-ui/react-collapsible';
import { ChevronDown, ExternalLink, Lightbulb } from 'lucide-react';
import { CategoryBadge } from './CategoryBadge';
import { cn } from '../lib/utils';
import type { Issue } from '../types';

interface IssueCardProps {
  issue: Issue;
  repoUrl: string;
  index: number;
}

export function IssueCard({ issue, repoUrl, index }: IssueCardProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'border-l-red-500';
      case 'warning': return 'border-l-orange-500';
      case 'improvement': return 'border-l-amber-500';
      default: return 'border-l-blue-500';
    }
  };

  const getFileLink = () => {
    if (!issue.file_path) return null;
    let link = `${repoUrl}/blob/main/${issue.file_path}`;
    if (issue.line_number) {
      link += `#L${issue.line_number}`;
    }
    return link;
  };

  const fileLink = getFileLink();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Collapsible.Root open={isOpen} onOpenChange={setIsOpen}>
        <motion.div 
          whileHover={{ y: -2 }} 
          transition={{ duration: 0.2 }}
          className={cn(
            "glass-card rounded-xl overflow-hidden border-l-4 transition-all duration-300",
            getSeverityColor(issue.severity)
          )}
        >
          <Collapsible.Trigger asChild>
            <div className="p-5 cursor-pointer flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <CategoryBadge type="severity" value={issue.severity} />
                  <CategoryBadge type="category" value={issue.category} />
                </div>
                <h3 className="text-lg font-semibold text-white break-words mb-1">
                  {issue.title}
                </h3>
                {issue.file_path && (
                  <div className="flex items-center gap-1.5 text-sm text-slate-400 font-mono">
                    <span className="truncate">{issue.file_path}</span>
                    {issue.line_number && <span>:{issue.line_number}</span>}
                    {fileLink && (
                      <a 
                        href={fileLink} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-violet-400 hover:text-violet-300 ml-1 inline-flex items-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0 mt-1 md:mt-0">
                <motion.div animate={{ rotate: isOpen ? 180 : 0 }}>
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                </motion.div>
              </div>
            </div>
          </Collapsible.Trigger>

          <AnimatePresence initial={false}>
            {isOpen && (
              <Collapsible.Content asChild forceMount>
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: 'easeInOut' }}
                  className="overflow-hidden"
                >
                  <div className="p-5 pt-0 border-t border-white/5 mt-2">
                    <p className="text-slate-300 whitespace-pre-wrap mt-4 mb-4">
                      {issue.description}
                    </p>
                    {issue.suggestion && (
                      <div className="bg-violet-500/5 border border-violet-500/10 rounded-lg p-4 flex gap-3">
                        <Lightbulb className="w-5 h-5 text-violet-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-medium text-violet-400 mb-1">Suggested Fix</h4>
                          <p className="text-slate-300 text-sm whitespace-pre-wrap">
                            {issue.suggestion}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              </Collapsible.Content>
            )}
          </AnimatePresence>
        </motion.div>
      </Collapsible.Root>
    </motion.div>
  );
}
