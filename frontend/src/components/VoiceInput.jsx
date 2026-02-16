import { LoaderCircle, Mic, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import api from "../services/api";

function getSpeechRecognition() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export default function VoiceInput({
  onTranscript = () => {},
  language = "en",
  className = "",
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const chunksRef = useRef([]);
  const recognitionRef = useRef(null);

  const stopMediaTracks = () => {
    const stream = mediaStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
  };

  const fallbackSpeechRecognition = () => {
    return new Promise((resolve, reject) => {
      const SpeechRecognition = getSpeechRecognition();
      if (!SpeechRecognition) {
        reject(new Error("Speech recognition unavailable"));
        return;
      }

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.lang = language === "en" ? "en-US" : `${language}-IN`;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript?.trim() || "";
        resolve(transcript);
      };
      recognition.onerror = () => reject(new Error("Recognition failed"));
      recognition.onnomatch = () => reject(new Error("No speech match"));
      recognition.start();
    });
  };

  const transcribeWithBackend = async () => {
    if (!Array.isArray(chunksRef.current) || chunksRef.current.length === 0) {
      throw new Error("No audio captured");
    }

    const blob = new Blob(chunksRef.current, {
      type: chunksRef.current[0]?.type || "audio/webm",
    });

    const formData = new FormData();
    formData.append("audio", blob, "voice.webm");
    formData.append("language", language || "en");

    const response = await api.transcribeAudio(formData);
    const transcript = (
      response?.transcript ||
      response?.text ||
      response?.result ||
      response?.message ||
      ""
    )
      .toString()
      .trim();

    if (!transcript) {
      throw new Error("Empty transcription from backend");
    }

    return transcript;
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  };

  const startRecording = async () => {
    if (isRecording || isProcessing) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        setIsProcessing(true);

        try {
          let transcript = "";

          try {
            transcript = await transcribeWithBackend();
          } catch {
            transcript = await fallbackSpeechRecognition();
          }

          if (transcript) {
            onTranscript(transcript);
          }
        } finally {
          setIsProcessing(false);
          stopMediaTracks();
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch {
      try {
        setIsProcessing(true);
        const transcript = await fallbackSpeechRecognition();
        if (transcript) {
          onTranscript(transcript);
        }
      } finally {
        setIsProcessing(false);
      }
    }
  };

  useEffect(() => {
    return () => {
      stopRecording();
      stopMediaTracks();
      if (recognitionRef.current) {
        recognitionRef.current.abort?.();
      }
    };
  }, []);

  return (
    <button
      type="button"
      onClick={isRecording ? stopRecording : startRecording}
      disabled={isProcessing}
      aria-label={isRecording ? "Stop recording" : "Start voice input"}
      className={`btn-ghost ${isRecording ? "border-red-400/70 text-red-200 animate-pulse" : ""} ${className}`}
    >
      {isProcessing ? (
        <LoaderCircle size={18} className="animate-spin" />
      ) : isRecording ? (
        <Square size={16} className="fill-red-300 text-red-300" />
      ) : (
        <Mic size={18} />
      )}
    </button>
  );
}
