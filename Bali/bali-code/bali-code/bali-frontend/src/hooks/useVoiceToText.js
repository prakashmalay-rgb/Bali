import { useState, useCallback } from 'react';

export const useVoiceToText = (onTranscript, onFinalTranscript) => {
    const [isListening, setIsListening] = useState(false);

    const toggleListening = useCallback(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("Browser does not support speech recognition.");
            return;
        }

        if (isListening) {
            setIsListening(false);
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            setIsListening(true);
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (onTranscript) onTranscript(transcript);
            if (onFinalTranscript) onFinalTranscript(transcript);
        };

        recognition.onerror = (event) => {
            console.error("🎙️ Speech recognition error:", event.error);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognition.start();
    }, [isListening, onTranscript, onFinalTranscript]);

    return { isListening, toggleListening };
};
