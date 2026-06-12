import { AuthFrame } from "@/components/auth/AuthFrame";
import { LoginForm } from "./LoginForm";

function safeRedirect(value: string | undefined) {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const { redirect } = await searchParams;
  return (
    <AuthFrame
      eyebrow="Welcome back"
      title="Sign in"
      description="Continue your interview practice and pick up where you left off."
    >
      <LoginForm redirectPath={safeRedirect(redirect)} />
    </AuthFrame>
  );
}
