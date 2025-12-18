import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import DocumentList from './components/DocumentList';
import { useStore } from './store/useStore';
import { documentApi, healthApi } from './services/api';
import { AlertCircle, X } from 'lucide-react';

const queryClient = new QueryClient();

function AppContent() {
  const {
    documents,
    selectedDocument,
    setDocuments,
    setError,
    error,
  } = useStore();
  const [healthStatus, setHealthStatus] = useState<any>(null);

  useEffect(() => {
    // Load documents
    documentApi
      .list()
      .then(setDocuments)
      .catch((err) => setError('Failed to load documents'));

    // Check health
    healthApi
      .check()
      .then(setHealthStatus)
      .catch(() => setHealthStatus({ status: 'unknown' }));
  }, [setDocuments, setError]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              AI Document Q&A
            </h1>
            {healthStatus && (
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    healthStatus.ollama_connected
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {healthStatus.ollama_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-700 dark:text-red-400">{error}</p>
              </div>
              <button
                onClick={() => useStore.getState().setError(null)}
                className="text-red-500 hover:text-red-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* File Upload */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Upload Document
              </h2>
              <FileUpload />
            </div>

            {/* Document List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                Documents ({documents.length})
              </h2>
              <DocumentList documents={documents} />
            </div>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
              <ChatInterface />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;

