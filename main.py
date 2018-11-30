import numpy as np
import cv2
import math
from networktables import NetworkTables
import time

def nothing(self):
    pass

# main
if __name__ == "__main__":
    cap = cv2.VideoCapture('http://root:root@10.45.86.11/mjpg/video.mjpg')
    half_fov = 27.7665349671
    tan = math.tan(math.radians(half_fov))
    # tan_angle = math.tan(40.0/108.0)
    #if true, prints some values
    debug= True

    #Setting sliders
    slider_img = np.zeros((300, 512, 300), np.uint8)
    cv2.namedWindow('Slider')
    name = 'Slider'
    cv2.createTrackbar('Hmin', name, 0, 180, nothing)
    cv2.createTrackbar('Smin', name, 0, 255, nothing)
    cv2.createTrackbar('Vmin', name, 0, 255, nothing)
    cv2.createTrackbar('Hmax', name, 0, 180, nothing)
    cv2.createTrackbar('Smax', name, 0, 255, nothing)
    cv2.createTrackbar('Vmax', name, 0, 255, nothing)

    #Helps the RP communicate with the RIO
    NetworkTables.initialize(server = "10.45.86.2")
    #NetworkTables.setClientMode()
    table = NetworkTables.getTable('imgProc')
    table.putValue("angle", 0)
    table.putValue("distance",0)

    while (True):
        start_time = time.time() #Counts time of each calculation cycle
        _, img = cap.read() #Saves image to img
        height, width, _ = img.shape #set the vars of heigt and with
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # hsv_lower = np.array([cv2.getTrackbarPos('Hmin', name),cv2.getTrackbarPos('Smin', name),cv2.getTrackbarPos('Vmin', name)])
        # hsv_upper = np.array([cv2.getTrackbarPos('Hmax', name),cv2.getTrackbarPos('Smax', name),cv2.getTrackbarPos('Vmax', name)])

        #Sets the values of the HSV
        hsv_lower = np.array([22, 200, 56])
        hsv_upper = np.array([31, 255, 255])
        mask = cv2.inRange(hsv_img, hsv_lower, hsv_upper)
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        filterContours = []
        cover_areaContours = []

        #Calculates Contours (area, perimeter)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            # print area
            if (area > 100) and (perimeter > 50):

                # filterContours.append(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
                cover_area = area / (w * h)

                #filtering contours so we end up with only 2 and not 200
                if cover_area > 0.7:
                    if len(filterContours) < 2:
                        filterContours.append(cnt)
                        cover_areaContours.append(cover_area)
                    else:
                        if cover_areaContours[0] < cover_areaContours[1]:
                            i = 0
                        else:
                            i = 1
                        if cover_area > cover_areaContours[i]:
                            cover_areaContours[i] = cover_area
                            filterContours[i] = cnt
        # average of the middle points of the 2 contours
        midxSum=0
        for cnt in filterContours:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            midx = x + w / 2
            midxSum+=midx
        #calculates angles and lengths
        if len(filterContours) is not 0:
            midxAvg=midxSum/len(filterContours)
            tan_angle = ((midxAvg - width / 2) * tan) / (width / 2) #tangens of angle alfa
            angle = math.degrees(math.atan(tan_angle))
            table.putValue('angle',angle) #sends value to the RIO
            tan_angle = ((midx - width / 2) * tan) / (width / 2)
            angle = math.degrees(math.atan(tan_angle))
            # print angle
            mt = 30  # in cm
            dis = (mt * width) / (2 * w * tan)
            distance = dis / (math.cos((math.radians(angle))))
            print distance
            table.putValue('distance',distance)

            # print angle
            # tan_teta = (tan_angle * width * 0.5) / (w - 0.5*width)
            # teta= math.degrees(math.atan(tan_teta))
            # print teta
            # print angle
        #prints "debugging" (values), if key==27 so stop

        if debug:
            cv2.drawContours(img, filterContours, -1, (255, 0, 0), 1)
            cv2.imshow("image", img)
            cv2.imshow("image2", mask)
            key = 0xff & cv2.waitKey(1)
            if key == 27:
                cv2.destroyAllWindows()
                break
