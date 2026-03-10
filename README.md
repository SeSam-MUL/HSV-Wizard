# HSV-Wizard

Interactive HSV color threshold adjuster with calibration and measurement tools for scientific image analysis.

HSV-Wizard is a Python/Tkinter desktop application designed for microscopy and materials science workflows. It allows users to interactively segment images by HSV color thresholds, calibrate a spatial scale, and measure distances directly on the image.

## Features

- **HSV Color Thresholding** — Adjust Hue (0-360°), Saturation (0-100%), and Value (0-100%) ranges via sliders or an interactive color wheel. Pixels outside the selected range are masked to black.
- **Interactive Color Wheel** — Drag threshold lines directly on a visual HSV color wheel for intuitive hue selection. Supports circular hue wrap-around (e.g., selecting reds across 350°–10°).
- **Color Picker** — Click any pixel on the image to automatically set HSV thresholds around that color (±10° hue, ±20% saturation/value).
- **Scale Calibration** — Draw a line of known length on the image or enter a pixel-to-unit conversion factor directly. Supports any unit (nm, µm, mm, etc.).
- **Distance Measurement** — Click and drag to measure distances on calibrated images. Results are displayed on-screen and in a dedicated dialog.
- **Scale Bar** — Add a draggable, labeled scale bar to the image based on the calibration.
- **Export** — Save processed (thresholded) images with overlays. Export measurements as CSV.
- **Undo** — Revert measurements, calibration lines, and scale bars.
- **Zoom & Pan** — Scroll to zoom (0.1x–10.0x), click-drag to pan. Cross-platform scroll support (Windows, macOS, Linux).

## Requirements

- Python 3.8 or higher
- Dependencies: see [requirements.txt](requirements.txt)

## Installation

```bash
git clone https://github.com/SeSam-MUL/HSV-Wizard.git
cd HSV-Wizard
pip install -r requirements.txt
```

## Usage

```bash
python code/hsv_wizard.py
```

### Workflow

1. **Load an image** — Use `File > Load New Image` or the "Load New Image" button. Supported formats: TIFF, PNG, JPEG, BMP.
2. **Adjust thresholds** — Use the color wheel, sliders, or color picker to select the HSV range of interest.
3. **Calibrate** — Click "Calibrate", draw a line of known length, and enter the real-world distance and units.
4. **Measure** — Click "Measure" and draw lines on the image to measure distances.
5. **Export** — Save the processed image or export measurements as CSV.

## Pre-built Executable

A standalone Windows executable (`HSV-Wizard.exe`) is available on the [Releases](https://github.com/SeSam-MUL/HSV-Wizard/releases) page (built with PyInstaller). No Python installation required — just download and run.

## Running Tests

```bash
pip install pytest
pytest tests/
```

## Citation

If you use HSV-Wizard in your research, please cite:

```bibtex
@software{hsv_wizard,
  title = {HSV-Wizard: Interactive HSV Color Threshold Adjuster},
  author = {Samberger, Sebastian},
  year = {2026},
  url = {https://github.com/SeSam-MUL/HSV-Wizard}
}
```

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
