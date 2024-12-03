from PIL import Image, ImageOps, ImageEnhance
import os


def convertOptimized(img_name: str) -> tuple[str, Image.Image]:
    MAX_HEIGHT = 600
    MAX_WIDTH = 400

    img = Image.open(img_name).convert("RGB")
    ImageOps.exif_transpose(img, in_place=True)
    width, height = img.size
    if width > height:
        img = img.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
        width, height = img.size

    new_width = MAX_WIDTH
    new_height = int(height * new_width / width)
    if new_height > MAX_HEIGHT:
        new_width = int(new_width * MAX_HEIGHT / new_height)
        new_height = MAX_HEIGHT
    imgRes = img.resize((new_width, new_height), Image.Resampling.BICUBIC)

    imgRes = ImageEnhance.Contrast(imgRes).enhance(1.5)
    imgWBorderSize = (MAX_WIDTH, MAX_HEIGHT)
    imgWBorder = Image.new("RGB", imgWBorderSize, "white")

    box = tuple((n - o) // 2 for n, o in zip(imgWBorderSize, imgRes.size))
    imgWBorder.paste(imgRes, box)  # type: ignore
    saveName = "conv_" + os.path.splitext(os.path.basename(img_name))[0] + ".bmp"
    savePath = os.path.dirname(img_name)
    imgWBorder.save(os.path.join(savePath, saveName), "BMP")

    return saveName, imgWBorder


if __name__ == "__main__":
    convertOptimized("DSC00364.jpg")
