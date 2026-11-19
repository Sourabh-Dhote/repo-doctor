import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { Sparkles, Shield, Code2, Package, Zap } from 'lucide-react';
import { UrlInput } from '../components/UrlInput';
import { startAnalysis } from '../api/analysis';

export function HomePage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (url: string) => {
    try {
      setIsLoading(true);
      const result = await startAnalysis(url);
      toast.success('Analysis started!');
      navigate(`/report/${result.analysis_id}`);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to start analysis. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.12 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 24 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 300, damping: 30 } }
  };

  const features = [
    { icon: Shield, label: 'Security Scanning', color: 'text-violet-400' },
    { icon: Code2, label: 'Code Quality', color: 'text-indigo-400' },
    { icon: Package, label: 'Dependency Audit', color: 'text-purple-400' },
  ];

  return (
    <div className="min-h-screen bg-black dot-pattern relative flex flex-col items-center justify-center overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 z-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at 50% 40%, rgba(139, 92, 246, 0.06) 0%, transparent 55%)'
      }} />

      <motion.div 
        className="z-10 w-full max-w-2xl px-6 flex flex-col items-center text-center"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Badge */}
        <motion.div variants={itemVariants} className="mb-8 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium">
          <Sparkles className="w-3.5 h-3.5" />
          AI-Powered Code Analysis
        </motion.div>

        {/* Title */}
        <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl font-bold tracking-tight mb-4">
          <span className="text-white">Repo</span>
          <span className="text-gradient-violet">Doctor</span>
          <span className="text-white ml-3 text-4xl md:text-5xl opacity-60">AI</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p variants={itemVariants} className="text-lg text-neutral-400 mb-14 max-w-lg leading-relaxed">
          Analyze any GitHub repository for security vulnerabilities, code quality issues, and best practices.
        </motion.p>

        {/* Feature cards */}
        <motion.div variants={itemVariants} className="grid grid-cols-3 gap-3 w-full mb-14">
          {features.map(({ icon: Icon, label, color }) => (
            <motion.div 
              key={label}
              whileHover={{ y: -3, borderColor: 'rgba(139, 92, 246, 0.2)' }} 
              className="glass-card rounded-xl p-4 flex flex-col items-center gap-2 cursor-default"
            >
              <div className="w-10 h-10 rounded-lg bg-white/[0.03] flex items-center justify-center">
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <span className="text-xs font-medium text-neutral-300">{label}</span>
            </motion.div>
          ))}
        </motion.div>

        {/* URL Input */}
        <motion.div variants={itemVariants} className="w-full">
          <UrlInput onSubmit={handleSubmit} isLoading={isLoading} />
        </motion.div>

        {/* Footer */}
        <motion.div variants={itemVariants} className="mt-20 flex items-center gap-2 text-xs text-neutral-600">
          <Zap className="w-3 h-3" />
          Public GitHub repositories • Powered by Gemini AI
        </motion.div>
      </motion.div>
    </div>
  );
}
