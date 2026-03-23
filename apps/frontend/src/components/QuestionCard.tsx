'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { QuizQuestion } from '@/types/api';

interface QuestionCardProps {
  question: QuizQuestion;
  index: number;
  onAnswer?: (answer: string) => void;
  selectedAnswer?: string;
  showCorrect?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  index,
  onAnswer,
  selectedAnswer,
  showCorrect = false,
}) => {
  const [draftAnswer, setDraftAnswer] = useState(selectedAnswer || '');
  const hasOptions = useMemo(() => (question.options || []).length > 0, [question.options]);

  useEffect(() => {
    // Keep textarea draft in sync when parent-selected answer changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDraftAnswer(selectedAnswer || '');
  }, [selectedAnswer]);

  return (
    <div className="mb-6 rounded-2xl border border-violet-300/20 bg-white/10 p-6 shadow-xl shadow-violet-950/25 backdrop-blur-sm">
      <div className="mb-4">
        <span className="rounded-full border border-violet-300/35 bg-violet-500/20 px-3 py-1 text-xs font-semibold text-violet-100">
          Question {index + 1}
        </span>
        <h3 className="mt-3 text-lg font-bold text-white">{question.question}</h3>
      </div>

      {hasOptions ? (
        <div className="space-y-3">
          {(question.options || []).map((option, optionIndex) => {
            const isSelected = selectedAnswer === option;
            const isCorrect = option === question.correct_answer;
            const showAsCorrect = showCorrect && isCorrect;
            const showAsIncorrect = showCorrect && isSelected && !isCorrect;

            let bgColor = 'bg-white/5 hover:bg-white/10';
            let borderColor = 'border-violet-300/20';

            if (showAsCorrect) {
              bgColor = 'bg-emerald-500/15';
              borderColor = 'border-emerald-300/50';
            } else if (showAsIncorrect) {
              bgColor = 'bg-rose-500/15';
              borderColor = 'border-rose-300/50';
            } else if (isSelected) {
              bgColor = 'bg-violet-500/20';
              borderColor = 'border-violet-300/50';
            }

            return (
              <button
                key={optionIndex}
                onClick={() => onAnswer?.(option)}
                disabled={showCorrect || !onAnswer}
                className={`
                  w-full p-4 text-left border-2 rounded-lg transition-all
                  ${bgColor} ${borderColor}
                  disabled:cursor-default font-medium text-violet-50
                `}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`
                      w-5 h-5 rounded-full border-2 flex items-center justify-center
                      ${
                        showAsCorrect
                          ? 'border-green-500 bg-green-500'
                          : showAsIncorrect
                          ? 'border-red-500 bg-red-500'
                          : isSelected
                          ? 'border-violet-300 bg-violet-500'
                          : 'border-violet-200/40'
                      }
                    `}
                  >
                    {(showAsCorrect || (isSelected && !showCorrect)) && (
                      <span className="text-white text-sm">✓</span>
                    )}
                    {showAsIncorrect && <span className="text-white text-sm">✕</span>}
                  </div>
                  <span>{option}</span>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            rows={3}
            value={draftAnswer}
            onChange={(event) => setDraftAnswer(event.target.value)}
            disabled={showCorrect || !onAnswer}
            placeholder="Write your answer here..."
            className="w-full rounded-xl border border-violet-300/30 bg-[#180d33] p-3 text-violet-50 placeholder:text-violet-200/55 focus:border-violet-300 focus:outline-none"
          />
          {!showCorrect && onAnswer && (
            <button
              onClick={() => onAnswer(draftAnswer.trim())}
              disabled={!draftAnswer.trim()}
              className="rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2 font-semibold text-white disabled:opacity-50"
            >
              Save Answer
            </button>
          )}
          {showCorrect && (
            <div className="rounded-lg border border-emerald-300/45 bg-emerald-500/15 p-3">
              <p className="text-sm text-emerald-100">
                <strong>Reference answer:</strong> {question.correct_answer}
              </p>
            </div>
          )}
        </div>
      )}

      {question.explanation && showCorrect && (
        <div className="mt-4 rounded-lg border border-violet-300/30 bg-violet-500/15 p-3">
          <p className="text-sm text-violet-100">
            <strong>Explanation:</strong> {question.explanation}
          </p>
        </div>
      )}
    </div>
  );
};
