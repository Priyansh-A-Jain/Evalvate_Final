"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { TID } from "@/constants/landingTestIds";
import Nav from "@/components/landing/Nav";
import SceneCurtain from "@/components/landing/SceneCurtain";
import ScenePinned from "@/components/landing/ScenePinned";
import SceneReveal from "@/components/landing/SceneReveal";
import ProductShowcase from "@/components/landing/ProductShowcase";
import FinalCTA from "@/components/landing/FinalCTA";

import CustomCursor from "@/components/CustomCursor";
import "./landing.css";

gsap.registerPlugin(ScrollTrigger);

export default function LandingClient() {
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize Lenis
    const lenis = new Lenis({
      duration: 1.4,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    // Initialize GSAP progress bar
    const ctx = gsap.context(() => {
      gsap.to(progressRef.current, {
        scaleX: 1,
        ease: "none",
        scrollTrigger: {
          trigger: document.body,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.2,
        },
      });
    });

    return () => {
      lenis.destroy();
      ctx.revert();
    };
  }, []);

  return (
    <div className="landing-page">
      <CustomCursor />
      <div className="grain" />
      <main className="relative bg-[#050505] text-white">
        <div className="fixed top-0 left-0 right-0 h-[2px] z-[200] bg-white/5">
          <div ref={progressRef} className="h-full bg-gradient-to-r from-amber-500 via-amber-400 to-amber-300 origin-left scale-x-0" />
        </div>
        <Nav />
        <SceneCurtain />
        <ScenePinned
          testId={TID.scene2Section}
          image="/scenes/scene2_waiting_room.png"
          eyebrow="01 - The Waiting"
          lines={[
            { id: TID.scene2Line1, text: "Every interview begins" },
            { id: TID.scene2Line1 + "-b", text: "before you enter the room.", accent: true },
            { id: TID.scene2Line2, text: "Nervousness is certain." },
            { id: TID.scene2Line3, text: "Everyone prepares." },
            { id: TID.scene2Line4, text: "But preparation alone isn't enough.", emphasize: true },
          ]}
          align="left"
        />
        <ScenePinned
          testId={TID.scene3Section}
          image="/scenes/scene3_hands.png"
          eyebrow="02 - The Detail"
          lines={[
            { id: TID.scene3Line1, text: "Knowing the answer isn't enough." },
            { id: TID.scene3Line2, text: "The way you speak matters." },
            { id: TID.scene3Line3, text: "The way you present yourself matters." },
            { id: TID.scene3Line4, text: "Confidence is visible.", accent: true, emphasize: true },
          ]}
          align="right"
          imageScale={1.15}
        />
        <ScenePinned
          testId={TID.scene4Section}
          image="/scenes/scene4_walk.png"
          eyebrow="03 - The Threshold"
          lines={[
            { id: TID.scene4Line1, text: "The moment always arrives." },
            { id: TID.scene4Line2, text: "Will you be ready?", accent: true, emphasize: true, large: true },
          ]}
          align="center"
          tall
        />
        <SceneReveal />
        <ProductShowcase />
        <FinalCTA />

      </main>
    </div>
  );
}
