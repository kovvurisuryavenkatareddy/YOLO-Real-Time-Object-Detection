import React, { useState } from "react";
import './livestream-styles.css'; // Import the CSS file

const LiveStream = () => {
    const [cameraStatus, setCameraStatus] = useState("stopped");

    const toggleCamera = async () => {
        try {
            const response = await fetch("http://127.0.0.1:5000/toggle_camera", { method: "POST" });
            const data = await response.json();
            setCameraStatus(data.status);
        } catch (error) {
            console.error("Error toggling camera:", error);
        }
    };

    return (
        <div className="live-stream-container">
            <h1 className="live-stream-title">Live Object Detection</h1>

            <button
                className={`camera-toggle-button ${cameraStatus === "running" ? "camera-stop" : "camera-start"}`}
                onClick={toggleCamera}
            >
                {cameraStatus === "running" ? "Stop Camera" : "Start Camera"}
            </button>

            <div className="video-feed-container">
                {cameraStatus === "running" ? (
                    <img
                        src="http://127.0.0.1:5000/video_feed"
                        alt="Camera Feed"
                        className="video-feed"
                    />
                ) : (
                    <p className="camera-off-message">Camera is Off</p>
                )}
            </div>
        </div>
    );
};

export default LiveStream;