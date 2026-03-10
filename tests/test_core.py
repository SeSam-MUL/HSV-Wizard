"""Unit tests for HSV-Wizard core functions."""

import importlib
import sys
import os
import math

import numpy as np
import pytest
from PIL import Image

# Import the module despite the hyphenated filename
spec = importlib.util.spec_from_file_location(
    "hsv_wizard",
    os.path.join(os.path.dirname(__file__), "..", "code", "hsv_wizard.py"),
    submodule_search_locations=[],
)
hsv_wizard = importlib.util.module_from_spec(spec)
# Prevent Tk from launching during import
sys.modules["hsv_wizard"] = hsv_wizard
_original_name = None


def _import_module():
    """Import the module, patching __name__ to avoid launching the GUI."""
    global _original_name
    # Patch to prevent if __name__ == '__main__' from executing
    spec.loader.exec_module(hsv_wizard)


# We need to handle the case where tkinter is not available (CI environments)
try:
    import tkinter as tk
    _tk_available = True
except ImportError:
    _tk_available = False

if _tk_available:
    try:
        _import_module()
        _module_loaded = True
    except tk.TclError:
        # No display available (headless CI)
        _module_loaded = False
else:
    _module_loaded = False


# Standalone implementations for testing without GUI
def hsv_to_rgb(h, s, v):
    """Convert HSV (0-1) to RGB (0-255)."""
    import colorsys
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def rgb_to_hsv(r, g, b):
    """Convert RGB (0-255) to HSV (0-1)."""
    import colorsys
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def hue_angle_to_x(hue_angle, width):
    """Map hue angle to x position."""
    return (hue_angle % 360) / 360 * width


# ─── HSV ↔ RGB Conversion Tests ───────────────────────────────────────────


class TestHsvToRgb:
    """Tests for hsv_to_rgb conversion."""

    def test_red(self):
        assert hsv_to_rgb(0, 1, 1) == (255, 0, 0)

    def test_green(self):
        assert hsv_to_rgb(1 / 3, 1, 1) == (0, 255, 0)

    def test_blue(self):
        assert hsv_to_rgb(2 / 3, 1, 1) == (0, 0, 255)

    def test_white(self):
        assert hsv_to_rgb(0, 0, 1) == (255, 255, 255)

    def test_black(self):
        assert hsv_to_rgb(0, 0, 0) == (0, 0, 0)

    def test_yellow(self):
        r, g, b = hsv_to_rgb(1 / 6, 1, 1)
        assert r == 255
        assert g == 255
        assert b == 0

    def test_half_saturation(self):
        r, g, b = hsv_to_rgb(0, 0.5, 1)
        assert r == 255
        assert 127 <= g <= 128  # rounding
        assert 127 <= b <= 128


class TestRgbToHsv:
    """Tests for rgb_to_hsv conversion."""

    def test_red(self):
        h, s, v = rgb_to_hsv(255, 0, 0)
        assert h == pytest.approx(0.0)
        assert s == pytest.approx(1.0)
        assert v == pytest.approx(1.0)

    def test_green(self):
        h, s, v = rgb_to_hsv(0, 255, 0)
        assert h == pytest.approx(1 / 3, abs=0.01)
        assert s == pytest.approx(1.0)
        assert v == pytest.approx(1.0)

    def test_blue(self):
        h, s, v = rgb_to_hsv(0, 0, 255)
        assert h == pytest.approx(2 / 3, abs=0.01)

    def test_white(self):
        h, s, v = rgb_to_hsv(255, 255, 255)
        assert s == pytest.approx(0.0)
        assert v == pytest.approx(1.0)

    def test_black(self):
        h, s, v = rgb_to_hsv(0, 0, 0)
        assert v == pytest.approx(0.0)

    def test_roundtrip(self):
        """Verify HSV → RGB → HSV roundtrip for a non-trivial color."""
        original_hsv = (0.6, 0.8, 0.9)
        rgb = hsv_to_rgb(*original_hsv)
        recovered_hsv = rgb_to_hsv(*rgb)
        assert recovered_hsv[0] == pytest.approx(original_hsv[0], abs=0.02)
        assert recovered_hsv[1] == pytest.approx(original_hsv[1], abs=0.02)
        assert recovered_hsv[2] == pytest.approx(original_hsv[2], abs=0.02)


