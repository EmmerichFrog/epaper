import os
import numpy as np
from numpy import typing as npt
from numba import jit, njit
from PIL import Image, ImageEnhance, ImageOps

GREYSCALE = False
MAX_RGB = 255
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PALETTE = [BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE]

paletteFloat = list()
for color in PALETTE:
    channelFloat = list()
    for channel in color:
        channelFloat.append(channel / MAX_RGB)
    paletteFloat.append(channelFloat)


@njit()
def get_new_val_jit(old_val: npt.NDArray[np.float32], p: npt.NDArray[np.float32]):
    idx = np.argmin(np.sum((old_val[None, :] - p) ** 2, axis=1))
    return p[idx]


def fs_dither(
    img: Image.Image, new_height: int, new_width: int, palette: npt.NDArray[np.float32]
) -> Image.Image:
    """
    Floyd-Steinberg dither the image img into a palette with 7 colors per
    channel.
    """
    arr = np.array(img.resize((new_width, new_height)), dtype=float) / 255
    padded_arr = np.pad(
        arr, ((0, 1), (0, 1), (0, 0)), mode="constant"
    )  # Pad to avoid boundary checks

    for ir in range(new_height):
        for ic in range(new_width):
            old_val = padded_arr[ir, ic].copy()
            new_val = get_new_val_jit(old_val, palette)
            padded_arr[ir, ic] = new_val
            err = old_val - new_val

            # Apply the error to neighboring pixels
            padded_arr[ir, ic + 1] += err * 7 / 16
            padded_arr[ir + 1, ic - 1] += err * 3 / 16
            padded_arr[ir + 1, ic] += err * 5 / 16
            padded_arr[ir + 1, ic + 1] += err / 16

    # Remove padding and scale back
    arr = padded_arr[:new_height, :new_width]
    carr = np.clip(arr * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(carr)


@njit()
def fs_dither_numba(
    imageArr: npt.NDArray[np.float32], palette: npt.NDArray[np.float32]
) -> npt.NDArray[np.uint8]:
    # image: np.array of shape (height, width), dtype=float, 0.0-1.0
    # works in-place!
    h = imageArr.shape[0]
    w = imageArr.shape[1]
    for y in range(h - 1):
        for x in range(w - 1):
            old = imageArr[y, x].copy()
            new = get_new_val_jit(old, palette)
            imageArr[y, x] = new
            error = old - new

            imageArr[y, x + 1] += error * 0.4375  # right, 7 / 16
            imageArr[y + 1, x + 1] += error * 0.0625  # right, down, 1 / 16
            imageArr[y + 1, x] += error * 0.3125  # down, 5 / 16
            imageArr[y + 1, x - 1] += error * 0.1875  # left, down, 3 / 16

    arr = imageArr[: h - 1, : w - 1]
    return np.clip(arr * 255, 0, 255).astype(np.uint8)


def convert(img_name: str) -> str:
    img = Image.open(img_name).convert("RGB")
    if GREYSCALE:
        img = img.convert("L")
    ImageOps.exif_transpose(img, in_place=True)
    width, height = img.size
    if height > width:
        img = img.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
        width, height = img.size

    new_width = 800
    new_height = int(height * new_width / width)
    imgRes = img.resize((new_width, new_height), Image.Resampling.BICUBIC)

    imgResArray = np.array(imgRes, dtype=float) / 255
    paddedImgResArray = np.pad(
        imgResArray, ((0, 1), (0, 1), (0, 0)), mode="constant"
    )  # Pad to avoid boundary checks
    paletteFloatArray = np.array(paletteFloat, dtype=float)

    dimArr = fs_dither_numba(paddedImgResArray, paletteFloatArray)
    dim = Image.fromarray(dimArr)
    imgWBorderSize = (800, 480)
    imgWBorder = Image.new("RGB", imgWBorderSize, "white")
    box = tuple((n - o) // 2 for n, o in zip(imgWBorderSize, dim.size))
    imgWBorder.paste(dim, box)  # type: ignore
    saveName = "conv_" + os.path.splitext(os.path.basename(img_name))[0] + ".bmp"
    savePath = os.path.join(os.path.dirname(os.path.dirname(img_name)), "pic")
    imgWBorder.save(os.path.join(savePath, saveName), "BMP")
    return saveName


if __name__ == "__main__":
    convert("DSC00364.jpg")
