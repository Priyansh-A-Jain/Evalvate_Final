"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Legacy route — all interview starts go through /pre-interview now. */
export default function InterviewAgentRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/pre-interview");
  }, [router]);

  return null;
}
