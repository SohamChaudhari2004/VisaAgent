/**
 * Utility for checking connections to the backend server
 */

/**
 * Check HTTP API connection to the backend
 * @returns {Promise<{success: boolean, message: string}>} Connection result
 */
export const checkApiConnection = async () => {
    try {
        // Fix: Use the correct path that's properly proxied
        const response = await fetch('/api/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            // Short timeout to quickly identify connection issues
            signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
            const data = await response.json();
            return { success: true, message: 'API connection successful', data };
        } else {
            return {
                success: false,
                message: `API connection failed: ${response.status} ${response.statusText}`
            };
        }
    } catch (error) {
        console.error('API connection check error:', error);
        return {
            success: false,
            message: `API connection error: ${error.name === 'AbortError' ? 'Timeout' : error.message}`
        };
    }
};

/**
 * Check WebSocket connection to the backend
 * @returns {Promise<{success: boolean, message: string}>} Connection result
 */
export const checkWebSocketConnection = () => {
    return new Promise((resolve) => {
        try {
            // Fix: Use the correct WebSocket path that will be properly proxied
            const wsUrl = `/ws/health`;

            console.log(`Testing WebSocket connection to: ${wsUrl}`);
            const socket = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
                window.location.host + wsUrl);

            // Set a timeout to detect hanging connections
            const timeout = setTimeout(() => {
                socket.close();
                resolve({
                    success: false,
                    message: 'WebSocket connection timed out'
                });
            }, 5000);

            socket.onopen = () => {
                clearTimeout(timeout);
                console.log('WebSocket connection test successful');
                socket.close();
                resolve({ success: true, message: 'WebSocket connection successful' });
            };

            socket.onerror = (error) => {
                clearTimeout(timeout);
                console.error('WebSocket connection test error:', error);
                socket.close();
                resolve({
                    success: false,
                    message: 'WebSocket connection failed'
                });
            };
        } catch (error) {
            console.error('WebSocket connection check error:', error);
            resolve({
                success: false,
                message: `WebSocket connection error: ${error.message}`
            });
        }
    });
};

/**
 * Check both API and WebSocket connections
 * @returns {Promise<{api: {success: boolean, message: string}, websocket: {success: boolean, message: string}}>}
 */
export const checkConnections = async () => {
    const api = await checkApiConnection();
    const websocket = await checkWebSocketConnection();

    return { api, websocket };
};
