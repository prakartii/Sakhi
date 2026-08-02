import { useCallback, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { postVoiceConverse, ApiError, type VoiceConverseResponse } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";

export type VoiceState = "idle" | "recording" | "processing" | "speaking" | "error";

export interface VoiceChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

/** Drives the Companion mic button: record -> upload -> play the reply,
 * while also building a visible chat thread (spoken text + Sakhi's reply,
 * one pair per turn) — not just a single flip-through status line.
 *
 * Language comes from the app's single global switcher (see
 * components/sakhi/Layout.tsx's LanguageSwitcher, SUPPORTED_LANGUAGES in
 * lib/i18n.ts) rather than its own control — one selection now drives both
 * the on-screen text and the STT/TTS language Sarvam uses. The backend
 * also replies in whatever it actually detected, so a wrong guess here
 * still self-corrects turn to turn (see app.ai.orchestrator.prompts). */
export function useVoiceCompanion() {
  const { profile } = usePrimaryBusinessProfile();
  const { i18n } = useTranslation();
  const [state, setState] = useState<VoiceState>("idle");
  const [result, setResult] = useState<VoiceConverseResponse | null>(null);
  const [messages, setMessages] = useState<VoiceChatMessage[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const sessionIdRef = useRef<string | undefined>(undefined);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    if (!profile) {
      setErrorMessage("Set up your business first so Sakhi knows who she's talking to.");
      setState("error");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setErrorMessage("This browser can't record audio.");
      setState("error");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        void handleRecordingComplete();
      };
      recorderRef.current = recorder;
      recorder.start();
      setErrorMessage(null);
      setState("recording");
    } catch {
      setErrorMessage("Microphone access was denied.");
      setState("error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    stopStream();
  }, [stopStream]);

  async function handleRecordingComplete() {
    if (!profile) return;
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    chunksRef.current = [];
    if (blob.size === 0) {
      setState("idle");
      return;
    }

    setState("processing");
    try {
      const response = await postVoiceConverse({
        businessProfileId: profile.id,
        audio: blob,
        language: i18n.language,
        sessionId: sessionIdRef.current,
      });
      sessionIdRef.current = response.session_id;
      setResult(response);
      const now = new Date().toISOString();
      setMessages((prev) => [
        ...prev,
        { role: "user", content: response.transcript, created_at: now },
        { role: "assistant", content: response.answer, created_at: now },
      ]);

      if (response.audio_base64) {
        setState("speaking");
        const audio = new Audio(
          `data:audio/${response.audio_format};base64,${response.audio_base64}`,
        );
        audio.onended = () => setState("idle");
        audio.onerror = () => setState("idle");
        await audio.play();
      } else {
        setState("idle");
      }
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.message : "Sakhi couldn't respond — try again.",
      );
      setState("error");
    }
  }

  return {
    state,
    isRecording: state === "recording",
    isBusy: state === "processing" || state === "speaking",
    result,
    messages,
    errorMessage,
    startRecording,
    stopRecording,
    hasProfile: !!profile,
  };
}
