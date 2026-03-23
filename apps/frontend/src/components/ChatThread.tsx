'use client';

import React from 'react';
import { useEffect, useRef } from 'react';

interface ChatThreadMessage {
  id: string;
  role: 'user' | 'assistant' | string;
  content: string;
  createdAt?: string;
  meta?: string;
}

interface ChatThreadProps {
  messages: ChatThreadMessage[];
  emptyMessage?: string;
  assistantLabel?: string;
  isTyping?: boolean;
  className?: string;
}

export const ChatThread: React.FC<ChatThreadProps> = ({
  messages,
  emptyMessage = 'No messages yet.',
  assistantLabel = 'Tutor AI',
  isTyping = false,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    containerRef.current.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages.length, isTyping]);

  if (messages.length === 0 && !isTyping) {
    return (
      <div className={`rounded-xl border border-dashed border-violet-300/35 bg-white/5 p-4 text-sm text-violet-100/75 ${className || ''}`}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`space-y-3 overflow-y-auto rounded-xl border border-violet-200/25 bg-[#130a2b]/70 p-3 shadow-inner shadow-violet-950/30 ${
        className || 'max-h-[430px]'
      }`}
    >
      {messages.map((message) => {
        const isUser = message.role === 'user';
        return (
          <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[88%] items-end gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                  isUser
                    ? 'bg-gradient-to-br from-violet-400 to-fuchsia-500 text-white'
                    : 'border border-violet-300/40 bg-violet-500/20 text-violet-100'
                }`}
              >
                {isUser ? 'You' : 'AI'}
              </div>

              <div
                className={`rounded-2xl px-4 py-3 shadow-lg ${
                  isUser
                    ? 'rounded-br-md bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white shadow-violet-900/35'
                    : 'rounded-bl-md border border-violet-200/20 bg-white/10 text-violet-50 shadow-violet-950/25'
                }`}
              >
                {!isUser && <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-violet-200/80">{assistantLabel}</p>}
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                {(message.meta || message.createdAt) && (
                  <p className={`mt-2 text-[11px] ${isUser ? 'text-violet-100/80' : 'text-violet-200/75'}`}>
                    {message.meta || message.createdAt}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {isTyping && (
        <div className="flex justify-start">
          <div className="flex items-end gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-violet-300/40 bg-violet-500/20 text-[11px] font-bold text-violet-100">
              AI
            </div>
            <div className="rounded-2xl rounded-bl-md border border-violet-200/20 bg-white/10 px-4 py-3 text-violet-100">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 animate-bounce rounded-full bg-violet-200 [animation-delay:-0.2s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-violet-200 [animation-delay:-0.1s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-violet-200" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
