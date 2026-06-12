import { AuthFrame } from "@/components/auth/AuthFrame";
import { SignupForm } from "./SignupForm";

function safeRedirect(value: string | undefined) {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const { redirect } = await searchParams;
  return (
    <AuthFrame
      eyebrow="Start practicing"
      title="Create account"
      description="Use email and password, or sign in with Google from the login page."
    >
      <SignupForm redirectPath={safeRedirect(redirect)} />
    </AuthFrame>
  );
}
