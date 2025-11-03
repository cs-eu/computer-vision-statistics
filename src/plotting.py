"""Plotting and animation for table tennis trajectories."""

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from typing import List

from .data_structures import TrackingData


class PlotAnimator:
    def __init__(self) -> None:
        self.lines: List[List] = []

    def build(self, data: TrackingData):
        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1, projection="3d")
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

        n_plot = 0
        for i in range(len(data.plot_x)):
            line1, = ax1.plot(data.plot_x[max(0, n_plot - 20):n_plot], data.plot_y[max(0, n_plot - 20):n_plot], data.plot_z[max(0, n_plot - 20):n_plot], color='black')
            line1e, = ax1.plot([data.plot_x[n_plot]], [data.plot_y[n_plot]], [data.plot_z[n_plot]], color='orange', marker='o', markeredgecolor='orange')
            line2, = ax2.plot(data.plot_x[max(0, n_plot - 20):n_plot], data.plot_y[max(0, n_plot - 20):n_plot], color='black')
            line2e, = ax2.plot(data.plot_x[n_plot], data.plot_y[n_plot], color='orange', marker='o', markeredgecolor='orange')
            line3, = ax3.plot(data.plot_x[max(0, n_plot - 20):n_plot], data.plot_z[max(0, n_plot - 20):n_plot], color='black')
            line3e, = ax3.plot(data.plot_x[n_plot], data.plot_z[n_plot], color='orange', marker='o', markeredgecolor='orange')
            self.lines.append([line1, line1e, line2, line2e, line3, line3e])
            n_plot = n_plot + 1

        plt.tight_layout()
        return fig

    def save(self, fig, out_basename: str = 'tableTennisPlot', fps: int = 20) -> None:
        ani = animation.ArtistAnimation(fig, self.lines, interval=5, blit=True)
        ani.save(f'{out_basename}.mp4', writer='ffmpeg', fps=fps)


