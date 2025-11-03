from collections import deque
from IPython.display import HTML
import numpy as np
import array as arr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import mpl_toolkits.mplot3d.axes3d as p3
import math
import time
import argparse
import imutils
import xlwt
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-v1", "--video1", help="Video Datei mit XZ Koordinaten")
ap.add_argument("-v2", "--video2", help="Video Datei mit XY Koordinaten")
ap.add_argument("-i1", "--image1", help="Ueberlagerndes Bild fuer XZ")
ap.add_argument("-i2", "--image2", help="Ueberlagerndes Bild fuer XY")
ap.add_argument("-b1", "--buffer1", type=int, default=64, help="max buffer size")
ap.add_argument("-b2", "--buffer2", type=int, default=64, help="max buffer size")
args = vars(ap.parse_args())

fps = 120.0                     # Aufnahmegeschwindigkeit der Kamera
angleOfViewVertical = 159.76    # Bildwinkel in vertikaler Richtung
angleOfViewHorizontal = 168.54  # Bildwinkel in horizontaler Richtung
XNet = 285.0                    # X-Wert des Netzes
YMinTable = 18.0                # kleinster Y-Wert der Kante der Tischtennisplatte
YMaxTable = 312.0               # groesster Y-Wert der Kante der Tischtennisplatte

NetHight = 15.25                # Hoehe des Tischtennistetzes in Zentimeter
ZBackNetHight = 199.0           # Hoehe des Tischtennistetzes am hinteren Ende in Z-Koordinaten
ZFrontNetHight = 150.0          # Hoehe des Tischtennistetzes am vorderen Ende in Z-Koordinaten

DiffRods = 0.87                 # Abstand der beiden Stuetzen der Platte auf einer Seite in Meter zur Umrechnug
XRodFrontLeft = 122.0           # X-Wert der Stuetze im Bildhintergrund links
XRodFrontRight = 486.0          # X-Wert der Stuetze im Bildvordergrund rechts

grayLower1 = 105                # Grenzwerte der Helligkeit des Balls im verarbeiteten Bild
grayUpper1 = 255
grayLower2 = 150
grayUpper2 = 255

SaveX = []
SaveY = []
SaveY2 = []
SaveZ = []
SaveFrame1 = []
SaveFrame2 = []
PlotIndex = []
PlotX = []
PlotY = []
PlotZ = []
Player1NetHight = []
Player1BallSpeed = []
Player1BallBounce = []
Player2NetHight = []
Player2BallSpeed = []
Player2BallBounce = []
LastHit = None
StartPoint1Found = False
StartPoint2Found = False

toleranceExtremum = 1.5
frame = 0
d_plot = 0
n_plot = 0
lineBuffer_plot = 20
pts1 = deque(maxlen=args["buffer1"])
pts2 = deque(maxlen=args["buffer2"])

def checkAllOf(arr, val):       # Ueberpruefen, ob alle Werte von arr val entsprechen
    m = 0
    for i in arr: 
        if val == i and m == 0: 
            m = 0
        else:
            m = 1
    if m == 0:
        return True
    else:
        return False
    
def checkOneOf(arr, val):       # Ueberpruefen, ob ein Wert von arr val entspricht
    for i in arr: 
        if val == i: 
            return True
    return False

def GetParabola(X1, Y1, X2, Y2, X3, Y3):        # Geradengleichung y = a(x*x) + bx + c zurueckgeben
    a = ((Y3 - Y2) * (X2 - X1) - (Y2 - Y1) * (X3 - X2)) / (((X3*X3) - (X2*X2)) * (X2 - X1) -  ((X2*X2) - (X1*X1)) * (X3 - X2))
    b = (Y2 - Y1 - a * ((X2*X2) - (X1*X1))) / (X2 - X1)
    c = Y1 - a * (X1*X1) - b * X1
    
    return a, b, c

def GetLine(X1, Y1, X2, Y2):                    # Geradengleichung y = mx + t zurueckgeben
    m = (Y1 - Y2) / (X1 - X2)
    t = Y1 - m * X1
    return m, t

