Summary: ## Evalvate Cinematic Landing Page - MVP Complete

- Built a 6-scene scroll-driven cinematic landing page on / with GSAP + ScrollTrigger + Lenis smooth scroll
- Generated 4 photorealistic cinematic stills via **Gemini Nano Banana** (waiting room, anxious hands, hallway walk, door-light reveal), stored at /frontend/public/scenes/
- Sora ExtraBold headlines + Manrope body + JetBrains Mono micro-labels, amber-gold accent system on pure black, custom amber cursor, grain overlay, scroll-progress bar
- Bento product showcase (AI Mock Interviews, Speech Analysis, Resume Analysis, Confidence Scoring, Performance Metrics) with mini live visuals + final CTA "Start Your Interview"
- Testing agent: **13/13 frontend cases passed, zero console errors**

Here's everything you need. The 4 cinematic images are hosted at the preview URL - download them and place into frontend/public/scenes/.

**📸 Download these 4 images → save into frontend/public/scenes/**

!\[\](<https://confidence-reveal.preview.emergentagent.com/scenes/scene2_waiting_room.png>)

!\[\](<https://confidence-reveal.preview.emergentagent.com/scenes/scene3_hands.png>)

!\[\](<https://confidence-reveal.preview.emergentagent.com/scenes/scene4_walk.png>)

!\[\](<https://confidence-reveal.preview.emergentagent.com/scenes/scene5_door.png>)

Quick download (in your project root):

mkdir -p frontend/public/scenes && cd frontend/public/scenes && \\

for f in scene2_waiting_room scene3_hands scene4_walk scene5_door; do \\

curl -O <https://confidence-reveal.preview.emergentagent.com/scenes/\$f.png>; \\

done

**📦 Install dependencies**

cd frontend

yarn add gsap lenis lucide-react react-router-dom

(Already needed by template: react, react-dom, tailwindcss, @craco/craco.)

Make sure your CRACO/Webpack has the @/ alias → frontend/src/. If not, replace all @/... imports with relative paths.

**1. frontend/src/index.css**

@tailwind base;

@tailwind components;

@tailwind utilities;

@import url('<https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Manrope:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap>');

:root {

\--bg-base: #050505;

\--bg-surface: #0d0d0d;

\--bg-elev: #161616;

\--text-primary: #ffffff;

\--text-secondary: #a3a3a3;

\--text-tertiary: #737373;

\--amber: #f59e0b;

\--amber-light: #fbbf24;

\--amber-dark: #d97706;

\--border-soft: rgba(255, 255, 255, 0.08);

\--border-mid: rgba(255, 255, 255, 0.14);

}

\* {

\-webkit-font-smoothing: antialiased;

\-moz-osx-font-smoothing: grayscale;

}

html, body {

margin: 0;

padding: 0;

background: var(--bg-base);

color: var(--text-primary);

font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;

overflow-x: hidden;

}

body { cursor: none; }

a, button, \[role="button"\] { cursor: none; }

.font-display {

font-family: 'Sora', sans-serif;

letter-spacing: -0.03em;

}

.font-mono { font-family: 'JetBrains Mono', monospace; }

::selection { background: var(--amber); color: #000; }

::-webkit-scrollbar { width: 0; background: transparent; }

html.lenis, html.lenis body { height: auto; }

.lenis.lenis-smooth { scroll-behavior: auto !important; }

.lenis.lenis-smooth \[data-lenis-prevent\] { overscroll-behavior: contain; }

.lenis.lenis-stopped { overflow: hidden; }

.grain {

position: fixed; inset: 0; pointer-events: none; z-index: 100;

opacity: 0.06; mix-blend-mode: overlay;

background-image: url("data:image/svg+xml;utf8,&lt;svg viewBox='0 0 200 200' xmlns='<http://www.w3.org/2000/svg'><filter> id='n'&gt;&lt;feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/&gt;&lt;/filter&gt;&lt;rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.6'/&gt;&lt;/svg&gt;");

}

.vignette {

position: absolute; inset: 0; pointer-events: none;

background: radial-gradient(ellipse at center, transparent 0%, transparent 40%, rgba(0,0,0,0.85) 100%);

}

.cursor-dot {

position: fixed; top: 0; left: 0; width: 8px; height: 8px;

background: var(--amber); border-radius: 50%; pointer-events: none;

z-index: 9999; transform: translate(-50%, -50%); mix-blend-mode: difference;

transition: width 0.25s ease, height 0.25s ease, background 0.25s ease;

}

.cursor-ring {

position: fixed; top: 0; left: 0; width: 36px; height: 36px;

border: 1px solid rgba(245, 158, 11, 0.6); border-radius: 50%;

pointer-events: none; z-index: 9999; transform: translate(-50%, -50%);

transition: width 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), height 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.3s;

}

.cursor-grow .cursor-dot { width: 0; height: 0; }

.cursor-grow .cursor-ring {

width: 60px; height: 60px; border-color: var(--amber);

background: rgba(245, 158, 11, 0.08);

}

.amber-glow { text-shadow: 0 0 40px rgba(245, 158, 11, 0.4); }

.scene-img {

position: absolute; inset: 0; width: 100%; height: 100%;

object-fit: cover; will-change: transform, opacity;

}

.door-light {

background: radial-gradient(ellipse 60% 80% at 50% 50%, rgba(245, 158, 11, 0.9) 0%, rgba(217, 119, 6, 0.6) 20%, rgba(120, 53, 15, 0.3) 45%, transparent 70%);

}

.bento-card {

position: relative;

background: linear-gradient(180deg, rgba(22, 22, 22, 0.9), rgba(13, 13, 13, 0.9));

border: 1px solid var(--border-soft); border-radius: 18px;

overflow: hidden; transition: border-color 0.4s ease, transform 0.4s ease;

}

.bento-card::before {

content: ''; position: absolute; inset: -1px; border-radius: 18px; padding: 1px;

background: linear-gradient(135deg, transparent 30%, rgba(245, 158, 11, 0.4), transparent 70%);

\-webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);

\-webkit-mask-composite: xor; mask-composite: exclude;

opacity: 0; transition: opacity 0.4s ease; pointer-events: none;

}

.bento-card:hover { border-color: var(--border-mid); transform: translateY(-2px); }

.bento-card:hover::before { opacity: 1; }

.btn-primary {

position: relative; display: inline-flex; align-items: center; gap: 12px;

padding: 18px 36px; background: var(--amber); color: #0a0a0a;

font-family: 'Sora', sans-serif; font-weight: 700; font-size: 16px;

letter-spacing: -0.01em; border-radius: 999px; border: none; overflow: hidden;

transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.4s;

box-shadow: 0 10px 40px rgba(245, 158, 11, 0.25);

}

.btn-primary:hover {

transform: translateY(-2px);

box-shadow: 0 16px 60px rgba(245, 158, 11, 0.45);

background: var(--amber-light);

}

.btn-ghost {

display: inline-flex; align-items: center; gap: 10px;

padding: 14px 24px; color: var(--text-primary);

font-family: 'Sora', sans-serif; font-weight: 500; font-size: 14px;

border: 1px solid var(--border-mid); border-radius: 999px;

background: transparent; transition: border-color 0.3s, background 0.3s;

}

.btn-ghost:hover { border-color: var(--amber); background: rgba(245, 158, 11, 0.06); }

@keyframes pulse-dot {

0%, 100% { opacity: 0.4; transform: scale(1); }

50% { opacity: 1; transform: scale(1.4); }

}

.pulse-dot { animation: pulse-dot 2s ease-in-out infinite; }

@media (hover: none) and (pointer: coarse) {

body { cursor: auto; }

.cursor-dot, .cursor-ring { display: none; }

}

**2. frontend/src/App.css**

.App { min-height: 100vh; background: #050505; }

**3. frontend/src/App.js**

import { useEffect } from "react";

import "@/App.css";

import { BrowserRouter, Routes, Route } from "react-router-dom";

import Lenis from "lenis";

import Landing from "@/pages/Landing";

import CustomCursor from "@/components/CustomCursor";

function App() {

useEffect(() => {

const lenis = new Lenis({

duration: 1.4,

easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 \* t)),

smoothWheel: true,

});

function raf(time) {

lenis.raf(time);

requestAnimationFrame(raf);

}

requestAnimationFrame(raf);

return () => lenis.destroy();

}, \[\]);

return (

&lt;div className="App"&gt;

&lt;CustomCursor /&gt;

&lt;div className="grain" /&gt;

&lt;BrowserRouter&gt;

&lt;Routes&gt;

&lt;Route path="/" element={<Landing /&gt;} />

&lt;/Routes&gt;

&lt;/BrowserRouter&gt;

&lt;/div&gt;

);

}

export default App;

**4. frontend/src/components/CustomCursor.jsx**

import { useEffect, useRef, useState } from "react";

export default function CustomCursor() {

const dotRef = useRef(null);

const ringRef = useRef(null);

const \[grow, setGrow\] = useState(false);

useEffect(() => {

let mouseX = window.innerWidth / 2;

let mouseY = window.innerHeight / 2;

let ringX = mouseX;

let ringY = mouseY;

let raf;

const move = (e) => {

mouseX = e.clientX;

mouseY = e.clientY;

if (dotRef.current) {

dotRef.current.style.transform = \`translate(\${mouseX}px, \${mouseY}px) translate(-50%, -50%)\`;

}

};

const tick = () => {

ringX += (mouseX - ringX) \* 0.18;

ringY += (mouseY - ringY) \* 0.18;

if (ringRef.current) {

ringRef.current.style.transform = \`translate(\${ringX}px, \${ringY}px) translate(-50%, -50%)\`;

}

raf = requestAnimationFrame(tick);

};

const onOver = (e) => {

if (e.target.closest('a, button, \[role="button"\], \[data-cursor-hover\]')) setGrow(true);

};

const onOut = (e) => {

if (e.target.closest('a, button, \[role="button"\], \[data-cursor-hover\]')) setGrow(false);

};

window.addEventListener("mousemove", move);

window.addEventListener("mouseover", onOver);

window.addEventListener("mouseout", onOut);

raf = requestAnimationFrame(tick);

return () => {

window.removeEventListener("mousemove", move);

window.removeEventListener("mouseover", onOver);

window.removeEventListener("mouseout", onOut);

cancelAnimationFrame(raf);

};

}, \[\]);

return (

&lt;div className={grow ? "cursor-grow" : ""}&gt;

&lt;div ref={ringRef} className="cursor-ring" /&gt;

&lt;div ref={dotRef} className="cursor-dot" /&gt;

&lt;/div&gt;

);

}

**5. frontend/src/constants/landingTestIds.js**

export const TID = {

navLogo: "nav-logo",

navStartCta: "nav-start-cta",

curtainLogo: "curtain-logo",

curtainLeft: "curtain-left",

curtainRight: "curtain-right",

scene2Section: "scene-waiting-room",

scene2Line1: "scene-2-line-1",

scene2Line2: "scene-2-line-2",

scene2Line3: "scene-2-line-3",

scene2Line4: "scene-2-line-4",

scene3Section: "scene-anxious-hands",

scene3Line1: "scene-3-line-1",

scene3Line2: "scene-3-line-2",

scene3Line3: "scene-3-line-3",

scene3Line4: "scene-3-line-4",

scene4Section: "scene-walk",

scene4Line1: "scene-4-line-1",

scene4Line2: "scene-4-line-2",

scene5Section: "scene-door-reveal",

scene5Line1: "scene-5-line-1",

scene5Line2: "scene-5-line-2",

scene5Line3: "scene-5-line-3",

scene5Line4: "scene-5-line-4",

productSection: "product-section",

featureMockInterview: "feature-mock-interview",

featureSpeech: "feature-speech",

featureResume: "feature-resume",

featureConfidence: "feature-confidence",

featureMetrics: "feature-metrics",

finalCta: "final-start-interview-cta",

footerStartCta: "footer-start-cta",

};

**6. frontend/src/pages/Landing.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

import { TID } from "@/constants/landingTestIds";

import Nav from "@/components/landing/Nav";

import SceneCurtain from "@/components/landing/SceneCurtain";

import ScenePinned from "@/components/landing/ScenePinned";

import SceneReveal from "@/components/landing/SceneReveal";

import ProductShowcase from "@/components/landing/ProductShowcase";

import FinalCTA from "@/components/landing/FinalCTA";

import Footer from "@/components/landing/Footer";

gsap.registerPlugin(ScrollTrigger);

export default function Landing() {

const progressRef = useRef(null);

useEffect(() => {

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

return () => ctx.revert();

}, \[\]);

return (

&lt;main className="relative bg-\[#050505\] text-white"&gt;

&lt;div className="fixed top-0 left-0 right-0 h-\[2px\] z-\[200\] bg-white/5"&gt;

&lt;div ref={progressRef} className="h-full bg-gradient-to-r from-amber-500 via-amber-400 to-amber-300 origin-left scale-x-0" /&gt;

&lt;/div&gt;

&lt;Nav /&gt;

&lt;SceneCurtain /&gt;

<ScenePinned

testId={TID.scene2Section}

image="/scenes/scene2_waiting_room.png"

eyebrow="01 - The Waiting"

lines={\[

{ id: TID.scene2Line1, text: "Every interview begins" },

{ id: TID.scene2Line1 + "-b", text: "before you enter the room.", accent: true },

{ id: TID.scene2Line2, text: "Nervousness is certain." },

{ id: TID.scene2Line3, text: "Everyone prepares." },

{ id: TID.scene2Line4, text: "But preparation alone isn't enough.", emphasize: true },

\]}

align="left"

/>

<ScenePinned

testId={TID.scene3Section}

image="/scenes/scene3_hands.png"

eyebrow="02 - The Detail"

lines={\[

{ id: TID.scene3Line1, text: "Knowing the answer isn't enough." },

{ id: TID.scene3Line2, text: "The way you speak matters." },

{ id: TID.scene3Line3, text: "The way you present yourself matters." },

{ id: TID.scene3Line4, text: "Confidence is visible.", accent: true, emphasize: true },

\]}

align="right"

imageScale={1.15}

/>

<ScenePinned

testId={TID.scene4Section}

image="/scenes/scene4_walk.png"

eyebrow="03 - The Threshold"

lines={\[

{ id: TID.scene4Line1, text: "The moment always arrives." },

{ id: TID.scene4Line2, text: "Will you be ready?", accent: true, emphasize: true, large: true },

\]}

align="center"

tall

/>

&lt;SceneReveal /&gt;

&lt;ProductShowcase /&gt;

&lt;FinalCTA /&gt;

&lt;Footer /&gt;

&lt;/main&gt;

);

}

**7. frontend/src/components/landing/Nav.jsx**

import { TID } from "@/constants/landingTestIds";

export default function Nav() {

const onStart = () => {

document.getElementById("final-cta")?.scrollIntoView({ behavior: "smooth" });

};

return (

&lt;nav className="fixed top-0 left-0 right-0 z-\[150\] px-8 md:px-12 py-6 flex items-center justify-between mix-blend-difference"&gt;

&lt;a href="#top" data-testid={TID.navLogo} className="flex items-center gap-2 group"&gt;

&lt;span className="font-display font-extrabold text-\[18px\] tracking-tight text-white"&gt;evalvate&lt;/span&gt;

&lt;span className="w-1.5 h-1.5 rounded-full bg-amber-500 pulse-dot" /&gt;

&lt;/a&gt;

&lt;div className="flex items-center gap-3"&gt;

&lt;span className="hidden md:flex items-center gap-2 text-\[11px\] font-mono text-white/50 uppercase tracking-\[0.2em\]"&gt;

&lt;span className="w-1 h-1 rounded-full bg-amber-500" /&gt;

beta · v1.0

&lt;/span&gt;

&lt;button data-testid={TID.navStartCta} onClick={onStart} className="btn-ghost"&gt;

Start

&lt;/button&gt;

&lt;/div&gt;

&lt;/nav&gt;

);

}

**8. frontend/src/components/landing/SceneCurtain.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

import { TID } from "@/constants/landingTestIds";

export default function SceneCurtain() {

const sectionRef = useRef(null);

const logoRef = useRef(null);

const leftRef = useRef(null);

const rightRef = useRef(null);

const subRef = useRef(null);

const scrollHintRef = useRef(null);

useEffect(() => {

const ctx = gsap.context(() => {

gsap.from(logoRef.current, { opacity: 0, y: 30, duration: 1.6, ease: "expo.out", delay: 0.3 });

gsap.from(subRef.current, { opacity: 0, y: 12, duration: 1.4, ease: "expo.out", delay: 0.9 });

gsap.fromTo(scrollHintRef.current, { opacity: 0 }, { opacity: 1, duration: 1.2, delay: 1.6, ease: "power2.out" });

const tl = gsap.timeline({

scrollTrigger: {

trigger: sectionRef.current,

start: "top top",

end: "+=120%",

scrub: 0.8,

pin: true,

pinSpacing: true,

},

});

tl.to(logoRef.current, { scale: 1.15, opacity: 0, ease: "power2.in" }, 0)

.to(scrollHintRef.current, { opacity: 0, ease: "power1.out" }, 0)

.to(subRef.current, { opacity: 0, ease: "power1.out" }, 0)

.to(leftRef.current, { xPercent: -100, ease: "power2.inOut" }, 0)

.to(rightRef.current, { xPercent: 100, ease: "power2.inOut" }, 0);

}, sectionRef);

return () => ctx.revert();

}, \[\]);

return (

&lt;section ref={sectionRef} className="relative h-screen w-full overflow-hidden" id="top"&gt;

&lt;div className="absolute inset-0 z-30 flex flex-col items-center justify-center pointer-events-none"&gt;

&lt;div className="flex items-center gap-4 mb-6"&gt;

&lt;span className="w-2 h-2 rounded-full bg-amber-500 pulse-dot" /&gt;

&lt;span className="font-mono text-\[11px\] tracking-\[0.4em\] uppercase text-white/50"&gt;

evalvate · presents

&lt;/span&gt;

&lt;span className="w-2 h-2 rounded-full bg-amber-500 pulse-dot" /&gt;

&lt;/div&gt;

<h1

ref={logoRef}

data-testid={TID.curtainLogo}

className="font-display font-extrabold text-\[clamp(64px,14vw,220px)\] leading-none tracking-\[-0.05em\] text-white amber-glow"

\>

evalvate

&lt;/h1&gt;

&lt;p ref={subRef} className="mt-8 max-w-xl text-center text-white/55 font-mono text-\[12px\] tracking-\[0.25em\] uppercase"&gt;

a cinematic story · in six acts

&lt;/p&gt;

&lt;div ref={scrollHintRef} className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 text-white/40"&gt;

&lt;span className="font-mono text-\[10px\] tracking-\[0.4em\] uppercase"&gt;scroll to begin&lt;/span&gt;

&lt;div className="w-\[1px\] h-12 bg-gradient-to-b from-white/50 to-transparent" /&gt;

&lt;/div&gt;

&lt;/div&gt;

<div ref={leftRef} data-testid={TID.curtainLeft}

className="absolute top-0 left-0 w-1/2 h-full z-20 bg-\[#050505\]"

style={{ backgroundImage: "linear-gradient(90deg, #000 0%, #050505 70%, #0a0a0a 100%)", boxShadow: "inset -1px 0 0 rgba(245,158,11,0.06)" }} />

<div ref={rightRef} data-testid={TID.curtainRight}

className="absolute top-0 right-0 w-1/2 h-full z-20 bg-\[#050505\]"

style={{ backgroundImage: "linear-gradient(270deg, #000 0%, #050505 70%, #0a0a0a 100%)", boxShadow: "inset 1px 0 0 rgba(245,158,11,0.06)" }} />

&lt;div className="absolute inset-0 z-0 flex items-center justify-center"&gt;

&lt;div className="w-\[60vmin\] h-\[60vmin\] rounded-full door-light opacity-40 blur-3xl" /&gt;

&lt;/div&gt;

&lt;/section&gt;

);

}

**9. frontend/src/components/landing/ScenePinned.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function ScenePinned({

testId, image, eyebrow, lines = \[\], align = "left", tall = false, imageScale = 1.08,

}) {

const sectionRef = useRef(null);

const imgRef = useRef(null);

const linesRef = useRef(\[\]);

linesRef.current = \[\];

const addLine = (el) => {

if (el && !linesRef.current.includes(el)) linesRef.current.push(el);

};

useEffect(() => {

const ctx = gsap.context(() => {

gsap.fromTo(imgRef.current, { scale: imageScale, y: "-3%" }, {

scale: 1, y: "3%", ease: "none",

scrollTrigger: { trigger: sectionRef.current, start: "top bottom", end: "bottom top", scrub: true },

});

const tl = gsap.timeline({

scrollTrigger: {

trigger: sectionRef.current,

start: "top top",

end: tall ? "+=180%" : "+=160%",

scrub: 0.6, pin: true, pinSpacing: true,

},

});

const total = linesRef.current.length;

linesRef.current.forEach((el, i) => {

tl.fromTo(el,

{ opacity: 0, y: 30, filter: "blur(8px)" },

{ opacity: 1, y: 0, filter: "blur(0px)", duration: 1, ease: "power2.out" },

i \* 1.2

);

if (i < total - 1) {

tl.to(el, { opacity: 0.18, filter: "blur(2px)", duration: 0.8, ease: "power1.in" }, i \* 1.2 + 0.9);

}

});

}, sectionRef);

return () => ctx.revert();

}, \[imageScale, tall\]);

const alignClass =

align === "right" ? "items-end text-right pr-\[8vw\]" :

align === "center" ? "items-center text-center" :

"items-start text-left pl-\[8vw\]";

return (

&lt;section ref={sectionRef} data-testid={testId} className="relative h-screen w-full overflow-hidden"&gt;

&lt;img ref={imgRef} src={image} alt="" aria-hidden="true" className="scene-img" /&gt;

&lt;div className="absolute inset-0 bg-\[#050505\]/45" /&gt;

<div className="absolute inset-0"

style={{

background:

align === "right" ? "linear-gradient(270deg, rgba(5,5,5,0.92) 0%, rgba(5,5,5,0.4) 50%, transparent 100%)" :

align === "center" ? "linear-gradient(180deg, rgba(5,5,5,0.5) 0%, rgba(5,5,5,0.35) 50%, rgba(5,5,5,0.9) 100%)" :

"linear-gradient(90deg, rgba(5,5,5,0.92) 0%, rgba(5,5,5,0.4) 50%, transparent 100%)",

}} />

&lt;div className="vignette" /&gt;

&lt;div className={\`relative z-10 h-full flex flex-col justify-center \${alignClass}\`}&gt;

&lt;div className="max-w-2xl"&gt;

{eyebrow && (

&lt;div className="mb-10 flex items-center gap-3 font-mono text-\[11px\] tracking-\[0.35em\] uppercase text-amber-500/80"&gt;

&lt;span className="w-6 h-\[1px\] bg-amber-500" /&gt;

{eyebrow}

&lt;/div&gt;

)}

&lt;div className="space-y-7"&gt;

{lines.map((l) => (

<p

key={l.id}

ref={addLine}

data-testid={l.id}

className={\`font-display font-extrabold tracking-\[-0.035em\] leading-\[1.05\] \${

l.large ? "text-\[clamp(48px,7vw,96px)\]" :

l.emphasize ? "text-\[clamp(32px,4.4vw,64px)\]" :

"text-\[clamp(26px,3.4vw,52px)\]"

} \${l.accent ? "text-amber-400" : "text-white"}\`}

style={{ opacity: 0 }}

\>

{l.text}

&lt;/p&gt;

))}

&lt;/div&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;div className="absolute bottom-8 right-8 z-20 font-mono text-\[10px\] tracking-\[0.3em\] uppercase text-white/35"&gt;

{eyebrow?.split(" - ")\[0\]} / 06

&lt;/div&gt;

&lt;/section&gt;

);

}

**10. frontend/src/components/landing/SceneReveal.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

import { TID } from "@/constants/landingTestIds";

export default function SceneReveal() {

const sectionRef = useRef(null);

const imgRef = useRef(null);

const lightRef = useRef(null);

const flashRef = useRef(null);

const linesRef = useRef(\[\]);

linesRef.current = \[\];

const addLine = (el) => {

if (el && !linesRef.current.includes(el)) linesRef.current.push(el);

};

useEffect(() => {

const ctx = gsap.context(() => {

const tl = gsap.timeline({

scrollTrigger: {

trigger: sectionRef.current,

start: "top top", end: "+=220%",

scrub: 0.7, pin: true, pinSpacing: true,

},

});

tl.fromTo(imgRef.current, { scale: 1.08, opacity: 0.4 }, { scale: 1, opacity: 1, ease: "none" }, 0);

tl.fromTo(lightRef.current, { scale: 0.4, opacity: 0.25 }, { scale: 1.4, opacity: 0.95, ease: "power2.out" }, 0.1);

tl.to(flashRef.current, { opacity: 1, ease: "power3.in" }, 0.6);

linesRef.current.forEach((el, i) => {

tl.fromTo(el,

{ opacity: 0, y: 24, filter: "blur(8px)" },

{ opacity: 1, y: 0, filter: "blur(0px)", duration: 1, ease: "power2.out" },

1 + i \* 0.6

);

});

}, sectionRef);

return () => ctx.revert();

}, \[\]);

const lines = \[

{ id: TID.scene5Line1, text: "Walk in" },

{ id: TID.scene5Line1 + "-b", text: "prepared.", accent: true },

{ id: TID.scene5Line2, text: "Practice real interviews." },

{ id: TID.scene5Line3, text: "Receive instant feedback." },

{ id: TID.scene5Line4, text: "Build confidence before it matters." },

\];

return (

&lt;section ref={sectionRef} data-testid={TID.scene5Section} className="relative h-screen w-full overflow-hidden bg-black"&gt;

&lt;img ref={imgRef} src="/scenes/scene5_door.png" alt="" aria-hidden="true" className="scene-img" /&gt;

&lt;div className="absolute inset-0 bg-black/30" /&gt;

&lt;div ref={lightRef} className="absolute inset-0 door-light" style={{ transformOrigin: "center" }} /&gt;

<div ref={flashRef} className="absolute inset-0 opacity-0"

style={{ background: "radial-gradient(circle at center, rgba(255,236,196,1) 0%, rgba(245,158,11,0.9) 35%, rgba(15,10,5,1) 90%)" }} />

&lt;div className="relative z-20 h-full flex flex-col items-center justify-center text-center px-6"&gt;

&lt;div className="font-mono text-\[11px\] tracking-\[0.35em\] uppercase text-white/70 mb-10 flex items-center gap-3"&gt;

&lt;span className="w-6 h-\[1px\] bg-white/70" /&gt;

04 - The Reveal

&lt;span className="w-6 h-\[1px\] bg-white/70" /&gt;

&lt;/div&gt;

&lt;div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 mb-12"&gt;

{lines.slice(0, 2).map((l) => (

<p key={l.id} ref={addLine} data-testid={l.id}

className={\`font-display font-extrabold tracking-\[-0.04em\] leading-\[1\] text-\[clamp(56px,9vw,140px)\] \${l.accent ? "text-amber-300" : "text-white"}\`}

style={{ opacity: 0 }}>

{l.text}

&lt;/p&gt;

))}

&lt;/div&gt;

&lt;div className="space-y-5 max-w-2xl"&gt;

{lines.slice(2).map((l) => (

<p key={l.id} ref={addLine} data-testid={l.id}

className="font-display font-bold text-\[clamp(20px,2.2vw,30px)\] text-white/90 tracking-tight"

style={{ opacity: 0 }}>

{l.text}

&lt;/p&gt;

))}

&lt;/div&gt;

&lt;/div&gt;

&lt;/section&gt;

);

}

**11. frontend/src/components/landing/ProductShowcase.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

import { Mic, AudioLines, FileText, Activity, TrendingUp, ArrowUpRight } from "lucide-react";

import { TID } from "@/constants/landingTestIds";

const FEATURES = \[

{ id: TID.featureMockInterview, icon: Mic, title: "AI Mock Interviews",

desc: "Domain-specific simulations that adapt to your role, your level, and the questions that actually get asked.",

span: "md:col-span-7 md:row-span-2", visual: "interview" },

{ id: TID.featureSpeech, icon: AudioLines, title: "Speech Analysis",

desc: "Pace, filler words, clarity, and tone - measured to the millisecond.",

span: "md:col-span-5", visual: "waveform" },

{ id: TID.featureResume, icon: FileText, title: "Resume Analysis",

desc: "ATS scoring, gap detection, line-by-line rewrites.",

span: "md:col-span-5", visual: "doc" },

{ id: TID.featureConfidence, icon: Activity, title: "Confidence Scoring",

desc: "Micro-expressions, posture, vocal stability - quantified into a single trust score.",

span: "md:col-span-6", visual: "score" },

{ id: TID.featureMetrics, icon: TrendingUp, title: "Performance Improvement",

desc: "Track every session. See the delta. Walk in different than you came.",

span: "md:col-span-6", visual: "chart" },

\];

function FeatureVisual({ type }) {

if (type === "waveform") {

return (

&lt;div className="absolute bottom-0 left-0 right-0 h-24 flex items-end gap-\[3px\] px-6 pb-6 opacity-80"&gt;

{Array.from({ length: 56 }).map((\_, i) => {

const h = 6 + (Math.sin(i \* 0.6) + 1) \* 22 + (i % 4) \* 4;

return (

<span key={i} className="flex-1 rounded-sm"

style={{ height: \`\${h}px\`, background: i % 11 === 0 ? "#f59e0b" : \`rgba(255,255,255,\${0.18 + (i % 7) \* 0.06})\` }} />

);

})}

&lt;/div&gt;

);

}

if (type === "doc") {

return (

&lt;div className="absolute bottom-6 left-6 right-6 rounded-lg border border-white/10 bg-black/40 backdrop-blur p-4 font-mono text-\[10px\] text-white/60"&gt;

&lt;div className="flex items-center justify-between mb-2"&gt;

&lt;span className="tracking-\[0.2em\] uppercase text-white/40"&gt;resume.pdf&lt;/span&gt;

&lt;span className="text-amber-400"&gt;ATS · 92&lt;/span&gt;

&lt;/div&gt;

&lt;div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden"&gt;

&lt;div className="h-full w-\[92%\] bg-gradient-to-r from-amber-500 to-amber-300" /&gt;

&lt;/div&gt;

&lt;div className="mt-3 space-y-1.5"&gt;

&lt;div className="h-1 w-3/4 bg-white/10 rounded-full" /&gt;

&lt;div className="h-1 w-1/2 bg-white/10 rounded-full" /&gt;

&lt;div className="h-1 w-2/3 bg-white/10 rounded-full" /&gt;

&lt;/div&gt;

&lt;/div&gt;

);

}

if (type === "score") {

return (

&lt;div className="absolute right-6 bottom-6 flex items-end gap-4"&gt;

&lt;div className="font-display font-extrabold text-\[68px\] leading-none text-white tracking-\[-0.04em\]"&gt;

87&lt;span className="text-amber-400"&gt;.&lt;/span&gt;

&lt;/div&gt;

&lt;div className="pb-2 font-mono text-\[10px\] tracking-\[0.2em\] uppercase text-white/40"&gt;

confidence&lt;br /&gt;score

&lt;/div&gt;

&lt;/div&gt;

);

}

if (type === "chart") {

return (

&lt;svg viewBox="0 0 300 100" className="absolute bottom-0 left-0 right-0 w-full h-32 opacity-90"&gt;

&lt;defs&gt;

&lt;linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"&gt;

&lt;stop offset="0%" stopColor="#f59e0b" stopOpacity="0.4" /&gt;

&lt;stop offset="100%" stopColor="#f59e0b" stopOpacity="0" /&gt;

&lt;/linearGradient&gt;

&lt;/defs&gt;

&lt;path d="M0,80 C40,75 60,65 90,55 C120,45 150,52 180,38 C210,25 240,20 270,12 L300,8 L300,100 L0,100 Z" fill="url(#cg)" /&gt;

&lt;path d="M0,80 C40,75 60,65 90,55 C120,45 150,52 180,38 C210,25 240,20 270,12 L300,8" fill="none" stroke="#f59e0b" strokeWidth="1.5" /&gt;

{\[10, 40, 70, 100, 130, 160, 190, 220, 250, 280\].map((x, i) => (

&lt;circle key={i} cx={x} cy={80 - i \* 7} r="1.6" fill="#fff" opacity="0.5" /&gt;

))}

&lt;/svg&gt;

);

}

// interview

return (

&lt;div className="absolute inset-0 p-6 flex flex-col justify-end"&gt;

&lt;div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-5"&gt;

&lt;div className="flex items-center justify-between mb-4"&gt;

&lt;div className="flex items-center gap-2"&gt;

&lt;span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /&gt;

&lt;span className="font-mono text-\[10px\] tracking-\[0.25em\] uppercase text-white/60"&gt;live · session 04&lt;/span&gt;

&lt;/div&gt;

&lt;span className="font-mono text-\[10px\] tracking-\[0.2em\] text-amber-400"&gt;00:12:48&lt;/span&gt;

&lt;/div&gt;

&lt;div className="space-y-3"&gt;

&lt;div className="flex items-start gap-3"&gt;

&lt;span className="font-mono text-\[10px\] tracking-\[0.2em\] uppercase text-amber-400 pt-1"&gt;AI&lt;/span&gt;

&lt;p className="text-white/90 text-\[14px\] font-medium leading-snug"&gt;

Walk me through a time you led a project under pressure. What was the moment you knew it would work?

&lt;/p&gt;

&lt;/div&gt;

&lt;div className="flex items-start gap-3"&gt;

&lt;span className="font-mono text-\[10px\] tracking-\[0.2em\] uppercase text-white/40 pt-1"&gt;YOU&lt;/span&gt;

&lt;div className="flex items-end gap-\[2px\] h-6"&gt;

{Array.from({ length: 32 }).map((\_, i) => (

<span key={i} className="w-\[2px\] rounded-sm bg-white/70"

style={{ height: \`\${8 + (Math.sin(i \* 0.7) + 1) \* 8}px\` }} />

))}

&lt;/div&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;/div&gt;

);

}

export default function ProductShowcase() {

const sectionRef = useRef(null);

const headingRef = useRef(null);

const cardsRef = useRef(\[\]);

cardsRef.current = \[\];

const addCard = (el) => {

if (el && !cardsRef.current.includes(el)) cardsRef.current.push(el);

};

useEffect(() => {

const ctx = gsap.context(() => {

gsap.from(headingRef.current, {

opacity: 0, y: 60, duration: 1.2, ease: "expo.out",

scrollTrigger: { trigger: headingRef.current, start: "top 80%" },

});

gsap.from(cardsRef.current, {

opacity: 0, y: 40, duration: 1, ease: "expo.out", stagger: 0.1,

scrollTrigger: { trigger: cardsRef.current\[0\], start: "top 85%" },

});

}, sectionRef);

return () => ctx.revert();

}, \[\]);

return (

&lt;section ref={sectionRef} data-testid={TID.productSection} className="relative bg-\[#050505\] pt-32 pb-32 px-6 md:px-12"&gt;

&lt;div className="absolute top-0 left-1/2 -translate-x-1/2 w-\[120vmin\] h-\[40vmin\] door-light opacity-25 blur-3xl pointer-events-none" /&gt;

&lt;div className="relative max-w-7xl mx-auto"&gt;

&lt;div className="flex items-center gap-3 font-mono text-\[11px\] tracking-\[0.35em\] uppercase text-amber-500/80 mb-8"&gt;

&lt;span className="w-6 h-\[1px\] bg-amber-500" /&gt;

05 - The Platform

&lt;/div&gt;

&lt;div ref={headingRef} className="max-w-4xl mb-20"&gt;

&lt;h2 className="font-display font-extrabold text-\[clamp(40px,6vw,84px)\] leading-\[1.02\] tracking-\[-0.04em\] text-white"&gt;

Everything you need &lt;br /&gt;

&lt;span className="text-amber-400"&gt;before you walk in.&lt;/span&gt;

&lt;/h2&gt;

&lt;p className="mt-8 text-white/55 text-\[17px\] max-w-xl leading-relaxed"&gt;

Five surfaces. One quiet, ruthless preparation engine. Built for the twelve minutes that change a career.

&lt;/p&gt;

&lt;/div&gt;

&lt;div className="grid grid-cols-1 md:grid-cols-12 auto-rows-\[260px\] gap-5"&gt;

{FEATURES.map((f) => {

const Icon = f.icon;

return (

<div key={f.id} ref={addCard} data-testid={f.id}

className={\`bento-card group p-7 flex flex-col justify-between \${f.span}\`}>

&lt;div className="flex items-start justify-between relative z-10"&gt;

&lt;div className="w-11 h-11 rounded-xl border border-white/10 bg-white/\[0.03\] flex items-center justify-center text-amber-400"&gt;

&lt;Icon strokeWidth={1.5} className="w-5 h-5" /&gt;

&lt;/div&gt;

<ArrowUpRight strokeWidth={1.5}

className="w-5 h-5 text-white/30 group-hover:text-amber-400 group-hover:rotate-\[12deg\] transition-all duration-300" />

&lt;/div&gt;

&lt;div className="relative z-10 max-w-md"&gt;

&lt;h3 className="font-display font-bold text-\[22px\] md:text-\[26px\] text-white tracking-\[-0.02em\] mb-2.5"&gt;

{f.title}

&lt;/h3&gt;

&lt;p className="text-\[14px\] text-white/55 leading-relaxed"&gt;{f.desc}&lt;/p&gt;

&lt;/div&gt;

&lt;FeatureVisual type={f.visual} /&gt;

&lt;/div&gt;

);

})}

&lt;/div&gt;

&lt;/div&gt;

&lt;/section&gt;

);

}

**12. frontend/src/components/landing/FinalCTA.jsx**

import { useEffect, useRef } from "react";

import { gsap } from "gsap";

import { ScrollTrigger } from "gsap/ScrollTrigger";

import { ArrowRight } from "lucide-react";

import { TID } from "@/constants/landingTestIds";

export default function FinalCTA() {

const sectionRef = useRef(null);

const headingRef = useRef(null);

const ctaRef = useRef(null);

useEffect(() => {

const ctx = gsap.context(() => {

gsap.from(headingRef.current, {

opacity: 0, y: 60, duration: 1.4, ease: "expo.out",

scrollTrigger: { trigger: sectionRef.current, start: "top 75%" },

});

gsap.from(ctaRef.current, {

opacity: 0, y: 24, duration: 1, delay: 0.2, ease: "expo.out",

scrollTrigger: { trigger: sectionRef.current, start: "top 75%" },

});

}, sectionRef);

return () => ctx.revert();

}, \[\]);

return (

<section id="final-cta" ref={sectionRef}

className="relative bg-\[#050505\] py-40 px-6 md:px-12 overflow-hidden">

&lt;div className="absolute -bottom-40 left-1/2 -translate-x-1/2 w-\[140vmin\] h-\[80vmin\] door-light opacity-25 blur-3xl pointer-events-none" /&gt;

<div className="absolute inset-0 opacity-\[0.04\] pointer-events-none"

style={{

backgroundImage: "linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)",

backgroundSize: "80px 80px",

}} />

&lt;div className="relative max-w-5xl mx-auto text-center"&gt;

&lt;div className="flex items-center justify-center gap-3 mb-10 font-mono text-\[11px\] tracking-\[0.35em\] uppercase text-amber-500/80"&gt;

&lt;span className="w-6 h-\[1px\] bg-amber-500" /&gt;

06 - Your Turn

&lt;span className="w-6 h-\[1px\] bg-amber-500" /&gt;

&lt;/div&gt;

<h2 ref={headingRef}

className="font-display font-extrabold text-\[clamp(56px,10vw,160px)\] leading-\[0.92\] tracking-\[-0.05em\] text-white">

The door &lt;br /&gt;

&lt;span className="text-amber-400"&gt;opens once.&lt;/span&gt;

&lt;/h2&gt;

&lt;p className="mt-10 max-w-xl mx-auto text-white/55 text-\[17px\] leading-relaxed"&gt;

You don't get a second take. But you can rehearse the take until it feels like memory. Walk in different.

&lt;/p&gt;

&lt;div ref={ctaRef} className="mt-14 flex flex-col sm:flex-row items-center justify-center gap-5"&gt;

&lt;button data-testid={TID.finalCta} className="btn-primary"&gt;

Start Your Interview

&lt;ArrowRight strokeWidth={2} className="w-4 h-4" /&gt;

&lt;/button&gt;

&lt;button data-testid={TID.footerStartCta} className="btn-ghost"&gt;Watch the demo&lt;/button&gt;

&lt;/div&gt;

&lt;div className="mt-10 flex items-center justify-center gap-6 font-mono text-\[10px\] tracking-\[0.25em\] uppercase text-white/35"&gt;

&lt;span&gt;no card required&lt;/span&gt;

&lt;span className="w-1 h-1 rounded-full bg-white/20" /&gt;

&lt;span&gt;3 free sessions&lt;/span&gt;

&lt;span className="w-1 h-1 rounded-full bg-white/20" /&gt;

&lt;span&gt;full feedback&lt;/span&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;/section&gt;

);

}

**13. frontend/src/components/landing/Footer.jsx**

export default function Footer() {

return (

&lt;footer className="relative border-t border-white/5 bg-black px-6 md:px-12 py-16"&gt;

&lt;div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-end justify-between gap-12"&gt;

&lt;div&gt;

&lt;div className="flex items-center gap-2 mb-6"&gt;

&lt;span className="font-display font-extrabold text-\[22px\] tracking-tight text-white"&gt;evalvate&lt;/span&gt;

&lt;span className="w-1.5 h-1.5 rounded-full bg-amber-500" /&gt;

&lt;/div&gt;

&lt;p className="max-w-xs text-white/40 text-\[13px\] leading-relaxed"&gt;

A quiet, ruthless interview preparation engine. Built for the moment before the moment.

&lt;/p&gt;

&lt;/div&gt;

&lt;div className="grid grid-cols-3 gap-12 text-\[12px\] font-mono tracking-\[0.15em\] uppercase"&gt;

&lt;div&gt;

&lt;div className="text-white/30 mb-4"&gt;Product&lt;/div&gt;

&lt;ul className="space-y-3 text-white/70"&gt;

&lt;li&gt;&lt;a href="#"&gt;Mock interviews&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;Speech analysis&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;Resume audit&lt;/a&gt;&lt;/li&gt;

&lt;/ul&gt;

&lt;/div&gt;

&lt;div&gt;

&lt;div className="text-white/30 mb-4"&gt;Company&lt;/div&gt;

&lt;ul className="space-y-3 text-white/70"&gt;

&lt;li&gt;&lt;a href="#"&gt;Manifesto&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;Careers&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;Press&lt;/a&gt;&lt;/li&gt;

&lt;/ul&gt;

&lt;/div&gt;

&lt;div&gt;

&lt;div className="text-white/30 mb-4"&gt;Connect&lt;/div&gt;

&lt;ul className="space-y-3 text-white/70"&gt;

&lt;li&gt;&lt;a href="#"&gt;Twitter&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;LinkedIn&lt;/a&gt;&lt;/li&gt;

&lt;li&gt;&lt;a href="#"&gt;Contact&lt;/a&gt;&lt;/li&gt;

&lt;/ul&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;/div&gt;

&lt;div className="max-w-7xl mx-auto mt-16 pt-6 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-3 text-\[11px\] font-mono tracking-\[0.2em\] uppercase text-white/30"&gt;

&lt;span&gt;© 2025 evalvate - all rights reserved&lt;/span&gt;

&lt;span&gt;built for the twelve minutes that change a career&lt;/span&gt;

&lt;/div&gt;

&lt;/footer&gt;

);

}

**Final folder structure**

frontend/

├── public/

│ └── scenes/

│ ├── scene2_waiting_room.png ← download

│ ├── scene3_hands.png ← download

│ ├── scene4_walk.png ← download

│ └── scene5_door.png ← download

└── src/

├── App.js

├── App.css

├── index.css

├── components/

│ ├── CustomCursor.jsx

│ └── landing/

│ ├── Nav.jsx

│ ├── SceneCurtain.jsx

│ ├── ScenePinned.jsx

│ ├── SceneReveal.jsx

│ ├── ProductShowcase.jsx

│ ├── FinalCTA.jsx

│ └── Footer.jsx

├── constants/

│ └── landingTestIds.js

└── pages/

└── Landing.jsx

If your project doesn't use the @/ path alias, do a find-and-replace: @/ → ../ (and ../../ from nested folders) - or set up the alias in craco.config.js/jsconfig.json.