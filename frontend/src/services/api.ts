import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunks_count: number;
  status: string;
  uploaded_at: string;
  processed_at: string | null;
}

export interface QuestionRequest {
  question: string;
  document_id?: string;
  session_id?: string;
  use_internet?: boolean;
}

export interface QuestionResponse {
  answer: string;
  sources: Array<{
    chunk_id?: string;
    content?: string;
    similarity?: number;
    title?: string;
    url?: string;
    snippet?: string;
    metadata?: any;
  }>;
  session_id: string;
  document_id?: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<any>;
  created_at: string;
}

// Document APIs
export const documentApi = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<Document>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (): Promise<Document[]> => {
    const response = await api.get<Document[]>('/api/documents');
    return response.data;
  },

  get: async (documentId: string): Promise<Document> => {
    const response = await api.get<Document>(`/api/documents/${documentId}`);
    return response.data;
  },

  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/api/documents/${documentId}`);
  },

  getChunks: async (documentId: string): Promise<any[]> => {
    const response = await api.get(`/api/documents/${documentId}/chunks`);
    return response.data;
  },
};

// Chat APIs
export const chatApi = {
  askQuestion: async (request: QuestionRequest): Promise<QuestionResponse> => {
    const response = await api.post<QuestionResponse>('/api/chat/question', request);
    return response.data;
  },

  getHistory: async (sessionId: string): Promise<ChatMessage[]> => {
    const response = await api.get<ChatMessage[]>(`/api/chat/history/${sessionId}`);
    return response.data;
  },

  deleteHistory: async (sessionId: string): Promise<void> => {
    await api.delete(`/api/chat/history/${sessionId}`);
  },
};

// Health API
export const healthApi = {
  check: async (): Promise<any> => {
    const response = await api.get('/api/health');
    return response.data;
  },
};

export default api;

