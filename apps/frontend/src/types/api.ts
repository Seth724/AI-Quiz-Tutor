export interface DocumentUploadResponse {
  document_id: string;
  title: string;
  status: string;
  message: string;
  chunks_count?: number;
}

export interface DocumentStatusResponse {
  document_id: string;
  status: 'processing' | 'ready' | 'failed' | string;
  message: string;
  chunks_count?: number;
  processing_error?: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options?: string[];
  correct_answer: string;
  explanation?: string;
  topic?: string;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  document_id: string;
  questions: QuizQuestion[];
  total_questions: number;
  created_at: string;
  difficulty?: 'easy' | 'medium' | 'hard' | string;
  question_type?: 'multiple_choice' | 'short_answer' | 'true_false' | string;
}

export interface QuizSummary {
  quiz_id: string;
  document_id?: string;
  user_id?: string;
  total_questions?: number;
  difficulty?: 'easy' | 'medium' | 'hard' | string;
  question_type?: 'multiple_choice' | 'short_answer' | 'true_false' | string;
  created_at?: string;
}

export interface QuizResult {
  quiz_id: string;
  score: number;
  correct_count: number;
  total_questions: number;
  weak_areas: Array<{
    topic: string;
    accuracy: number;
    correct: number;
    total: number;
  }>;
  recommendations: string[];
}

export interface Document {
  document_id: string;
  title: string;
  file_type?: string;
  supabase_url?: string;
  pages?: number;
  tables_count?: number;
  created_at: string;
  updated_at?: string;
  status: string;
  message?: string;
  processing_error?: string;
  chunks_count?: number;
  quizzes_generated?: number;
  attempts_count?: number;
  average_score?: number;
}

export interface Attempt {
  attempt_id: string;
  quiz_id: string;
  document_id?: string;
  document_title?: string;
  score: number;
  correct_count: number;
  total_questions: number;
  percentage: string;
  completed_at: string;
}

export interface ProgressResponse {
  total_quizzes: number;
  average_score: number;
  quizzes_completed: number;
  weak_areas: Array<{
    topic: string;
    accuracy: number;
    attempts: number;
    priority: 'high' | 'medium' | 'low' | string;
  }>;
  recent_activity: Array<{
    attempt_id: string;
    quiz_id: string;
    document_id?: string;
    score: number;
    percentage: string;
    completed_at: string;
  }>;
  improvement_trend: 'improving' | 'stable' | 'needs_work' | 'no_data' | string;
}

export interface ReviewNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  created_at: string;
}

export interface DocumentChatResponse {
  response: string;
  sources: Array<{
    text: string;
    score: number;
  }>;
  confidence: number;
}

export interface ChatHistoryMessage {
  chat_id: string;
  user_id: string;
  document_id?: string;
  question: string;
  response: string;
  created_at: string;
}

export interface ExternalChatHistoryMessage {
  chat_id?: string;
  user_id?: string;
  document_id?: string;
  role: 'user' | 'assistant' | string;
  content: string;
  confidence?: number;
  sources?: Array<{
    text: string;
    score: number;
  }>;
  created_at?: string;
}

export interface StudyPlan {
  plan_id: string;
  user_id: string;
  title: string;
  document_id?: string;
  document_title?: string;
  notes?: string;
  target_date: string;
  status: 'pending' | 'done' | 'in_progress' | string;
  reminder_days_before: number;
  user_email?: string;
  reminder_sent_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
  // Time-based scheduling fields (new)
  start_time?: string; // HH:MM format
  end_time?: string; // HH:MM format
  duration_minutes?: number; // Duration in minutes
  activities?: StudyActivity[];
  source_plan_id?: string;
  source_plan_title?: string;
  is_generated_timetable?: boolean;
}

export interface StudyActivity {
  id?: string;
  name: string; // e.g., "Review Chapter 3"
  duration_minutes: number;
  status: 'todo' | 'in_progress' | 'done';
  notes?: string;
}

export interface StudyPlanNotification {
  id: string;
  type: 'upcoming' | 'today' | 'overdue' | string;
  title: string;
  message: string;
  target_date: string;
  plan_id: string;
}

export interface StudyPlanGenerateResponse {
  generated_schedules: StudyPlan[];
  total_sessions: number;
  message: string;
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}
