import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, Globe } from 'lucide-react';
import { chatApi, QuestionRequest } from '../services/api';
import { useStore } from '../store/useStore';
import ChatMessage from './ChatMessage';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    selectedDocument,
    currentSessionId,
    messages,
    addMessage,
    setCurrentSession,
    setLoading,
    setError,
  } = useStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const question = input.trim();
    setInput('');
    setSending(true);
    setLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: question,
      created_at: new Date().toISOString(),
    };
    addMessage(userMessage);

    try {
      const request: QuestionRequest = {
        question,
        document_id: selectedDocument?.id,
        session_id: currentSessionId || undefined,
        use_internet: !selectedDocument,
      };

      const response = await chatApi.askQuestion(request);

      // Update session ID
      if (response.session_id) {
        setCurrentSession(response.session_id);
      }

      // Add assistant message
      const assistantMessage = {
        id: response.timestamp,
        role: 'assistant' as const,
        content: response.answer,
        sources: response.sources,
        created_at: response.timestamp,
      };
      addMessage(assistantMessage);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to get answer');
      
      // Add error message
      const errorMessage = {
        id: Date.now().toString(),
        role: 'assistant' as const,
        content: 'Sorry, I encountered an error while processing your question.',
        created_at: new Date().toISOString(),
      };
      addMessage(errorMessage);
    } finally {
      setSending(false);
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2">
          {selectedDocument ? (
            <>
              <FileText className="w-5 h-5 text-blue-500" />
              <span className="font-medium text-gray-700 dark:text-gray-300">
                {selectedDocument.filename}
              </span>
            </>
          ) : (
            <>
              <Globe className="w-5 h-5 text-green-500" />
              <span className="font-medium text-gray-700 dark:text-gray-300">
                General Questions (Internet)
              </span>
            </>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <p className="text-lg mb-2">Start a conversation</p>
              <p className="text-sm">
                {selectedDocument
                  ? 'Ask questions about the uploaded document'
                  : 'Ask any question and I will search the internet for answers'}
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedDocument
                ? 'Ask a question about the document...'
                : 'Ask any question...'
            }
            className="flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            rows={2}
            disabled={sending}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {sending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

