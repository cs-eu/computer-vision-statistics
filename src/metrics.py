"""Computation utilities for interpolation, perspective, and match metrics."""

import math
from typing import Tuple

from . import config
from .data_structures import TrackingData
from .geometry import get_parabola, get_line, find_extremum


def locate_area(x_val: float, y_val: float, width: float) -> str:
    n = 1.0
    row = str(int(n))
    while n <= 6 and x_val > ((n / 6) * (width - 200) + 100):
        n = n + 1
        row = str(int(n))
    if y_val > config.Y_MIN_TABLE + (2 * (config.Y_MAX_TABLE - config.Y_MIN_TABLE) / 3):
        column = "C"
    elif y_val < config.Y_MIN_TABLE + ((config.Y_MAX_TABLE - config.Y_MIN_TABLE) / 3):
        column = "A"
    else:
        column = "B"
    return column + " " + row


def get_speed(data: TrackingData, idx_start: int, idx_end: int, x_rod_left: float, x_rod_right: float) -> str:
    if idx_start > idx_end:
        idx_start, idx_end = idx_end, idx_start
    n = 0
    s = 0.0
    while idx_start + n + 1 < idx_end:
        x_dist = config.DIFF_RODS_M / abs(x_rod_right - x_rod_left) * abs(data.save_x[idx_start + n] - data.save_x[idx_start + n + 1])
        y_dist = config.DIFF_RODS_M / abs(x_rod_right - x_rod_left) * abs(data.save_y[idx_start + n] - data.save_y[idx_start + n + 1])
        z_dist = config.DIFF_RODS_M / abs(x_rod_right - x_rod_left) * abs(data.save_z[idx_start + n] - data.save_z[idx_start + n + 1])
        s = s + math.sqrt(x_dist * x_dist + y_dist * y_dist + z_dist * z_dist)
        n = n + 1
    t = abs(data.save_frame1[idx_start] - data.save_frame1[idx_end]) / config.FPS
    v = s / t if t != 0 else 0.0
    v = round(v, 1)
    return ("  " if v < 10.0 else "") + str(v) + " m/s"


def get_height_over_net(data: TrackingData, idx_start: int, idx_end: int) -> str:
    # Find three points around X_NET crossing via parabola in Z(X)
    if data.save_x[idx_start] > data.save_x[idx_end]:
        n = 0
        while idx_start + n < len(data.save_x) and data.save_x[idx_start + n] > config.X_NET:
            n = n + 1
    else:
        n = 0
        while idx_start + n < len(data.save_x) and data.save_x[idx_start + n] < config.X_NET:
            n = n + 1
    idx_p1 = idx_start + n - 1
    idx_p2 = idx_start + n
    idx_p3 = idx_start + n + 1
    a, b, c = get_parabola(data.save_x[idx_p1], data.save_z[idx_p1], data.save_x[idx_p2], data.save_z[idx_p2], data.save_x[idx_p3], data.save_z[idx_p3])
    z_ball = a * (config.X_NET ** 2) + b * config.X_NET + c
    y_ball = data.save_y[idx_p1] + ((abs(config.X_NET - data.save_x[idx_p1]) / abs(data.save_x[idx_p2] - data.save_x[idx_p1])) * abs(data.save_y[idx_p2] - data.save_y[idx_p1]))
    slope, intercept = get_line(config.Y_MIN_TABLE, config.Z_FRONT_NET_HEIGHT, config.Y_MAX_TABLE, config.Z_BACK_NET_HEIGHT)
    z_net = slope * y_ball + intercept
    z_net = (2 * z_net * (45 * data.height + config.ANGLE_OF_VIEW_VERTICAL * y_ball) + config.ANGLE_OF_VIEW_VERTICAL * data.height * (data.height - y_ball)) / (2 * (45 * data.height + config.ANGLE_OF_VIEW_VERTICAL * data.height))
    z_net_diff = z_net - z_ball
    net_diff_cm = config.DIFF_RODS_M / abs(config.X_ROD_FRONT_RIGHT - config.X_ROD_FRONT_LEFT) * z_net_diff * 100.0
    net_diff_cm = round(net_diff_cm, 1)
    return (" " if net_diff_cm < 10.0 else "") + str(net_diff_cm) + " cm"


