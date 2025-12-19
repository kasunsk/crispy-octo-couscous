import { create } from 'zustand';
import { Document, ChatMessage } from '../services/api';

interface AppState {
  // Documents
  documents: Document[];
  selectedDocument: Document | null;
  
  // Chat
  currentSessionId: string | null;
  messages: ChatMessage[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  removeDocument: (documentId: string) => void;
  setSelectedDocument: (document: Document | null) => void;
  
  setCurrentSession: (sessionId: string | null) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;
  
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  documents: [],
  selectedDocument: null,
  currentSessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  
  // Document actions
  setDocuments: (documents) => set({ documents }),
  addDocument: (document) => set((state) => ({
    documents: [document, ...state.documents]
  })),
  removeDocument: (documentId) => set((state) => ({
    documents: state.documents.filter(doc => doc.id !== documentId),
    selectedDocument: state.selectedDocument?.id === documentId 
      ? null 
      : state.selectedDocument
  })),
  setSelectedDocument: (document) => set({ selectedDocument: document }),
  
  // Chat actions
  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  setMessages: (messages) => set({ messages }),
  clearMessages: () => set({ messages: [], currentSessionId: null }),
  
  // UI actions
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));


