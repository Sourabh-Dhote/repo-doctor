import { useState } from 'react';
import { motion } from 'framer-motion';
import { Github, Loader2 } from 'lucide-react';

interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export function UrlInput({ onSubmit, isLoading }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let cleaned = url.trim();
    if (!cleaned) {
      setError('Please enter a GitHub repository URL');
      return;
    }
    if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
      cleaned = `https://${cleaned}`;
    }
    try {
      const parsed = new URL(cleaned);
      if (!parsed.hostname.includes('github.com')) {
        setError('URL must be a github.com repository');
        return;
      }
      const parts = parsed.pathname.replace(/^\/|\/$/g, '').split('/');
      if (parts.length < 2 || !parts[0] || !parts[1]) {
        setError('URL must include both owner and repository (e.g. github.com/owner/repo)');
        return;
      }
    } catch {
      setError('Please enter a valid URL');
      return;
    }
    setError('');
    onSubmit(cleaned);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-xl mx-auto mt-8"
    >
      <form onSubmit={handleSubmit} className="relative glass-card rounded-2xl p-2 flex items-center focus-within:ring-2 focus-within:ring-violet-500/30 transition-all">
        <Github className="w-6 h-6 text-slate-400 ml-4 mr-2" />
        <input
          type="text"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            if (error) setError('');
          }}
          placeholder="https://github.com/username/repository"
          className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-slate-500 py-3 px-2"
          disabled={isLoading}
        />
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          disabled={isLoading}
          type="submit"
          className="btn-gradient text-white font-medium px-6 py-3 rounded-xl flex items-center justify-center min-w-[120px] transition-opacity disabled:opacity-70"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Analyze'}
        </motion.button>
      </form>
      
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-red-400 text-sm mt-3 ml-4"
        >
          {error}
        </motion.div>
      )}
    </motion.div>
  );
}
