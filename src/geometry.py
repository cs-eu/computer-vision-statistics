"""Geometry and numeric helpers for trajectory analysis."""

from typing import List, Tuple

from . import config


def get_parabola(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> Tuple[float, float, float]:
    """Return coefficients a, b, c for y = a*x^2 + b*x + c through three points."""
    numerator_a = ((y3 - y2) * (x2 - x1) - (y2 - y1) * (x3 - x2))
    denominator_a = (((x3 * x3) - (x2 * x2)) * (x2 - x1) - ((x2 * x2) - (x1 * x1)) * (x3 - x2))
    a = numerator_a / denominator_a
    b = (y2 - y1 - a * ((x2 * x2) - (x1 * x1))) / (x2 - x1)
    c = y1 - a * (x1 * x1) - b * x1
    return a, b, c


def get_line(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """Return slope and intercept (m, t) for y = m*x + t through two points."""
    m = (y1 - y2) / (x1 - x2)
    t = y1 - m * x1
    return m, t


def find_extremum(values: List[float], type_extremum: int) -> Tuple[List[float], List[int]]:
    """Find extrema in a list of values.

    type_extremum: -1 -> minima, +1 -> maxima, 0 -> both
    Returns (extrema_values, extrema_indices)
    """
    n = 0
    p = 0
    i = 1
    extrema_values: List[float] = []
    extrema_indices: List[int] = []
    tol = config.TOLERANCE_EXTREMUM
    while i < len(values) - 1:
        while abs(values[i - n] - values[i]) <= tol and i - n > 0:
            n = n + 1
        while abs(values[i + p] - values[i]) <= tol and i + p < len(values) - 1:
            p = p + 1
        if values[i - n] < values[i] and values[i] > values[i + p] and (type_extremum == 1 or type_extremum == 0):
            extrema_values.append(values[i])
            extrema_indices.append(i)
        if values[i - n] > values[i] and values[i] < values[i + p] and (type_extremum == -1 or type_extremum == 0):
            extrema_values.append(values[i])
            extrema_indices.append(i)
        i = i + p
        n = 1
        p = 1
    return extrema_values, extrema_indices


