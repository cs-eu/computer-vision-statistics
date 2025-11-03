"""Ball tracking from two synchronized views to collect trajectories."""

from collections import deque
from typing import Optional, Tuple

import cv2
import imutils
import numpy as np

from . import config
from .data_structures import TrackingData


class BallTracker:
    def __init__(self, buffer1: int = 64, buffer2: int = 64) -> None:
        self.buffer1 = buffer1
        self.buffer2 = buffer2

    def _preprocess(self, frame, overlay) -> Tuple[np.ndarray, np.ndarray]:
        frame = cv2.bitwise_and(frame, overlay)
        frame = imutils.resize(frame, width=600)
        channels = cv2.split(frame)
        blue = cv2.subtract(channels[1], channels[0])
        red = cv2.subtract(channels[2], channels[0])
        processed = cv2.addWeighted(blue, 0.5, red, 0.5, 1)
        return frame, processed

    @staticmethod
    def _mask_band(frame_proc, lower: int, upper: int) -> np.ndarray:
        mask = cv2.inRange(frame_proc, lower, upper)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)
        return mask

    @staticmethod
    def _largest_contour(mask) -> Tuple[Optional[Tuple[float, float]], float, Optional[np.ndarray]]:
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(cnts) == 0:
            return None, 0.0, None
        c = max(cnts, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])) if M["m00"] != 0 else None
        return center, radius, c

    def run(self, video1_path: str, video2_path: str, image1_path: str, image2_path: str, show_windows: bool = True) -> TrackingData:
        data = TrackingData()

        video1 = cv2.VideoCapture(video1_path)
        grabbed1, frame1 = video1.read()
        if not grabbed1:
            video1.release()
            raise RuntimeError("Failed to read first frame from video1")
        overlay1 = cv2.imread(image1_path)
        overlay1 = cv2.resize(overlay1, frame1.shape[1::-1])

        video2 = cv2.VideoCapture(video2_path)
        grabbed2, frame2 = video2.read()
        if not grabbed2:
            video1.release()
            video2.release()
            raise RuntimeError("Failed to read first frame from video2")
        overlay2 = cv2.imread(image2_path)
        overlay2 = cv2.resize(overlay2, frame2.shape[1::-1])

        start1_found = False
        start2_found = False
        pts1 = deque(maxlen=self.buffer1)
        pts2 = deque(maxlen=self.buffer2)

        # Find first detection for sync (cam1)
        while not start1_found:
            grabbed1, frame1 = video1.read()
            if not grabbed1:
                break
            frame1_raw, frame1_proc = self._preprocess(frame1, overlay1)
            data.height = float(frame1_raw.shape[0])
            data.width = float(frame1_raw.shape[1])
            mask1 = self._mask_band(frame1_proc, config.GRAY_LOWER_1, config.GRAY_UPPER_1)
            center1, radius1, _ = self._largest_contour(mask1)
            if center1 is not None and radius1 > 0:
                start1_found = True
            if show_windows:
                cv2.imshow("Mask1", mask1)
                cv2.imshow("Frame1", frame1_raw)
                cv2.waitKey(1)

        # Find first detection for sync (cam2)
        while not start2_found:
            grabbed2, frame2 = video2.read()
            if not grabbed2:
                break
            frame2_raw, frame2_proc = self._preprocess(frame2, overlay2)
            mask2 = self._mask_band(frame2_proc, config.GRAY_LOWER_2, config.GRAY_UPPER_2)
            center2, radius2, _ = self._largest_contour(mask2)
            if center2 is not None and radius2 > 0:
                start2_found = True
            if show_windows:
                cv2.imshow("Mask2", mask2)
                cv2.imshow("Frame2", frame2_raw)
                cv2.waitKey(1)

        # Perspective-correct rod x positions
        x_rod_left = (2 * config.X_ROD_FRONT_LEFT * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * config.Y_MIN_TABLE) + config.ANGLE_OF_VIEW_HORIZONTAL * data.width * (data.height - config.Y_MIN_TABLE)) / (2 * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * data.height))
        x_rod_right = (2 * config.X_ROD_FRONT_RIGHT * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * config.Y_MIN_TABLE) + config.ANGLE_OF_VIEW_HORIZONTAL * data.width * (data.height - config.Y_MIN_TABLE)) / (2 * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * data.height))

        total_frame = 0
        while True:
            grabbed1, frame1 = video1.read()
            grabbed2, frame2 = video2.read()
            total_frame = total_frame + 1
            if not grabbed1 or not grabbed2:
                break

            frame1_raw, frame1_proc = self._preprocess(frame1, overlay1)
            frame2_raw, frame2_proc = self._preprocess(frame2, overlay2)

            mask1 = self._mask_band(frame1_proc, config.GRAY_LOWER_1, config.GRAY_UPPER_1)
            mask2 = self._mask_band(frame2_proc, config.GRAY_LOWER_2, config.GRAY_UPPER_2)

            center1, radius1, c1 = self._largest_contour(mask1)
            if center1 is not None and radius1 > 0:
                cv2.circle(frame1_raw, (int(center1[0]), int(center1[1])), int(radius1), (255), 2)
                data.save_x.append(float(center1[0]))
                data.save_z.append(float(center1[1]))
                data.save_frame1.append(total_frame)

            center2, radius2, c2 = self._largest_contour(mask2)
            if center2 is not None and radius2 > 0:
                cv2.circle(frame2_raw, (int(center2[0]), int(center2[1])), int(radius2), (255), 2)
                data.save_y2.append(float(center2[1]))
                data.save_frame2.append(total_frame)

            pts1.appendleft(center1)
            pts2.appendleft(center2)

            if len(data.save_frame1) > 1:
                if len(data.save_x) >= 9 and all(v == -1 for v in data.save_x[-9:]):
                    del data.save_x[-9:]
                    del data.save_z[-9:]
                    del data.save_frame1[-9:]
                elif total_frame - data.save_frame1[-1] > 4:
                    data.save_x.append(-1)
                    data.save_z.append(-1)
                    data.save_frame1.append(total_frame)

            # Draw trails (optional)
            for i in range(1, len(pts1)):
                if pts1[i - 1] is None or pts1[i] is None:
                    continue
                thickness = int(np.sqrt(self.buffer1 / float(i + 1)) * 2.5)
                cv2.line(mask1, pts1[i - 1], pts1[i], (255), thickness)
                thickness = int(np.sqrt(self.buffer2 / float(i + 1)) * 2.5)
                cv2.line(mask2, pts2[i - 1], pts2[i], (255), thickness)

            if show_windows:
                cv2.imshow("Frame1", frame1_raw)
                cv2.imshow("Frame2", frame2_raw)
                cv2.imshow("Mask1", mask1)
                cv2.imshow("Mask2", mask2)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

        video1.release()
        video2.release()
        cv2.destroyAllWindows()

        data.total_frames = total_frame

        # Store perspective-corrected rods for later metric conversions
        # We stash them on the object for metrics to read via properties if needed
        self.x_rod_left = x_rod_left
        self.x_rod_right = x_rod_right
        return data


