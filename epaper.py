#!/usr/bin/python
import sys
import os
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from waveshare_epd import epd7in3f, epd4in0e


class Panel:
    def __init__(self) -> None:
        self.done = False
        self.PANEL_TYPE = os.environ.get("PANEL_TYPE", "epd7in3f")
        print(f"Panel type: {self.PANEL_TYPE}")
        match self.PANEL_TYPE:
            case "epd7in3f":
                self.epd = epd7in3f.EPD()
                pass
            case "epd4in0e":
                self.epd = epd4in0e.EPD()
                pass

    def is_done(self) -> bool:
        return self.done

    def rotate_enhance(self, img_name: str) -> tuple[str, Image.Image]:
        self.done = False
        img = Image.open(img_name).convert("RGB")
        ImageOps.exif_transpose(img, in_place=True)
        width, height = img.size
        print(f"Width: {width} - Height {height} - Need to rotate: {self.epd.LANDSCAPE}")
        if height > width and self.epd.LANDSCAPE:
            img = img.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
            width, height = img.size
        elif height < width and not self.epd.LANDSCAPE:
            img = img.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
            width, height = img.size

        new_width = self.epd.WIDTH
        new_height = int(height * new_width / width)
        if new_height > self.epd.HEIGHT:
            new_width = int(new_width * self.epd.HEIGHT / new_height)
            new_height = self.epd.HEIGHT
        imgRes = img.resize((new_width, new_height), Image.Resampling.BICUBIC)
        imgRes = imgRes.convert("CMYK")
        imgArr = np.array(imgRes, np.uint8)
        imgArr[::, ::, 2] = imgArr[::, ::, 2] * 0.99
        imgRes = Image.fromarray(imgArr, mode="CMYK").convert("RGB")
        imgRes = ImageEnhance.Contrast(imgRes).enhance(1.3)
        # imgRes = ImageEnhance.Brightness(imgRes).enhance(1.3)
        imgWBorderSize = (self.epd.WIDTH, self.epd.HEIGHT)
        imgWBorder = Image.new("RGB", imgWBorderSize, "white")

        box = tuple((n - o) // 2 for n, o in zip(imgWBorderSize, imgRes.size))
        imgWBorder.paste(imgRes, box)  # type: ignore
        saveName = "conv_" + os.path.splitext(os.path.basename(img_name))[0] + ".bmp"
        savePath = os.path.dirname(img_name)
        imgWBorder.save(os.path.join(savePath, saveName), "BMP")

        return saveName, imgWBorder

    def set_pic(self, imgFile: Image.Image) -> None:
        libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
        if os.path.exists(libdir):
            sys.path.append(libdir)

        import logging

        import time

        logging.basicConfig(level=logging.INFO)
        try:
            logging.info(f"{self.PANEL_TYPE}: apply image")
            logging.info("init and Clear")
            self.epd.init()
            self.epd.clear()
            logging.info("init done")
            # read bmp file
            logging.info(f"Read picture")
            # Himage = Image.open(imgFile)
            self.epd.display(self.epd.getbuffer(imgFile))
            time.sleep(3)

            logging.info("Success. Sleeping...")
            self.epd.sleep()
            self.done = True

        except IOError as e:
            logging.info(e)
            raise

        except KeyboardInterrupt:
            logging.info("ctrl + c:")
            self.epd.exit_clean(cleanup=True)
