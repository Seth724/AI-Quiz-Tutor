import React, { useState, useMemo } from 'react';
import { StudyPlan, StudyActivity } from '@/types/api';
import { formatDate, formatMonthYear } from '@/utils/helpers';
import { Button } from './Button';

interface StudyPlanCalendarProps {
  plans: StudyPlan[];
  onToggleStatus: (plan: StudyPlan) => void;
  onToggleActivity: (plan: StudyPlan, activity: StudyActivity) => void;
  onDeletePlan: (planId: string) => void;
  loading: boolean;
}

export default function StudyPlanCalendar({
  plans,
  onToggleStatus,
  onToggleActivity,
  onDeletePlan,
  loading,
}: StudyPlanCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  // Get all days in the current month
  const daysInMonth = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysArray = [];

    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay.getDay(); i++) {
      daysArray.push(null);
    }

    // Add all days of the month
    for (let day = 1; day <= lastDay.getDate(); day++) {
      daysArray.push(new Date(year, month, day));
    }

    return daysArray;
  }, [currentDate]);

  // Group plans by date
  const plansByDate = useMemo(() => {
    const grouped: { [key: string]: StudyPlan[] } = {};
    plans.forEach((plan) => {
      const date = plan.target_date.split('T')[0]; // YYYY-MM-DD
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(plan);
    });
    return grouped;
  }, [plans]);

  const getPlansForDate = (date: Date | null) => {
    if (!date) return [];
    const dateStr = date.toISOString().split('T')[0];
    return plansByDate[dateStr] || [];
  };

  const getPlanColor = (status: string) => {
    switch (status) {
      case 'done':
        return 'border-emerald-300/40 bg-emerald-500/15 text-emerald-100';
      case 'in_progress':
        return 'border-amber-300/40 bg-amber-500/15 text-amber-100';
      case 'pending':
        return 'border-violet-300/40 bg-violet-500/20 text-violet-100';
      default:
        return 'border-violet-300/40 bg-violet-500/20 text-violet-100';
    }
  };

  const getNextAction = (status: string): { label: string; variant: 'success' | 'warning' | 'primary' } => {
    if (status === 'pending' || status === 'todo') {
      return { label: 'Mark In Progress', variant: 'primary' };
    }
    if (status === 'in_progress') {
      return { label: 'Mark Done', variant: 'success' };
    }
    return { label: 'Mark Todo', variant: 'warning' };
  };

  const selectedDatePlans = selectedDate ? plansByDate[selectedDate] || [] : [];

  return (
    <div className="space-y-4">
      {/* Calendar Header */}
      <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
            className="rounded-lg border border-violet-300/30 bg-violet-500/20 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-violet-500/30"
          >
            ← Prev
          </button>
          <h3 className="text-lg font-bold text-white">
            {formatMonthYear(currentDate)}
          </h3>
          <button
            onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
            className="rounded-lg border border-violet-300/30 bg-violet-500/20 px-3 py-2 text-sm font-semibold text-violet-100 hover:bg-violet-500/30"
          >
            Next →
          </button>
        </div>

        {/* Weekday headers */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-center text-xs font-semibold text-violet-100/75">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="grid grid-cols-7 gap-2">
          {daysInMonth.map((date, idx) => {
            const dateStr = date ? date.toISOString().split('T')[0] : null;
            const dayPlans = date ? getPlansForDate(date) : [];
            const isSelected = dateStr === selectedDate;
            const isToday =
              date &&
              date.toDateString() === new Date().toDateString();

            return (
              <div
                key={idx}
                onClick={() => date && setSelectedDate(dateStr)}
                className={`relative min-h-24 cursor-pointer rounded-lg border p-2 text-xs transition-colors ${
                  date
                    ? isSelected
                      ? 'border-violet-300/70 bg-violet-500/25'
                      : isToday
                      ? 'border-amber-300/40 bg-amber-500/10'
                      : 'border-violet-300/15 bg-white/5 hover:bg-white/10'
                    : 'bg-transparent'
                }`}
              >
                {date && (
                  <>
                    <p className={`font-semibold ${isToday ? 'text-amber-100' : 'text-violet-100'}`}>
                      {date.getDate()}
                    </p>
                    {dayPlans.length > 0 && (
                      <div className="mt-1 space-y-1">
                        {dayPlans.map((plan) => (
                          <div
                            key={plan.plan_id}
                            className={`rounded px-1 py-0.5 text-xs font-semibold ${getPlanColor(plan.status)}`}
                          >
                            {plan.title.length > 12 ? `${plan.title.substring(0, 12)}...` : plan.title}
                          </div>
                        ))}
                        {dayPlans.length > 2 && (
                          <p className="text-xs text-violet-100/60">+{dayPlans.length - 2} more</p>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Date Details */}
      {selectedDate && selectedDatePlans.length > 0 && (
        <div className="rounded-xl border border-violet-300/25 bg-white/10 p-4">
          <h3 className="mb-4 text-lg font-bold text-white">
            Plans for {formatDate(selectedDate)}
          </h3>

          <div className="space-y-4">
            {selectedDatePlans.map((plan) => {
              const action = getNextAction(plan.status);

              return (
                <div
                  key={plan.plan_id}
                  className={`rounded-lg border p-4 ${getPlanColor(plan.status)}`}
                >
                {/* Plan header */}
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <p className="font-bold text-white">{plan.title}</p>
                    {plan.start_time && plan.end_time && (
                      <p className="text-sm font-semibold text-white/85">
                        {plan.start_time} - {plan.end_time} ({plan.duration_minutes || 0} min)
                      </p>
                    )}
                    {plan.document_title && (
                      <p className="text-sm text-white/75">Document: {plan.document_title}</p>
                    )}
                    {plan.notes && (
                      <p className="mt-1 text-sm text-white/75">Notes: {plan.notes}</p>
                    )}
                  </div>

                  {/* Status badge */}
                  <span
                    className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold ${getPlanColor(
                      plan.status
                    )}`}
                  >
                    {plan.status.replace('_', ' ')}
                  </span>
                </div>

                {/* Activities */}
                {plan.activities && plan.activities.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-sm font-semibold text-white">Activities:</p>
                    {plan.activities.map((activity) => (
                      <div
                        key={activity.id || activity.name}
                        className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 p-2"
                      >
                        <input
                          type="checkbox"
                          checked={activity.status === 'done'}
                          onChange={() => onToggleActivity(plan, activity)}
                          disabled={loading}
                          className="size-4 cursor-pointer"
                        />
                        <div className="flex-1">
                          <p
                            className={`text-sm font-medium ${
                              activity.status === 'done'
                                ? 'line-through text-white/50'
                                : 'text-white'
                            }`}
                          >
                            {activity.name} ({activity.duration_minutes} min)
                          </p>
                          {activity.notes && (
                            <p className="text-xs text-white/50">{activity.notes}</p>
                          )}
                        </div>
                        <span
                          className={`text-xs font-semibold px-2 py-1 rounded ${
                            activity.status === 'done'
                              ? 'bg-emerald-500/20 text-emerald-100'
                              : activity.status === 'in_progress'
                              ? 'bg-amber-500/20 text-amber-100'
                              : 'bg-violet-500/20 text-violet-100'
                          }`}
                        >
                          {activity.status.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Plan actions */}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    size="small"
                    variant={action.variant}
                    onClick={() => onToggleStatus(plan)}
                    loading={loading}
                  >
                    {action.label}
                  </Button>
                  <Button
                    size="small"
                    variant="error"
                    onClick={() => onDeletePlan(plan.plan_id)}
                    loading={loading}
                  >
                    Delete
                  </Button>
                </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedDate && selectedDatePlans.length === 0 && (
        <div className="rounded-xl border border-violet-300/15 bg-white/5 p-4 text-center text-violet-100/75">
          No plans scheduled for {formatDate(selectedDate)}
        </div>
      )}
    </div>
  );
}
