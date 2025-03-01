import threading
import requests
import base64
import numpy as np
import cv2

from flask import Flask, Response, request, jsonify
from ultralytics import YOLO
import supervision as sv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ULTRALYTICS_URL = "https://predict.ultralytics.com"
HEADERS = {"x-api-key": "4924b2713f51a7f016155fce8dea003839428ead7b"}
MODEL_URL = "https://hub.ultralytics.com/models/BZhXSEAF7TvTMY5nWT3X"


ZONE_POLYGON = np.array([
    [0, 0],
    [0.5, 0],
    [0.5, 1],
    [0, 1]
])

model = YOLO("yolov8n.pt")
lock = threading.Lock()
camera_active = False
cap = None

box_annotator = sv.BoxAnnotator(thickness=2, text_scale=1)
zone_polygon = (ZONE_POLYGON * np.array([1280, 720])).astype(int)
zone = sv.PolygonZone(polygon=zone_polygon, frame_resolution_wh=(1280, 720))
zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.red(), thickness=2, text_scale=2)

def generate_frames():
    """ Continuously captures frames and applies object detection """
    global cap, camera_active

    while camera_active:
        success, frame = cap.read()
        if not success:
            break
        
        with lock:
            if frame is not None:
                result = model(frame, agnostic_nms=True)[0]
                detections = sv.Detections.from_yolov8(result)

                labels = [
                    f"{model.model.names[int(class_id)]} {conf:.2f}"
                    for class_id, conf in zip(detections.class_id, detections.confidence)
                ] if len(detections.class_id) > 0 else []

                frame = box_annotator.annotate(scene=frame, detections=detections, labels=labels)
                zone.trigger(detections=detections)
                frame = zone_annotator.annotate(scene=frame)

                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    """ Toggles the camera ON/OFF """
    global camera_active, cap

    if not camera_active:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera_active = True
    else:
        camera_active = False
        cap.release()

    return jsonify({"status": "running" if camera_active else "stopped"})

@app.route('/video_feed')
def video_feed():
    """ Serves the video feed """
    if camera_active:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(b'')

@app.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    image_path = "temp.jpg"
    file.save(image_path)

    # Send request to Ultralytics API
    data = {"model": MODEL_URL, "imgsz": 640, "conf": 0.25, "iou": 0.45}
    with open(image_path, "rb") as f:
        response = requests.post(ULTRALYTICS_URL, headers=HEADERS, data=data, files={"file": f})

    # Process response
    if response.status_code != 200:
        return jsonify({"error": "Failed to process image"}), 500

    result = response.json()
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    detected_objects = []
    for img_data in result.get("images", []):
        for obj in img_data.get("results", []):
            class_name = obj["name"]
            confidence = obj["confidence"]
            x1, y1, x2, y2 = map(int, (obj["box"]["x1"], obj["box"]["y1"], obj["box"]["x2"], obj["box"]["y2"]))

            # Draw bounding box and label
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
            label = f"{class_name} ({confidence:.2f})"
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            detected_objects.append({"name": class_name, "confidence": confidence})

    # Convert image to base64
    _, buffer = cv2.imencode(".jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    base64_image = base64.b64encode(buffer).decode("utf-8")

    return jsonify({"image": base64_image, "object_count": len(detected_objects), "objects": detected_objects})

if __name__ == "__main__":
    app.run(debug=True)