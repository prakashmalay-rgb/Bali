import { useState, useRef, useCallback } from 'react';

/**
 * useVoiceToText
 * – Shows live interim text in the input box as the user speaks.
 * – Accumulates ALL finalised chunks so the auto-send always has the FULL message.
 * – Auto-sends when speech ends (recognition.onend → "AUTO_SUBMIT_SIGNAL").
 */
export const useVoiceToText = (onTranscript, onFinalTranscript) => {
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);
    // Running accumulator of every finalised speech chunk in this session
    const fullTranscriptRef = useRef('');

    const toggleListening = useCallback(async () => {
        if (isListening) {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            setIsListening(false);
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Your browser does not support real-time speech recognition. Please try Chrome, Edge, or Safari.");
            return;
        }

        // Clear accumulator for this new session
        fullTranscriptRef.current = '';

        try {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;    // Stop automatically when user stops talking
            recognition.interimResults = true; // Stream partial words into input box
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                setIsListening(true);
            };

            recognition.onresult = (event) => {
                let interimTranscript = '';
                let finalTranscriptChunk = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscriptChunk += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                // Append confirmed chunk to the running total
                if (finalTranscriptChunk) {
                    fullTranscriptRef.current += finalTranscriptChunk;
                }

                // Show live text in the input box: confirmed + whatever is still being recognised
                const liveText = (fullTranscriptRef.current + interimTranscript).trim();
                if (onTranscript && liveText) {
                    onTranscript(liveText);
                }
            };

            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                if (event.error !== 'no-speech') {
                    alert("Microphone error: " + event.error);
                }
                setIsListening(false);
            };

            recognition.onend = () => {
                setIsListening(false);
                // Signal chat.jsx to auto-submit whatever is in the input box
                if (onFinalTranscript) {
                    onFinalTranscript("AUTO_SUBMIT_SIGNAL");
                }
            };

            recognitionRef.current = recognition;
            recognition.start();
        } catch (error) {
            console.error("Microphone access denied or error:", error);
            alert("Could not start microphone.");
        }
    }, [isListening, onTranscript, onFinalTranscript]);

    return { isListening, toggleListening };
};
