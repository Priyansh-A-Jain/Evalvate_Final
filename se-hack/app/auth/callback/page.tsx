import { AuthFrame } from "@/components/auth/AuthFrame";
import { CallbackClient } from "./CallbackClient";

export default async function AuthCallbackPage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string }>;
}) {
  const { code } = await searchParams;
  return (
    <AuthFrame
      eyebrow="Google sign-in"
      title="Finishing up"
      description="This one-time exchange keeps your session cookie on the Evalvate frontend."
    >
      <CallbackClient code={code} />
    </AuthFrame>
  );
}
