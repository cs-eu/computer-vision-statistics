# Computer Vision Statistics for Table Tennis

**Automated Match Statistics from Video Using Computer Vision**

---

## Overview

This project explores whether a **camera-only, Python-based computer vision pipeline** can produce **quantitative match statistics** for recreational table tennis — without dedicated tracking hardware. It uses **dual synchronized cameras**, **color-based object detection**, **3D trajectory reconstruction**, and **statistical analysis** to measure:

* Ball speed (m/s)
* Impact position on the table (x–y grid)
* Ball height over the net (cm)

Inspired by systems like **Hawk-Eye**, the project demonstrates that accurate 3D ball tracking and analytics are achievable using open-source tools and basic geometry.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Key Features](#key-features)
3. [Pipeline Overview](#pipeline-overview)
4. [Data](#data)
5. [Usage](#usage)
6. [Outputs](#outputs)
7. [Dependencies](#dependencies)
8. [Results](#results)
9. [Limitations and Future Work](#limitations-and-future-work)
10. [References](#references)
11. [License](#license)

---

## Project Structure

```
computer-vision-statistics/
├── data/
│   ├── raw/                # Original recordings, extracted frame lists
│   ├── processed/          # Intermediate trajectory and coordinate data
│   └── tables/             # Exported Excel tables with computed statistics
├── docs/                   # Figures illustrating overlays, geometry, etc.
├── results/
│   ├── figures/            # Processed images, detection samples, assemblies
│   ├── reports/            # Generated box plots and per-set summaries (PDF)
│   └── videos/             # Animated trajectory visualizations (MP4)
├── src/                    # Source code implementing the pipeline
│   ├── config.py
│   ├── data_structures.py
│   ├── geometry.py
│   ├── main.py
│   ├── metrics.py
│   ├── plotting.py
│   ├── report.py
│   └── tracker.py
├── LICENSE
├── requirements.txt
└── README.md
```

---

## Key Features

* **Color-based detection** of orange table-tennis balls via RGB channel differencing
* **Dual-camera setup** for lateral and overhead views
* **3D trajectory reconstruction** using geometric correction and synchronization
* **Gap filling** using quadratic (parabolic) trajectory fitting
* **Automated statistics**: speed, bounce location, height over net
* **Visualization** via Matplotlib and OpenCV
* **Excel export** for per-rally and per-set statistics
* **Descriptive analysis** (mean, median, IQR, boxplots)

---

## Pipeline Overview

1. **Detection**
   Frames are decomposed into RGB channels; orange pixels are isolated by differencing (`R−B` and `G−B`).
   A saliency map highlights likely ball regions, followed by circular Hough detection to refine (x, y) positions.

2. **Camera Geometry**
   Two synchronized cameras (side and top views) capture the ball’s 2D coordinates.
   These are mapped into a shared Cartesian court frame using perspective corrections.

3. **Frame Synchronization**
   Manual or semi-automatic alignment ensures corresponding frames between both views.

4. **3D Reconstruction**
   The combined camera views reconstruct the ball’s 3D trajectory across frames.

5. **Gap Filling**
   Short occlusions (e.g., when the ball passes behind the net) are interpolated using a fitted parabola.

6. **Statistics and Export**

   * Compute speed, bounce position, and height per rally
   * Generate Excel tables and visualizations (plots, boxplots, trajectory figures)

---

## Data

| Folder            | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `data/raw`        | Original ball-tracking data (frame lists, raw positions)                 |
| `data/processed`  | Cleaned and synchronized coordinates (X, Y, Z)                           |
| `data/tables`     | Exported `.xls` tables with aggregated statistics                        |
| `results/reports` | PDF reports with per-set boxplots                                        |
| `results/videos`  | Reconstructed trajectories as animations                                 |
| `docs`            | Supporting visual documentation (e.g., overlays, geometry illustrations) |

---

## Usage

1. **Setup environment**

   ```bash
   git clone https://github.com/yourusername/computer-vision-statistics.git
   cd computer-vision-statistics
   pip install -r requirements.txt
   ```

2. **Configure parameters**

   Edit `src/config.py` to specify:

   * Input video paths
   * Camera calibration and synchronization offsets
   * Detection thresholds
   * Output directories

3. **Run the pipeline**

   ```bash
   python src/main.py
   ```

4. **Generate reports and visualizations**

   ```bash
   python src/report.py
   ```

---

## Outputs

| Output Type | Location           | Description                        |
| ----------- | ------------------ | ---------------------------------- |
| Figures     | `results/figures/` | Detection and geometry images      |
| Reports     | `results/reports/` | Statistical summaries and boxplots |
| Videos      | `results/videos/`  | Animated trajectories              |
| Tables      | `data/tables/`     | Excel sheets with per-set data     |

---

## Dependencies

* **Python 3.8+**
* **OpenCV** (`cv2`) – for image and video processing
* **NumPy**, **SciPy** – for numerical and geometric computations
* **Matplotlib** – for visualization
* **xlwt** or **pandas** – for Excel export
* **os**, **glob**, **argparse** – for I/O and configuration

Install dependencies via:

```bash
pip install -r requirements.txt
```

---

## Results

The validation dataset contained **382 ball trajectories** across three sets.

| Metric               | Accuracy (vs manual)                         |
| -------------------- | -------------------------------------------- |
| Detection robustness | >99% true positive, minimal false detections |
| Speed measurement    | ±0.1 m/s agreement                           |
| Height over net      | ±0.1 cm agreement                            |
| Impact location      | 100% correct grid cell assignments           |

Example findings:

* Winners tended to hit **slightly deeper** and **lower over the net** on average.
* Boxplots reveal small but consistent strategic tendencies.

---

## Limitations and Future Work

**Limitations**

* Manual synchronization between cameras
* Approximate geometry correction (no full stereo calibration)
* Sensitivity to lighting and orange hue variations
* Occasional occlusion handling failures

**Future Work**

* Automated multi-camera time alignment
* Camera calibration using homography or stereo triangulation
* Adaptive or learned color detection
* Integration with lightweight trackers (e.g., SORT/DeepSORT)
* Tactical analysis at rally and match levels

---

## References

1. Hawk-Eye system overviews (public documentation, accessed 2025)
2. Autonomous driving perception systems – sensor fusion surveys (2018–2022)
3. P. Viola & M. Jones, “Rapid Object Detection using a Boosted Cascade of Simple Features,” 2001
4. A. Kaehler & G. Bradski, *Learning OpenCV 3*, O’Reilly, 2017

