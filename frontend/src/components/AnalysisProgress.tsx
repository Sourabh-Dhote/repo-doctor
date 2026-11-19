import { motion, AnimatePresence } from 'framer-motion';
import { Stethoscope } from 'lucide-react';
import { cn } from '../lib/utils';

interface AnalysisProgressProps {
  status: string; // 'pending' | 'scanning' | 'analyzing' | 'completed' | 'failed'
}

export function AnalysisProgress({ status }: AnalysisProgressProps) {
  const getStatusMessage = () => {
    switch (status) {
      case 'pending': return 'Preparing analysis...';
      case 'scanning': return 'Cloning & scanning repository...';
      case 'analyzing': return 'AI is analyzing your code...';
      case 'completed': return 'Analysis complete!';
      case 'failed': return 'Analysis failed.';
      default: return 'Initializing...';
    }
  };

  const getStepStatus = (step: number) => {
    let currentStep = 0;
    if (status === 'pending') currentStep = 1;
    else if (status === 'scanning') currentStep = 2;
    else if (status === 'analyzing') currentStep = 3;
    else if (status === 'completed') currentStep = 4;
    
    if (step < currentStep) return 'completed';
    if (step === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full flex items-center justify-center py-20 px-4">
      <div className="glass-card rounded-2xl p-8 max-w-md w-full flex flex-col items-center">
        <motion.div
          animate={{ scale: [1, 1.1, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
          className="mb-8 relative"
        >
          <div className="absolute inset-0 bg-violet-500/20 blur-xl rounded-full" />
          <Stethoscope className="w-16 h-16 text-violet-400 relative z-10" />
        </motion.div>

        <div className="h-8 mb-6 overflow-hidden relative w-full flex justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={status}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="absolute text-lg font-medium text-white"
            >
              {getStatusMessage()}
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="flex gap-3 mb-6">
          {[1, 2, 3].map((step) => {
            const state = getStepStatus(step);
            return (
              <motion.div
                key={step}
                layout
                className={cn(
                  "h-2 w-12 rounded-full transition-colors duration-500",
                  state === 'completed' ? "bg-violet-500" :
                  state === 'active' ? "bg-violet-400/60" : "bg-neutral-800"
                )}
              />
            );
          })}
        </div>

        <p className="text-sm text-slate-400">This usually takes 30-60 seconds</p>
      </div>
    </div>
  );
}
