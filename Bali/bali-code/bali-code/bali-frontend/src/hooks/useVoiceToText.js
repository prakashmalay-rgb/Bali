import { useState, useRef, useCallback } from 'react';

export const useVoiceToText = (onTranscript, onFinalTranscript) => {
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);

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

        try {
            const recognition = new SpeechRecognition();
            recognition.continuous = false; // Stop when the user stops talking
            recognition.interimResults = true; // Stream partially recognized sentences
            recognition.lang = 'en-US'; // Default to english, can be dynamic based on current user context if needed.

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

                // If we have an interim guess, feed it into the text box for real-time typing
                if (interimTranscript && onTranscript) {
                    onTranscript(finalTranscriptChunk + interimTranscript);
                }

                // If the engine finalized a chunk early, pass it up
                if (finalTranscriptChunk && !interimTranscript && onTranscript) {
                    onTranscript(finalTranscriptChunk);
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
                if (onFinalTranscript) {
                    // Send a ping to chat.jsx letting it know voice input is entirely finished so it can auto-submit.
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

