import { useCallback, useRef, useState } from "react";
import { postVoiceConverse, ApiError, type VoiceConverseResponse } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";

export type VoiceState = "idle" | "recording" | "processing" | "speaking" | "error";

/** Drives the Companion mic button: record -> upload -> play the reply.
 * One MediaRecorder session per turn; `sessionId` persists across turns
 * within a page visit so conversation_history groups them together. */
export function useVoiceCompanion() {
  const { profile } = usePrimaryBusinessProfile();
  const [state, setState] = useState<VoiceState>("idle");
  const [result, setResult] = useState<VoiceConverseResponse | null>(null);
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
        sessionId: sessionIdRef.current,
      });
      sessionIdRef.current = response.session_id;
      setResult(response);

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
      setErrorMessage(error instanceof ApiError ? error.message : "Sakhi couldn't respond — try again.");
      setState("error");
    }
  }

  return {
    state,
    isRecording: state === "recording",
    isBusy: state === "processing" || state === "speaking",
    result,
    errorMessage,
    startRecording,
    stopRecording,
    hasProfile: !!profile,
  };
}