def interpolate_missing_xz(data: TrackingData) -> None:
    missing_points = 0
    i = 0
    while i < len(data.save_x):
        if not all(v == -1 for v in data.save_x[i:]):
            if data.save_x[i] < 0:
                p1x = data.save_x[(i - 2)]
                p1y = data.save_z[(i - 2)]
                p2x = data.save_x[(i - 1)]
                p2y = data.save_z[(i - 1)]
                while i + missing_points + 1 < len(data.save_x) and data.save_x[(i + missing_points)] < 0:
                    missing_points = missing_points + 1
                p3x = data.save_x[(i + missing_points)]
                p3y = data.save_z[(i + missing_points)]
                if abs(p1x - p2x) > config.TOLERANCE_EXTREMUM and abs(p1x - p3x) > config.TOLERANCE_EXTREMUM and abs(p2x - p3x) > config.TOLERANCE_EXTREMUM and abs(p1y - p2y) > config.TOLERANCE_EXTREMUM and abs(p1y - p3y) > config.TOLERANCE_EXTREMUM and abs(p2y - p3y) > config.TOLERANCE_EXTREMUM:
                    a, b, c = get_parabola(p1x, p1y, p2x, p2y, p3x, p3y)
                    data.save_x[i] = data.save_x[(i - 1)] + (((data.save_frame1[i] - data.save_frame1[(i - 1)]) / (data.save_frame1[(i + missing_points)] - data.save_frame1[(i - 1)])) * (data.save_x[(i + missing_points)] - data.save_x[(i - 1)]))
                    data.save_z[i] = a * (data.save_x[i] ** 2) + b * data.save_x[i] + c
                else:
                    del data.save_x[i]
                    del data.save_z[i]
                    del data.save_frame1[i]
                    i = i - 1
        else:
            del data.save_x[i:]
            del data.save_z[i:]
            del data.save_frame1[i:]
        i = i + 1
        missing_points = 0


def align_y_series(data: TrackingData) -> None:
    i = 0
    while i < len(data.save_x):
        n = 0
        while n + 1 < len(data.save_frame2) and data.save_frame1[i] > data.save_frame2[n]:
            n = n + 1
        if n < len(data.save_frame2) and data.save_frame1[i] == data.save_frame2[n]:
            data.save_y.append(data.save_y2[n])
        elif n > 0:
            upper_idx = n
            lower_idx = n - 1
            interpolated_y = data.save_y2[lower_idx] + (((data.save_frame1[i] - data.save_frame2[lower_idx]) / (data.save_frame2[upper_idx] - data.save_frame2[lower_idx])) * (data.save_y2[upper_idx] - data.save_y2[lower_idx]))
            data.save_y.append(interpolated_y)
        else:
            del data.save_x[i]
            del data.save_z[i]
            del data.save_frame1[i]
            i = i - 1
        i = i + 1


def perspective_transform(data: TrackingData) -> None:
    for i in range(len(data.save_x)):
        data.save_x[i] = (2 * data.save_x[i] * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * data.save_y[i]) + config.ANGLE_OF_VIEW_HORIZONTAL * data.width * (data.height - data.save_y[i])) / (2 * (45 * data.width + config.ANGLE_OF_VIEW_HORIZONTAL * data.height))
        data.save_z[i] = (2 * data.save_z[i] * (45 * data.height + config.ANGLE_OF_VIEW_VERTICAL * data.save_y[i]) + config.ANGLE_OF_VIEW_VERTICAL * data.height * (data.height - data.save_y[i])) / (2 * (45 * data.height + config.ANGLE_OF_VIEW_VERTICAL * data.height))


