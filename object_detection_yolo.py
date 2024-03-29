##-*- coding:utf-8 -*-

# This code is written at BigVision LLC. It is based on the OpenCV project. It is subject to the license terms in the LICENSE file found in this distribution and at http://opencv.org/license.html

# Usage example:  python3 object_detection_yolo.py --video=run.mp4
#                 python3 object_detection_yolo.py --image=bird.jpg

import cv2 as cv
import argparse
import sys
import numpy as np
import os.path
import time
from PIL import ImageFont, ImageDraw, Image

import requests

item_key = np.empty(80)
item_key[70] = 1
item_key[3]  = 2
item_key[11] = 3
item_key[41] = 4
item_key[18] = 5


#url = 'http://api.asoft-test1.p-e.kr/process.php?facecode='f1234'&itemkey=4&action='pick''

server_url = "http://api.asoft-test1.p-e.kr/process.php?facecode='f1234'&itemkey={}&action='pick'"

# Initialize the parameters
confThreshold = 0.5  #Confidence threshold
nmsThreshold = 0.4   #Non-maximum suppression threshold
inpWidth = 416       #Width of network's input image
inpHeight = 416      #Height of network's input image

parser = argparse.ArgumentParser(description='Object Detection using YOLO in OPENCV')
parser.add_argument('--image', help='Path to image file.')
parser.add_argument('--video', help='Path to video file.')
parser.add_argument('--cam_no')
args = parser.parse_args()
        
# Load names of classes
#classesFile = "coco.names"
classesFile = "prod_ori_76.names"

classes = None
with open(classesFile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

# Give the configuration and weight files for the model and load the network using them.
modelConfiguration = "yolov3_prod_76.cfg"
modelWeights = "yolov3_prod_76_55000.weights"

# modelConfiguration = "yolov3.cfg"
# modelWeights = "yolov3.weights"

#intel GPU only
#back to CPU model if we don't have intel GPU ( nvidia not supported)
net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# Get the names of the output layers
def getOutputsNames(net):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers, i.e. the layers with unconnected outputs
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Draw the predicted bounding box
def drawPred(frame, classId, conf, left, top, right, bottom):
    # Draw a bounding box.
    cv.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)
    
    label = '%.2f' % conf
        
    # Get the label for the class name and its confidence
    if classes:
        assert(classId < len(classes))
        label = '%s:%s' % (classes[classId], label)

    #Display the label at the top of the bounding box
    labelSize, baseLine = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv.rectangle(frame, (left, top - round(1.5*labelSize[1])), (left + round(1.5*labelSize[0]), top + baseLine), (255, 255, 255), cv.FILLED)
    #cv.putText(frame, label, (left, top), cv.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0), 1)

    # 한글 입력 using PIL
    img_pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(img_pil)

    # ft = cv.freetype.createFreeType2()
    # ft.loadFontData(fontFileName='Ubuntu-R.ttf',
    #                 id=0)
    # ft.putText(img=frame,
    #            text='Quick Fox',
    #            org=(15, 70),
    #            fontHeight=60,
    #            color=(255, 255, 255),
    #            thickness=-1,
    #            line_type=cv.LINE_AA,
    #            bottomLeftOrigin=True)

    font_size = 20
    font_color = (0, 0, 0)
    unicode_font = ImageFont.truetype(font = "NanumGothic.ttf", size = 25)

    # unicode_label =
    # draw.text((10, 10), unicode_label, font=unicode_font, fill=font_color)

    draw.text((left, top-20), label,  fill=font_color, font = unicode_font)
    #bbb = np.array(img_pil)
    frame = np.array(img_pil)
    return frame
    #cv.imshow(winName,bbb)
    #cv.waitKey(100)


# Remove the bounding boxes with low confidence using non-maxima suppression
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    #s_time = time.time()
    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    #e_time = time.time()
    #print('nms elapsed : {}'.format(1/ (e_time-s_time)))
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        frame = drawPred(frame, classIds[i], confidences[i], left, top, left + width, top + height)
    return frame, confidences, classIds
# Process inputs
winName = 'Deep learning object detection in OpenCV'
cv.namedWindow(winName, cv.WINDOW_NORMAL)

outputFile = "yolo_out_py.avi"
if (args.image):
    # Open the image file
    if not os.path.isfile(args.image):
        print("Input image file ", args.image, " doesn't exist")
        sys.exit(1)
    cap = cv.VideoCapture(args.image)
    outputFile = args.image[:-4]+'_yolo_out_py.jpg'
