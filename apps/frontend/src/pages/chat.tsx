import Head from 'next/head';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useUser } from '@clerk/nextjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Alert, Card, ChatThread, SiteShell } from '@/components';
import apiService from '@/services/api';
import { ChatHistoryMessage, Document, ExternalChatHistoryMessage } from '@/types/api';
import { formatDate, getErrorMessage } from '@/utils/helpers';

const PDF_PROMPTS = [
  'Summarize this chapter in 5 key points',
  'Give me likely exam questions from this section',
  'Explain this topic like I am a beginner',
];

const ASSISTANT_PROMPTS = [
  'What are my weak areas right now?',
  'Give me a 7-day revision strategy',
  'Do you remember my name?',
];

export default function ChatPage() {
  const { user } = useUser();

  const [pdfLoading, setPdfLoading] = useState(false);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  const [pdfQuestion, setPdfQuestion] = useState('');
  const [assistantQuestion, setAssistantQuestion] = useState('');

  const [pdfChatHistory, setPdfChatHistory] = useState<ChatHistoryMessage[]>([]);
  const [assistantHistory, setAssistantHistory] = useState<ExternalChatHistoryMessage[]>([]);

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );
  const isSelectedDocumentReady = selectedDocument?.status === 'ready';

  const pdfMessages = useMemo(() => {
    const ordered = [...pdfChatHistory].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    return ordered.flatMap((entry, idx) => [
      {
        id: `${entry.chat_id}-q-${idx}`,
        role: 'user',
        content: entry.question,
        createdAt: formatDate(entry.created_at),
      },
      {
        id: `${entry.chat_id}-a-${idx}`,
        role: 'assistant',
        content: entry.response,
        createdAt: formatDate(entry.created_at),
      },
    ]);
  }, [pdfChatHistory]);

  const assistantMessages = useMemo(() => {
    const ordered = [...assistantHistory].sort((a, b) => {
      const first = a.created_at ? new Date(a.created_at).getTime() : 0;
      const second = b.created_at ? new Date(b.created_at).getTime() : 0;
      return first - second;
    });

    return ordered.map((entry, idx) => ({
      id: entry.chat_id || `${entry.role}-${idx}`,
      role: entry.role,
      content: entry.content,
      createdAt: entry.created_at ? formatDate(entry.created_at) : undefined,
    }));
  }, [assistantHistory]);

  const loadData = useCallback(async (userId: string, documentId?: string) => {
    try {
      const [docs, pdfHistory, assistant] = await Promise.all([
        apiService.getDocuments(userId),
        apiService.getDocumentChatHistory(userId, documentId),
        apiService.getExternalChatHistory(userId),
      ]);

      setDocuments(docs);
      setPdfChatHistory(pdfHistory);
      setAssistantHistory(assistant);

      setSelectedDocumentId((prev) => {
        if (prev || docs.length === 0) {
          return prev;
        }
        const firstReady = docs.find((doc) => doc.status === 'ready');
        return (firstReady || docs[0]).document_id;
      });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    if (!user?.id) {
      return;
    }

    void loadData(user.id);
  }, [loadData, user?.id]);

  useEffect(() => {
    if (!user?.id || !selectedDocumentId) {
      return;
    }

    void apiService
      .getDocumentChatHistory(user.id, selectedDocumentId)
      .then(setPdfChatHistory)
      .catch(() => undefined);
  }, [selectedDocumentId, user?.id]);

  const handleAskPdf = async () => {
    if (!user?.id || !selectedDocumentId || !pdfQuestion.trim()) {
      return;
    }

    if (!isSelectedDocumentReady) {
      setError('Selected document is still processing. Please wait for Ready status before asking PDF questions.');
      return;
    }

    setPdfLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.askDocumentQuestion(pdfQuestion, selectedDocumentId, user.id);
      setPdfQuestion('');
      setSuccess(`PDF response generated with ${(response.confidence * 100).toFixed(1)}% confidence.`);
      const history = await apiService.getDocumentChatHistory(user.id, selectedDocumentId);
      setPdfChatHistory(history);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setPdfLoading(false);
    }
  };

  const handleAskAssistant = async () => {
    if (!user?.id || !assistantQuestion.trim()) {
      return;
    }

    setAssistantLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.sendExternalChatMessage(user.id, assistantQuestion, selectedDocumentId || undefined);
      setAssistantQuestion('');
      setSuccess('Assistant response received.');
      const history = await apiService.getExternalChatHistory(user.id);
      setAssistantHistory(history);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setAssistantLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Chat • Quiz Tutor</title>
      </Head>

      <SiteShell title="AI Chat Center" subtitle="Real-time PDF Q&A and personalized memory assistant in chat format">
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        <SignedOut>
          <Card title="Authentication required" subtitle="Sign in to use your personalized assistant and PDF chat">
            <div className="flex flex-col gap-3 sm:flex-row">
              <SignInButton mode="modal">
                <button className="rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-5 py-3 font-semibold text-white">Sign in</button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="rounded-lg border border-violet-300/35 bg-white/10 px-5 py-3 font-semibold text-violet-100 hover:bg-white/15">
                  Create account
                </button>
              </SignUpButton>
            </div>
          </Card>
        </SignedOut>

        <SignedIn>
          <Card title="How Chat Works" subtitle="Choose a document for grounded answers, then switch between two chat modes.">
            <div className="grid gap-3 text-sm md:grid-cols-3">
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">1. Pick a document context (optional).</div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">2. Ask from PDF for source-grounded explanations.</div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">3. Ask assistant for strategy, memory, and progress coaching.</div>
            </div>
          </Card>

          <Card title="Select Document Context" subtitle="Assistant can combine your selected document with your progress data">
            <select
              value={selectedDocumentId || ''}
              onChange={(event) => setSelectedDocumentId(event.target.value || null)}
              className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
            >
              <option value="">No document context</option>
              {documents.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.title} ({doc.status})
                </option>
              ))}
            </select>
            {selectedDocument && (
              <p className="mt-2 text-sm text-white/75">
                Selected: {selectedDocument.title} • {selectedDocument.pages || 0} pages • {selectedDocument.tables_count || 0} tables • {selectedDocument.chunks_count || 0} chunks
              </p>
            )}
            {selectedDocument && selectedDocument.status !== 'ready' && (
              <p className="mt-2 text-sm text-amber-200/95">
                Document status is {selectedDocument.status}. Chat answers may be incomplete until processing finishes.
              </p>
            )}
          </Card>

          <div className="mt-6 grid gap-6 xl:grid-cols-2">
            <Card title="Ask from PDF" subtitle="Document-grounded responses only">
              <div className="space-y-3">
                <ChatThread
                  messages={pdfMessages}
                  emptyMessage="No PDF chat yet. Select a document and ask your first question."
                  assistantLabel="PDF Tutor"
                  isTyping={pdfLoading}
                  className="h-[420px] md:h-[520px]"
                />

                <div className="flex flex-wrap gap-2">
                  {PDF_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => setPdfQuestion(prompt)}
                      className="rounded-full border border-violet-300/35 bg-white/10 px-3 py-1.5 text-xs font-semibold text-violet-100 hover:bg-white/15"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>

                <div className="rounded-xl border border-violet-300/30 bg-[#180d33]/90 p-2">
                  <textarea
                    rows={2}
                    value={pdfQuestion}
                    onChange={(event) => setPdfQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        void handleAskPdf();
                      }
                    }}
                    placeholder="Ask anything from the selected PDF..."
                    className="w-full resize-none rounded-lg border border-transparent bg-transparent p-2 text-violet-50 placeholder:text-violet-200/55 focus:border-violet-300/30 focus:outline-none"
                  />

                  <div className="mt-2 flex items-center justify-between px-2 pb-1">
                    <p className="text-xs text-violet-100/70">Enter sends. Shift + Enter adds a new line.</p>
                    <button
                      onClick={() => void handleAskPdf()}
                      disabled={!selectedDocumentId || !pdfQuestion.trim() || pdfLoading || !isSelectedDocumentReady}
                      aria-label="Send PDF question"
                      className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white shadow-lg shadow-violet-950/35 transition hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14" />
                        <path d="M13 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Study Assistant" subtitle="General knowledge + memory + progress coaching">
              <div className="space-y-3">
                <ChatThread
                  messages={assistantMessages}
                  emptyMessage="No assistant conversation yet. Say hi or ask for your study performance."
                  assistantLabel="Study Coach"
                  isTyping={assistantLoading}
                  className="h-[420px] md:h-[520px]"
                />

                <div className="flex flex-wrap gap-2">
                  {ASSISTANT_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => setAssistantQuestion(prompt)}
                      className="rounded-full border border-violet-300/35 bg-white/10 px-3 py-1.5 text-xs font-semibold text-violet-100 hover:bg-white/15"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>

                <div className="rounded-xl border border-violet-300/30 bg-[#180d33]/90 p-2">
                  <textarea
                    rows={2}
                    value={assistantQuestion}
                    onChange={(event) => setAssistantQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        void handleAskAssistant();
                      }
                    }}
                    placeholder="Ask anything, including your progress and weak areas..."
                    className="w-full resize-none rounded-lg border border-transparent bg-transparent p-2 text-violet-50 placeholder:text-violet-200/55 focus:border-violet-300/30 focus:outline-none"
                  />

                  <div className="mt-2 flex items-center justify-between px-2 pb-1">
                    <p className="text-xs text-violet-100/70">Tip: ask strategy questions like &quot;What should I study first this week?&quot;</p>
                    <button
                      onClick={() => void handleAskAssistant()}
                      disabled={!assistantQuestion.trim() || assistantLoading}
                      aria-label="Send assistant message"
                      className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white shadow-lg shadow-violet-950/35 transition hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14" />
                        <path d="M13 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </SignedIn>
      </SiteShell>
    </>
  );
}
