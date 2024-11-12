#!/usr/bin/python
import sys
import os
from PIL import Image


# picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pic")
def setPic(imgFile: Image.Image) -> None:
    libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
    if os.path.exists(libdir):
        sys.path.append(libdir)

    import logging
    from waveshare_epd import epd7in3f
    import time

    logging.basicConfig(level=logging.INFO)
    try:
        logging.info("epd7in3f Demo")

        epd = epd7in3f.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        # read bmp file
        logging.info(f"Read picture")
        # Himage = Image.open(imgFile)
        epd.display(epd.getbuffer(imgFile))
        time.sleep(3)

        logging.info("Success. Sleeping...")
        epd.sleep()

    except IOError as e:
        logging.info(e)
        raise

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in3f.epdconfig.module_exit(cleanup=True)  # type: ignore
        exit()


if __name__ == "__main__":
    img = Image.open("DSC00364.bmp").convert("RGB")
    setPic(img)
