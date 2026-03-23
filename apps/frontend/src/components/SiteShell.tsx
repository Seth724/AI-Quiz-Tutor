'use client';

import Link from 'next/link';
import { useRouter } from 'next/router';
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs';
import { useState } from 'react';
import CursorTrail from './CursorTrail';
import { OrbitalCoreScene } from './OrbitalCoreScene';

interface SiteShellProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showHeaderText?: boolean;
  showAmbientModel?: boolean;
}

const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/documents', label: 'Documents' },
  { href: '/quiz', label: 'Quiz' },
  { href: '/chat', label: 'Chat' },
  { href: '/planner', label: 'Planner' },
  { href: '/planner-generator', label: 'Plan Generator' },
];

export const SiteShell: React.FC<SiteShellProps> = ({
  children,
  title,
  subtitle,
  showHeaderText = true,
  showAmbientModel = true,
}) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const router = useRouter();

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-[#070311] text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 top-12 h-72 w-72 rounded-full bg-fuchsia-600/30 blur-3xl" />
        <div className="absolute right-0 top-64 h-96 w-96 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-indigo-500/20 blur-3xl" />

        {showAmbientModel && (
          <>
            <div className="float-wave-slow absolute right-[-8%] top-[8%] hidden h-[500px] w-[680px] opacity-65 mix-blend-screen [mask-image:radial-gradient(ellipse_at_center,black_46%,transparent_78%)] lg:block">
              <OrbitalCoreScene className="h-full w-full" density="ambient" />
            </div>

            <div className="float-wave-fast absolute bottom-[-120px] left-[-7%] hidden h-[430px] w-[590px] opacity-56 mix-blend-screen [mask-image:radial-gradient(ellipse_at_center,black_44%,transparent_76%)] xl:block">
              <OrbitalCoreScene className="h-full w-full" density="ambient" />
            </div>

            <div className="absolute left-[30%] top-[12%] hidden h-[300px] w-[430px] opacity-33 mix-blend-screen [mask-image:radial-gradient(ellipse_at_center,black_45%,transparent_77%)] 2xl:block">
              <OrbitalCoreScene className="h-full w-full" density="ambient" />
            </div>
          </>
        )}
      </div>

      <CursorTrail />

      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#120a26]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:px-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <span className="rounded-md bg-gradient-to-r from-fuchsia-500 to-violet-500 px-2 py-1 text-xs font-bold uppercase tracking-[0.2em] text-white">
              QT
            </span>
            <span className="text-base font-semibold tracking-wide text-white/95 md:text-lg">Quiz Tutor</span>
          </Link>

          <nav className="hidden items-center gap-2 md:flex">
            {NAV_LINKS.map((link) => {
              const active = router.pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    active
                      ? 'bg-violet-500/35 text-white ring-1 ring-violet-300/50'
                      : 'text-white/75 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="rounded-full border border-white/30 px-4 py-2 text-sm font-semibold text-white/90 hover:bg-white/10">
                  Sign in
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-violet-600/30">
                  Sign up
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>

          <button
            className="rounded-md border border-white/20 px-3 py-2 text-sm font-semibold text-white md:hidden"
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-label="Toggle menu"
          >
            Menu
          </button>
        </div>

        {menuOpen && (
          <div className="border-t border-white/10 bg-[#120a26]/95 px-4 py-3 md:hidden">
            <div className="flex flex-col gap-2">
              {NAV_LINKS.map((link) => {
                const active = router.pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMenuOpen(false)}
                    className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                      active ? 'bg-violet-500/30 text-white' : 'text-white/80 hover:bg-white/10'
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="rounded-lg border border-white/30 px-4 py-2 text-sm font-semibold text-white/90">Sign in</button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white">
                    Sign up
                  </button>
                </SignUpButton>
              </SignedOut>
            </div>
          </div>
        )}
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col px-4 pb-16 pt-10 md:px-8">
        {showHeaderText && title && (
          <div className="mb-10 rounded-3xl border border-violet-200/20 bg-white/5 p-7 backdrop-blur-xl md:p-8">
            <div>
              <h1 className="text-3xl font-bold leading-tight text-white md:text-4xl">{title}</h1>
              {subtitle && <p className="mt-2 max-w-3xl text-sm text-white/75 md:text-base">{subtitle}</p>}
            </div>
          </div>
        )}
        {children}
      </main>

      <footer className="relative z-10 border-t border-white/10 bg-[#120a26]/65 px-4 py-8 text-sm text-white/70 md:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <p>Quiz Tutor • Personalized revision from your PDFs</p>
          <p>Built for students with AI quizzes, chat memory, and study planning.</p>
        </div>
      </footer>
    </div>
  );
};
