import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for audio recording and playback
 * @returns {Object} Audio state and methods
 */
export const useAudio = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioChunks, setAudioChunks] = useState([]);
    const [audioBlob, setAudioBlob] = useState(null);
    const [error, setError] = useState(null);
    const [audioLevel, setAudioLevel] = useState(0);

    const mediaRecorderRef = useRef(null);
    const streamRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const animationFrameRef = useRef(null);

    // Initialize audio context
    useEffect(() => {
        if (!audioContextRef.current) {
            try {
                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
            } catch (err) {
                setError('Audio Context not supported in this browser');
            }
        }

        return () => {
            if (audioContextRef.current) {
                audioContextRef.current.close();
            }
        };
    }, []);

    // Start audio recording
    const startRecording = useCallback(async () => {
        try {
            if (isRecording) return;

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Set up audio analysis
            const audioContext = audioContextRef.current;
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyserRef.current = analyser;

            // Update audio level
            const updateAudioLevel = () => {
                if (!isRecording) return;

                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                const average = sum / bufferLength;
                const level = Math.min(100, average * 2); // Scale to 0-100
                setAudioLevel(level);

                animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
            };

            animationFrameRef.current = requestAnimationFrame(updateAudioLevel);

            // Set up media recorder
            const options = { mimeType: 'audio/webm;codecs=opus' };
            const recorder = new MediaRecorder(stream, options);

            const chunks = [];
            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                    // Add the latest chunk to state for real-time streaming
                    setAudioChunks((prevChunks) => [...prevChunks, event.data]);
                }
            };

            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                setAudioBlob(blob);

                stream.getTracks().forEach((track) => track.stop());
                streamRef.current = null;

                if (animationFrameRef.current) {
                    cancelAnimationFrame(animationFrameRef.current);
                }
            };

            setAudioChunks([]);
            recorder.start(100); // Collect data every 100ms for streaming
            mediaRecorderRef.current = recorder;
            setIsRecording(true);
            setError(null);
        } catch (err) {
            setError(err.message || 'Error accessing microphone');
        }
    }, [isRecording]);

    // Stop audio recording
    const stopRecording = useCallback(() => {
        if (!isRecording || !mediaRecorderRef.current) return;

        mediaRecorderRef.current.stop();
        setIsRecording(false);
    }, [isRecording]);

    // Play audio from ArrayBuffer
    const playAudio = useCallback((arrayBuffer) => {
        // Fix: Use browser's Audio API for MP3 or other audio formats
        if (!arrayBuffer) return;

        try {
            // Try to play as MP3 (edge-tts returns MP3)
            const blob = new Blob([arrayBuffer], { type: "audio/mp3" });
            const url = URL.createObjectURL(blob);
            const audio = new window.Audio(url);
            audio.play().catch((err) => {
                setError('Failed to play audio: ' + err.message);
            });
            // Clean up the URL after playback
            audio.onended = () => {
                URL.revokeObjectURL(url);
            };
        } catch (err) {
            setError('Failed to play audio: ' + err.message);
        }
    }, []);

    // Get the latest chunk for streaming
    const getLatestChunk = useCallback(() => {
        if (audioChunks.length === 0) return null;
        return audioChunks[audioChunks.length - 1];
    }, [audioChunks]);

    return {
        isRecording,
        audioBlob,
        audioChunks,
        audioLevel,
        error,
        startRecording,
        stopRecording,
        playAudio,
        getLatestChunk
    };
};
