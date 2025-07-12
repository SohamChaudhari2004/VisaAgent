import React, { useState, useEffect } from "react";
import { checkConnections } from "../utils/connectionChecker";

/**
 * Connection status indicator component
 * Shows the status of API and WebSocket connections
 */
const ConnectionStatus = () => {
  const [status, setStatus] = useState({
    api: { success: false, message: "Checking..." },
    websocket: { success: false, message: "Checking..." },
    lastChecked: null,
    isLoading: true,
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // Check connections on component mount
  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      if (!isMounted) return;

      setStatus((prev) => ({ ...prev, isLoading: true }));
      try {
        const result = await checkConnections();
        if (isMounted) {
          setStatus({
            ...result,
            lastChecked: new Date(),
            isLoading: false,
          });
        }
      } catch (err) {
        console.error("Error checking connections:", err);
        if (isMounted) {
          setStatus({
            api: { success: false, message: "Connection check failed" },
            websocket: { success: false, message: "Connection check failed" },
            lastChecked: new Date(),
            isLoading: false,
          });
        }
      }
    };

    // Initial check
    checkStatus();

    // Set up interval for periodic checks
    const interval = setInterval(checkStatus, 30000); // Every 30 seconds

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Handle manual refresh
  const handleRefresh = async () => {
    setStatus((prev) => ({ ...prev, isLoading: true }));
    try {
      const result = await checkConnections();
      setStatus({
        ...result,
        lastChecked: new Date(),
        isLoading: false,
      });
    } catch (err) {
      console.error("Error checking connections:", err);
      setStatus({
        api: { success: false, message: "Connection check failed" },
        websocket: { success: false, message: "Connection check failed" },
        lastChecked: new Date(),
        isLoading: false,
      });
    }
  };

  // Get overall status
  const isOnline = status.api.success && status.websocket.success;
  const statusClass = status.isLoading
    ? "loading"
    : isOnline
    ? "online"
    : "offline";

  return (
    <div className={`connection-status-widget ${statusClass}`}>
      <div
        className="connection-status-summary"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="connection-status-indicator"></div>
        <span>
          Server:{" "}
          {status.isLoading
            ? "Checking..."
            : isOnline
            ? "Connected"
            : "Disconnected"}
        </span>
        <button
          className="refresh-button"
          onClick={(e) => {
            e.stopPropagation();
            handleRefresh();
          }}
          disabled={status.isLoading}
        >
          {status.isLoading ? "..." : "↻"}
        </button>
      </div>

      {isExpanded && (
        <div className="connection-status-details">
          <div
            className={`connection-detail ${
              status.api.success ? "success" : "error"
            }`}
          >
            <span>API:</span> {status.api.message}
          </div>
          <div
            className={`connection-detail ${
              status.websocket.success ? "success" : "error"
            }`}
          >
            <span>WebSocket:</span> {status.websocket.message}
          </div>
          <div className="connection-last-checked">
            Last checked:{" "}
            {status.lastChecked
              ? status.lastChecked.toLocaleTimeString()
              : "Never"}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
