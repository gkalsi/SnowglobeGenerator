import random
from enum import Enum
from os import listdir
from os.path import isfile, join, splitext, basename
import re

from PIL import Image, ImageDraw


class Wind(Enum):
  NONE = 0
  LITTLE = 1
  SOME = 2
  LOTS = 3


class SnowflakeShape(Enum):
  CIRCLE = 0
  SQUARE = 1


SNOWFLAKE_DENSITY = 7  # 1 to 48
FRAME_COUNT = 60
FRAME_DELAY = 100  # Milliseconds
WIND = Wind.NONE
SHAPE = SnowflakeShape.SQUARE
INPUT_DIR = "./sources/"
OUTPUT_DIR = "./gifs/"

BGCOLOR_LUT = {
  "jonsit": (89, 86, 82),
  "gkalsi": (118, 66, 138),
  "edward": (217, 87, 99),
  "ngai": (217, 160, 102),
  "syd": (203, 219, 252),
  "roy": (75, 105, 47),
  "scott": (48, 96, 130),
  "phil": (143, 86, 59),
  "andrea": (203, 219, 252),
}


class Snowflake:

  def __init__(self, x, y, dx, dy, canvas_width, canvas_height, pixel_width,
               pixel_height):
    self.x = x
    self.y = y
    self.dx = dx
    self.dy = dy
    self.canvas_width = canvas_width
    self.canvas_height = canvas_height
    self.pixel_width = pixel_width
    self.pixel_height = pixel_height

  def Advance(self):
    self.x = (self.x + self.dx) % self.canvas_width
    self.y = (self.y + self.dy) % self.canvas_height

  def Draw(self, img):
    img_draw = ImageDraw.Draw(img)
    # size_jitter = random.randint(0, 5)
    size_jitter = 0
    x, y = self.x * self.pixel_width, self.y * self.pixel_height
    shape = ((x, y), (x + self.pixel_width + size_jitter,
                      y + self.pixel_height + size_jitter))

    if SHAPE == SnowflakeShape.CIRCLE:
      img_draw.ellipse(shape, "#FFFFFF")
    elif SHAPE == SnowflakeShape.SQUARE:
      img_draw.rectangle(shape, "#FFFFFF")


class SnowflakeFactory:

  def __init__(self, canvas_width, canvas_height, velocity, pixel_width,
               pixel_height):
    self.canvas_width = canvas_width
    self.canvas_height = canvas_height

    self.pixel_width = pixel_width
    self.pixel_height = pixel_height

    self.mindx = velocity[0]
    self.maxdx = velocity[1]
    self.mindy = velocity[2]
    self.maxdy = velocity[3]

  def GetRandomSnowflake(self):
    result = Snowflake(random.randint(0, self.canvas_width),
                       random.randint(0, self.canvas_height),
                       random.randint(self.mindx, self.maxdx),
                       random.randint(self.mindy,
                                      self.maxdy), self.canvas_width,
                       self.canvas_height, self.pixel_width, self.pixel_height)

    return result

  def GetDistributedSnowflakes(self, x_segments, y_segments):
    segment_width = self.canvas_width // x_segments
    segment_height = self.canvas_height // y_segments

    result = []
    for x in range(x_segments):
      for y in range(y_segments):
        x_jitter = random.randint(0, segment_width)
        y_jitter = random.randint(0, segment_height)

        flake = Snowflake(x * segment_width + x_jitter,
                          y * segment_height + y_jitter,
                          random.randint(self.mindx, self.maxdx),
                          random.randint(self.mindy, self.maxdy),
                          self.canvas_width, self.canvas_height,
                          self.pixel_width, self.pixel_height)
        result.append(flake)

    return result


def infer_bgcolor(path):
  r = re.compile(r"([\d]+)-([a-zA-Z]+)-(.*)")
  groups = r.findall(path)
  group = groups[0]
  name = group[1]
  return BGCOLOR_LUT[name]


def AddSnowToImage(path):
  avatar = Image.open(path)
  width, height = avatar.size
  pixel_width = width // 48
  pixel_height = height // 48

  snowflake_lut = {
    Wind.NONE: (-1, 1, 1, 1),
    Wind.LITTLE: (0, 1, 1, 1),
    Wind.SOME: (1, 2, 1, 1),
    Wind.LOTS: (1, 3, 1, 1),
  }

  fct = SnowflakeFactory(48, 48, snowflake_lut[WIND], pixel_width,
                         pixel_height)
  # snowflakes = []
  # for i in range(SNOWFLAKE_COUNT):
  #   snowflakes.append(fct.GetRandomSnowflake())
  snowflakes = fct.GetDistributedSnowflakes(SNOWFLAKE_DENSITY,
                                            SNOWFLAKE_DENSITY)

  bg_color = infer_bgcolor(path)

  frames = []
  for i in range(FRAME_COUNT):
    background = Image.new(mode="RGBA", size=avatar.size)

    # Draw a solid colored background
    background.paste(bg_color, [0, 0, width, height])

    # Draw the avatar.
    background.paste(avatar, (0, 0), avatar)

    # Draw more snow in the foreground.
    for snowflake in snowflakes:
      snowflake.Draw(background)

    frames.append(background)

    # Animate the snow.
    for snowflake in snowflakes:
      snowflake.Advance()

  base = basename(path)
  root, _ = splitext(base)
  filename = "{}.gif".format(root)
  frames[0].save(join(OUTPUT_DIR, filename),
                 format='GIF',
                 append_images=frames[1:],
                 save_all=True,
                 duration=FRAME_DELAY,
                 loop=1,
                 disposal=2)


if __name__ == "__main__":
  files = [f for f in listdir(INPUT_DIR) if isfile(join(INPUT_DIR, f))]
  files = [f for f in files if f.endswith(".png")]
  for f in files:
    print("Processing {}...".format(f), end="")
    AddSnowToImage(join(INPUT_DIR, f))
    print("Done!")
