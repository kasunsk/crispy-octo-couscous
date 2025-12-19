import { User, Bot } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../services/api';
import clsx from 'clsx';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'flex gap-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}

      <div
        className={clsx(
          'max-w-[80%] rounded-lg px-4 py-2',
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        </div>
      )}
    </div>
  );
}


