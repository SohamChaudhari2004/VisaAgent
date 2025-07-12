import { useEffect, useRef, useState, useCallback } from 'react';
import { useInterview } from '../context/InterviewContext';

export default function useWebSocket() {
    const { interviewState, dispatch } = useInterview();
    const [isConnected, setIsConnected] = useState(false);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [audioData, setAudioData] = useState(null);
    const socketRef = useRef(null);
    const reconnectAttemptRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectTimeoutRef = useRef(null);

    const createWebSocketConnection = useCallback((config = null) => {
        // Always connect to backend port 8000 for WebSocket, regardless of frontend port
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use localhost:8000 in dev, or window.location.hostname:8000 in production
        const wsHost =
            import.meta.env.DEV
                ? 'localhost:8000'
                : `${window.location.hostname}:8000`;
        const wsUrl = `${wsProtocol}//${wsHost}/ws/agent`;

        console.log(`Connecting to WebSocket at: ${wsUrl}`);

        try {
            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                console.log("WebSocket connection established");
                setIsConnected(true);
                setError(null);
                reconnectAttemptRef.current = 0;

                // If we have a config, send it immediately
                if (config) {
                    console.log("Sending initial config:", config);
                    socket.send(JSON.stringify(config));
                }
            };

            socket.onmessage = async (event) => {
                if (event.data instanceof Blob) {
                    console.log("Received binary audio data");
                    // Handle binary data (audio)
                    try {
                        const arrayBuffer = await event.data.arrayBuffer();
                        setAudioData(arrayBuffer);
                    } catch (err) {
                        console.error("Error processing audio data:", err);
                    }
                } else {
                    // Handle text data (JSON)
                    try {
                        console.log("Received text message:", event.data);
                        const parsedData = JSON.parse(event.data);
                        setMessage(parsedData);

                        if (parsedData.cmd === "start_record") {
                            // Start recording user's answer
                            console.log("Received start_record command");
                            window.dispatchEvent(new CustomEvent('startRecording'));
                        } else if (parsedData.cmd === "ack") {
                            // Server acknowledged the answer
                            console.log("Received answer acknowledgment:", parsedData.answerText);
                            dispatch({ type: 'SET_ANSWER', payload: parsedData.answerText });
                            dispatch({ type: 'LOG_QA', payload: parsedData.answerText });
                        } else if (parsedData.cmd === "complete") {
                            // Interview completed
                            console.log("Interview completed. Metrics:", parsedData.metrics);
                            dispatch({
                                type: 'COMPLETE_INTERVIEW',
                                payload: {
                                    feedback: parsedData.feedback,
                                    metrics: parsedData.metrics
                                }
                            });
                            socket.close();
                        } else if (parsedData.question) {
                            // New question received
                            console.log("Received new question:", parsedData.question);
                            dispatch({ type: 'SET_QUESTION', payload: parsedData.question });
                        }
                    } catch (err) {
                        console.error("Error parsing WebSocket message:", err);
                        setMessage(event.data);
                    }
                }
            };

            socket.onerror = (err) => {
                const errorMsg = 'WebSocket connection error';
                console.error(errorMsg, err);
                setError(errorMsg);
                dispatch({ type: 'SET_ERROR', payload: errorMsg });
            };

            socket.onclose = (event) => {
                const wasConnected = isConnected;
                setIsConnected(false);
                console.log(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason}`);

                // Attempt reconnection for unexpected closures during an interview
                if (
                    wasConnected &&
                    event.code !== 1000 && // Not normal closure
                    interviewState.status === 'interviewing' &&
                    reconnectAttemptRef.current < maxReconnectAttempts
                ) {
                    const delay = Math.min(1000 * 2 ** reconnectAttemptRef.current, 10000);
                    console.log(`Attempting reconnect in ${delay}ms (attempt ${reconnectAttemptRef.current + 1}/${maxReconnectAttempts})`);

                    // Clear any existing timeout
                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                    }

                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectAttemptRef.current += 1;
                        console.log(`Reconnecting... Attempt ${reconnectAttemptRef.current}`);
                        createWebSocketConnection(interviewState);
                    }, delay);
                }

                if (event.code !== 1000) { // Not normal closure
                    setError(`Connection closed unexpectedly (${event.code})`);
                }
            };

            return socket;
        } catch (error) {
            console.error("Error creating WebSocket:", error);
            setError(`Failed to create WebSocket connection: ${error.message}`);
            setIsConnected(false);
            return null;
        }
    }, [dispatch, interviewState, isConnected]);

    const startInterview = useCallback(({ visaType, voice, questionCount }) => {
        // Clean up any existing connection
        if (socketRef.current) {
            console.log("Closing existing WebSocket connection");
            socketRef.current.close();
            socketRef.current = null;
        }

        // Reset reconnect counter
        reconnectAttemptRef.current = 0;

        // Update interview state
        dispatch({
            type: 'START_INTERVIEW',
            payload: { visaType, voice, questionCount }
        });

        // Create a new connection with the config
        createWebSocketConnection({ visaType, voice, questionCount });

    }, [dispatch, createWebSocketConnection]);

    const sendMessage = useCallback((data) => {
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
            console.warn("Can't send message, socket not connected");
            return false;
        }

        const message = typeof data === 'string' ? data : JSON.stringify(data);
        console.log("Sending message:", message);
        socketRef.current.send(message);
        return true;
    }, []);

    const sendBinary = useCallback((data) => {
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
            console.warn("Can't send binary data, socket not connected");
            return false;
        }

        console.log("Sending binary data, size:", data.byteLength);
        socketRef.current.send(data);
        return true;
    }, []);

    const disconnect = useCallback(() => {
        // Clear any pending reconnect attempts
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (socketRef.current) {
            console.log("Manually disconnecting WebSocket");
            socketRef.current.close(1000, "Normal closure");
            socketRef.current = null;
        }
    }, []);

    // Check if the connection is still alive periodically
    useEffect(() => {
        if (isConnected && interviewState.status === 'interviewing') {
            const pingInterval = setInterval(() => {
                if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    // Send a ping message
                    try {
                        socketRef.current.send(JSON.stringify({ cmd: "ping" }));
                    } catch (err) {
                        console.error("Error sending ping:", err);
                    }
                }
            }, 30000); // Every 30 seconds

            return () => clearInterval(pingInterval);
        }
    }, [isConnected, interviewState.status]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }

            if (socketRef.current) {
                console.log("Cleaning up WebSocket connection");
                socketRef.current.close();
                socketRef.current = null;
            }
        };
    }, []);

    return {
        isConnected,
        message,
        error,
        audioData,
        startInterview,
        sendMessage,
        sendBinary,
        disconnect,
        reconnect: () => createWebSocketConnection(interviewState)
    };
}
