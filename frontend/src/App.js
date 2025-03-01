import React from "react";
import CameraCapture from "./components/CameraCapture";
import LiveStream from "./components/LiveStream";

const App = () => {
  return (
    <div>
      <h1>Object Detection Application</h1>
      <CameraCapture />
      <LiveStream />
    </div>
  );
};

export default App;