def FindExtremum(values, typeExtremum):         # bei typeExtremum gleich -1 Minima in values finden
    n = 0                                       # bei typeExtremum gleich +1 Maxima in values finden
    p = 0                                       # bei typeExtremum gleich 0 alle Extrema in values finden 
    i = 1
    Extrema = []
    ExtremaIndex = arr.array('i', [])
    while i < len(values) - 1:
        while abs(values[i-n] - values[i]) <= toleranceExtremum and i - n > 0:
            n = n + 1
        while abs(values[i+p] - values[i]) <= toleranceExtremum and i + p < len(values) - 1:
            p = p + 1
        if values[i-n] < values[i] and values[i] > values[i+p] and (typeExtremum == 1 or typeExtremum == 0):
            Extrema.append(values[i])
            ExtremaIndex.append(i)
        if values[i-n] > values[i] and values[i] < values[i+p] and (typeExtremum == -1 or typeExtremum == 0):
            Extrema.append(values[i])
            ExtremaIndex.append(i)
        i = i + p
        n = 1
        p = 1
    return Extrema, ExtremaIndex

def LocateArea(valX, valY):                     # Position von (valX, valY) auf der Platte bestimmen
    n = 1.0
    row = str(int(n))
    while n <= 6 and valX > ((n/6) * (width-200) + 100):
        n = n + 1
        row = str(int(n))
    if  valY > YMinTable + (2 * (YMaxTable - YMinTable) / 3):
        column = 'C'
    elif  valY < YMinTable + ((YMaxTable - YMinTable) / 3):
        column = 'A'
    else:
        column = 'B'
    return column + ' ' + row

def GetSpeed(GraphStart, GraphEnd):             # Geschwindigkeit der Ballkurve bestimmen
    if GraphStart > GraphEnd:
        cache = GraphStart
        GraphStart = GraphEnd
        GraphEnd = cache
    n = 0
    s = 0
    while GraphStart + n + 1 < GraphEnd:
        XDistance = DiffRods / abs(XRodFrontRight - XRodFrontLeft) * abs(SaveX[GraphStart+n] - SaveX[GraphStart+n+1])
        YDistance = DiffRods / abs(XRodFrontRight - XRodFrontLeft) * abs(SaveY[GraphStart+n] - SaveY[GraphStart+n+1])
        ZDistance = DiffRods / abs(XRodFrontRight - XRodFrontLeft) * abs(SaveZ[GraphStart+n] - SaveZ[GraphStart+n+1])
        s = s + math.sqrt(math.pow(abs(XDistance), 2) + math.pow(abs(YDistance), 2) + math.pow(abs(ZDistance), 2))
        n = n + 1
    t = abs(SaveFrame1[GraphStart] - SaveFrame1[GraphEnd]) / fps
    v = s / t
    v = round(v, 1)
    if v < 10.0:
        v = ' ' + str(v) + ' m/s'
    else:
        v = str(v) + ' m/s'
    return v

def GetHightOverNet(GraphStart, GraphEnd):      # Hoehe des Balls beim Ueberqueren des Netzes besimmen
    if SaveX[GraphStart] > SaveX[GraphEnd]:
        n = 0
        while SaveX[GraphStart+n] > XNet:
            n = n + 1
    else:
        n = 0
        while SaveX[GraphStart+n] < XNet:
            n = n + 1
    IndexP1 = GraphStart + n - 1
    IndexP2 = GraphStart + n
    IndexP3 = GraphStart + n + 1
    a, b, c = GetParabola(SaveX[IndexP1], SaveZ[IndexP1], SaveX[IndexP2], SaveZ[IndexP2], SaveX[IndexP3], SaveZ[IndexP3])
    ZBall = a * math.pow(XNet, 2) + b * XNet + c
    YBall = SaveY[IndexP1] + ((abs(XNet - SaveX[IndexP1]) / abs(SaveX[IndexP2] - SaveX[IndexP1])) * abs(SaveY[IndexP2] - SaveY[IndexP1]))
    Slope, Intercept = GetLine(YMinTable, ZFrontNetHight, YMaxTable, ZBackNetHight)
    ZNet = Slope * YBall + Intercept
    ZNet = (2 * ZNet * (45 * height + angleOfViewVertical * YBall) + angleOfViewVertical * height * (height - YBall)) / (2 * (45 * height + angleOfViewVertical * height))
    ZNetDiff = ZNet - ZBall
    NetDiffCm = DiffRods / abs(XRodFrontRight - XRodFrontLeft) * ZNetDiff * 100.0
    NetDiffCm = round(NetDiffCm, 1)
    if NetDiffCm < 10.0:
        NetDiffCm = ' ' + str(NetDiffCm) + ' cm'
    else:
        NetDiffCm = str(NetDiffCm) + ' cm'
    return NetDiffCm