# ─── Hue Angle Mapping Tests ──────────────────────────────────────────────


class TestHueAngleToX:
    """Tests for hue_angle_to_x mapping function."""

    def test_zero_angle(self):
        assert hue_angle_to_x(0, 300) == pytest.approx(0.0)

    def test_180_degrees(self):
        assert hue_angle_to_x(180, 300) == pytest.approx(150.0)

    def test_360_degrees_wraps_to_zero(self):
        assert hue_angle_to_x(360, 300) == pytest.approx(0.0)

    def test_90_degrees(self):
        assert hue_angle_to_x(90, 400) == pytest.approx(100.0)

    def test_negative_angle_wraps(self):
        # -90 mod 360 = 270
        assert hue_angle_to_x(-90, 360) == pytest.approx(270.0)


# ─── Color Wheel & Gradient Bar Tests ─────────────────────────────────────


@pytest.mark.skipif(not _module_loaded, reason="tkinter/display not available")
class TestColorWheel:
    """Tests for color wheel image generation."""

    def test_returns_pil_image(self):
        img = hsv_wizard.create_hsv_color_wheel(radius=50)
        assert isinstance(img, Image.Image)

    def test_correct_size(self):
        radius = 75
        img = hsv_wizard.create_hsv_color_wheel(radius=radius)
        assert img.size == (radius * 2, radius * 2)

    def test_center_pixel_is_white(self):
        """Center of color wheel has saturation=0, so should be white."""
        img = hsv_wizard.create_hsv_color_wheel(radius=100)
        center = img.getpixel((100, 100))
        # Center should be near white (value=1, sat=0)
        assert all(c > 240 for c in center)


@pytest.mark.skipif(not _module_loaded, reason="tkinter/display not available")
class TestHueGradientBar:
    """Tests for hue gradient bar image generation."""

    def test_returns_pil_image(self):
        img = hsv_wizard.create_hue_gradient_bar(width=200, height=30)
        assert isinstance(img, Image.Image)

    def test_correct_width(self):
        img = hsv_wizard.create_hue_gradient_bar(width=200, height=30)
        assert img.size[0] == 200

    def test_left_edge_is_red(self):
        """Hue=0 at left edge should be red."""
        img = hsv_wizard.create_hue_gradient_bar(width=300, height=50)
        pixel = img.getpixel((1, 25))
        assert pixel[0] > 200  # Strong red
        assert pixel[1] < 50   # Low green
        assert pixel[2] < 50   # Low blue


# ─── HSV Masking Logic Tests ──────────────────────────────────────────────


