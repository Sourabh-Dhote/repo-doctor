import { Analysis, AnalysisStatus } from '../types';

export const startAnalysis = async (url: string): Promise<{ analysis_id: string; status: string }> => {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    let errorMsg = 'Failed to start analysis';
    try {
      const errData = await response.json();
      if (errData && errData.detail) {
        errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      // fallback
    }
    throw new Error(errorMsg);
  }

  return response.json();
};

export const getAnalysis = async (id: string): Promise<Analysis> => {
  const response = await fetch(`/api/analysis/${id}`);

  if (!response.ok) {
    throw new Error('Failed to fetch analysis');
  }

  return response.json();
};

export const getAnalysisStatus = async (id: string): Promise<AnalysisStatus> => {
  const response = await fetch(`/api/analysis/${id}/status`);

  if (!response.ok) {
    throw new Error('Failed to fetch analysis status');
  }

  return response.json();
};
