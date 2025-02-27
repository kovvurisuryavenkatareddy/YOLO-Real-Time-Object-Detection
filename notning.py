from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app)

ULTRALYTICS_URL = "https://predict.ultralytics.com"
HEADERS = {"x-api-key": "4924b2713f51a7f016155fce8dea003839428ead7b"}
MODEL_URL = "https://hub.ultralytics.com/models/BZhXSEAF7TvTMY5nWT3X"

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