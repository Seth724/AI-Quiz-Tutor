import Head from 'next/head';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useUser } from '@clerk/nextjs';
import { useEffect, useState } from 'react';

import { Alert, Button, Card, SiteShell, StudyPlanCalendar } from '@/components';
import apiService from '@/services/api';
import { Document, StudyPlan, StudyPlanNotification } from '@/types/api';
import { formatDate, getErrorMessage } from '@/utils/helpers';

export default function PlannerPage() {
  const { user } = useUser();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [studyPlans, setStudyPlans] = useState<StudyPlan[]>([]);
  const [notifications, setNotifications] = useState<StudyPlanNotification[]>([]);

  const [title, setTitle] = useState('');
  const [targetDate, setTargetDate] = useState<string>(() =>
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  );
  const [notes, setNotes] = useState('');
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [reminderDays, setReminderDays] = useState(2);

  const loadData = async (userId: string) => {
    try {
      const [docs, plans, notesData] = await Promise.all([
        apiService.getDocuments(userId),
        apiService.getStudyPlans(userId),
        apiService.getStudyPlanNotifications(userId),
      ]);
      setDocuments(docs);
      setStudyPlans(plans);
      setNotifications(notesData);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    if (!user?.id) {
      return;
    }

    void loadData(user.id);
  }, [user?.id]);

  const handleCreatePlan = async () => {
    if (!user?.id || !targetDate) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const selectedDoc = documents.find((doc) => doc.document_id === selectedDocId);

      await apiService.createStudyPlan({
        user_id: user.id,
        title: title.trim() || `Finish revising ${selectedDoc?.title || 'selected topics'}`,
        target_date: targetDate,
        document_id: selectedDocId || undefined,
        document_title: selectedDoc?.title,
        notes: notes.trim() || undefined,
        reminder_days_before: reminderDays,
        user_email: user.primaryEmailAddress?.emailAddress || undefined,
      });

      setTitle('');
      setNotes('');
      setSuccess('Study plan created successfully.');
      await loadData(user.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const getNextPlanStatus = (status: string): 'pending' | 'in_progress' | 'done' => {
    if (status === 'pending' || status === 'todo') {
      return 'in_progress';
    }
    if (status === 'in_progress') {
      return 'done';
    }
    return 'pending';
  };

  const handleToggleStatus = async (plan: StudyPlan) => {
    if (!user?.id) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const nextStatus = getNextPlanStatus(plan.status);
      await apiService.updateStudyPlanStatus(plan.plan_id, user.id, nextStatus);
      setSuccess(`Plan status updated to ${nextStatus.replace('_', ' ')}.`);
      await loadData(user.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePlan = async (planId: string) => {
    if (!user?.id) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.deleteStudyPlan(planId, user.id);
      setSuccess('Study plan deleted.');
      await loadData(user.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Planner • Quiz Tutor</title>
      </Head>

      <SiteShell title="Study Planner" subtitle="Manage all your plans in calendar view with todo, in-progress, and done states">
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        <SignedOut>
          <Card title="Authentication required" subtitle="Sign in to create and manage study plans">
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
          <Card title="Study Plans Calendar" subtitle="View and manage your study schedule">
            {studyPlans.length === 0 ? (
              <p className="text-violet-100/75">No study plans yet. Create one below.</p>
            ) : (
              <StudyPlanCalendar
                plans={studyPlans}
                onToggleStatus={handleToggleStatus}
                onToggleActivity={() => {}}
                onDeletePlan={handleDeletePlan}
                loading={loading}
              />
            )}
          </Card>

          <Card title="Create Single Plan" subtitle="Quickly add one manual plan">
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Plan title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Finish biology revision"
                  className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 placeholder:text-violet-200/55 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Target date</label>
                <input
                  type="date"
                  value={targetDate}
                  onChange={(event) => setTargetDate(event.target.value)}
                  className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                />
              </div>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Linked document (optional)</label>
                <select
                  value={selectedDocId}
                  onChange={(event) => setSelectedDocId(event.target.value)}
                  className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                >
                  <option value="">No document</option>
                  {documents.map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-violet-100/90">Reminder days before</label>
                <input
                  type="number"
                  min={0}
                  max={30}
                  value={reminderDays}
                  onChange={(event) => setReminderDays(Math.max(0, Math.min(30, Number(event.target.value) || 0)))}
                  className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="mb-2 block text-sm font-semibold text-violet-100/90">Notes</label>
              <textarea
                rows={3}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Topics to complete before exam day..."
                className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 placeholder:text-violet-200/55 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
              />
            </div>

            <div className="mt-4">
              <Button onClick={handleCreatePlan} loading={loading}>
                Create Plan
              </Button>
            </div>
          </Card>

          <Card title="Upcoming Notifications" subtitle="Generated from your pending deadlines">
            <div className="space-y-3">
              {notifications.length === 0 && <p className="text-violet-100/75">No upcoming notifications yet.</p>}
              {notifications.map((item) => (
                <div key={item.id} className="rounded-xl border border-amber-300/45 bg-amber-500/15 p-3">
                  <p className="font-semibold text-amber-100">{item.title}</p>
                  <p className="text-sm text-amber-100/90">{item.message}</p>
                  <p className="mt-1 text-xs text-amber-100/75">Target: {formatDate(item.target_date)}</p>
                </div>
              ))}
            </div>
          </Card>
        </SignedIn>
      </SiteShell>
    </>
  );
}
