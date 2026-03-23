import Head from 'next/head';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useUser } from '@clerk/nextjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { Alert, Button, Card, QuestionCard, SiteShell } from '@/components';
import apiService from '@/services/api';
import { Document, QuizGenerateResponse, QuizResult, QuizSummary } from '@/types/api';
import { formatDate, getErrorMessage } from '@/utils/helpers';

const QUESTION_COUNTS = [3, 5, 8, 10, 15];

export default function QuizPage() {
  const { user } = useUser();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');
  const [documentQuizzes, setDocumentQuizzes] = useState<QuizSummary[]>([]);

  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [questionType, setQuestionType] = useState<'multiple_choice' | 'short_answer'>('multiple_choice');
  const [numQuestions, setNumQuestions] = useState<number>(5);

  const [activeQuiz, setActiveQuiz] = useState<QuizGenerateResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);

  const readyDocuments = useMemo(
    () => documents.filter((doc) => doc.status === 'ready'),
    [documents]
  );

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  const answeredCount = useMemo(() => {
    if (!activeQuiz) {
      return 0;
    }

    return activeQuiz.questions.filter((question) => (answers[question.id] || '').trim().length > 0).length;
  }, [activeQuiz, answers]);

  const loadDocuments = useCallback(async (userId: string) => {
    try {
      const docs = await apiService.getDocuments(userId);
      setDocuments(docs);

      setSelectedDocumentId((prev) => {
        if (prev) {
          return prev;
        }
        const ready = docs.find((doc) => doc.status === 'ready');
        return ready?.document_id || prev;
      });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  const loadDocumentQuizzes = useCallback(async (documentId: string) => {
    if (!documentId) {
      setDocumentQuizzes([]);
      return;
    }

    try {
      const quizzes = await apiService.getDocumentQuizzes(documentId);
      setDocumentQuizzes(quizzes);
    } catch {
      setDocumentQuizzes([]);
    }
  }, []);

  useEffect(() => {
    if (!user?.id) {
      return;
    }

    void loadDocuments(user.id);
  }, [loadDocuments, user?.id]);

  useEffect(() => {
    if (!selectedDocumentId) {
      setDocumentQuizzes([]);
      return;
    }

    void loadDocumentQuizzes(selectedDocumentId);
  }, [loadDocumentQuizzes, selectedDocumentId]);

  const handleGenerateQuiz = async () => {
    if (!selectedDocumentId) {
      setError('Select a ready document first.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const quiz = await apiService.generateQuiz(selectedDocumentId, numQuestions, difficulty, questionType);
      setActiveQuiz(quiz);
      setAnswers({});
      setResult(null);
      setSuccess(`Quiz generated successfully with ${quiz.total_questions} questions.`);
      await loadDocumentQuizzes(selectedDocumentId);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenQuiz = async (quizId: string) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const quiz = await apiService.getQuiz(quizId);
      setActiveQuiz(quiz);
      setAnswers({});
      setResult(null);
      setSuccess('Saved quiz loaded. You can answer and submit now.');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionId: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  const handleSubmit = async () => {
    if (!user?.id || !activeQuiz) {
      return;
    }

    if (answeredCount === 0) {
      setError('Add at least one answer before submitting.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const grade = await apiService.submitQuiz(activeQuiz.quiz_id, answers, user.id);
      setResult(grade);
      setSuccess(`Quiz submitted. You scored ${(grade.score * 100).toFixed(1)}%.`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Quiz • Quiz Tutor</title>
      </Head>

      <SiteShell
        title="Quiz Center"
        subtitle="Generate quizzes from your documents, answer in-app, and review detailed explanations to improve faster"
      >
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        <SignedOut>
          <Card title="Authentication required" subtitle="Sign in to generate and attempt quizzes">
            <div className="flex flex-col gap-3 sm:flex-row">
              <SignInButton mode="modal">
                <button className="rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-5 py-3 font-semibold text-white">
                  Sign in
                </button>
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
          <Card title="How Quizzes Work" subtitle="Build by preference and learn from detailed explanations.">
            <div className="grid gap-3 text-sm md:grid-cols-3">
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">1. Select a ready document.</div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">2. Choose MCQ or short-answer format.</div>
              <div className="rounded-xl border border-violet-300/25 bg-white/10 p-3 text-violet-100/85">3. Submit and review score + explanations.</div>
            </div>
          </Card>

          <Card title="Create Or Open Quiz" subtitle="Use your preferred difficulty and question type.">
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Document</label>
                <select
                  value={selectedDocumentId}
                  onChange={(event) => setSelectedDocumentId(event.target.value)}
                  className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                >
                  <option value="">Select ready document</option>
                  {readyDocuments.map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Difficulty</label>
                <select
                  value={difficulty}
                  onChange={(event) => setDifficulty(event.target.value as 'easy' | 'medium' | 'hard')}
                  className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Question type</label>
                <select
                  value={questionType}
                  onChange={(event) => setQuestionType(event.target.value as 'multiple_choice' | 'short_answer')}
                  className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                >
                  <option value="multiple_choice">Multiple Choice</option>
                  <option value="short_answer">Short Answer (single response)</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Question count</label>
                <select
                  value={String(numQuestions)}
                  onChange={(event) => setNumQuestions(Number(event.target.value))}
                  className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                >
                  {QUESTION_COUNTS.map((count) => (
                    <option key={count} value={count}>
                      {count}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={handleGenerateQuiz} loading={loading} disabled={!selectedDocumentId}>
                Generate Quiz
              </Button>
              {selectedDocument && (
                <p className="text-sm text-violet-100/75">
                  Current document: {selectedDocument.title}
                </p>
              )}
            </div>

            <div className="mt-6 space-y-2">
              <p className="text-sm font-semibold text-violet-100/90">Saved quizzes for selected document</p>
              {documentQuizzes.length === 0 && (
                <p className="text-sm text-violet-100/70">No saved quizzes yet for this document.</p>
              )}
              {documentQuizzes.map((quiz) => (
                <div key={quiz.quiz_id} className="flex flex-col gap-2 rounded-xl border border-violet-300/25 bg-white/10 p-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-white">Quiz {quiz.quiz_id.slice(0, 8)}...</p>
                    <p className="text-xs text-violet-100/75">
                      {quiz.total_questions || 0} questions • {quiz.question_type || 'mixed'} • {quiz.difficulty || 'medium'}
                      {quiz.created_at ? ` • ${formatDate(quiz.created_at)}` : ''}
                    </p>
                  </div>
                  <Button size="small" variant="secondary" onClick={() => void handleOpenQuiz(quiz.quiz_id)} loading={loading}>
                    Open Quiz
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Attempt Quiz" subtitle="Answer, submit, and review detailed explanations question by question.">
            {!activeQuiz && <p className="text-violet-100/75">Generate a new quiz or open a saved quiz to start.</p>}

            {activeQuiz && (
              <>
                <div className="mb-4 rounded-xl border border-violet-300/25 bg-white/10 p-3 text-sm text-violet-100/85">
                  <p>
                    Quiz ID: {activeQuiz.quiz_id} • Questions: {activeQuiz.total_questions} • Type:{' '}
                    {activeQuiz.question_type || questionType} • Difficulty: {activeQuiz.difficulty || difficulty}
                  </p>
                  <p className="mt-1">Answered: {answeredCount}/{activeQuiz.total_questions}</p>
                </div>

                <div>
                  {activeQuiz.questions.map((question, index) => (
                    <QuestionCard
                      key={question.id}
                      question={question}
                      index={index}
                      onAnswer={
                        result
                          ? undefined
                          : (answer) => {
                              handleAnswer(question.id, answer);
                            }
                      }
                      selectedAnswer={answers[question.id]}
                      showCorrect={!!result}
                    />
                  ))}
                </div>

                {!result && (
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={handleSubmit} loading={loading} disabled={answeredCount === 0}>
                      Submit Quiz
                    </Button>
                    <p className="self-center text-sm text-violet-100/70">
                      You can submit even if not all questions are answered.
                    </p>
                  </div>
                )}

                {result && (
                  <div className="mt-5 rounded-2xl border border-emerald-300/40 bg-emerald-500/15 p-5">
                    <p className="text-2xl font-bold text-emerald-100">
                      Score: {(result.score * 100).toFixed(1)}% ({result.correct_count}/{result.total_questions})
                    </p>

                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <div>
                        <p className="text-sm font-semibold text-emerald-100/90">Weak areas</p>
                        {result.weak_areas.length === 0 && <p className="text-sm text-emerald-100/80">No major weak areas detected.</p>}
                        {result.weak_areas.map((area) => (
                          <p key={area.topic} className="text-sm text-emerald-100/85">
                            {area.topic}: {(area.accuracy * 100).toFixed(0)}% accuracy
                          </p>
                        ))}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-emerald-100/90">Recommendations</p>
                        {result.recommendations.length === 0 && <p className="text-sm text-emerald-100/80">No recommendations available.</p>}
                        {result.recommendations.map((item, index) => (
                          <p key={`${item}-${index}`} className="text-sm text-emerald-100/85">• {item}</p>
                        ))}
                      </div>
                    </div>

                    <div className="mt-4">
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setAnswers({});
                          setResult(null);
                          setSuccess('You can attempt this quiz again now.');
                        }}
                      >
                        Retake This Quiz
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </Card>
        </SignedIn>
      </SiteShell>
    </>
  );
}
