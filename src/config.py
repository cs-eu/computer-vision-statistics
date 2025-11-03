"""Configuration and constants for table tennis tracking.

This module centralizes tunables and physical constants. Keep names descriptive.
"""

# Camera / capture
FPS = 120.0
ANGLE_OF_VIEW_VERTICAL = 159.76
ANGLE_OF_VIEW_HORIZONTAL = 168.54

# Table / scene coordinates (in same units as original code)
X_NET = 285.0
Y_MIN_TABLE = 18.0
Y_MAX_TABLE = 312.0

# Net height references (centimeters in source space before conversion)
NET_HEIGHT_CM = 15.25
Z_BACK_NET_HEIGHT = 199.0
Z_FRONT_NET_HEIGHT = 150.0

# Conversion helpers from image distances to meters via rod distance
DIFF_RODS_M = 0.87
X_ROD_FRONT_LEFT = 122.0
X_ROD_FRONT_RIGHT = 486.0

# Detection thresholds (grayscale bandpass in transformed channels)
GRAY_LOWER_1 = 105
GRAY_UPPER_1 = 255
GRAY_LOWER_2 = 150
GRAY_UPPER_2 = 255

# Plot appearance
LINE_BUFFER_PLOT = 20

# Extrema detection
TOLERANCE_EXTREMUM = 1.5


