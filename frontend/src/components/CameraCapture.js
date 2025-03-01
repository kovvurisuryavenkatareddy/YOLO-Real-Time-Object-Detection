import React, { useState, useRef } from "react";
import axios from "axios";
import './Cam.css'; // Import the CSS file

const CameraCapture = () => {
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [processedImage, setProcessedImage] = useState(null);
    const [objectCount, setObjectCount] = useState(0);
    const [isCameraOn, setIsCameraOn] = useState(false);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);

    // Toggle Camera
    const toggleCamera = async () => {
        if (isCameraOn) {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                videoRef.current.srcObject = null;
            }
            setIsCameraOn(false);
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 400, height: 300 },
                });
                videoRef.current.srcObject = stream;
                streamRef.current = stream;
                setIsCameraOn(true);
            } catch (error) {
                console.error("Error accessing camera:", error);
            }
        }
    };

    // Capture Image
    const captureImage = () => {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        if (!video.srcObject) {
            alert("Please open the camera first.");
            return;
        }

        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            const file = new File([blob], "captured.jpg", { type: "image/jpeg" });
            setImage(file);
            setPreview(URL.createObjectURL(blob));
        }, "image/jpeg");
    };

    // Handle File Upload
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setImage(file);
            setPreview(URL.createObjectURL(file));
        }
    };

    // Detect Objects
    const detectObjects = async () => {
        if (!image) return alert("Please upload or capture an image first");

        const formData = new FormData();
        formData.append("image", image);

        try {
            const response = await axios.post("http://127.0.0.1:5000/detect", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            setProcessedImage(`data:image/jpeg;base64,${response.data.image}`);
            setObjectCount(response.data.object_count || 0);
        } catch (error) {
            console.error("Error detecting objects:", error);
        }
    };

    return (
        <div className="container">
            <h2>Image Object Detection</h2>

            <div className="video-section">
                <div className="video-container">
                    <video ref={videoRef} autoPlay playsInline width="400" height="300" className="video"></video>
                    {!isCameraOn && <p className="camera-off-text">Camera is Off</p>}
                </div>
            </div>


            <div className="controls-container">
                <div className="controls">
                    <button
                        className={` ${isCameraOn ? "turn-off-camera" : "open-camera"}`}
                        onClick={toggleCamera}
                    >
                        {isCameraOn ? "Turn Off Camera" : "Open Camera"}
                    </button>

                    <button
                        onClick={captureImage}
                        disabled={!isCameraOn}
                        className={`capture-image ${!isCameraOn ? "" : ""}`}
                    >
                        Capture Image
                    </button>
                </div>

                <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                />
            </div>


            <canvas ref={canvasRef} style={{ display: "none" }} width="400" height="300"></canvas>

            {preview && (
                <div className="preview-section">
                    <h3>Preview</h3>
                    <img src={preview} alt="Preview" width="300" className="preview-image" />
                </div>
            )}

            <button
                onClick={detectObjects}
                className="detect-objects"
            >
                Detect Objects
            </button>

            {objectCount > 0 && <h3 className="object-count">Objects Detected: {objectCount}</h3>}

            {processedImage && (
                <div className="processed-section">
                    <h3>Processed Image</h3>
                    <img src={processedImage} alt="Processed" width="400" className="processed-image" />
                </div>
            )}
        </div>
    );
};

export default CameraCapture;