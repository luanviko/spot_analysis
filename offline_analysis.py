from typing import Optional, Tuple
from pathlib import Path
import numpy as np, json, yaml, os
import cv2 as cv, rawpy
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from scipy import interpolate
from scipy.optimize import least_squares
from utils import Database


def circle_residuals(
    params: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    x_error: Optional[np.ndarray] = None,
    y_error: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Computes residuals between given (x, y) points and a circle defined by `params`.

    Args:
        params (np.ndarray): Circle parameters (x0, y0, R).
        x (np.ndarray): x-coordinates.
        y (np.ndarray): y-coordinates.
        x_error (Optional[np.ndarray]): Uncertainty in x.
        y_error (Optional[np.ndarray]): Uncertainty in y.

    Returns:
        np.ndarray: Residuals for least-squares fitting.
    """
    x0, y0, R = params
    dx = x - x0
    dy = y - y0
    r = np.sqrt(dx**2 + dy**2)
    residuals = r - R

    if x_error is not None and y_error is not None:
        sigma_r = np.sqrt(((dx / r) * x_error)**2 + ((dy / r) * y_error)**2)
        residuals = residuals / sigma_r

    return residuals


def prepare_image(
    photo: dict,
    auto_focus: Optional[float] = None,
    mode: str = '',
    blurvar: int = 10,
    norm: bool = True,
    blurthreshold: float = 0.01
) -> Tuple[np.ndarray, Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]]:
    """
    Loads and preprocesses an image from a photo dictionary.

    Args:
        photo (dict): Photo metadata containing 'photo_path', coordinates, etc.
        auto_focus (Optional[float]): Crop factor based on circle radius.
        mode (str): 'gray' for grayscale or anything else for blurred.
        blurvar (int): Blur kernel size.
        norm (bool): Normalize grayscale image.
        blurthreshold (float): Threshold to zero weak blur responses.

    Returns:
        Tuple[np.ndarray, Tuple[int, int, int, int]]: Processed image and extent.
    """
    file = Path(photo['photo_path'][0])
    print(file)

    # if os.name == 'posix': => change to platform.system()
        # file = file.replace('home','Users')

    extent = (None, None, None, None)

    if file.suffix == ".ARW":
        
        raw_base = rawpy.imread(str(file))
        rgb_base_linear = raw_base.postprocess(
            output_color=rawpy.ColorSpace.raw,
            gamma=(1, 1),
            user_wb=[1.0, 1.0, 1.0, 1.0],
            no_auto_bright=True
        )

        if auto_focus is not None and auto_focus >= 1:
            height = raw_base.sizes.raw_height
            width = raw_base.sizes.raw_width

            x0 = photo['best_x0']
            y0 = photo['best_y0']
            R = photo['best_R']

            row_start = int(y0 - auto_focus * R)
            row_end   = int(y0 + auto_focus * R)
            col_start = int(x0 - auto_focus * R)
            col_end   = int(x0 + auto_focus * R)
            extent = (col_start, col_end, row_end, row_start)

            rgb_base_linear = rgb_base_linear[row_start:row_end, col_start:col_end]
    else:
        rgb_base_linear = cv.imread(file, cv.IMREAD_UNCHANGED)

    gray = cv.cvtColor(rgb_base_linear, cv.COLOR_BGR2GRAY)

    if norm:
        gray = gray / np.max(gray)

    blur = cv.blur(gray, (blurvar, blurvar))
    blur = blur / np.max(blur)
    blur[blur < blurthreshold] = 0

    z = gray if mode == 'gray' else blur

    return z, extent


def spot_display(
    z: np.ndarray,
    extent: Tuple[int, int, int, int],
    steps: int = 10,
    transparent: bool = False,
    save: str = ''
) -> None:
    """
    Displays the processed image with contours and axis annotations.

    Args:
        z (np.ndarray): The image array.
        extent (Tuple[int, int, int, int]): Image bounds for display.
        steps (int): Number of contour levels.
        save (str): Path to save the figure. If empty, figure is not saved.
    """
    if transparent:
        spot_cmap = LinearSegmentedColormap.from_list('white_salmon', [to_rgba('white', alpha=0.0), to_rgba('papayawhip', alpha=1.0)])
    else:
        spot_cmap = LinearSegmentedColormap.from_list('white_salmon', [to_rgba('white', alpha=1.0), to_rgba('papayawhip', alpha=1.0)])

    fig, axes = plt.subplots(1, 1, figsize=(8, 7))
    im = axes.imshow(z, extent=extent, cmap=spot_cmap)

    x_min, x_max = axes.get_xlim()
    y_min, y_max = axes.get_ylim()

    x_centre = extent[0] + (extent[1] - extent[0]) / 2.
    y_centre = extent[2] + (extent[3] - extent[2]) / 2.

    # Custom ticks
    step = 100
    xticks = np.arange(x_centre - 2*step, x_centre + 3*step, step)
    yticks = np.arange(y_centre - 2*step, y_centre + 3*step, step)

    axes.set_xticks(xticks)
    axes.set_yticks(yticks)
    axes.axis('off')

    # Draw custom axes
    axes.hlines(y_min + 5, xticks[0], xticks[-1], color='black', linewidth=1.1)
    axes.vlines(x_min - 5, yticks[0], yticks[-1], color='black', linewidth=1.1)

    for i, tick in enumerate(xticks):
        label = i * step - 2 * step
        axes.vlines(tick, y_min + 5, y_min + 10, color='black', linewidth=1.1)
        axes.text(tick, y_min + 21, f'{label}', ha='center', va='center', fontsize=10)

    for i, tick in enumerate(yticks):
        label = i * step - 2 * step
        axes.hlines(tick, x_min - 5, x_min - 10, color='black', linewidth=1.1)
        axes.text(x_min - 13, tick, f'{label}', ha='right', va='center', fontsize=10)

    axes.text(x_min - 50, y_centre, 'Pixel', ha='center', va='center', fontsize=10, rotation=90)
    axes.text(x_centre, y_min + 60, 'Pixel', ha='center', va='center', fontsize=10)

    # Contours
    t = np.linspace(0, z.max(), 2)
    integral = ((z >= t[:, None, None]) * z).sum(axis=(1, 2))
    f = interpolate.interp1d(integral, t)
    t_contours = np.linspace(f(integral.max()), f(integral.min()), steps)

    contour_cmap = LinearSegmentedColormap.from_list('white_salmon', ['teal', 'orangered'])
    axes.contour(z, t_contours, extent=extent, cmap=contour_cmap)

    if save:
        plt.tight_layout()
        plt.savefig(save, transparent = transparent, dpi = 500)


def load_json(json_path: str | Path) -> dict:
    """
    Loads a JSON file into a Python dictionary.

    Args:
        json_path (str): Path to JSON file.

    Returns:
        dict: Parsed JSON content.
    """
    with open(json_path, 'r') as json_input:
        return json.load(json_input)


def offline_analysis() -> None:
    """
    Loads photos from a database and performs offline visualization.
    """
    db = Database('./photos.sqlite')

    json_paths = db.fetch_photos(run_number='9998', led_serial='1')

    for json_file in json_paths:
        photo = load_json(json_file)
        z, extent = prepare_image(photo, auto_focus=2.)
        with plt.rc_context({'font.family': 'DejaVu Sans Mono'}):
            spot_display(z, extent, steps=10, save='./spot.png', transparent=True)


if __name__ == '__main__':
    offline_analysis()
