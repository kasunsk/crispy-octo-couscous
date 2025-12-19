import { FileText, Trash2, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Document } from '../services/api';
import { documentApi } from '../services/api';
import { useStore } from '../store/useStore';
import { useState } from 'react';
import clsx from 'clsx';

interface DocumentListProps {
  documents: Document[];
}

export default function DocumentList({ documents }: DocumentListProps) {
  const { setSelectedDocument, removeDocument, setError, clearMessages } = useStore();
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleSelect = (document: Document) => {
    setSelectedDocument(document);
    clearMessages();
  };

  const handleDelete = async (documentId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleting(documentId);
    setError(null);

    try {
      await documentApi.delete(documentId);
      removeDocument(documentId);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to delete document');
    } finally {
      setDeleting(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <p>No documents uploaded yet</p>
        <p className="text-sm mt-1">Upload a document to start asking questions</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          onClick={() => handleSelect(doc)}
          className={clsx(
            'p-3 rounded-lg border cursor-pointer transition-colors',
            'hover:bg-gray-50 dark:hover:bg-gray-800',
            'border-gray-200 dark:border-gray-700'
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <FileText className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                  {doc.filename}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(doc.status)}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(doc.file_size)} • {doc.chunks_count} chunks
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={(e) => handleDelete(doc.id, e)}
              disabled={deleting === doc.id}
              className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
            >
              {deleting === doc.id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}


