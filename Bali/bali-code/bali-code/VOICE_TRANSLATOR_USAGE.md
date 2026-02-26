# Voice Translator Usage & Implementation Documentation

## Overview

The Voice Translator module has been overhauled to provide enterprise-grade transcription using **OpenAI's Whisper API**. This replaces the legacy, often unreliable, browser-native `SpeechRecognition` API.

## Frontend Implementation (`useVoiceToText.js`)

The React application utilizes a custom hook leveraging the modern `MediaRecorder API`:

1. **Audio Capture**: The user's microphone streams audio directly into a `MediaRecorder` instance. Audio chunks are aggregated until the user toggles off the "recording mode".
2. **Blob Generation**: The chunks are compiled into an `audio/webm` Blob.
3. **Optimistic UI Feedback**: While computing locally/sending to the backend, the text input displays _"Processing audio transcription..."_.
4. **Backend Offloading**: The `.webm` blob is bundled inside a `FormData` object and posted to the `/chatbot/upload-audio` backend endpoint.

## Backend Implementation (`chatbot_routes.py`)

1. **Route Endpoint**: `POST /chatbot/upload-audio`
2. **Data Handling**: The route accepts an HTTP `UploadFile` (Multipart).
3. **Whisper Transcription**: The received byte stream is converted to an IO Buffer and passed directly to the `client.audio.transcriptions.create` OpenAI SDK utility using the `whisper-1` model.
4. **Language Detection**: Whisper inherently detects the source language (including nuanced Bahasa Indonesia vs. native Balinese syntax strings) and automatically returns an accurate English representation, or strictly transcribes the native tongue accurately without requiring explicit language flags.

## Error Handling & Fallback logic

- If browser permissions are denied, an alert is immediately presented: `"Could not access microphone."`.
- If the audio quality is too garbled or Whisper fails, an exception is caught in the `.catch()` block.
- The user is proactively alerted: `"Poor audio quality or transcription error. Please try text input instead."`, maintaining the fallback-to-text safety net instructed during initial architecture planning.
