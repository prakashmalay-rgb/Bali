import { useState, useRef, useCallback } from 'react';
import { chatAPI } from '../api/chatApi';

export const useVoiceToText = (onTranscript, onFinalTranscript) => {
    const [isListening, setIsListening] = useState(false);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const toggleListening = useCallback(async () => {
        // If already listening, stop recording
        if (isListening) {
            setIsListening(false);
            if (mediaRecorderRef.current) {
                mediaRecorderRef.current.stop();
            }
            return;
        }

        // Start new recording
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Browser does not support audio recording.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setIsListening(false);
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                try {
                    // Show some "Processing..." feedback if needed
                    if (onTranscript) onTranscript("Processing audio transcription...");

                    // Call the backend Whisper API
                    const response = await chatAPI.uploadAudio(audioBlob);

                    if (response && response.transcript && response.transcript.text) {
                        const finalString = response.transcript.text;
                        if (onTranscript) onTranscript(finalString);
                        if (onFinalTranscript) onFinalTranscript(finalString);
                    } else {
                        throw new Error("Invalid transcription response");
                    }
                } catch (error) {
                    console.error("🎙️ Whisper Transcription error:", error);
                    alert("Poor audio quality or transcription error. Please try text input instead.");
                    if (onTranscript) onTranscript(""); // Clear "Processing..."
                } finally {
                    // Turn off tracks to release mic light
                    stream.getTracks().forEach(track => track.stop());
                }
            };

            setIsListening(true);
            mediaRecorder.start();
        } catch (error) {
            console.error("Microphone access denied or error:", error);
            alert("Could not access microphone.");
        }
    }, [isListening, onTranscript, onFinalTranscript]);

    return { isListening, toggleListening };
};
