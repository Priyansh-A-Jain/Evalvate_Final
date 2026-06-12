import Link from "next/link";

type AuthFrameProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
};

export function AuthFrame({
  eyebrow,
  title,
  description,
  children,
  footer,
}: AuthFrameProps) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[var(--background)] px-4 py-12 text-[var(--foreground)]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 top-10 h-80 w-80 rounded-full bg-[var(--accent-primary)]/10 blur-[110px]" />
        <div className="absolute -right-20 bottom-0 h-96 w-96 rounded-full bg-[var(--accent-secondary)]/10 blur-[120px]" />
      </div>
      <section className="relative w-full max-w-md border border-[var(--border-default)] bg-[var(--surface-primary)]/90 p-7 shadow-2xl backdrop-blur-xl sm:p-9">
        <Link href="/" className="text-sm font-bold tracking-tight text-[var(--text-primary)]">
          Evalvate
        </Link>
        <p className="mt-8 text-xs font-semibold uppercase tracking-[0.22em] text-[var(--accent-primary)]">
          {eyebrow}
        </p>
        <h1 className="mt-3 font-serif text-4xl text-[var(--text-primary)]">{title}</h1>
        <p className="mt-3 text-sm leading-6 text-[var(--text-secondary)]">{description}</p>
        <div className="mt-7">{children}</div>
        {footer ? (
          <div className="mt-7 border-t border-[var(--border-subtle)] pt-5 text-center text-sm text-[var(--text-secondary)]">
            {footer}
          </div>
        ) : null}
      </section>
    </main>
  );
}
