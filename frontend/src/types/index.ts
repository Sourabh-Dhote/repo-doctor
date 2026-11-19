export interface Repository {
  id: string;
  url: string;
  name: string;
  owner: string;
  total_files: number;
  languages: Record<string, number>;
}

export interface Issue {
  id: string;
  severity: 'critical' | 'warning' | 'improvement' | 'info';
  category: 'security' | 'code_quality' | 'dependencies' | 'testing' | 'documentation' | 'architecture';
  title: string;
  description: string;
  file_path: string | null;
  line_number: number | null;
  suggestion: string | null;
}

export interface Analysis {
  id: string;
  status: 'pending' | 'scanning' | 'analyzing' | 'completed' | 'failed';
  health_score: number | null;
  summary: string | null;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  repository: Repository;
  issues: Issue[];
}

export interface AnalysisStatus {
  id: string;
  status: string;
  health_score: number | null;
  error_message?: string | null;
}

export type SeverityType = Issue['severity'];
export type CategoryType = Issue['category'];
