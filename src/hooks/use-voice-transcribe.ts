import { useCallback, useRef, useState } from "react";
import { postVoiceTranscribe, ApiError } from "@/lib/api-client";

export type TranscribeState = "idle" | "recording" | "transcribing" | "error";

/** Drives a plain "record -> transcript text" mic button — no business
 * profile, no AI reply, no TTS playback. Used by Business Setup's Step 1
 * (speak your story) before any business profile exists to converse
 * against; see use-voice-companion.ts for the full Companion-page flow
 * this deliberately doesn't replicate. */
export function useVoiceTranscribe(onTranscript: (text: string) => void) {
  const [state, setState] = useState<TranscribeState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
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
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    stopStream();
  }, [stopStream]);

  async function handleRecordingComplete() {
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    chunksRef.current = [];
    if (blob.size === 0) {
      setState("idle");
      return;
    }

    setState("transcribing");
    try {
      const response = await postVoiceTranscribe({ audio: blob });
      onTranscript(response.transcript);
      setState("idle");
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.message : "Couldn't transcribe that — try again.",
      );
      setState("error");
    }
  }

  return {
    state,
    isRecording: state === "recording",
    isBusy: state === "transcribing",
    errorMessage,
    startRecording,
    stopRecording,
  };
}