video1 = cv2.VideoCapture(args["video1"])
(grabbed1, frame1) = video1.read()
overlay1 = cv2.imread(args["image1"])
overlay1 = cv2.resize(overlay1, frame1.shape[1::-1])
video2 = cv2.VideoCapture(args["video2"])
(grabbed2, frame2) = video2.read()
overlay2 = cv2.imread(args["image2"])
overlay2 = cv2.resize(overlay2, frame2.shape[1::-1])

while not StartPoint1Found:                     # Finden des Zeitpunkts der ersten Balldetektion zum Videoangleich
    (grabbed1, frame1) = video1.read()
    if args.get("video1") and not grabbed1:
        break
    
    frame1 = cv2.bitwise_and(frame1, overlay1)
    
    frame1 = imutils.resize(frame1, width=600)
    height = float(frame1.shape[0])
    width = float(frame1.shape[1])
    (blueChannel1, greenChannel1, redChannel1) = cv2.split(frame1)
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    
    blue1 = cv2.subtract(greenChannel1, blueChannel1)
    red1 = cv2.subtract(redChannel1, blueChannel1)
    frame1 = cv2.addWeighted(blue1, 0.5, red1, 0.5, 1)
    
    mask1 = cv2.inRange(frame1, grayLower1, grayUpper1)
    mask1 = cv2.erode(mask1, None, iterations=1)
    mask1 = cv2.dilate(mask1, None, iterations=1)

    cnts1 = cv2.findContours(mask1.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center1 = None

    if len(cnts1) > 0:
        c1 = max(cnts1, key=cv2.contourArea)
        ((x1, y1), radius1) = cv2.minEnclosingCircle(c1)

        if radius1 > 0:
            cv2.circle(frame1, (int(x1), int(y1)), int(radius1), (255), 2)
            StartPoint1Found = True

    cv2.imshow("Mask1", mask1)
    cv2.imshow("Frame1", frame1)
    key = cv2.waitKey(1) & 0xFF

while not StartPoint2Found:                     # Finden des Zeitpunkts der ersten Balldetektion zum Videoangleich
    (grabbed2, frame2) = video2.read()
    if args.get("video2") and not grabbed2:
        break
    
    frame2 = cv2.bitwise_and(frame2, overlay2)

    frame2 = imutils.resize(frame2, width=600)
    (blueChannel2, greenChannel2, redChannel2) = cv2.split(frame2)

    blue2 = cv2.subtract(greenChannel2, blueChannel2)
    red2 = cv2.subtract(redChannel2, blueChannel2)
    frame2 = cv2.addWeighted(blue2, 0.5, red2, 0.5, 1)
    
    mask2 = cv2.inRange(frame2, grayLower2, grayUpper2)
    mask2 = cv2.erode(mask2, None, iterations=1)
    mask2 = cv2.dilate(mask2, None, iterations=1)
    
    cnts2 = cv2.findContours(mask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center2 = None
    
    if len(cnts2) > 0:
        c2 = max(cnts2, key=cv2.contourArea)
        ((x2, y2), radius2) = cv2.minEnclosingCircle(c2)

        if radius2 > 0:
            cv2.circle(frame2, (int(x2), int(y2)), int(radius2), (255), 2)
            StartPoint2Found = True
            
    cv2.imshow("Mask2", mask2)
    cv2.imshow("Frame2", frame2)
    key = cv2.waitKey(1) & 0xFF

XRodFrontLeft = (2 * XRodFrontLeft * (45 * width + angleOfViewHorizontal * YMinTable) + angleOfViewHorizontal * width * (height - YMinTable)) / (2 * (45 * width + angleOfViewHorizontal * height))
XRodFrontRight = (2 * XRodFrontRight * (45 * width + angleOfViewHorizontal * YMinTable) + angleOfViewHorizontal * width * (height - YMinTable)) / (2 * (45 * width + angleOfViewHorizontal * height))

while True:                             # Bildverarbeitung, Detektieren des Balls und Speichern der Koordinaten
    (grabbed1, frame1) = video1.read()
    
    (grabbed2, frame2) = video2.read()
    
    frame = frame + 1
    print 'frame ', frame

    if args.get("video1") and not grabbed1:
        break
    
    if args.get("video2") and not grabbed2:
        break
    
    frame1 = cv2.bitwise_and(frame1, overlay1)
    frame2 = cv2.bitwise_and(frame2, overlay2)
    
    frame1 = imutils.resize(frame1, width=600)
    (blueChannel1, greenChannel1, redChannel1) = cv2.split(frame1)
    
    frame2 = imutils.resize(frame2, width=600)
    (blueChannel2, greenChannel2, redChannel2) = cv2.split(frame2)
    
    blue1 = cv2.subtract(greenChannel1, blueChannel1)
    red1 = cv2.subtract(redChannel1, blueChannel1)
    frame1 = cv2.addWeighted(blue1, 0.5, red1, 0.5, 1)
    
    blue2 = cv2.subtract(greenChannel2, blueChannel2)
    red2 = cv2.subtract(redChannel2, blueChannel2)
    frame2 = cv2.addWeighted(blue2, 0.5, red2, 0.5, 1)
    
    mask1 = cv2.inRange(frame1, grayLower1, grayUpper1)
    mask1 = cv2.erode(mask1, None, iterations=1)
    mask1 = cv2.dilate(mask1, None, iterations=1)
    
    mask2 = cv2.inRange(frame2, grayLower2, grayUpper2)
    mask2 = cv2.erode(mask2, None, iterations=1)
    mask2 = cv2.dilate(mask2, None, iterations=1)

    cnts1 = cv2.findContours(mask1.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center1 = None
    
    cnts2 = cv2.findContours(mask2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center2 = None
    
    if len(cnts1) > 0:
        c1 = max(cnts1, key=cv2.contourArea)
        ((x1, y1), radius1) = cv2.minEnclosingCircle(c1)
        M1 = cv2.moments(c1)
        center1 = (int(M1["m10"] / M1["m00"]), int(M1["m01"] / M1["m00"]))
        
        if radius1 > 0:
            cv2.circle(frame1, (int(x1), int(y1)), int(radius1), (255), 2)
            SaveX.append(x1)
            SaveZ.append(y1)
            SaveFrame1.append(frame)
            
    if len(cnts2) > 0:
        c2 = max(cnts2, key=cv2.contourArea)
        ((x2, y2), radius2) = cv2.minEnclosingCircle(c2)
        M2 = cv2.moments(c2)
        center2 = (int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"]))
        
        if radius2 > 0:
            cv2.circle(frame2, (int(x2), int(y2)), int(radius2), (255), 2)
            SaveY2.append(y2)
            SaveFrame2.append(frame)
    
    pts1.appendleft(center1)
    pts2.appendleft(center2)
    
    if len(SaveFrame1) > 1:
        if checkAllOf(SaveX[-9:], -1):
            del SaveX[-9:]
            del SaveZ[-9:]
            del SaveFrame1[-9:]
        elif frame - SaveFrame1[-1] > 4:
            SaveX.append(-1)
            SaveZ.append(-1)
            SaveFrame1.append(frame)
            
    for i in range(1, len(pts1)):
        if pts1[i - 1] is None or pts1[i] is None:
            continue

        thickness = int(np.sqrt(args["buffer1"] / float(i + 1)) * 2.5)
        cv2.line(mask1, pts1[i - 1], pts1[i], (255), thickness)
        thickness = int(np.sqrt(args["buffer2"] / float(i + 1)) * 2.5)
        cv2.line(mask2, pts2[i - 1], pts2[i], (255), thickness)

    cv2.imshow("Frame1", frame1)
    cv2.imshow("Frame2", frame2)
    cv2.imshow("Mask1", mask1)
    cv2.imshow("Mask2", mask2)
    
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    
video1.release()
video2.release()
cv2.destroyAllWindows()

missingPoints = 0
i = 0
while i < len(SaveX):               # fehlende X und Z Koordinaten bestimmen
    if not checkAllOf(SaveX[i:], -1):
        if SaveX[i] < 0:
            P1X = SaveX[(i-2)]
            P1Y = SaveZ[(i-2)]
            P2X = SaveX[(i-1)]
            P2Y = SaveZ[(i-1)]
            
            while i + missingPoints + 1 < len(SaveX) and SaveX[(i+missingPoints)] < 0:
                missingPoints = missingPoints + 1
            
            P3X = SaveX[(i+missingPoints)]
            P3Y = SaveZ[(i+missingPoints)]
            
            if abs(P1X-P2X) > toleranceExtremum and abs(P1X-P3X) > toleranceExtremum and abs(P2X-P3X) > toleranceExtremum and abs(P1Y-P2Y) > toleranceExtremum and abs(P1Y-P3Y) > toleranceExtremum and abs(P2Y-P3Y) > toleranceExtremum:     
                a, b, c = GetParabola(P1X, P1Y, P2X, P2Y, P3X, P3Y)
                
                SaveX[i] = SaveX[(i-1)] + (((SaveFrame1[i] - SaveFrame1[(i-1)]) / (SaveFrame1[(i+missingPoints)] - SaveFrame1[(i-1)])) * (SaveX[(i+missingPoints)] - SaveX[(i-1)]))
                SaveZ[i] = a * math.pow(SaveX[i], 2) + b * SaveX[i] + c
            
            else:
                del SaveX[i]
                del SaveZ[i]
                del SaveFrame1[i]
                i = i - 1
    
    else:
        del SaveX[i:]
        del SaveZ[i:]
        del SaveFrame1[i:]
    i = i + 1
    missingPoints = 0

i = 0
while i < len(SaveX):                   # fehlende Y Koordinaten bestimmen
    n = 0
    while n + 1 < len(SaveFrame2) and SaveFrame1[i] > SaveFrame2[n]:
        n = n + 1
    if SaveFrame1[i] == SaveFrame2[n]:
        SaveY.append(SaveY2[n])
    elif n > 0:
        UpperYIndex = n
        n = n - 1
        LowerYIndex = n
        SaveY.append(SaveY2[LowerYIndex] + (((SaveFrame1[i] - SaveFrame2[LowerYIndex]) / (SaveFrame2[UpperYIndex] - SaveFrame2[LowerYIndex])) * (SaveY2[UpperYIndex] - SaveY2[LowerYIndex])))
    else:
        del SaveX[i]
        del SaveZ[i]
        del SaveFrame1[i]
        i = i - 1
    i = i + 1

for i in range(len(SaveX)):             # perspektivische Koordinaten in kartesische umrechnen
    SaveX[i] = (2 * SaveX[i] * (45 * width + angleOfViewHorizontal * SaveY[i]) + angleOfViewHorizontal * width * (height - SaveY[i])) / (2 * (45 * width + angleOfViewHorizontal * height))
    SaveZ[i] = (2 * SaveZ[i] * (45 * height + angleOfViewVertical * SaveY[i]) + angleOfViewVertical * height * (height - SaveY[i])) / (2 * (45 * height + angleOfViewVertical * height))

ExtremaX, ExtremaIndexX = FindExtremum(SaveX, 0)        # Start - und Endpunkte der Flugkurven bestimmen
for i in range(len(ExtremaX)):
    if i > 0:
        if ExtremaX[i] > XNet + 40 and ExtremaX[i-1] < XNet - 40:
            if LastHit == 'Player1':
                Player2BallBounce.append('f.S.')
                Player2BallSpeed.append('f.S.')
                Player2NetHight.append('f.S.')
            LastHit = 'Player1'
            GraphStart = ExtremaIndexX[i-1]
            GraphEnd = ExtremaIndexX[i]
            PlotIndex.append(GraphStart)
            PlotIndex.append(GraphEnd)
            
            ExtremaZ, ExtremaIndexZ = FindExtremum(SaveZ[GraphStart:(GraphEnd+1)], 1)
            # Auftreffpunkte auf der Platte bestimmen
            n = 0
            while n < len(ExtremaZ):
                ExtremaIndexZ[n] = GraphStart + ExtremaIndexZ[n]
                n = n + 1
            if len(ExtremaZ) >= 1 and SaveX[ExtremaIndexZ[-1]] > XNet:
                Player1BallBounce.append(LocateArea(SaveX[ExtremaIndexZ[-1]], SaveY[ExtremaIndexZ[-1]]))
                Player1BallSpeed.append(GetSpeed(GraphStart, GraphEnd))
                Player1NetHight.append(GetHightOverNet(GraphStart, GraphEnd))
            else:
                Player1BallBounce.append('f.S.')
                Player1BallSpeed.append('f.S.')
                Player1NetHight.append('f.S.')
            
        elif i > 0 and ExtremaX[i] < XNet - 40 and ExtremaX[i-1] > XNet + 40:
            if LastHit == 'Player2':
                Player1BallBounce.append('f.S.')
                Player1BallSpeed.append('f.S.')
                Player1NetHight.append('f.S.')
            LastHit = 'Player2'
            GraphStart = ExtremaIndexX[i-1]
            GraphEnd = ExtremaIndexX[i]
            PlotIndex.append(GraphStart)
            PlotIndex.append(GraphEnd)
            
            ExtremaZ, ExtremaIndexZ = FindExtremum(SaveZ[GraphStart:(GraphEnd+1)], 1)
            # Auftreffpunkte auf der Platte bestimmen
            n = 0
            while n < len(ExtremaZ):
                ExtremaIndexZ[n] = GraphStart + ExtremaIndexZ[n]
                n = n + 1
            if len(ExtremaZ) >= 1 and SaveX[ExtremaIndexZ[-1]] < XNet:
                Player2BallBounce.append(LocateArea(SaveX[ExtremaIndexZ[-1]], SaveY[ExtremaIndexZ[-1]]))
                Player2BallSpeed.append(GetSpeed(GraphStart, GraphEnd))
                Player2NetHight.append(GetHightOverNet(GraphStart, GraphEnd))
            else:
                Player2BallBounce.append('f.S.')
                Player2BallSpeed.append('f.S.')
                Player2NetHight.append('f.S.')

while len(Player1NetHight) < len(Player2NetHight):
    Player1BallBounce.append('')
    Player1BallSpeed.append('')
    Player1NetHight.append('')
while len(Player1NetHight) > len(Player2NetHight):
    Player2BallBounce.append('')
    Player2BallSpeed.append('')
    Player2NetHight.append('')

wb = xlwt.Workbook()                # Tabelle erstellen und danach Werte hinzufuegen
style_headline = xlwt.easyxf('font: bold on, height 320, underline on; align: horiz left;')
style_title = xlwt.easyxf('font: bold on, height 240, underline off; align: horiz left;')
style_cellAlignCenter = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz center;')
style_cellAlignRight = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz right;')
style_cellAlignLeft = xlwt.easyxf('font: bold off, height 200, underline off;  align: horiz left;')

Sheet1 = wb.add_sheet("HightOverNet")
Sheet1.write(0, 0, "Abstand des Balls zum Netz", style_headline)
Sheet1.write(2, 0, "Schlag Nr.", style_title)
Sheet1.write(2, 1, "", style_title)
Sheet1.write(2, 2, "Spieler 1", style_title)
Sheet1.write(2, 3, "", style_title)
Sheet1.write(2, 4, "Spieler 2", style_title)
Sheet1.write(3, 6, "f.S. = fehlerhafter Schlag", style_cellAlignLeft)
for i in range(len(Player1NetHight)):
    Sheet1.write(i+3, 0, i+1, style_cellAlignCenter)
    Sheet1.write(i+3, 1, "", style_cellAlignCenter)
    if Player1NetHight[i] == 'Detektion nicht moeglich':
        Sheet1.write(i+3, 2, Player1NetHight[i], style_cellAlignLeft)
    else:
        Sheet1.write(i+3, 2, Player1NetHight[i], style_cellAlignRight)
    Sheet1.write(i+3, 3, "", style_cellAlignCenter)
    if Player2NetHight[i] == 'Detektion nicht moeglich':
        Sheet1.write(i+3, 4, Player2NetHight[i], style_cellAlignLeft)
    else:
        Sheet1.write(i+3, 4, Player2NetHight[i], style_cellAlignRight)

Sheet2 = wb.add_sheet("BallSpeed")
Sheet2.write(0, 0, "Geschwindigkeit des Balls", style_headline)
Sheet2.write(2, 0, "Schlag Nr.", style_title)
Sheet2.write(2, 1, "", style_title)
Sheet2.write(2, 2, "Spieler 1", style_title)
Sheet2.write(2, 3, "", style_title)
Sheet2.write(2, 4, "Spieler 2", style_title)
Sheet2.write(3, 6, "f.S. = fehlerhafter Schlag", style_cellAlignLeft)
for i in range(len(Player1BallSpeed)):
    Sheet2.write(i+3, 0, i+1, style_cellAlignCenter)
    Sheet2.write(i+3, 1, "", style_cellAlignCenter)
    if Player1BallSpeed[i] == 'Detektion nicht moeglich':
        Sheet2.write(i+3, 2, Player1BallSpeed[i], style_cellAlignLeft)
    else:
        Sheet2.write(i+3, 2, Player1BallSpeed[i], style_cellAlignRight)
    Sheet2.write(i+3, 3, "", style_cellAlignCenter)
    if Player2BallSpeed[i] == 'Detektion nicht moeglich':
        Sheet2.write(i+3, 4, Player2BallSpeed[i], style_cellAlignLeft)
    else:
        Sheet2.write(i+3, 4, Player2BallSpeed[i], style_cellAlignRight)

Sheet3 = wb.add_sheet("BallBouncePoint")
Sheet3.write(0, 0, "Auftreffpunkt des Balls", style_headline)
Sheet3.write(2, 0, "Schlag Nr.", style_title)
Sheet3.write(2, 1, "", style_title)
Sheet3.write(2, 2, "Spieler 1", style_title)
Sheet3.write(2, 3, "", style_title)
Sheet3.write(2, 4, "Spieler 2", style_title)
Sheet3.write(3, 6, "f.S. = fehlerhafter Schlag", style_cellAlignLeft)
for i in range(len(Player1BallBounce)):
    Sheet3.write(i+3, 0, i+1, style_cellAlignCenter)
    Sheet3.write(i+3, 1, "", style_cellAlignCenter)
    if Player1BallBounce[i] == 'Detektion nicht moeglich':
        Sheet3.write(i+3, 2, Player1BallBounce[i], style_cellAlignLeft)
    else:
        Sheet3.write(i+3, 2, Player1BallBounce[i], style_cellAlignRight)
    Sheet3.write(i+3, 3, "", style_cellAlignCenter)
    if Player2BallBounce[i] == 'Detektion nicht moeglich':
        Sheet3.write(i+3, 4, Player2BallBounce[i], style_cellAlignLeft)
    else:
        Sheet3.write(i+3, 4, Player2BallBounce[i], style_cellAlignRight)

Sheet1.col(0).width = 256 * 12
Sheet1.col(1).width = 256 * 3
Sheet1.col(2).width = 256 * 12
Sheet1.col(3).width = 256 * 3
Sheet1.col(4).width = 256 * 12
Sheet1.row(0).height = (256/10) * 16
Sheet1.row(2).height = (256/10) * 12

Sheet2.col(0).width = 256 * 12
Sheet2.col(1).width = 256 * 3
Sheet2.col(2).width = 256 * 12
Sheet2.col(3).width = 256 * 3
Sheet2.col(4).width = 256 * 12
Sheet2.row(0).height = (256/10) * 16
Sheet2.row(2).height = (256/10) * 12

Sheet3.col(0).width = 256 * 12
Sheet3.col(1).width = 256 * 3
Sheet3.col(2).width = 256 * 12
Sheet3.col(3).width = 256 * 3
Sheet3.col(4).width = 256 * 12
Sheet3.row(0).height = (256/10) * 16
Sheet3.row(2).height = (256/10) * 12
Sheet3.insert_bitmap('tischtennis-platte.bmp', 2, 8)
wb.save("TableTennisData.xls")

i = 1
n = 0
while i <= frame and n < len(SaveFrame1):           # fuer jeden Frame Koordinaten hinzufuegen
    if i == SaveFrame1[n]:
        n = n + 1
    elif i >= 2:
        SaveX.insert(i-1, SaveX[i-2])
        SaveY.insert(i-1, SaveY[i-2])
        SaveZ.insert(i-1, SaveZ[i-2])
    i = i + 1
    
i = 0
n = 1
while i <= PlotIndex[-1] and n < len(PlotIndex):
    if i >= PlotIndex[n-1] and i <= PlotIndex[n]:
        PlotX.append(SaveX[i])
        PlotY.append(SaveY[i])
        PlotZ.append(SaveZ[i])
    if i > PlotIndex[n]:
        n = n + 2
    else:
        i = i + 1
    
for i in range(len(PlotZ)):
    PlotZ[i] = -PlotZ[i] + 400

fig = plt.figure()                                  # 3d-Plot erstellen und Werte hinzufuegen
ax1 = fig.add_subplot(1, 1, 1,projection="3d")
ax2 = fig.add_subplot(4, 2, 1)
ax3 = fig.add_subplot(4, 2, 2)

ax1.view_init(azim=250)
ax1.set_xlabel('x')
ax1.set_ylabel('y')
ax1.set_zlabel('z')
ax1.set_xlim(0, 700)
ax1.set_ylim(0, 500)
ax1.set_zlim(0, 400)

ax2.set_xlabel('x')
ax2.set_ylabel('y')
ax2.set_xlim(0, 700)
ax2.set_ylim(0, 500)

ax3.set_xlabel('x')
ax3.set_ylabel('z')
ax3.set_xlim(0, 700)
ax3.set_ylim(0, 400)

lines = []
for i in range(len(PlotX)):
    line1,  = ax1.plot(PlotX[max(0, n_plot-lineBuffer_plot):n_plot], PlotY[max(0, n_plot-lineBuffer_plot):n_plot], PlotZ[max(0, n_plot-lineBuffer_plot):n_plot], color='black')
    line1e, = ax1.plot([PlotX[n_plot]], [PlotY[n_plot]], [PlotZ[n_plot]], color='orange', marker='o', markeredgecolor='orange')
    line2,  = ax2.plot(PlotX[max(0, n_plot-lineBuffer_plot):n_plot], PlotY[max(0, n_plot-lineBuffer_plot):n_plot], color='black')
    line2e, = ax2.plot(PlotX[n_plot], PlotY[n_plot], color='orange', marker='o', markeredgecolor='orange')
    line3,  = ax3.plot(PlotX[max(0, n_plot-lineBuffer_plot):n_plot], PlotZ[max(0, n_plot-lineBuffer_plot):n_plot], color='black')
    line3e, = ax3.plot(PlotX[n_plot], PlotZ[n_plot], color='orange', marker='o', markeredgecolor='orange')
    lines.append([line1,line1e,line2,line2e,line3,line3e])
    n_plot = n_plot + 1
    
plt.tight_layout()
ani = animation.ArtistAnimation(fig, lines, interval=5, blit=True)
fn = 'tableTennisPlot'
ani.save('%s.mp4'%(fn), writer='ffmpeg',fps=20)
