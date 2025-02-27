import React, { useState, useRef } from "react";
import axios from "axios";

const App = () => {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [objectCount, setObjectCount] = useState(0);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Open Camera
  const openCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 400, height: 300 } });
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
    } catch (error) {
      console.error("Error accessing camera:", error);
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

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        video.srcObject = null;
      }
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
    <div>
      <h2>Object Detection</h2>

      <video ref={videoRef} autoPlay playsInline width="400" height="300"></video>
      <button onClick={openCamera}>Open Camera</button>
      <button onClick={captureImage}>Capture Image</button>

      <canvas ref={canvasRef} style={{ display: "none" }} width="400" height="300"></canvas>

      <input type="file" accept="image/*" onChange={handleFileChange} />

      {preview && <img src={preview} alt="Preview" width="300" />}

      <button onClick={detectObjects}>Detect Objects</button>

      {objectCount > 0 && <h3>Objects Detected: {objectCount}</h3>}

      {processedImage && <img src={processedImage} alt="Processed" width="400" />}
    </div>
  );
};

export default App;
