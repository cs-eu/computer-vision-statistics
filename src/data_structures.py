"""Strongly-typed containers for tracking data and results."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TrackingData:
    # Raw detection series
    save_x: List[float] = field(default_factory=list)
    save_y: List[float] = field(default_factory=list)
    save_y2: List[float] = field(default_factory=list)
    save_z: List[float] = field(default_factory=list)
    save_frame1: List[int] = field(default_factory=list)
    save_frame2: List[int] = field(default_factory=list)

    # Plot series and indices
    plot_index: List[int] = field(default_factory=list)
    plot_x: List[float] = field(default_factory=list)
    plot_y: List[float] = field(default_factory=list)
    plot_z: List[float] = field(default_factory=list)

    # Per-player stats
    player1_net_height: List[str] = field(default_factory=list)
    player1_ball_speed: List[str] = field(default_factory=list)
    player1_ball_bounce: List[str] = field(default_factory=list)
    player2_net_height: List[str] = field(default_factory=list)
    player2_ball_speed: List[str] = field(default_factory=list)
    player2_ball_bounce: List[str] = field(default_factory=list)

    # Scene
    width: float = 0.0
    height: float = 0.0
    total_frames: int = 0


