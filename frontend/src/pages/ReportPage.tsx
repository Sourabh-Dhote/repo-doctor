import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { AnalysisProgress } from '../components/AnalysisProgress';
import { ReportDashboard } from '../components/ReportDashboard';
import { getAnalysis, getAnalysisStatus } from '../api/analysis';
import type { Analysis } from '../types';

export function ReportPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [status, setStatus] = useState<string>('pending');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) return;

    let pollInterval: number;
    let isMounted = true;

    const checkStatus = async () => {
      try {
        const data = await getAnalysisStatus(analysisId);
        if (!isMounted) return;

        setStatus(data.status);

        if (data.status === 'completed') {
          clearInterval(pollInterval);
          // Fetch the full analysis with all issues
          const fullAnalysis = await getAnalysis(analysisId);
          if (!isMounted) return;
          setAnalysis(fullAnalysis);
          toast.success('Analysis complete!');
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          setError(data.error_message || 'Analysis failed due to an error cloning or scanning the repository.');
          toast.error('Analysis failed');
        }
      } catch (err) {
        console.error('Failed to fetch analysis status', err);
      }
    };

    checkStatus();
    pollInterval = window.setInterval(checkStatus, 2000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, [analysisId]);

  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }}
      className="min-h-screen bg-black dot-pattern relative overflow-x-hidden"
    >
      {/* Background Glow */}
      <div className="fixed inset-0 z-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at top, rgba(139, 92, 246, 0.05) 0%, transparent 70%)'
      }} />

      {/* Sticky Header */}
      <header className="sticky top-0 z-40 bg-black/50 backdrop-blur-md border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Back to Home</span>
          </button>
          
          <div className="font-bold text-xl bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-indigo-400">
            🩺 RepoDoctor
          </div>
          
          <button 
            onClick={() => navigate('/')}
            className="text-sm font-medium bg-white/5 hover:bg-white/10 text-white px-4 py-2 rounded-lg transition-colors border border-white/10"
          >
            Analyze Another
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 min-h-[calc(100vh-64px)] pb-20">
        {status === 'failed' ? (
          <div className="w-full h-[60vh] flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="glass-card p-8 rounded-2xl max-w-md w-full text-center"
            >
              <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Analysis Failed</h2>
              <p className="text-slate-400 mb-6">{error}</p>
              <button 
                onClick={() => navigate('/')}
                className="bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-lg font-medium transition-colors w-full"
              >
                Try Again
              </button>
            </motion.div>
          </div>
        ) : status === 'completed' && analysis ? (
          <ReportDashboard analysis={analysis} />
        ) : (
          <AnalysisProgress status={status} />
        )}
      </main>
    </motion.div>
  );
}
