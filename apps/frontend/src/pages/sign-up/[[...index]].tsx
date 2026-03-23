import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#070311] p-4">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(168,85,247,0.22),transparent_40%),radial-gradient(circle_at_80%_30%,rgba(99,102,241,0.2),transparent_45%)]" />
      <div className="relative flex min-h-screen items-center justify-center">
        <SignUp path="/sign-up" routing="path" signInUrl="/sign-in" />
      </div>
    </div>
  );
}