def compute_segments_and_stats(data: TrackingData) -> None:
    extrema_x, extrema_idx_x = find_extremum(data.save_x, 0)
    last_hit = None
    for i in range(len(extrema_x)):
        if i > 0:
            if extrema_x[i] > config.X_NET + 40 and extrema_x[i - 1] < config.X_NET - 40:
                if last_hit == "Player1":
                    data.player2_ball_bounce.append("f.S.")
                    data.player2_ball_speed.append("f.S.")
                    data.player2_net_height.append("f.S.")
                last_hit = "Player1"
                graph_start = extrema_idx_x[i - 1]
                graph_end = extrema_idx_x[i]
                data.plot_index.append(graph_start)
                data.plot_index.append(graph_end)
                extrema_z, extrema_idx_z = find_extremum(data.save_z[graph_start:(graph_end + 1)], 1)
                n = 0
                while n < len(extrema_z):
                    extrema_idx_z[n] = graph_start + extrema_idx_z[n]
                    n = n + 1
                if len(extrema_z) >= 1 and data.save_x[extrema_idx_z[-1]] > config.X_NET:
                    data.player1_ball_bounce.append(locate_area(data.save_x[extrema_idx_z[-1]], data.save_y[extrema_idx_z[-1]], data.width))
                    data.player1_ball_speed.append("pending")
                    data.player1_net_height.append("pending")
                else:
                    data.player1_ball_bounce.append("f.S.")
                    data.player1_ball_speed.append("f.S.")
                    data.player1_net_height.append("f.S.")
            elif i > 0 and extrema_x[i] < config.X_NET - 40 and extrema_x[i - 1] > config.X_NET + 40:
                if last_hit == "Player2":
                    data.player1_ball_bounce.append("f.S.")
                    data.player1_ball_speed.append("f.S.")
                    data.player1_net_height.append("f.S.")
                last_hit = "Player2"
                graph_start = extrema_idx_x[i - 1]
                graph_end = extrema_idx_x[i]
                data.plot_index.append(graph_start)
                data.plot_index.append(graph_end)
                extrema_z, extrema_idx_z = find_extremum(data.save_z[graph_start:(graph_end + 1)], 1)
                n = 0
                while n < len(extrema_z):
                    extrema_idx_z[n] = graph_start + extrema_idx_z[n]
                    n = n + 1
                if len(extrema_z) >= 1 and data.save_x[extrema_idx_z[-1]] < config.X_NET:
                    data.player2_ball_bounce.append(locate_area(data.save_x[extrema_idx_z[-1]], data.save_y[extrema_idx_z[-1]], data.width))
                    data.player2_ball_speed.append("pending")
                    data.player2_net_height.append("pending")
                else:
                    data.player2_ball_bounce.append("f.S.")
                    data.player2_ball_speed.append("f.S.")
                    data.player2_net_height.append("f.S.")


def backfill_stats_strings(data: TrackingData, x_rod_left: float, x_rod_right: float) -> None:
    # Equalize list lengths
    while len(data.player1_net_height) < len(data.player2_net_height):
        data.player1_ball_bounce.append("")
        data.player1_ball_speed.append("")
        data.player1_net_height.append("")
    while len(data.player1_net_height) > len(data.player2_net_height):
        data.player2_ball_bounce.append("")
        data.player2_ball_speed.append("")
        data.player2_net_height.append("")

    # Resolve pending entries by computing metrics for each segment in plot_index pairs
    i = 0
    seg = 0
    while i + 1 < len(data.plot_index):
        start = data.plot_index[i]
        end = data.plot_index[i + 1]
        height_str = get_height_over_net(data, start, end)
        speed_str = get_speed(data, start, end, x_rod_left, x_rod_right)
        # Assign to whichever player segment it belongs to, alternating by seg parity
        if seg < len(data.player1_net_height) and data.player1_net_height[seg] == "pending":
            data.player1_net_height[seg] = height_str
            data.player1_ball_speed[seg] = speed_str
        elif seg < len(data.player2_net_height) and data.player2_net_height[seg] == "pending":
            data.player2_net_height[seg] = height_str
            data.player2_ball_speed[seg] = speed_str
        seg = seg + 1
        i = i + 2


def build_plot_series(data: TrackingData) -> None:
    i = 1
    n = 0
    while i <= data.total_frames and n < len(data.save_frame1):
        if i == data.save_frame1[n]:
            n = n + 1
        elif i >= 2:
            data.save_x.insert(i - 1, data.save_x[i - 2])
            data.save_y.insert(i - 1, data.save_y[i - 2])
            data.save_z.insert(i - 1, data.save_z[i - 2])
        i = i + 1

    i = 0
    n = 1
    if len(data.plot_index) == 0:
        return
    while i <= data.plot_index[-1] and n < len(data.plot_index):
        if i >= data.plot_index[n - 1] and i <= data.plot_index[n]:
            data.plot_x.append(data.save_x[i])
            data.plot_y.append(data.save_y[i])
            data.plot_z.append(-data.save_z[i] + 400)
        if i > data.plot_index[n]:
            n = n + 2
        else:
            i = i + 1


