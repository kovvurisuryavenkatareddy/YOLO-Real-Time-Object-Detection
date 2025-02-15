import cv2
import threading
import argparse
from ultralytics import YOLO
import supervision as sv
import numpy as np
import time

ZONE_POLYGON = np.array([
    [0, 0],
    [0.5, 0],
    [0.5, 1],
    [0, 1]
])

class FrameCaptureThread(threading.Thread):
    def __init__(self, cap, frame_holder, lock, stop_flag):
        threading.Thread.__init__(self)
        self.cap = cap
        self.frame_holder = frame_holder
        self.lock = lock
        self.stop_flag = stop_flag

    def run(self):
        while not self.stop_flag[0]:  # Check if stop_flag is False
            ret, frame = self.cap.read()
            if not ret:
                break
            with self.lock:
                self.frame_holder[0] = frame  # Capture the frame

class DetectionThread(threading.Thread):
    def __init__(self, frame_holder, model, box_annotator, zone, zone_annotator, lock, stop_flag):
        threading.Thread.__init__(self)
        self.frame_holder = frame_holder
        self.model = model
        self.box_annotator = box_annotator
        self.zone = zone
        self.zone_annotator = zone_annotator
        self.lock = lock
        self.stop_flag = stop_flag
        self.skip_frames = 2  # Number of frames to skip for performance optimization
        self.frame_counter = 0

    def run(self):
        while not self.stop_flag[0]:  # Check if stop_flag is False
            with self.lock:
                if self.frame_holder[0] is not None and self.frame_counter % self.skip_frames == 0:
                    frame = self.frame_holder[0]
                    result = self.model(frame, agnostic_nms=True)[0]
                    detections = sv.Detections.from_yolov8(result)

                    if len(detections.class_id) > 0:
                        labels = [
                            f"{self.model.model.names[int(class_id)]} {conf:.2f}"
                            for class_id, conf in zip(detections.class_id, detections.confidence)
                        ]
                    else:
                        labels = []

                    frame = self.box_annotator.annotate(scene=frame, detections=detections, labels=labels)
                    self.zone.trigger(detections=detections)
                    frame = self.zone_annotator.annotate(scene=frame)

                    cv2.imshow("YOLOv8 - Live Detection", frame)
                    
                    key = cv2.waitKey(1)
                    if key == 27:  # Press ESC to exit
                        self.stop_flag[0] = True  # Set stop flag to True to stop the loop
                        break
                self.frame_counter += 1

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 live")
    parser.add_argument(
        "--webcam-resolution", 
        default=[1280, 720], 
        nargs=2, 
        type=int
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()
    frame_width, frame_height = args.webcam_resolution

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    model = YOLO("yolov8l.pt")

    box_annotator = sv.BoxAnnotator(
        thickness=2,
        text_scale=1
    )

    zone_polygon = (ZONE_POLYGON * np.array(args.webcam_resolution)).astype(int)
    zone = sv.PolygonZone(polygon=zone_polygon, frame_resolution_wh=tuple(args.webcam_resolution))
    zone_annotator = sv.PolygonZoneAnnotator(
        zone=zone, 
        color=sv.Color.red(),
        thickness=2,
        text_scale=2
    )

    # Shared frame container, lock for synchronization, and stop flag
    frame_holder = [None]
    lock = threading.Lock()
    stop_flag = [False]  # Flag to signal when to stop the threads

    # Create threads
    frame_capture_thread = FrameCaptureThread(cap, frame_holder, lock, stop_flag)
    detection_thread = DetectionThread(frame_holder, model, box_annotator, zone, zone_annotator, lock, stop_flag)

    # Start threads
    frame_capture_thread.start()
    detection_thread.start()

    # Wait for threads to complete
    frame_capture_thread.join()
    detection_thread.join()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
