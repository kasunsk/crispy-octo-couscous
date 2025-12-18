import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2 } from 'lucide-react';
import { documentApi } from '../services/api';
import { useStore } from '../store/useStore';
import clsx from 'clsx';

export default function FileUpload() {
  const [uploading, setUploading] = useState(false);
  const { addDocument, setError } = useStore();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);

    try {
      const document = await documentApi.upload(file);
      addDocument(document);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  }, [addDocument, setError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
        isDragActive
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500',
        uploading && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      
      {uploading ? (
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">Uploading and processing document...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <Upload className="w-12 h-12 text-gray-400" />
          <div>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
              {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              or click to select a file
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              Supported: PDF, Word, Excel
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

