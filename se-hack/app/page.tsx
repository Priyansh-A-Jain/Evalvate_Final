import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import LandingClient from "@/components/landing/LandingClient";

export default async function Home() {
  const user = await getCurrentUser();

  if (user) {
    redirect("/dashboard");
  }

  return <LandingClient />;
}