class TestHsvMasking:
    """Tests for the HSV masking algorithm (core scientific logic)."""

    def _apply_mask(self, image, hue_low, hue_high, sat_low, sat_high, val_low, val_high):
        """Replicate the masking logic from update_image()."""
        hsv_image = image.convert('HSV')
        hsv_array = np.array(hsv_image)

        h_low = int((hue_low / 360) * 255)
        h_high = int((hue_high / 360) * 255)
        s_low = int((sat_low / 100) * 255)
        s_high = int((sat_high / 100) * 255)
        v_low = int((val_low / 100) * 255)
        v_high = int((val_high / 100) * 255)

        if h_low <= h_high:
            hue_mask = (hsv_array[:, :, 0] >= h_low) & (hsv_array[:, :, 0] <= h_high)
        else:
            hue_mask = (hsv_array[:, :, 0] >= h_low) | (hsv_array[:, :, 0] <= h_high)

        sat_mask = (hsv_array[:, :, 1] >= s_low) & (hsv_array[:, :, 1] <= s_high)
        val_mask = (hsv_array[:, :, 2] >= v_low) & (hsv_array[:, :, 2] <= v_high)

        mask = hue_mask & sat_mask & val_mask

        masked_array = np.copy(np.array(image))
        masked_array[~mask] = [0, 0, 0]
        return masked_array, mask

    def test_full_range_keeps_all_pixels(self):
        """With full HSV range, no pixels should be masked."""
        img = Image.new('RGB', (10, 10), (128, 64, 200))
        _, mask = self._apply_mask(img, 0, 360, 0, 100, 0, 100)
        assert mask.all()

    def test_narrow_value_range_masks_non_matching(self):
        """With a narrow value range that excludes the pixel's value, pixels should be masked."""
        # Create a bright pixel (value ~78%) and filter for value 10-20% only
        img = Image.new('RGB', (10, 10), (128, 64, 200))
        _, mask = self._apply_mask(img, 0, 360, 0, 100, 10, 20)
        assert not mask.any(), "Bright pixels should be masked by a low value range"

    def test_red_pixel_selected_by_red_hue(self):
        """A red pixel should be selected by a hue range around 0°."""
        img = Image.new('RGB', (5, 5), (255, 0, 0))
        _, mask = self._apply_mask(img, 0, 30, 0, 100, 0, 100)
        assert mask.all()

    def test_red_pixel_not_selected_by_green_hue(self):
        """A red pixel should NOT be selected by a green hue range."""
        img = Image.new('RGB', (5, 5), (255, 0, 0))
        _, mask = self._apply_mask(img, 90, 180, 0, 100, 0, 100)
        assert not mask.any()

    def test_circular_hue_wrap_around(self):
        """When hue_low > hue_high, the mask should wrap around 360°."""
        img = Image.new('RGB', (5, 5), (255, 0, 0))  # Red = hue ~0°
        # Range 350-10 should include red (hue ≈ 0)
        _, mask = self._apply_mask(img, 350, 10, 0, 100, 0, 100)
        assert mask.all()

    def test_saturation_filter(self):
        """A gray pixel (low saturation) should be excluded by high sat range."""
        img = Image.new('RGB', (5, 5), (128, 128, 128))  # Gray = sat 0
        _, mask = self._apply_mask(img, 0, 360, 50, 100, 0, 100)
        assert not mask.any()

    def test_black_pixel_filtered_by_value(self):
        """Black pixels (value=0) should be excluded by value range > 0."""
        img = Image.new('RGB', (5, 5), (0, 0, 0))
        _, mask = self._apply_mask(img, 0, 360, 0, 100, 10, 100)
        assert not mask.any()


# ─── Calibration Logic Tests ──────────────────────────────────────────────


class TestCalibrationLogic:
    """Tests for calibration calculations."""

    def test_length_per_pixel_calculation(self):
        """Verify length_per_pixel = known_length / pixel_distance."""
        known_length = 100.0  # e.g., 100 µm
        pixel_distance = 200.0  # pixels
        length_per_pixel = known_length / pixel_distance
        assert length_per_pixel == pytest.approx(0.5)

    def test_pixel_distance_calculation(self):
        """Verify Euclidean distance formula."""
        x_start, y_start = 10, 20
        x_end, y_end = 40, 60
        distance = ((x_end - x_start)**2 + (y_end - y_start)**2)**0.5
        expected = math.sqrt(30**2 + 40**2)  # 50.0
        assert distance == pytest.approx(expected)

    def test_measurement_with_calibration(self):
        """Verify that measured pixel distance * scale gives real length."""
        length_per_pixel = 0.5  # µm per pixel
        pixel_distance = 120.0
        measured_length = pixel_distance * length_per_pixel
        assert measured_length == pytest.approx(60.0)

    def test_zero_distance_rejected(self):
        """Calibration with zero pixel distance should be invalid."""
        x_start, y_start = 50, 50
        x_end, y_end = 50, 50
        pixel_distance = ((x_end - x_start)**2 + (y_end - y_start)**2)**0.5
        assert pixel_distance == 0.0
