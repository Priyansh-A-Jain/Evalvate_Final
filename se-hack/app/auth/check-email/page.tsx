import { AuthFrame } from "@/components/auth/AuthFrame";
import { CheckEmailClient } from "./CheckEmailClient";

export default async function CheckEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email } = await searchParams;
  return (
    <AuthFrame
      eyebrow="Almost there"
      title="Check your email"
      description="Open the verification link we sent you. It expires after 24 hours."
    >
      <CheckEmailClient initialEmail={email} />
    </AuthFrame>
  );
}
