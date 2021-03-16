import cv2
import argparse

from imutils.video import FPS

from yolov4.annotate import Detector
from deep_sort.tracker import Tracker
from tools import generate_detections as gdet
from deep_sort import nn_matching
from absl import app, flags, logging
import time, random
import tensorflow as tf
from absl.flags import FLAGS
from deep_sort.detection import Detection
import matplotlib.pyplot as plt
import numpy as np
from deep_sort import preprocessing

"""
Main file to run DeepSORT implementation with given tracker
"""
## Suppress Deprecated Warnings
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

parser = argparse.ArgumentParser(description = "Detect, Track and Count")
parser.add_argument('--stream_source', '-s', default=0, help="Source video stream. Default stream is the webcam")
args = parser.parse_args()

# Definition of the parameters
max_cosine_distance = 0.5
nn_budget = None
nms_max_overlap = 1.0

#initialize deepsort
model_filename = 'networks//mars-small128.pb'
encoder = gdet.create_box_encoder(model_filename, batch_size=1)
metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)





## Initialize Object Detector and Tracker
cap = cv2.VideoCapture(args.stream_source)
video_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # float
video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
det = Detector(video_width, video_height)
deep_sort_tracker = Tracker(metric, det, encoder)
w, h, video_fps = int(cap.get(3)), int(cap.get(4)), cap.get(5)
filename = args.stream_source.split('.')[0]
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('%s-output.mp4'%filename, fourcc, video_fps, (w, h))

total_frames = 0
total_fps = 0

cmap = plt.get_cmap('tab20b')
colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

## Read frames from stream
while(True):
    start_time = time.time()
    ret, frame = cap.read()
    
    if not ret: 
        break

    ## Tracker consumes a frame and spits out an annotated_frame
    
    tracks = deep_sort_tracker.consume(frame)

    for track in tracks:
        if not track.is_confirmed() or track.time_since_update > 1:
            continue
        bbox = track.to_tlbr()
        class_name = track.get_class()
        color = colors[int(track.track_id) % len(colors)]
        color = [i * 255 for i in color]
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color, 2)
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1]-30)), (int(bbox[0])+(len(class_name)+len(str(track.track_id)))*17, int(bbox[1])), color, -1)
        cv2.putText(frame, class_name + "-" + str(track.track_id),(int(bbox[0]), int(bbox[1]-10)),0, 0.75, (255,255,255),2)
    fps = round(1/(time.time()-start_time), 1)
    total_fps += fps
    total_frames += 1
    
    cv2.putText(frame, str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, .8, (255, 255, 255), 2)
    ## Show the frame
    cv2.imshow("Detect, Track and Count", frame)
    print("FPS: " + str(fps))
    ## Save the annotated frame
    out.write(frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


out.release()
cap.release()
cv2.destroyAllWindows()
print("Average FPS: " + str(total_fps/total_frames))