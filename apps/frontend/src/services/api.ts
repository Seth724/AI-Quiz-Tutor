import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  ApiError,
  Attempt,
  ChatHistoryMessage,
  Document,
  DocumentChatResponse,
  DocumentStatusResponse,
  DocumentUploadResponse,
  ExternalChatHistoryMessage,
  ProgressResponse,
  QuizGenerateResponse,
  QuizResult,
  QuizSummary,
  ReviewNotification,
  StudyPlan,
  StudyPlanGenerateResponse,
  StudyPlanNotification,
} from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async uploadDocument(file: File, userId: string): Promise<DocumentUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      const response = await this.api.post<DocumentUploadResponse>('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Upload should never timeout at client side; server now responds quickly,
        // but keeping this as a safety net for slow networks.
        timeout: 0,
      });

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
    try {
      const response = await this.api.get<DocumentStatusResponse>(`/api/documents/${documentId}/status`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async generateQuiz(
    documentId: string,
    numQuestions: number = 5,
    difficulty: 'easy' | 'medium' | 'hard' = 'medium',
    questionType: 'multiple_choice' | 'short_answer' = 'multiple_choice'
  ): Promise<QuizGenerateResponse> {
    try {
      const response = await this.api.post<QuizGenerateResponse>(
        '/api/quizzes/generate',
        {
          document_id: documentId,
          num_questions: numQuestions,
          difficulty,
          question_type: questionType,
        },
        {
          // Quiz generation can take longer for OCR-heavy documents.
          timeout: 0,
        }
      );

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async submitQuiz(quizId: string, answers: Record<string, string>, userId: string): Promise<QuizResult> {
    try {
      const response = await this.api.post<QuizResult>(`/api/quizzes/${quizId}/submit`, {
        quiz_id: quizId,
        answers,
        user_id: userId,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getQuiz(quizId: string): Promise<QuizGenerateResponse> {
    try {
      const response = await this.api.get<QuizGenerateResponse>(`/api/quizzes/${quizId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocumentQuizzes(documentId: string): Promise<QuizSummary[]> {
    try {
      const response = await this.api.get(`/api/documents/${documentId}/quizzes`);
      return response.data?.quizzes || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocuments(userId: string): Promise<Document[]> {
    try {
      const response = await this.api.get('/api/documents', {
        params: { user_id: userId },
      });
      return response.data?.documents || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocument(documentId: string): Promise<Document> {
    try {
      const response = await this.api.get<Document>(`/api/documents/${documentId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getAttempts(userId: string, documentId?: string): Promise<Attempt[]> {
    try {
      const response = await this.api.get('/api/attempts', {
        params: {
          user_id: userId,
          ...(documentId ? { document_id: documentId } : {}),
        },
      });
      return response.data?.attempts || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getProgress(userId: string): Promise<ProgressResponse> {
    try {
      const response = await this.api.get<ProgressResponse>('/api/progress', {
        params: { user_id: userId },
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getNotifications(userId: string): Promise<ReviewNotification[]> {
    try {
      const response = await this.api.get('/api/progress/notifications', {
        params: { user_id: userId },
      });
      return response.data?.notifications || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async askDocumentQuestion(message: string, documentId: string, userId: string): Promise<DocumentChatResponse> {
    try {
      const response = await this.api.post<DocumentChatResponse>(
        '/api/chat',
        {
          message,
          document_id: documentId,
          user_id: userId,
        },
        {
          // Document Q&A may include OCR and model latency.
          timeout: 0,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getDocumentChatHistory(userId: string, documentId?: string): Promise<ChatHistoryMessage[]> {
    try {
      const response = await this.api.get('/api/chat/history', {
        params: {
          user_id: userId,
          ...(documentId ? { document_id: documentId } : {}),
        },
      });
      return response.data?.messages || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async sendExternalChatMessage(userId: string, message: string, documentId?: string): Promise<DocumentChatResponse> {
    try {
      const response = await this.api.post<DocumentChatResponse>(
        '/api/assistant/chat',
        {
          user_id: userId,
          message,
          ...(documentId ? { document_id: documentId } : {}),
        },
        {
          timeout: 0,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getExternalChatHistory(userId: string, documentId?: string): Promise<ExternalChatHistoryMessage[]> {
    try {
      const response = await this.api.get('/api/assistant/history', {
        params: {
          user_id: userId,
          ...(documentId ? { document_id: documentId } : {}),
        },
      });

      if (Array.isArray(response.data?.messages)) {
        return response.data.messages;
      }

      return [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async createStudyPlan(payload: {
    user_id: string;
    title: string;
    target_date: string;
    document_id?: string;
    document_title?: string;
    notes?: string;
    reminder_days_before?: number;
    user_email?: string;
  }): Promise<StudyPlan> {
    try {
      const response = await this.api.post<StudyPlan>('/api/study-plans', payload);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getStudyPlans(userId: string): Promise<StudyPlan[]> {
    try {
      const response = await this.api.get('/api/study-plans', {
        params: { user_id: userId },
      });
      return response.data?.plans || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async updateStudyPlanStatus(planId: string, userId: string, status: 'pending' | 'done' | 'in_progress' | 'todo'): Promise<StudyPlan> {
    try {
      const response = await this.api.patch<StudyPlan>(`/api/study-plans/${planId}`, {
        user_id: userId,
        status,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async deleteStudyPlan(planId: string, userId: string): Promise<void> {
    try {
      await this.api.delete(`/api/study-plans/${planId}`, {
        params: { user_id: userId },
      });
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getStudyPlanNotifications(userId: string): Promise<StudyPlanNotification[]> {
    try {
      const response = await this.api.get('/api/study-plans/notifications', {
        params: { user_id: userId },
      });
      return response.data?.notifications || [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async generatePersonalizedStudyPlan(payload: {
    user_id: string;
    plan_ids: string[];
    available_days: string[];
    study_days: number;
    hours_per_day: number;
    preferred_start_time?: string;
    exam_date: string;
    learning_style?: string; // "visual", "auditory", "reading", "kinesthetic"
    difficulty_level?: string; // "beginner", "intermediate", "advanced"
  }): Promise<StudyPlanGenerateResponse> {
    try {
      const response = await this.api.post<StudyPlanGenerateResponse>('/api/study-plans/generate', payload);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private stringifyValidationDetail(detail: any): string | undefined {
    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === 'string') {
            return item;
          }
          if (item && typeof item === 'object') {
            const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
            const msg = typeof item.msg === 'string' ? item.msg : '';
            if (loc && msg) {
              return `${loc}: ${msg}`;
            }
            if (msg) {
              return msg;
            }
            try {
              return JSON.stringify(item);
            } catch {
              return String(item);
            }
          }
          return String(item ?? '');
        })
        .join(' | ');
    }

    if (detail && typeof detail === 'object') {
      try {
        return JSON.stringify(detail);
      } catch {
        return String(detail);
      }
    }

    return undefined;
  }

  private handleError(error: any): ApiError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      const status = axiosError.response?.status || 500;

      const responseData = axiosError.response?.data as any;
      const normalizedDetail = this.stringifyValidationDetail(responseData?.detail);
      const requestTimedOut = axiosError.code === 'ECONNABORTED';
      const message =
        responseData?.message ||
        normalizedDetail ||
        (requestTimedOut
          ? 'Request timed out while the server was still processing. Please retry or refresh to load completed results.'
          : undefined) ||
        axiosError.message ||
        'Request failed';

      return {
        status,
        message,
        detail: normalizedDetail,
      };
    }

    return {
      status: 500,
      message: 'An unexpected error occurred',
    };
  }
}

const apiService = new ApiService();

export default apiService;
