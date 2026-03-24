import Head from 'next/head';
import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useUser } from '@clerk/nextjs';
import { useEffect, useMemo, useState } from 'react';

import { Alert, Card, FileUpload, Loading, SiteShell } from '@/components';
import apiService from '@/services/api';
import { Document, DocumentUploadResponse } from '@/types/api';
import { formatDate, getErrorMessage, parseApiDate } from '@/utils/helpers';

const STATUS_COLORS: Record<string, string> = {
  ready: 'border-emerald-300/45 bg-emerald-500/15 text-emerald-100',
  processing: 'border-amber-300/45 bg-amber-500/15 text-amber-100',
  failed: 'border-rose-300/45 bg-rose-500/15 text-rose-100',
};
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getAgeLabel(value?: string): string | null {
  if (!value) {
    return null;
  }

  const timestamp = parseApiDate(value).getTime();
  if (Number.isNaN(timestamp)) {
    return null;
  }

  const minutes = Math.max(0, Math.floor((Date.now() - timestamp) / 60000));
  if (minutes < 1) {
    return 'just now';
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }

  const hours = Math.floor(minutes / 60);
  const remain = minutes % 60;
  return remain === 0 ? `${hours}h ago` : `${hours}h ${remain}m ago`;
}

export default function DocumentsPage() {
  const { user } = useUser();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploadResponse, setUploadResponse] = useState<DocumentUploadResponse | null>(null);
  const [processingDocumentId, setProcessingDocumentId] = useState<string | null>(null);

  const readyCount = useMemo(() => documents.filter((doc) => doc.status === 'ready').length, [documents]);
  const processingCount = useMemo(() => documents.filter((doc) => doc.status === 'processing').length, [documents]);

  const loadDocuments = async (userId: string) => {
    try {
      const docs = await apiService.getDocuments(userId);
      setDocuments(docs);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    if (!user?.id) {
      return;
    }
    void loadDocuments(user.id);
  }, [user?.id]);

  useEffect(() => {
    if (!user?.id) {
      return;
    }
    // Keep a light periodic refresh without hammering /status + /documents simultaneously.
    const interval = setInterval(() => {
      void loadDocuments(user.id);
    }, 20000);

    return () => clearInterval(interval);
  }, [user?.id]);

  const pollDocumentStatus = async (documentId: string) => {
    setProcessingDocumentId(documentId);

    for (let i = 0; i < 240; i++) {
      try {
        const status = await apiService.getDocumentStatus(documentId);
        if (status.status === 'ready') {
          setProcessingDocumentId(null);
          setSuccess('Document processing completed and is ready for chat and quizzes.');
          if (user?.id) {
            await loadDocuments(user.id);
          }
          return;
        }

        if (status.status === 'failed') {
          setProcessingDocumentId(null);
          setError(status.processing_error || status.message || 'Document processing failed.');
          if (user?.id) {
            await loadDocuments(user.id);
          }
          return;
        }
      } catch (err) {
        setProcessingDocumentId(null);
        setError(getErrorMessage(err));
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 8000));
    }

    setProcessingDocumentId(null);
    setError('Processing is taking longer than expected. Please refresh shortly.');
  };

  const handleFileSelect = async (file: File) => {
    if (!user?.id) {
      setError('Please sign in before uploading documents.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.uploadDocument(file, user.id);
      setUploadResponse(response);

      if (response.status === 'processing') {
        setSuccess(`Upload accepted for ${response.title}. Processing started.`);
        await loadDocuments(user.id);
        void pollDocumentStatus(response.document_id);
      } else {
        setSuccess(`Document ${response.title} uploaded successfully.`);
        await loadDocuments(user.id);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Documents • Quiz Tutor</title>
      </Head>

      <SiteShell
        title="My Documents"
        subtitle="Upload PDFs or scanned images once, reuse forever. Files open from local storage by default, with optional cloud URL support for production."
      >
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        <SignedOut>
          <Card title="Authentication required" subtitle="Sign in to upload and manage your documents">
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
          {loading && <Loading message="Working on your request..." size="medium" />}

          <div className="mb-6 grid gap-4 md:grid-cols-3">
            <Card>
              <p className="text-sm text-violet-100/70">Total documents</p>
              <p className="text-3xl font-bold text-white">{documents.length}</p>
            </Card>
            <Card>
              <p className="text-sm text-violet-100/70">Ready</p>
              <p className="text-3xl font-bold text-white">{readyCount}</p>
            </Card>
            <Card>
              <p className="text-sm text-violet-100/70">Processing now</p>
              <p className="text-3xl font-bold text-white">{processingCount || (processingDocumentId ? 1 : 0)}</p>
            </Card>
          </div>

          <Card title="Upload New File" subtitle="Your PDF or scanned image is indexed for chat, quiz, and planning workflows.">
            <FileUpload onFileSelect={handleFileSelect} disabled={loading} />
            {uploadResponse && (
              <div className="mt-4 rounded-xl border border-violet-300/35 bg-violet-400/15 p-3">
                <p className="font-semibold text-violet-100">{uploadResponse.title}</p>
                <p className="text-sm text-violet-100/85">Status: {uploadResponse.status}</p>
                <p className="text-sm text-violet-100/85">Document ID: {uploadResponse.document_id}</p>
              </div>
            )}
          </Card>

          <Card title="What To Do Next" subtitle="Simple workflow for each uploaded PDF">
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-200">Step 1</p>
                <p className="mt-2 font-semibold text-white">Upload and wait for Ready</p>
                <p className="mt-1 text-sm text-violet-100/75">Large PDFs process in background. Keep this page open or return later.</p>
              </div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-200">Step 2</p>
                <p className="mt-2 font-semibold text-white">Ask questions in Chat</p>
                <p className="mt-1 text-sm text-violet-100/75">Use the selected document context for grounded answers and assistant help.</p>
              </div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-200">Step 3</p>
                <p className="mt-2 font-semibold text-white">Create study deadlines</p>
                <p className="mt-1 text-sm text-violet-100/75">Use Plan Generator for full timetable creation, then manage everything in Planner calendar.</p>
              </div>
            </div>
          </Card>

          <Card title="Document Library" subtitle="Use these documents in Chat and Planner pages">
            <div className="space-y-3">
              {documents.length === 0 && <p className="text-violet-100/75">No documents uploaded yet.</p>}
              {documents.map((doc, index) => (
                <div key={doc.document_id} className="rounded-xl border border-violet-300/25 bg-white/10 p-4 backdrop-blur-sm">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-violet-200/80">Document {index + 1}</p>
                      <p className="text-lg font-semibold text-white">{doc.title || `Document ${index + 1}`}</p>
                      <p className="text-sm text-violet-100/75">Uploaded: {formatDate(doc.created_at)}</p>
                      <p className="text-sm text-violet-100/75">
                        Pages: {doc.pages || 0} | Tables: {doc.tables_count || 0} | Chunks: {doc.chunks_count || 0}
                      </p>
                      <p className="text-sm text-violet-100/75">Quizzes: {doc.quizzes_generated || 0} | Attempts: {doc.attempts_count || 0}</p>
                      <span className={`mt-2 inline-block rounded-full border px-3 py-1 text-xs font-semibold ${STATUS_COLORS[doc.status] || 'border-violet-300/35 bg-violet-500/15 text-violet-100'}`}>
                        {doc.status}
                      </span>
                      {!!doc.message && (
                        <p className="mt-2 max-w-2xl text-sm text-violet-100/80">{doc.message}</p>
                      )}
                      {doc.status === 'processing' && (
                        <p className="mt-1 text-sm text-amber-100/90">
                          Started: {getAgeLabel(doc.created_at) || 'unknown'} • Last update: {getAgeLabel(doc.updated_at) || 'unknown'}
                        </p>
                      )}
                      {doc.status === 'failed' && !!doc.processing_error && (
                        <p className="mt-1 text-sm text-rose-200/90">Error: {doc.processing_error}</p>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Link href="/chat" className="rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-3 py-2 text-sm font-semibold text-white">
                        Open Chat
                      </Link>
                      <Link href="/planner-generator" className="rounded-lg border border-violet-300/35 bg-white/10 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-white/15">
                        Open Generator
                      </Link>
                      <Link href="/planner" className="rounded-lg border border-violet-300/35 bg-white/10 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-white/15">
                        Plan Revision
                      </Link>
                      <a
                        href={doc.supabase_url || `${API_BASE_URL}/api/documents/${doc.document_id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-lg border border-violet-300/35 bg-white/10 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-white/15"
                      >
                        {doc.supabase_url ? 'Open PDF (Cloud)' : 'View / Download PDF'}
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </SignedIn>
      </SiteShell>
    </>
  );
}
