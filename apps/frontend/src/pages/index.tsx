import Head from 'next/head';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { SignedIn, SignedOut, SignInButton, SignUpButton } from '@clerk/nextjs';

import { SiteShell, ThreeHeroScene } from '@/components';

const FEATURES = [
  {
    title: 'Ask from your PDFs',
    body: 'Chat with your own study material and get grounded answers with confidence sources.',
  },
  {
    title: 'Memory-Powered Assistant',
    body: 'The assistant remembers your profile and can answer progress, weak-area, and strategy questions.',
  },
  {
    title: 'Smart Quiz Engine',
    body: 'Generate MCQ or short-answer quizzes with detailed explanations and attempt tracking.',
  },
  {
    title: 'Study Planner + Reminders',
    body: 'Set exam deadlines, track pending tasks, and receive in-app or email reminders.',
  },
];

export default function LandingPage() {
  return (
    <>
      <Head>
        <title>Quiz Tutor • AI Study Platform</title>
        <meta
          name="description"
          content="Quiz Tutor helps students revise faster with PDF RAG chat, personalized AI memory, quizzes, and study planning."
        />
      </Head>

      <SiteShell showHeaderText={false} showAmbientModel={false}>
        <section className="relative isolate -mx-4 -mt-10 min-h-[78vh] overflow-hidden px-6 py-16 md:-mx-8 md:px-10 md:py-20 lg:px-14 lg:py-24">
          <div className="pointer-events-none absolute inset-0 opacity-95">
            <ThreeHeroScene className="h-full w-full" density="hero" />
          </div>
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(17,10,32,0.08),rgba(7,3,17,0.8)_45%),linear-gradient(135deg,rgba(40,16,70,0.3),rgba(15,8,36,0.58))]" />
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_84%_12%,rgba(238,130,238,0.22),transparent_45%)]" />

          <motion.div
            initial={{ opacity: 0, y: 22 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: 'easeOut' }}
            className="relative z-10 mx-auto max-w-5xl space-y-8"
          >
            <div className="inline-flex items-center rounded-full border border-violet-300/30 bg-violet-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-violet-100">
              Built for Students
            </div>

            <h1 className="max-w-4xl text-4xl font-black leading-tight text-white md:text-6xl">
              Turn PDFs into a
              <span className="bg-gradient-to-r from-fuchsia-300 via-violet-300 to-indigo-200 bg-clip-text text-transparent">
                {' '}
                Personal AI Study Coach
              </span>
            </h1>

            <p className="max-w-3xl text-base leading-relaxed text-white/85 md:text-xl">
              Upload notes once, ask focused questions, chat with memory, generate quizzes, and plan your revision with
              deadlines. The flow is simple, fast, and built for exam prep.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="rounded-xl bg-gradient-to-r from-fuchsia-500 to-violet-500 px-6 py-3 text-sm font-bold text-white shadow-xl shadow-violet-700/30 transition hover:translate-y-[-1px]">
                    Start Free
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="rounded-xl border border-white/30 bg-white/5 px-6 py-3 text-sm font-bold text-white/90 transition hover:bg-white/10">
                    Create Account
                  </button>
                </SignUpButton>
              </SignedOut>

              <SignedIn>
                <Link
                  href="/documents"
                  className="rounded-xl bg-gradient-to-r from-fuchsia-500 to-violet-500 px-6 py-3 text-sm font-bold text-white shadow-xl shadow-violet-700/30 transition hover:translate-y-[-1px]"
                >
                  Open Documents
                </Link>
                <Link
                  href="/chat"
                  className="rounded-xl border border-white/30 bg-white/5 px-6 py-3 text-sm font-bold text-white/90 transition hover:bg-white/10"
                >
                  Open Chat
                </Link>
              </SignedIn>
            </div>

            <div className="grid max-w-3xl gap-3 text-sm text-white/80 sm:grid-cols-3">
              <div className="rounded-xl border border-white/15 bg-white/10 p-3">Upload PDFs</div>
              <div className="rounded-xl border border-white/15 bg-white/10 p-3">Ask + Quiz + Revise</div>
              <div className="rounded-xl border border-white/15 bg-white/10 p-3">Plan exam deadlines</div>
            </div>
          </motion.div>
        </section>

        <section className="mt-20 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {FEATURES.map((item, index) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.45, delay: index * 0.08 }}
              className="rounded-2xl border border-violet-200/15 bg-gradient-to-b from-white/10 to-white/5 p-6"
            >
              <h3 className="text-lg font-bold text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/75">{item.body}</p>
            </motion.div>
          ))}
        </section>

        <section className="mt-20 grid gap-6 rounded-3xl border border-violet-200/15 bg-gradient-to-r from-violet-900/35 to-fuchsia-900/25 p-6 md:grid-cols-3 md:p-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-200">01</p>
            <h4 className="mt-2 text-xl font-bold text-white">Upload once</h4>
            <p className="mt-2 text-sm text-white/75">Go to Documents and upload your PDF. Processing runs in the background.</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-200">02</p>
            <h4 className="mt-2 text-xl font-bold text-white">Revise deeply</h4>
            <p className="mt-2 text-sm text-white/75">Open Chat to ask from PDF or talk with the memory-enabled assistant.</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-200">03</p>
            <h4 className="mt-2 text-xl font-bold text-white">Finish on time</h4>
            <p className="mt-2 text-sm text-white/75">Use Planner to set target dates, mark done, and follow reminders.</p>
          </div>
        </section>
      </SiteShell>
    </>
  );
}
