# DEMO_CHECKLIST.md

## Purpose

This checklist should be completed before:

* Investor demos
* Client demos
* Production releases

---

# Core Interview Flow

## Pre-Interview

* User authentication works
* Role selection works
* Difficulty selection works
* Resume upload works (if enabled)
* Camera permission check works
* Microphone permission check works

## During Interview

* Question generation works
* Question audio playback works
* Speech-to-text works
* User answer submission works
* Follow-up question generation works
* Video analysis runs continuously
* Session data is saved correctly

## Post Interview

* Interview completes successfully
* Report generation succeeds
* Scores are generated from real session data
* Interview history is saved
* Report is viewable after refresh

---

# AI Verification

## Question Generation

Verify:

* Questions are generated dynamically
* Role affects question quality
* Difficulty affects question quality
* Follow-up questions use previous context

## Evaluation

Verify:

* Answer evaluation uses real LLM responses
* No hardcoded feedback
* No hardcoded scores
* Empty AI responses are handled gracefully
* Invalid JSON responses are handled gracefully

---

# Speech Systems

Verify:

* Speech-to-text works
* Text-to-speech works
* Browser permission failures are handled
* Audio streams are cleaned up correctly

Fallbacks:

* Question text visible if TTS fails
* Manual answer input available if STT fails

---

# Video Analysis

Verify:

* Camera feed loads
* Face detection works
* Eye-contact scoring works
* Emotion detection works
* Multi-person detection works

Failure Cases:

* No camera
* Camera denied
* Mobile device performance

---

# Security Checklist

Verify:

* No API keys exposed in frontend
* Protected routes require authentication
* User data is scoped correctly
* No auth bypass flags enabled
* Sensitive information is not logged

---

# Database Checklist

Verify:

* Sessions are saved
* Reports are saved
* User history loads correctly
* Database connection failures are handled
* Session end times are recorded

---

# Frontend Checklist

Verify:

* No broken routes
* No broken images
* Loading states exist
* Error states exist
* Mobile responsiveness works
* No console errors

---

# Deployment Checklist

Verify:

* Environment variables configured
* Database reachable
* AI services reachable
* Build succeeds
* No TypeScript errors
* No ESLint errors

---

# Demo Mode Verification

Verify:

* Demo mode login works
* Complete interview flow works
* Report generation works
* Demo can be completed without external setup

---

# Release Gate

Before release:

* No mock data
* No placeholder content
* No fake analytics
* No hardcoded scores
* No TODOs in production code
* No committed secrets

If any item above fails, do not demo or release.