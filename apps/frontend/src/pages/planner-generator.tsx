import Head from 'next/head';
import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, SignUpButton, useUser } from '@clerk/nextjs';
import { useEffect, useMemo, useState } from 'react';

import { Alert, Button, Card, SiteShell } from '@/components';
import apiService from '@/services/api';
import { StudyPlan } from '@/types/api';
import { formatDate, formatMonthYear, getErrorMessage } from '@/utils/helpers';

const DAY_OPTIONS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const toDateKey = (value: string) => value.split('T')[0];

export default function PlannerGeneratorPage() {
  const { user } = useUser();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [existingPlans, setExistingPlans] = useState<StudyPlan[]>([]);
  const [selectedPlanIds, setSelectedPlanIds] = useState<string[]>([]);
  const [generatedPlans, setGeneratedPlans] = useState<StudyPlan[]>([]);

  const [examDate, setExamDate] = useState<string>(() =>
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  );
  const [studyDays, setStudyDays] = useState(10);
  const [hoursPerDay, setHoursPerDay] = useState(2);
  const [preferredStartTime, setPreferredStartTime] = useState('09:00');
  const [availableDays, setAvailableDays] = useState<string[]>(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']);
  const [learningStyle, setLearningStyle] = useState('visual');
  const [difficultyLevel, setDifficultyLevel] = useState('intermediate');

  const [calendarDate, setCalendarDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      if (!user?.id) {
        return;
      }

      try {
        const plans = await apiService.getStudyPlans(user.id);
        const notDonePlans = plans.filter((plan) => plan.status !== 'done');
        setExistingPlans(notDonePlans);
      } catch (err) {
        setError(getErrorMessage(err));
      }
    };

    void run();
  }, [user?.id]);

  const togglePlan = (planId: string, checked: boolean) => {
    if (checked) {
      if (!selectedPlanIds.includes(planId)) {
        setSelectedPlanIds((prev) => [...prev, planId]);
      }
      return;
    }

    setSelectedPlanIds((prev) => prev.filter((id) => id !== planId));
  };

  const toggleDay = (day: string, checked: boolean) => {
    if (checked) {
      if (!availableDays.includes(day)) {
        setAvailableDays((prev) => [...prev, day]);
      }
      return;
    }

    setAvailableDays((prev) => prev.filter((d) => d !== day));
  };

  const handleGenerate = async () => {
    if (!user?.id) {
      return;
    }

    if (selectedPlanIds.length === 0) {
      setError('Please select at least one not-done plan.');
      return;
    }

    if (availableDays.length === 0) {
      setError('Please select at least one available day.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await apiService.generatePersonalizedStudyPlan({
        user_id: user.id,
        plan_ids: selectedPlanIds,
        available_days: availableDays,
        study_days: Math.max(1, Math.min(120, studyDays)),
        hours_per_day: Math.max(0.5, Math.min(12, hoursPerDay)),
        preferred_start_time: preferredStartTime,
        exam_date: examDate,
        learning_style: learningStyle,
        difficulty_level: difficultyLevel,
      });

      setGeneratedPlans(result.generated_schedules || []);
      setSuccess(result.message || 'Timetable generated successfully.');
      if ((result.generated_schedules || []).length > 0) {
        const firstDate = toDateKey(result.generated_schedules[0].target_date);
        setSelectedDate(firstDate);
        setCalendarDate(new Date(result.generated_schedules[0].target_date));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const daysInMonth = useMemo(() => {
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: Array<Date | null> = [];

    for (let i = 0; i < firstDay.getDay(); i += 1) {
      days.push(null);
    }

    for (let day = 1; day <= lastDay.getDate(); day += 1) {
      days.push(new Date(year, month, day));
    }

    return days;
  }, [calendarDate]);

  const plansByDate = useMemo(() => {
    const grouped: Record<string, StudyPlan[]> = {};
    generatedPlans.forEach((plan) => {
      const dateKey = toDateKey(plan.target_date);
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(plan);
    });
    return grouped;
  }, [generatedPlans]);

  const selectedDatePlans = selectedDate ? plansByDate[selectedDate] || [] : [];

  return (
    <>
      <Head>
        <title>Plan Generator • Quiz Tutor</title>
      </Head>

      <SiteShell
        title="AI Timetable Generator"
        subtitle="Select not-done plans once, set your availability once, and generate one clear timetable calendar"
      >
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

        <SignedOut>
          <Card title="Authentication required" subtitle="Sign in to generate personalized study plans">
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
          {existingPlans.length === 0 ? (
            <Card title="No not-done plans" subtitle="Create a plan first in Planner, then generate timetable">
              <Link
                href="/planner"
                className="inline-block rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white hover:shadow-lg"
              >
                Go to Planner
              </Link>
            </Card>
          ) : (
            <>
              <Card title="Timetable Inputs" subtitle="One setup for all selected plans">
                <div className="grid gap-3 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Exam date</label>
                    <input
                      type="date"
                      value={examDate}
                      onChange={(event) => setExamDate(event.target.value)}
                      className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Study days</label>
                    <input
                      type="number"
                      min={1}
                      max={120}
                      value={studyDays}
                      onChange={(event) => setStudyDays(Math.max(1, Math.min(120, Number(event.target.value) || 1)))}
                      className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Hours per day</label>
                    <input
                      type="number"
                      min={0.5}
                      max={12}
                      step={0.5}
                      value={hoursPerDay}
                      onChange={(event) => setHoursPerDay(Math.max(0.5, Math.min(12, Number(event.target.value) || 1)))}
                      className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    />
                  </div>
                </div>

                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Preferred start time</label>
                    <input
                      type="time"
                      value={preferredStartTime}
                      onChange={(event) => setPreferredStartTime(event.target.value)}
                      className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Learning style</label>
                    <select
                      value={learningStyle}
                      onChange={(event) => setLearningStyle(event.target.value)}
                      className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    >
                      <option value="visual">Visual</option>
                      <option value="auditory">Auditory</option>
                      <option value="reading">Reading/Writing</option>
                      <option value="kinesthetic">Kinesthetic</option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-violet-100/90">Difficulty level</label>
                    <select
                      value={difficultyLevel}
                      onChange={(event) => setDifficultyLevel(event.target.value)}
                      className="w-full appearance-none rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 focus:border-violet-300/70 focus:outline-none focus:ring-2 focus:ring-violet-400/45"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                </div>

                <div className="mt-3">
                  <label className="mb-2 block text-sm font-semibold text-violet-100/90">Available days</label>
                  <div className="grid grid-cols-2 gap-2 rounded-xl border border-violet-300/20 bg-black/10 p-3 sm:grid-cols-4">
                    {DAY_OPTIONS.map((day) => (
                      <label key={day} className="flex items-center gap-2 text-violet-100/85">
                        <input
                          type="checkbox"
                          checked={availableDays.includes(day)}
                          onChange={(event) => toggleDay(day, event.target.checked)}
                          className="size-4 cursor-pointer"
                        />
                        <span className="text-sm">{day}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </Card>

              <Card title="Select Plans" subtitle="Only not-done plans are listed">
                <div className="space-y-2">
                  {existingPlans.map((plan) => (
                    <label key={plan.plan_id} className="flex items-start gap-3 rounded-lg border border-violet-300/20 bg-white/5 p-3">
                      <input
                        type="checkbox"
                        checked={selectedPlanIds.includes(plan.plan_id)}
                        onChange={(event) => togglePlan(plan.plan_id, event.target.checked)}
                        className="mt-1 size-4 cursor-pointer"
                      />
                      <span className="flex-1">
                        <span className="block font-semibold text-white">{plan.title}</span>
                        <span className="text-xs text-violet-100/65">
                          Target: {formatDate(plan.target_date)} | Status: {plan.status.replace('_', ' ')}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              </Card>

              <div className="flex flex-wrap gap-2">
                <Button onClick={handleGenerate} loading={loading}>
                  Generate Timetable ({selectedPlanIds.length} plans)
                </Button>
                <Link
                  href="/planner"
                  className="rounded-lg border border-violet-300/35 bg-white/10 px-4 py-2 text-sm font-semibold text-violet-100 hover:bg-white/15"
                >
                  Open Planner
                </Link>
              </div>

              {generatedPlans.length > 0 && (
                <Card
                  title="Generated Timetable (Calendar View)"
                  subtitle="AI allocated your selected plans into a date-wise timetable"
                >
                  <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
                    <div className="mb-4 flex items-center justify-between">
                      <button
                        onClick={() => setCalendarDate(new Date(calendarDate.getFullYear(), calendarDate.getMonth() - 1))}
                        className="rounded-lg border border-violet-300/30 bg-violet-500/20 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-violet-500/30"
                      >
                        {'<'} Prev
                      </button>
                      <h3 className="text-lg font-bold text-white">
                        {formatMonthYear(calendarDate)}
                      </h3>
                      <button
                        onClick={() => setCalendarDate(new Date(calendarDate.getFullYear(), calendarDate.getMonth() + 1))}
                        className="rounded-lg border border-violet-300/30 bg-violet-500/20 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-violet-500/30"
                      >
                        Next {'>'}
                      </button>
                    </div>

                    <div className="mb-2 grid grid-cols-7 gap-2">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                        <div key={day} className="text-center text-xs font-semibold text-violet-100/75">
                          {day}
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-7 gap-2">
                      {daysInMonth.map((day, idx) => {
                        if (!day) {
                          return <div key={`empty-${idx}`} className="min-h-24 rounded-lg" />;
                        }

                        const dateKey = day.toISOString().split('T')[0];
                        const dayPlans = plansByDate[dateKey] || [];
                        const isSelected = selectedDate === dateKey;

                        return (
                          <button
                            key={dateKey}
                            onClick={() => setSelectedDate(dateKey)}
                            className={`min-h-24 rounded-lg border p-2 text-left text-xs transition-colors ${
                              isSelected
                                ? 'border-violet-300/70 bg-violet-500/25'
                                : 'border-violet-300/15 bg-white/5 hover:bg-white/10'
                            }`}
                          >
                            <p className="font-semibold text-violet-100">{day.getDate()}</p>
                            {dayPlans.slice(0, 2).map((plan) => (
                              <div
                                key={plan.plan_id}
                                className="mt-1 rounded border border-violet-300/30 bg-violet-500/20 px-1 py-0.5 text-[10px] font-semibold text-violet-100"
                              >
                                {(plan.source_plan_title || plan.title).slice(0, 16)}
                              </div>
                            ))}
                            {dayPlans.length > 2 && <p className="mt-1 text-[10px] text-violet-100/60">+{dayPlans.length - 2} more</p>}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {selectedDate && (
                    <div className="mt-4 rounded-xl border border-violet-300/20 bg-black/15 p-4">
                      <h4 className="mb-3 text-base font-bold text-white">Sessions for {formatDate(selectedDate)}</h4>
                      {selectedDatePlans.length === 0 ? (
                        <p className="text-sm text-violet-100/70">No sessions on this day.</p>
                      ) : (
                        <div className="space-y-2">
                          {selectedDatePlans.map((plan) => (
                            <div key={plan.plan_id} className="rounded-lg border border-violet-300/20 bg-white/5 p-3">
                              <p className="font-semibold text-white">{plan.title}</p>
                              <p className="text-sm text-violet-100/80">
                                Time: {plan.start_time || '--:--'} - {plan.end_time || '--:--'}
                              </p>
                              {plan.source_plan_title && (
                                <p className="text-sm text-violet-100/75">Reference plan: {plan.source_plan_title}</p>
                              )}
                              {plan.notes && <p className="text-sm text-violet-100/70">{plan.notes}</p>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              )}
            </>
          )}
        </SignedIn>
      </SiteShell>
    </>
  );
}