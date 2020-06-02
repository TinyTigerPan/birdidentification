import cv2
import numpy as np


def fenge(image):
    m,n,_=image.shape
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)

    gradient = cv2.subtract(gradX, gradY)
    gradient = cv2.convertScaleAbs(gradient)
    blurred = cv2.blur(gradient, (9, 9))
    (_, thresh) = cv2.threshold(blurred, 90, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    closed = cv2.erode(closed, None, iterations=4)
    closed = cv2.dilate(closed, None, iterations=4)

    (cnts, _) = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

    # compute the rotated bounding box of the largest contour
    rect = cv2.minAreaRect(c)
    box = np.int0(cv2.boxPoints(rect))
    #cv2.drawContours(image, [box], -1, (0, 255, 0), 3)
    Xs = [i[0] for i in box]
    Ys = [i[1] for i in box]
    x1 = max(min(Xs),0)
    x2 = min(max(Xs),n)
    y1 = max(min(Ys),0)
    y2 = min(max(Ys),m)
    hight = y2 - y1
    width = x2 - x1
    cropImg = image[y1:y1+hight, x1:x1+width]
    # cv2.imwrite("D:/Sobel/fenge.jpg", cropImg)
    # cv2.imshow("Image", cropImg)
    #
    #
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return cropImg
#fenge(image)


def ruihua(image,sigma):
    ker1=np.array([[0,-1,0],
                  [-1,4,-1],
                  [0,-1,0]])

    b,g,r=cv2.split(image)
    bb=cv2.filter2D(b,ddepth=cv2.CV_16S,kernel=ker1)
    gg=cv2.filter2D(g,ddepth=cv2.CV_16S,kernel=ker1)
    rr=cv2.filter2D(r,ddepth=cv2.CV_16S,kernel=ker1)
    new=cv2.merge([bb,gg,rr])
    q=sigma*new//100+image
    q[q<0]=0
    q[q>255]=255
    p=np.uint8(q)
    # # cv2.imwrite('ruihuanew.jpg',p)
    # cv2.imshow('ruihua',p)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return p


def ruihua_(image,size,sigma):
    img = cv2.GaussianBlur(image,ksize=(size,size),sigmaX=0,sigmaY=0)

    new=np.int16(image)-np.int16(img)
    q=sigma*new//100+image
    q[q<0]=0
    q[q>255]=255
    p=np.uint8(q)
    # #cv2.imwrite(r'D:\Sobel\ruihua\aumount200G25.png',p)
    # cv2.imshow(r'D:\Sobel\ruihua\before.png',p)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return p


def image_process(image):
    #image = fenge(image)
    image = ruihua(image, 25)
    return image