elif (args.video):
    # Open the video file
    if not os.path.isfile(args.video):
        print("Input video file ", args.video, " doesn't exist")
        sys.exit(1)
    cap = cv.VideoCapture(args.video)
    outputFile = args.video[:-4]+'_yolo_out_py.avi'
else:
    # Webcam input
    # kyy
    print(args.cam_no)
    #type(args.cam_no)
    if (args.cam_no) :
        cap = cv.VideoCapture(int(args.cam_no))
    else :
        cap = cv.VideoCapture(0)

# Get the video writer initialized to save the output video
if (not args.image):
    vid_writer = cv.VideoWriter(outputFile, cv.VideoWriter_fourcc('M','J','P','G'), 30, (round(cap.get(cv.CAP_PROP_FRAME_WIDTH)),round(cap.get(cv.CAP_PROP_FRAME_HEIGHT))))

VALID_NUM = 40
frame_no = 1
valid_cnt = 0
det_class = None

lock = False

while cv.waitKey(1) < 0:

    start_time = time.time()
    # get frame from the video
    hasFrame, frame = cap.read()

    if frame_no % 10 != 0:
        frame_no +=1
        continue

    # Stop the program if reached end of video
    if not hasFrame:
        print("Done processing !!!")
        print("Output file is stored as ", outputFile)
        cv.waitKey(3000)
        # Release device
        cap.release()
        break

    # Create a 4D blob from a frame.
    blob = cv.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0,0,0], 1, crop=False)

    # Sets the input to the network
    net.setInput(blob)

    # Runs the forward pass to get output of the output layers
    outs = net.forward(getOutputsNames(net))

    # Remove the bounding boxes with low confidence
    frame, confidences, classIds = postprocess(frame, outs)


    #determine product class

    #print(det_class)
    #print(classes[classIds[0]])
    print('--')
    if classIds and len(set(classIds)) > 1 :
        cv.putText(frame, 'Please one product only !', (00, 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
        valid_cnt = 0

    elif classIds:

        if det_class is None :
            det_class = classIds[0]
        elif det_class == classIds[0] and confidences[0] > 0.75 :
            valid_cnt+=1

        # 현재 클래스랑 다르거나 점수가 낮다면
        else :
            det_class = None
            valid_cnt = 0

    else:
        valid_cnt = 0

    print('valid cnt : {}'.format(valid_cnt))
    if valid_cnt == VALID_NUM:
        print(classIds[0])
        response = requests.get(server_url.format(item_key[classIds[0]]))

        # 전송 실패시 재전송
        print('status : ' + str(response.status_code))
        if response.status_code != 200 :
            valid_cnt -=1


    if valid_cnt >= VALID_NUM :
        # Display the label at the top of the bounding box
        text = 'Item moved to cart!'
        labelSize, baseLine = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1, 1)


        #print(height)
        # get coords based on boundary

        textX = int((frame.shape[1]- labelSize[0]) / 2)
        textY = int((frame.shape[0] + labelSize[1]) / 2)

        #print(textX)
        #print(textY)

        cv.rectangle(frame, (textX - int(labelSize[0]/2) , textY - round(1.5 * labelSize[1])),
                     (textX + round(1.5 * labelSize[0]), textY + baseLine*5), (122, 122, 255), cv.FILLED)
        cv.putText(frame, '      OK!', (textX-10, textY), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
        cv.putText(frame, 'Item moved to cart!', (textX+20, textY + 40), cv.FONT_HERSHEY_SIMPLEX, 0.8,    (255, 255, 255), 2)

    #end time
    end_time = time.time()

    # Put efficiency information. The function getPerfProfile returns the overall time for inference(t) and the timings for each of the layers(in layersTimes)
    #t, _ = net.getPerfProfile()
    #label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
    fps = 'fps : {:.2f}'.format(1 / (end_time - start_time))

    #cv.putText(frame, label, (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
    cv.putText(frame, fps, (0, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))

    # Write the frame with the detection boxes
    #if (args.image):
    #    cv.imwrite(outputFile, frame.astype(np.uint8))
    #else:
    #    vid_writer.write(frame.astype(np.uint8))
    #frame = cv.resize(frame, (frame.shape[0]*2, frame.shape[0]*2))

    cv.imshow(winName, frame)

    frame_no +=1

