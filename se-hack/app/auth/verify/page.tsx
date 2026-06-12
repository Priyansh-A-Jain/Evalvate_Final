import { AuthFrame } from "@/components/auth/AuthFrame";
import { VerifyClient } from "./VerifyClient";

export default async function VerifyPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  return (
    <AuthFrame
      eyebrow="Email verification"
      title="Verify your email"
      description="Your link is checked once and then exchanged for a secure session."
    >
      <VerifyClient token={token} />
    </AuthFrame>
  );
}
