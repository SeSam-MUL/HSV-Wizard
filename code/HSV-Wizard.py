import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
import numpy as np
import colorsys
import sys
import os
import platform
import csv

# Helper function to convert HSV to RGB
def hsv_to_rgb(h, s, v):
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))

# Helper function to convert RGB to HSV
def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

# Function to create the HSV color wheel with angle scale
def create_hsv_color_wheel(radius=150):
    size = radius * 2
    image = Image.new('RGB', (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    center = radius
    # Draw the color wheel
    for x in range(size):
        for y in range(size):
            dx = x - center
            dy = y - center
            distance = (dx**2 + dy**2)**0.5
            if distance <= radius:
                angle = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
                hue = angle / 360.0
                saturation = distance / radius
                rgb = hsv_to_rgb(hue, saturation, 1)
                draw.point((x, y), fill=rgb)

    # Draw angle scale
    for angle_deg in range(0, 360, 15):  # Every 15 degrees
        angle_rad = np.radians(angle_deg)
        inner_radius = radius - 10
        outer_radius = radius
        if angle_deg % 45 == 0:
            # Major tick
            inner_radius = radius - 20
            tick_length = 20
            text_offset = 30
            # Calculate text position
            text_x = center + (radius - text_offset) * np.cos(angle_rad)
            text_y = center + (radius - text_offset) * np.sin(angle_rad)
            # Draw angle label
            text = f"{angle_deg}°"
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except (IOError, OSError):
                font = ImageFont.load_default()
            # Use of textbbox
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text((text_x - text_width / 2, text_y - text_height / 2), text, fill='black', font=font)
        else:
            # Minor tick
            tick_length = 10
        x1 = center + inner_radius * np.cos(angle_rad)
        y1 = center + inner_radius * np.sin(angle_rad)
        x2 = center + outer_radius * np.cos(angle_rad)
        y2 = center + outer_radius * np.sin(angle_rad)
        draw.line([(x1, y1), (x2, y2)], fill='black', width=1)

    return image

# Function to create the hue gradient bar with angle labels
def create_hue_gradient_bar(width=300, height=50):
    image = Image.new('RGB', (width, height + 20), 'white')
    draw = ImageDraw.Draw(image)
    for x in range(width):
        hue = x / width  # Hue varies from 0 to 1
        rgb = hsv_to_rgb(hue, 1, 1)
        draw.line([(x, 0), (x, height)], fill=rgb)

    # Draw angle labels every 45 degrees
    for angle_deg in range(0, 361, 45):
        x_pos = (angle_deg % 360) / 360 * width
        draw.line([(x_pos, height), (x_pos, height + 5)], fill='black')
        text = f"{angle_deg}°"
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except (IOError, OSError):
            font = ImageFont.load_default()
        # Use of textbbox
        # Use draw.textbbox to get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if angle_deg == 0:
               x_pos = text_width / 2 + 2    
        elif angle_deg == 360:
               x_pos = width - text_width / 2 - 2
        draw.text((x_pos - text_width / 2, height + 5), text, fill='black', font=font)
    return image

# Mapping function from hue angle to x position on hue bar
def hue_angle_to_x(hue_angle, width):
    return (hue_angle % 360) / 360 * width

class CalibrationDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calibration")
        self.resizable(False, False)
        self.length = None
        self.units = None

        tk.Label(self, text="Enter the actual length of the line:").pack(pady=(10, 0))
        self.length_entry = tk.Entry(self)
        self.length_entry.pack(padx=10, pady=5)

        tk.Label(self, text="Enter the units (e.g., nm, µm):").pack(pady=(10, 0))
        self.units_entry = tk.Entry(self)
        self.units_entry.pack(padx=10, pady=5)

        submit_button = tk.Button(self, text="Submit", command=self.on_submit)
        submit_button.pack(pady=10)

        self.length_entry.focus_set()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_submit(self):
        try:
            self.length = float(self.length_entry.get())
            self.units = self.units_entry.get()
            if not self.units:
                raise ValueError("Units cannot be empty.")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def on_close(self):
        self.length = None
        self.units = None
        self.destroy()

class MeasurementDialog(tk.Toplevel):
    def __init__(self, parent, measurements):
        super().__init__(parent)
        self.title("Measurements")
        self.resizable(True, True)
        self.parent = parent
        self.measurements = measurements

        self.text_widget = scrolledtext.ScrolledText(self, width=40, height=15)
        self.text_widget.pack(padx=10, pady=10)
        self.update_measurements(self.measurements)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        copy_button = tk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        copy_button.pack(side='left', padx=5)

        save_button = tk.Button(button_frame, text="Save to CSV", command=self.save_to_csv)
        save_button.pack(side='left', padx=5)

    def update_measurements(self, measurements):
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        text = "\n".join(f"{i+1}: {length:.2f} {self.parent.length_units}" for i, length in enumerate(measurements))
        self.text_widget.insert('1.0', text)
        self.text_widget.config(state='disabled')

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_widget.get('1.0', 'end').strip())
        messagebox.showinfo("Copied", "Measurements copied to clipboard.")

    def save_to_csv(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV File', '*.csv'), ('All Files', '*.*')],
            title='Save Measurements'
        )
        if save_path:
            try:
                with open(save_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Measurement', f'Length ({self.parent.length_units})'])
                    for i, length in enumerate(self.measurements):
                        writer.writerow([i+1, f"{length:.2f}"])
                messagebox.showinfo("Saved", "Measurements saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save measurements:\n{e}")

class HSVThresholdAdjuster(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('HSV Threshold Adjuster')

        # Check for necessary libraries
        self.check_dependencies()

        # Initialize thresholds
        self.hue_low = 0
        self.hue_high = 360
        self.sat_low = 0
        self.sat_high = 100
        self.val_low = 0
        self.val_high = 100
        self.dragging = None

        # Initialize zoom level
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # Initialize calibration variables
        self.scale_calibrated = False
        self.length_per_pixel = None
        self.length_units = None

        # Measurement instructions flag
        self.measurement_instructions_shown = False

        # List to store measurements
        self.measurements = []
        self.measure_lines = []

        # Undo stack
        self.undo_stack = []

        # Create GUI elements
        self.create_widgets()

        # Load image
        self.load_image_initial()

        # Update threshold lines
        self.update_threshold_lines()

        # Update the displayed image
        self.update_image()

    def check_dependencies(self):
        missing_packages = []
        try:
            import tkinter
        except ImportError:
            missing_packages.append('tkinter')
        try:
            import PIL
        except ImportError:
            missing_packages.append('Pillow')
        try:
            import numpy
        except ImportError:
            missing_packages.append('numpy')
        if missing_packages:
            messagebox.showerror("Missing Dependencies", f"The following packages are required but not installed:\n{', '.join(missing_packages)}\nPlease install them and try again.")
            self.destroy()
            sys.exit()

    def load_image_initial(self):
        # Prompt the user to select an image file
        image_path = filedialog.askopenfilename(
            title='Select Image',
            filetypes=[('Image Files', '*.tif;*.tiff;*.png;*.jpg;*.jpeg;*.bmp')]
        )

        if not image_path:
            # If no file is selected, exit the application
            self.destroy()
            return

        self.load_image(image_path)

    def load_image(self, image_path):
        try:
            # Open the image using Pillow
            self.original_image = Image.open(image_path)

            # Convert image to RGB if not already
            if self.original_image.mode != 'RGB':
                self.original_image = self.original_image.convert('RGB')

            self.image_width, self.image_height = self.original_image.size
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            self.destroy()
            sys.exit()

    def enable_color_picker(self):
        self.image_canvas.bind("<Button-1>", self.pick_color)
        self.image_canvas.config(cursor='cross')

    def pick_color(self, event):
        x = self.image_canvas.canvasx(event.x)
        y = self.image_canvas.canvasy(event.y)
        # Get the pixel color from the original image
        img_x = int(x / self.zoom_level)
        img_y = int(y / self.zoom_level)
        if 0 <= img_x < self.image_width and 0 <= img_y < self.image_height:
            pixel_color = self.original_image.getpixel((img_x, img_y))
            # Convert RGB to HSV
            hsv_color = colorsys.rgb_to_hsv(*(c / 255.0 for c in pixel_color))
            hue = hsv_color[0] * 360
            saturation = hsv_color[1] * 100
            value = hsv_color[2] * 100
            # Set thresholds based on picked color with some tolerance
            self.hue_low = (hue - 10) % 360
            self.hue_high = (hue + 10) % 360
            self.sat_low = max(saturation - 20, 0)
            self.sat_high = min(saturation + 20, 100)
            self.val_low = max(value - 20, 0)
            self.val_high = min(value + 20, 100)
            # Update GUI elements
            self.update_threshold_lines()
            self.sat_low_scale.set(self.sat_low)
            self.sat_high_scale.set(self.sat_high)
            self.val_low_scale.set(self.val_low)
            self.val_high_scale.set(self.val_high)
            self.update_image()
        # Disable color picker after selection
        self.image_canvas.unbind("<Button-1>")
        self.image_canvas.config(cursor='')
    

    def create_widgets(self):
        # Create menu bar
        self.create_menu()

        # Create a frame for the controls
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side='left', padx=10, pady=10)

        # Create the HSV color wheel
        self.wheel_radius = 150
        self.hsv_wheel_image = create_hsv_color_wheel(self.wheel_radius)
        self.hsv_wheel_tk = ImageTk.PhotoImage(self.hsv_wheel_image)

        # Create a canvas to display the color wheel
        self.wheel_canvas = tk.Canvas(self.controls_frame, width=self.wheel_radius*2, height=self.wheel_radius*2)
        self.wheel_canvas.pack()
        self.wheel_canvas.create_image(0, 0, anchor='nw', image=self.hsv_wheel_tk)
        self.wheel_canvas.bind('<Button-1>', self.on_click)
        self.wheel_canvas.bind('<B1-Motion>', self.on_drag)
        
        # Keep a reference to the image to prevent garbage collection
        self.wheel_canvas.image = self.hsv_wheel_tk 
        
        # Create lines for the thresholds
        self.lower_line = self.wheel_canvas.create_line(0, 0, 0, 0, fill='white', width=2)
        self.upper_line = self.wheel_canvas.create_line(0, 0, 0, 0, fill='white', width=2)

        # Create a frame for the hue bar
        self.hue_bar_frame = tk.Frame(self.controls_frame)
        self.hue_bar_frame.pack(pady=10)

        # Create the hue gradient bar
        bar_width = 300
        self.hue_bar_width = bar_width
        self.hue_bar_image = create_hue_gradient_bar(width=bar_width, height=50)
        self.hue_bar_tk = ImageTk.PhotoImage(self.hue_bar_image)

        # Create a canvas to display the hue bar
        self.hue_bar_canvas = tk.Canvas(self.hue_bar_frame, width=bar_width, height=70)
        self.hue_bar_canvas.pack()
        self.hue_bar_canvas.create_image(0, 0, anchor='nw', image=self.hue_bar_tk)
        self.hue_bar_selection = self.hue_bar_canvas.create_rectangle(0, 0, 0, 50, fill='gray', stipple='gray50', outline='')
        
        # Keep a reference to the image
        self.hue_bar_canvas.image = self.hue_bar_tk  # Add this line

        # Create sliders for hue thresholds
        self.hue_frame = tk.Frame(self.controls_frame)
        self.hue_frame.pack(pady=5)
        tk.Label(self.hue_frame, text="Hue Range:").pack()
        self.hue_low_scale = tk.Scale(self.hue_frame, from_=0, to=360, orient='horizontal', command=self.update_hue)
        self.hue_low_scale.set(self.hue_low)
        self.hue_low_scale.pack(side='left')
        self.hue_high_scale = tk.Scale(self.hue_frame, from_=0, to=360, orient='horizontal', command=self.update_hue)
        self.hue_high_scale.set(self.hue_high)
        self.hue_high_scale.pack(side='left')



        # RGB Input Fields
       # self.rgb_frame = tk.Frame(self.controls_frame)
       # self.rgb_frame.pack(pady=5)
        #tk.Label(self.rgb_frame, text="RGB Lower Limit:").grid(row=0, column=0, padx=5, pady=2)
       # self.rgb_lower_entry = tk.Entry(self.rgb_frame, width=15)
       # self.rgb_lower_entry.grid(row=0, column=1, padx=5, pady=2)
       # tk.Label(self.rgb_frame, text="RGB Upper Limit:").grid(row=1, column=0, padx=5, pady=2)
       # self.rgb_upper_entry = tk.Entry(self.rgb_frame, width=15)
       # self.rgb_upper_entry.grid(row=1, column=1, padx=5, pady=2)
       # self.rgb_lower_entry.bind("<Return>", self.update_from_rgb)
       # self.rgb_upper_entry.bind("<Return>", self.update_from_rgb)

        # Create sliders for saturation and value
        self.sat_frame = tk.Frame(self.controls_frame)
        self.sat_frame.pack(pady=5)
        tk.Label(self.sat_frame, text="Saturation Range:").pack()
        self.sat_low_scale = tk.Scale(self.sat_frame, from_=0, to=100, orient='horizontal', command=self.update_saturation)
        self.sat_low_scale.set(self.sat_low)
        self.sat_low_scale.pack(side='left')
        self.sat_high_scale = tk.Scale(self.sat_frame, from_=0, to=100, orient='horizontal', command=self.update_saturation)
        self.sat_high_scale.set(self.sat_high)
        self.sat_high_scale.pack(side='left')

        self.val_frame = tk.Frame(self.controls_frame)
        self.val_frame.pack(pady=5)
        tk.Label(self.val_frame, text="Value Range:").pack()
        self.val_low_scale = tk.Scale(self.val_frame, from_=0, to=100, orient='horizontal', command=self.update_value)
        self.val_low_scale.set(self.val_low)
        self.val_low_scale.pack(side='left')
        self.val_high_scale = tk.Scale(self.val_frame, from_=0, to=100, orient='horizontal', command=self.update_value)
        self.val_high_scale.set(self.val_high)
        self.val_high_scale.pack(side='left')

        # Create buttons for actions
        self.buttons_frame = tk.Frame(self.controls_frame)
        self.buttons_frame.pack(pady=10)

        calibrate_button = tk.Button(self.buttons_frame, text='Calibrate', command=self.calibrate_scale)
        calibrate_button.pack(fill='x', pady=2)

        measure_button = tk.Button(self.buttons_frame, text='Measure', command=self.start_measurement)
        measure_button.pack(fill='x', pady=2)

        load_button = tk.Button(self.buttons_frame, text='Load New Image', command=self.load_new_image)
        load_button.pack(fill='x', pady=2)

        save_button = tk.Button(self.buttons_frame, text='Save Image', command=self.save_image)
        save_button.pack(fill='x', pady=2)

        undo_button = tk.Button(self.buttons_frame, text='Undo', command=self.undo_action)
        undo_button.pack(fill='x', pady=2)

        zoom_in_button = tk.Button(self.buttons_frame, text='Zoom In', command=self.zoom_in)
        zoom_in_button.pack(fill='x', pady=2)

        zoom_out_button = tk.Button(self.buttons_frame, text='Zoom Out', command=self.zoom_out)
        zoom_out_button.pack(fill='x', pady=2)

        scale_bar_button = tk.Button(self.buttons_frame, text='Add Scale Bar', command=self.add_scale_bar)
        scale_bar_button.pack(fill='x', pady=2)

        # In create_widgets, under the buttons section
        color_picker_button = tk.Button(self.buttons_frame, text='Pick Color', command=self.enable_color_picker)
        color_picker_button.pack(fill='x', pady=2)


        # Create a frame for the image and scrollbars
        self.image_frame = tk.Frame(self)
        self.image_frame.pack(side='right', padx=10, pady=10, fill='both', expand=True)

        # Create a canvas for the image
        self.image_canvas = tk.Canvas(self.image_frame, bg='black')
        self.image_canvas.pack(side='left', fill='both', expand=True)

        # Create vertical scrollbar
        self.v_scroll = tk.Scrollbar(self.image_frame, orient='vertical', command=self.image_canvas.yview)
        self.v_scroll.pack(side='right', fill='y')
        self.image_canvas.config(yscrollcommand=self.v_scroll.set)

        # Create horizontal scrollbar
        self.h_scroll = tk.Scrollbar(self, orient='horizontal', command=self.image_canvas.xview)
        self.h_scroll.pack(side='bottom', fill='x')
        self.image_canvas.config(xscrollcommand=self.h_scroll.set)

        # Bind mouse wheel for zooming and panning
        if platform.system() == 'Windows':
            self.image_canvas.bind('<MouseWheel>', self.on_mousewheel)
        elif platform.system() == 'Darwin':
            self.image_canvas.bind('<Button-4>', self.on_mousewheel)
            self.image_canvas.bind('<Button-5>', self.on_mousewheel)
        else:
            self.image_canvas.bind('<Button-4>', self.on_mousewheel)
            self.image_canvas.bind('<Button-5>', self.on_mousewheel)

        self.image_canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.image_canvas.bind('<B1-Motion>', self.on_canvas_drag)

    def update_hue(self, val):
            self.hue_low = min(self.hue_low_scale.get(), self.hue_high_scale.get())
            self.hue_high = max(self.hue_low_scale.get(), self.hue_high_scale.get())
            self.update_threshold_lines()
            self.update_image()


    def create_menu(self):
        menu_bar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label='Load New Image', command=self.load_new_image)
        file_menu.add_command(label='Save Image', command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label='File', menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label='Instructions', command=self.show_instructions)
        help_menu.add_command(label='About', command=self.show_about)
        menu_bar.add_cascade(label='Help', menu=help_menu)

        self.config(menu=menu_bar)

    def show_instructions(self):
        instructions = (
            "Instructions:\n\n"
            "1. Load an image to begin.\n"
            "2. Use the color wheel to set hue thresholds by dragging the white lines.\n"
            "3. Adjust saturation and value ranges using the sliders.\n"
            "4. Calibrate the scale by drawing a line of known length or entering pixel size.\n"
            "5. Add a scale bar to the image if desired.\n"
            "6. Use the Measure tool to measure distances on the image.\n"
            "7. Save the processed image using the Save Image option.\n"
            "8. Use Undo to revert the last action.\n"
            "\n"
            "Controls:\n"
            "- Left-click and drag to pan the image.\n"
            "- Scroll wheel to zoom in/out.\n"
            "- Right-click to finish measurement mode.\n"
            "- Hold Shift during calibration to snap angles.\n"
        )
        messagebox.showinfo("Instructions", instructions)

    def show_about(self):
        about_text = (
            "HSV Threshold Adjuster\n"
            "Version 1.0\n\n"
            "Developed to assist with image processing tasks involving hue, saturation, and value adjustments."
        )
        messagebox.showinfo("About", about_text)

    def update_saturation(self, val):
        self.sat_low = min(self.sat_low_scale.get(), self.sat_high_scale.get())
        self.sat_high = max(self.sat_low_scale.get(), self.sat_high_scale.get())
        self.update_image()

    def update_value(self, val):
        self.val_low = min(self.val_low_scale.get(), self.val_high_scale.get())
        self.val_high = max(self.val_low_scale.get(), self.val_high_scale.get())
        self.update_image()

    def update_from_rgb(self, event):
        try:
            rgb_lower = tuple(int(x.strip()) for x in self.rgb_lower_entry.get().split(','))
            rgb_upper = tuple(int(x.strip()) for x in self.rgb_upper_entry.get().split(','))
            if len(rgb_lower) != 3 or len(rgb_upper) != 3:
                raise ValueError
            # Convert RGB to HSV
            hsv_lower = rgb_to_hsv(*rgb_lower)
            hsv_upper = rgb_to_hsv(*rgb_upper)
            # Update thresholds
            self.hue_low = hsv_lower[0] * 360
            self.hue_high = hsv_upper[0] * 360
            self.sat_low = hsv_lower[1] * 100
            self.sat_high = hsv_upper[1] * 100
            self.val_low = hsv_lower[2] * 100
            self.val_high = hsv_upper[2] * 100
            # Update GUI elements
            self.sat_low_scale.set(self.sat_low)
            self.sat_high_scale.set(self.sat_high)
            self.val_low_scale.set(self.val_low)
            self.val_high_scale.set(self.val_high)
            self.update_threshold_lines()
            self.update_image()
        except ValueError:
            messagebox.showerror("Input Error", "Please enter RGB values in the format R,G,B (e.g., 255,0,0).")

    def update_rgb_entries(self):
        # Convert HSV thresholds to RGB
        rgb_lower = hsv_to_rgb(self.hue_low / 360, self.sat_low / 100, self.val_low / 100)
        rgb_upper = hsv_to_rgb(self.hue_high / 360, self.sat_high / 100, self.val_high / 100)
        rgb_lower = tuple(int(c) for c in rgb_lower)
        rgb_upper = tuple(int(c) for c in rgb_upper)
        self.rgb_lower_entry.delete(0, 'end')
        self.rgb_lower_entry.insert(0, f"{rgb_lower[0]},{rgb_lower[1]},{rgb_lower[2]}")
        self.rgb_upper_entry.delete(0, 'end')
        self.rgb_upper_entry.insert(0, f"{rgb_upper[0]},{rgb_upper[1]},{rgb_upper[2]}")

    def calibrate_scale(self):
        # Ask the user if they want to calibrate the scale
        result = messagebox.askyesno("Calibrate Scale", "Do you want to calibrate the scale?")
        if result:
            # Choose calibration method
            method = messagebox.askyesno("Calibration Method", "Would you like to draw a line of known length?\nSelect 'No' to enter the pixel size.")
            if method:
                # Draw a line of known length
                messagebox.showinfo("Calibration", "Please draw a line of known length on the image.")
                self.image_canvas.bind("<ButtonPress-1>", self.start_calibration_line)
                self.image_canvas.bind("<ButtonRelease-1>", self.end_calibration_line)
            else:
                # Enter pixel size
                self.enter_pixel_size()
        else:
            self.scale_calibrated = False

    def start_calibration_line(self, event):
        # Disable panning
        self.image_canvas.unbind('<ButtonPress-1>')
        self.image_canvas.unbind('<B1-Motion>')
        # Start line drawing
        self.calibration_line_start = (self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y))
        self.calibration_line = self.image_canvas.create_line(
            self.calibration_line_start[0], self.calibration_line_start[1],
            self.calibration_line_start[0], self.calibration_line_start[1],
            fill='red', width=2)
        self.image_canvas.bind("<Motion>", self.draw_calibration_line)
        self.image_canvas.bind_all("<Shift_L>", self.enable_snap)
        self.image_canvas.bind_all("<KeyRelease-Shift_L>", self.disable_snap)
        self.snap_enabled = False
        self.image_canvas.focus_set()

    def enable_snap(self, event):
        self.snap_enabled = True

    def disable_snap(self, event):
        self.snap_enabled = False

    def draw_calibration_line(self, event):
        x, y = self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y)
        if self.snap_enabled:
            angle = np.degrees(np.arctan2(y - self.calibration_line_start[1], x - self.calibration_line_start[0]))
            snapped_angle = round(angle / 15) * 15
            length = ((x - self.calibration_line_start[0]) ** 2 + (y - self.calibration_line_start[1]) ** 2) ** 0.5
            x = self.calibration_line_start[0] + length * np.cos(np.radians(snapped_angle))
            y = self.calibration_line_start[1] + length * np.sin(np.radians(snapped_angle))
        self.image_canvas.coords(self.calibration_line, self.calibration_line_start[0], self.calibration_line_start[1], x, y)

    def end_calibration_line(self, event):
        self.image_canvas.unbind("<Motion>")
        self.image_canvas.unbind("<ButtonRelease-1>")
        self.image_canvas.unbind_all("<Shift_L>")
        self.image_canvas.unbind_all("<KeyRelease-Shift_L>")
        # Re-enable panning
        self.image_canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.image_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        
        x_end = self.image_canvas.canvasx(event.x) / self.zoom_level
        y_end = self.image_canvas.canvasy(event.y) / self.zoom_level
        
        # Get start coordinates adjusted for zoom level
        x_start = self.calibration_line_start[0] / self.zoom_level
        y_start = self.calibration_line_start[1] / self.zoom_level
        
        pixel_distance = pixel_distance = ((x_end - x_start)**2 + (y_end - y_start)**2)**0.5
        if pixel_distance == 0:
            messagebox.showerror("Calibration Error", "Calibration line length cannot be zero.")
            self.image_canvas.delete(self.calibration_line)
            self.scale_calibrated = False
            return
        dialog = CalibrationDialog(self)
        self.wait_window(dialog)
        if dialog.length is None or dialog.units is None:
            self.image_canvas.delete(self.calibration_line)
            self.scale_calibrated = False
            return
        try:
            self.length_per_pixel = dialog.length / pixel_distance
            self.length_units = dialog.units
            self.scale_calibrated = True
            messagebox.showinfo("Calibration Complete", f"Scale calibrated: {self.length_per_pixel:.4f} {self.length_units} per pixel.")
            self.undo_stack.append(('calibration_line', self.calibration_line))
        except Exception as e:
            messagebox.showerror("Calibration Error", f"Error during calibration:\n{e}")
            self.scale_calibrated = False
        self.image_canvas.delete(self.calibration_line)

    def enter_pixel_size(self):
        dialog = CalibrationDialog(self)
        self.wait_window(dialog)
        if dialog.length is None or dialog.units is None:
            self.scale_calibrated = False
            return
        try:
            self.length_per_pixel = dialog.length
            self.length_units = dialog.units
            self.scale_calibrated = True
            messagebox.showinfo("Calibration Complete", f"Scale calibrated: {self.length_per_pixel:.4f} {self.length_units} per pixel.")
        except Exception as e:
            messagebox.showerror("Calibration Error", f"Error during calibration:\n{e}")
            self.scale_calibrated = False

    def add_scale_bar(self):
        if not self.scale_calibrated:
            messagebox.showwarning("Scale Not Calibrated", "Please calibrate the scale first.")
            return
        desired_length = simpledialog.askfloat("Scale Bar Length", f"Enter the desired length of the scale bar ({self.length_units}):")
        if desired_length is None:
            return
        try:
            # Calculate pixel length
            pixel_length = desired_length / self.length_per_pixel
            pixel_length *= self.zoom_level
            # Position the scale bar
            x0 = 50
            y0 = self.image_height * self.zoom_level - 50
            x1 = x0 + pixel_length
            # Draw the scale bar
            if hasattr(self, 'scale_bar'):
                self.image_canvas.delete(self.scale_bar)
                self.image_canvas.delete(self.scale_bar_text)
            self.scale_bar = self.image_canvas.create_line(x0, y0, x1, y0, fill='white', width=5, tags='scale_bar')
            self.scale_bar_text = self.image_canvas.create_text((x0 + x1)/2, y0 - 10, text=f"{desired_length} {self.length_units}", fill='white', font=('Arial', 12), tags='scale_bar')
            # Enable dragging
            self.image_canvas.tag_bind('scale_bar', '<ButtonPress-1>', self.on_scale_bar_press)
            self.image_canvas.tag_bind('scale_bar', '<B1-Motion>', self.on_scale_bar_move)
            self.image_canvas.tag_bind('scale_bar', '<ButtonRelease-1>', self.on_scale_bar_release)
            
            self.undo_stack.append(('scale_bar', (self.scale_bar, self.scale_bar_text)))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add scale bar:\n{e}")

    def on_scale_bar_press(self, event):
        # Disable panning during scale bar movement
        self.image_canvas.unbind('<ButtonPress-1>')
        self.image_canvas.unbind('<B1-Motion>')
        
        self.scale_bar_x = self.image_canvas.canvasx(event.x)
        self.scale_bar_y = self.image_canvas.canvasy(event.y)

    def on_scale_bar_move(self, event):
        dx = self.image_canvas.canvasx(event.x) - self.scale_bar_x
        dy = self.image_canvas.canvasy(event.y) - self.scale_bar_y
        self.image_canvas.move('scale_bar', dx, dy)
        
        self.scale_bar_x = self.image_canvas.canvasx(event.x)
        self.scale_bar_y = self.image_canvas.canvasy(event.y)
    def on_scale_bar_release (self, event):
        # Re-enable panning after moving the scale bar
        self.image_canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.image_canvas.bind('<B1-Motion>', self.on_canvas_drag)
    def start_measurement(self):
        if not self.scale_calibrated:
            messagebox.showwarning("Scale Not Calibrated", "Please calibrate the scale first.")
            return
        if not self.measurement_instructions_shown:
            messagebox.showinfo("Measurement", "Draw lines on the image to measure lengths. Right-click to finish measuring.")
            self.measurement_instructions_shown = True
       
        # Disable panning during measurement
        self.image_canvas.unbind('<ButtonPress-1>')
        self.image_canvas.unbind('<B1-Motion>')
        self.image_canvas.bind("<ButtonPress-1>", self.start_measure_line)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_measure_line)
        self.image_canvas.bind("<Button-3>", self.finish_measurement)
        self.image_canvas.config(cursor='cross')

        # Create the measurement dialog if it doesn't exist
        if not hasattr(self, 'measurement_dialog') or not self.measurement_dialog.winfo_exists():
            self.measurement_dialog = MeasurementDialog(self, self.measurements)
        else:
            # Update the measurements in the dialog
            self.measurement_dialog.update_measurements(self.measurements)

    def start_measure_line(self, event):
        # Start line drawing
        self.measure_line_start = (self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y))
        self.current_measure_line = self.image_canvas.create_line(
            self.measure_line_start[0], self.measure_line_start[1],
            self.measure_line_start[0], self.measure_line_start[1],
            fill='yellow', width=2, tags='measurement')
        self.image_canvas.bind("<Motion>", self.draw_measure_line)


    def draw_measure_line(self, event):
        x, y = self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y)
        self.image_canvas.coords(self.current_measure_line, self.measure_line_start[0], self.measure_line_start[1], x, y)

    def end_measure_line(self, event):
        self.image_canvas.unbind("<Motion>")
        x_end, y_end = self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y)
        pixel_distance = ((x_end - self.measure_line_start[0])**2 + (y_end - self.measure_line_start[1])**2)**0.5 / self.zoom_level
        actual_length = pixel_distance * self.length_per_pixel
        self.measurements.append(actual_length)
        self.measure_lines.append(self.current_measure_line)
        # Display the length near the line
        mid_x = (self.measure_line_start[0] + x_end) / 2
        mid_y = (self.measure_line_start[1] + y_end) / 2
        text = f"{actual_length:.2f} {self.length_units}"
        text_id = self.image_canvas.create_text(
            mid_x, mid_y - 10, text=text, fill='yellow', font=('Arial', 12), tags='measurement')
        self.measure_lines.append(text_id)
        # Update the measurement dialog
        if hasattr(self, 'measurement_dialog') and self.measurement_dialog.winfo_exists():
            self.measurement_dialog.update_measurements(self.measurements)
        else:
            self.measurement_dialog = MeasurementDialog(self, self.measurements)
        # Undo stack
        self.undo_stack.append(('measurement', (self.current_measure_line, text_id)))
        # Re-bind events for next measurement
        self.image_canvas.bind("<ButtonPress-1>", self.start_measure_line)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_measure_line)

    def finish_measurement(self, event):
        self.image_canvas.unbind("<ButtonPress-1>")
        self.image_canvas.unbind("<ButtonRelease-1>")
        self.image_canvas.unbind("<Button-3>")
        self.image_canvas.config(cursor='')
        # Re-enable panning
        self.image_canvas.bind('<ButtonPress-1>', self.on_canvas_click)
        self.image_canvas.bind('<B1-Motion>', self.on_canvas_drag)

    def load_new_image(self):
        # Prompt the user to confirm
        result = messagebox.askyesno("Load New Image", "Do you want to close the current image and load a new one?")
        if result:
            # Ask the user to select a new image file
            image_path = filedialog.askopenfilename(
                title='Select Image',
                filetypes=[('Image Files', '*.tif;*.tiff;*.png;*.jpg;*.jpeg;*.bmp')]
            )
            if image_path:
                try:
                    # Load the new image
                    self.load_image(image_path)
                    # Reset zoom level
                    self.zoom_level = 1.0
                    # Clear measurements and scale bar
                    if hasattr(self, 'scale_bar'):
                        self.image_canvas.delete(self.scale_bar)
                        self.image_canvas.delete(self.scale_bar_text)
                        del self.scale_bar
                        del self.scale_bar_text
                    # Delete measurement lines and texts from the canvas
                    for item in self.measure_lines:
                        self.image_canvas.delete(item)
                    self.measure_lines.clear()
                    self.measurements.clear()
                    # Reset scale calibration
                    self.scale_calibrated = False
                    # Clear undo stack
                    self.undo_stack.clear()
                    # Reset HSV thresholds to default values
                    self.hue_low = 0
                    self.hue_high = 360
                    self.sat_low = 0
                    self.sat_high = 100
                    self.val_low = 0
                    self.val_high = 100
                    # Update GUI elements if necessary
                    self.sat_low_scale.set(self.sat_low)
                    self.sat_high_scale.set(self.sat_high)
                    self.val_low_scale.set(self.val_low)
                    self.val_high_scale.set(self.val_high)
                    # Update the image canvas
                    self.update_image()
                    # Update the threshold lines
                    self.update_threshold_lines()
                    # Update the scroll region
                    self.image_canvas.config(scrollregion=(0, 0, self.image_width * self.zoom_level, self.image_height * self.zoom_level))
                    # Close measurement dialog if open
                    if hasattr(self, 'measurement_dialog') and self.measurement_dialog.winfo_exists():
                        self.measurement_dialog.destroy()
                    # Reset event bindings if necessary
                    self.image_canvas.unbind("<ButtonPress-1>")
                    self.image_canvas.unbind("<B1-Motion>")
                    self.image_canvas.bind('<ButtonPress-1>', self.on_canvas_click)
                    self.image_canvas.bind('<B1-Motion>', self.on_canvas_drag)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image:\n{e}")


    def on_click(self, event):
        angle = self.get_angle(event.x, event.y)
        if self.is_near_angle(angle, self.hue_low):
            self.dragging = 'low'
        elif self.is_near_angle(angle, self.hue_high):
            self.dragging = 'high'
        else:
            self.dragging = None

    def on_drag(self, event):
        angle = self.get_angle(event.x, event.y)
        if self.dragging == 'low':
            self.hue_low = angle
            self.update_threshold_lines()
            self.update_image()
        elif self.dragging == 'high':
            self.hue_high = angle
            self.update_threshold_lines()
            self.update_image()
        self.update_rgb_entries()

    def get_angle(self, x, y):
        dx = x - self.wheel_radius
        dy = y - self.wheel_radius
        angle = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
        return angle

    def is_near_angle(self, angle1, angle2, threshold=5):
        return min(abs(angle1 - angle2), 360 - abs(angle1 - angle2)) < threshold

    def update_threshold_lines(self):
        # Remove existing sector if it exists
        if hasattr(self, 'sector'):
            self.wheel_canvas.delete(self.sector)

        # Lower threshold line
        x1, y1 = self.get_line_coords(self.hue_low)
        self.wheel_canvas.coords(self.lower_line, self.wheel_radius, self.wheel_radius, x1, y1)

        # Upper threshold line
        x2, y2 = self.get_line_coords(self.hue_high)
        self.wheel_canvas.coords(self.upper_line, self.wheel_radius, self.wheel_radius, x2, y2)

        # Draw the shaded sector
        points = [self.wheel_radius, self.wheel_radius, x1, y1]
        # Generate points along the arc
        angle_start = self.hue_low
        angle_end = self.hue_high
        if angle_start > angle_end:
            angle_end += 360  # Handle wrap-around
        num_points = int(abs(angle_end - angle_start))  # Number of points along the arc
        for angle in np.linspace(angle_start, angle_end, num_points):
            x, y = self.get_line_coords(angle % 360)
            points.extend([x, y])
        points.extend([x2, y2])
        # Draw the sector
        self.sector = self.wheel_canvas.create_polygon(points, fill='gray', stipple='gray50', outline='')

        # Update the hue bar selection
        bar_width = self.hue_bar_width
        x_start = hue_angle_to_x(self.hue_low, bar_width)
        x_end = hue_angle_to_x(self.hue_high, bar_width)
        if x_start > x_end:
            # Handle wrap-around by drawing two rectangles
            if hasattr(self, 'hue_bar_selection1'):
                self.hue_bar_canvas.delete(self.hue_bar_selection1)
                self.hue_bar_canvas.delete(self.hue_bar_selection2)
            self.hue_bar_selection1 = self.hue_bar_canvas.create_rectangle(0, 0, x_end, 50, fill='gray', stipple='gray50', outline='')
            self.hue_bar_selection2 = self.hue_bar_canvas.create_rectangle(x_start, 0, bar_width, 50, fill='gray', stipple='gray50', outline='')
            self.hue_bar_canvas.itemconfig(self.hue_bar_selection, state='hidden')
        else:
            if hasattr(self, 'hue_bar_selection1'):
                self.hue_bar_canvas.delete(self.hue_bar_selection1)
                self.hue_bar_canvas.delete(self.hue_bar_selection2)
            self.hue_bar_canvas.coords(self.hue_bar_selection, x_start, 0, x_end, 50)
            self.hue_bar_canvas.itemconfig(self.hue_bar_selection, state='normal')

    def get_line_coords(self, angle):
        radians = np.radians(angle)
        x = self.wheel_radius + self.wheel_radius * np.cos(radians)
        y = self.wheel_radius + self.wheel_radius * np.sin(radians)
        return x, y

    def update_image(self):
        # Convert the image to HSV
        hsv_image = self.original_image.convert('HSV')
        hsv_array = np.array(hsv_image)

        # Calculate hue thresholds
        hue_low = int((self.hue_low / 360) * 255)
        hue_high = int((self.hue_high / 360) * 255)

        # Calculate saturation thresholds
        sat_low = int((self.sat_low / 100) * 255)
        sat_high = int((self.sat_high / 100) * 255)

        # Calculate value thresholds
        val_low = int((self.val_low / 100) * 255)
        val_high = int((self.val_high / 100) * 255)

        # Handle the circular nature of hue
        if hue_low <= hue_high:
            hue_mask = (hsv_array[:, :, 0] >= hue_low) & (hsv_array[:, :, 0] <= hue_high)
        else:
            hue_mask = (hsv_array[:, :, 0] >= hue_low) | (hsv_array[:, :, 0] <= hue_high)

        sat_mask = (hsv_array[:, :, 1] >= sat_low) & (hsv_array[:, :, 1] <= sat_high)
        val_mask = (hsv_array[:, :, 2] >= val_low) & (hsv_array[:, :, 2] <= val_high)

        # Combine masks
        mask = hue_mask & sat_mask & val_mask

        # Apply the mask
        masked_array = np.copy(np.array(self.original_image))
        masked_array[~mask] = [0, 0, 0]  # Set pixels outside the threshold to black

        # Convert back to image
        masked_image = Image.fromarray(masked_array)

        # Resize the image according to the zoom level
        zoomed_width = int(self.image_width * self.zoom_level)
        zoomed_height = int(self.image_height * self.zoom_level)
        zoomed_image = masked_image.resize((zoomed_width, zoomed_height), Image.LANCZOS)

        self.masked_image_tk = ImageTk.PhotoImage(zoomed_image)

        # Update the image on the canvas
        if hasattr(self, 'image_id'):
            self.image_canvas.itemconfig(self.image_id, image=self.masked_image_tk)
        else:
            self.image_id = self.image_canvas.create_image(0, 0, anchor='nw', image=self.masked_image_tk)
            self.image_canvas.tag_lower(self.image_id)  # Ensure the image is at the bottom
            
        # Raise measurement items above the image
        self.image_canvas.tag_raise('measurement')
        
        # Raise scale bar above the image
        self.image_canvas.tag_raise('scale_bar') 
        
        # Update the scroll region
        self.image_canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))

    def on_canvas_click(self, event):
        self.image_canvas.scan_mark(event.x, event.y)

    def on_canvas_drag(self, event):
        self.image_canvas.scan_dragto(event.x, event.y, gain=1)

    def on_mousewheel(self, event):
        if platform.system() == 'Windows':
            delta = event.delta
        elif platform.system() == 'Darwin':
            delta = event.delta
        else:
            delta = -event.delta

        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self.zoom_level < self.max_zoom:
            self.zoom_level *= 1.1  # Increase zoom level by 10%
            self.update_image()

    def zoom_out(self):
        if self.zoom_level > self.min_zoom:
            self.zoom_level /= 1.1  # Decrease zoom level by 10%
            self.update_image()

    def undo_action(self):
        if self.undo_stack:
            action, item = self.undo_stack.pop()
            if action == 'measurement':
                line_id, text_id = item
                self.image_canvas.delete(line_id)
                self.image_canvas.delete(text_id)
                if self.measurements:
                    self.measurements.pop()
                if hasattr(self, 'measurement_dialog') and self.measurement_dialog.winfo_exists():
                    self.measurement_dialog.update_measurements(self.measurements)
            elif action == 'calibration_line':
                self.image_canvas.delete(item)
                self.scale_calibrated = False
            elif action == 'scale_bar':
                scale_line, scale_text = item
                self.image_canvas.delete(scale_line)
                self.image_canvas.delete(scale_text)
                if hasattr(self, 'scale_bar'):
                    del self.scale_bar
                    del self.scale_bar_text
            # Add more undo actions as needed
        else:
            messagebox.showinfo("Undo", "Nothing to undo.")

    def save_image(self):
        # Prompt the user to select a save location
        save_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG Image', '*.png'), ('JPEG Image', '*.jpg;*.jpeg'), ('All Files', '*.*')],
            title='Save Image'
        )
        if save_path:
            try:
                # Create a copy of the masked image
                save_image = self.original_image.copy()

                # Apply the HSV mask
                hsv_image = save_image.convert('HSV')
                hsv_array = np.array(hsv_image)
                hue_low = int((self.hue_low / 360) * 255)
                hue_high = int((self.hue_high / 360) * 255)
                sat_low = int((self.sat_low / 100) * 255)
                sat_high = int((self.sat_high / 100) * 255)
                val_low = int((self.val_low / 100) * 255)
                val_high = int((self.val_high / 100) * 255)

                if hue_low <= hue_high:
                    hue_mask = (hsv_array[:, :, 0] >= hue_low) & (hsv_array[:, :, 0] <= hue_high)
                else:
                    hue_mask = (hsv_array[:, :, 0] >= hue_low) | (hsv_array[:, :, 0] <= hue_high)

                sat_mask = (hsv_array[:, :, 1] >= sat_low) & (hsv_array[:, :, 1] <= sat_high)
                val_mask = (hsv_array[:, :, 2] >= val_low) & (hsv_array[:, :, 2] <= val_high)

                mask = hue_mask & sat_mask & val_mask

                masked_array = np.copy(np.array(save_image))
                masked_array[~mask] = [0, 0, 0]
                save_image = Image.fromarray(masked_array)

                # Draw scale bar onto the image if it exists
                if hasattr(self, 'scale_bar'):
                    draw = ImageDraw.Draw(save_image)
                    
                    # Get the coordinates of the scale bar and adjust for zoom level
                    coords = [coord / self.zoom_level for coord in self.image_canvas.coords(self.scale_bar)]
                    
                    # Adjust line width and font size based on scaling factor
                    scaling_factor = 1 / self.zoom_level
                    
                    # Adjust the line width, ensuring it stays reasonable for visibility
                    line_width = int(5 * scaling_factor)
                    if line_width < 2:
                        line_width = 2  # Set a minimum line width for readability
                    
                    # Adjust the font size, with a fallback for default font
                    font_size = int(26 * scaling_factor)
                    if font_size < 24:
                        font_size = 24  # Set a minimum font size for readability
                    
                    # Draw the scale bar line
                    draw.line(coords, fill='white', width=line_width)
            
                    # Draw the scale bar text
                    text = self.image_canvas.itemcget(self.scale_bar_text, 'text')
                    
                    # Use a TrueType font for better consistency in saved image
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except (IOError, OSError):
                        font = ImageFont.load_default()
            
                    # Calculate text position
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
            
                    # Calculate text coordinates to be centered above the scale bar
                    x0, y0, x1, _ = coords
                    text_x = (x0 + x1) / 2 - text_width / 2
                    text_y = y0 - text_height - 10  # 10 pixels above the line for spacing
            
                    # Draw the text on the image
                    draw.text((text_x, text_y), text, fill='white', font=font)
            
                # Save the image
                save_image.save(save_path)
                messagebox.showinfo("Save Image", "Image saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")

if __name__ == '__main__':
    app = HSVThresholdAdjuster()
    app.mainloop()
