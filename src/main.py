import argparse

from .tracker import BallTracker
from .metrics import interpolate_missing_xz, align_y_series, perspective_transform, compute_segments_and_stats, backfill_stats_strings, build_plot_series
from .report import ReportWriter
from .plotting import PlotAnimator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v1", "--video1", required=True, help="Video Datei mit XZ Koordinaten")
    parser.add_argument("-v2", "--video2", required=True, help="Video Datei mit XY Koordinaten")
    parser.add_argument("-i1", "--image1", required=True, help="Ueberlagerndes Bild fuer XZ")
    parser.add_argument("-i2", "--image2", required=True, help="Ueberlagerndes Bild fuer XY")
    parser.add_argument("-b1", "--buffer1", type=int, default=64, help="max buffer size")
    parser.add_argument("-b2", "--buffer2", type=int, default=64, help="max buffer size")
    parser.add_argument("--no-gui", action="store_true", help="Disable OpenCV windows during tracking")
    args = parser.parse_args()

    tracker = BallTracker(buffer1=args.buffer1, buffer2=args.buffer2)
    data = tracker.run(args.video1, args.video2, args.image1, args.image2, show_windows=(not args.no_gui))

    interpolate_missing_xz(data)
    align_y_series(data)
    perspective_transform(data)
    compute_segments_and_stats(data)
    x_rod_left = getattr(tracker, 'x_rod_left', None)
    x_rod_right = getattr(tracker, 'x_rod_right', None)
    if x_rod_left is None or x_rod_right is None:
        raise RuntimeError("Rod positions not computed")
    backfill_stats_strings(data, x_rod_left, x_rod_right)
    build_plot_series(data)

    report = ReportWriter()
    report.write(data, out_path="TableTennisData.xls")

    animator = PlotAnimator()
    fig = animator.build(data)
    animator.save(fig, out_basename='tableTennisPlot', fps=20)


if __name__ == "__main__":
    main()
