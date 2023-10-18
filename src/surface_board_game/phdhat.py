import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from PIL import ImageFont, ImageDraw
import adafruit_ssd1306

PI_PIN_NEOPIXELS = board.D18
PI_PIN_AIRBRIDGE = "TODO"
PI_NEOPIXEL_COUNT = 18
# Tick rate for sleeping between checking the buttons, 60 Hz
FRAME_TIME = 1.0/60.0

class PhDHat:

    def __init__():
        self.state = "pre-initialize"
        self.pixels = neopixel.NeoPixel(
            PI_PIN_NEOPIXELS,
            PI_NEOPIXEL_COUNT,
            brightness=0.2,
            auto_write=False,
            pixel_order=neopixel.RGB
        )
        # Create the I2C interface.
        self.i2c = busio.I2C(board.SCL, board.SDA)
        # Create the SSD1306 OLED class.
        self.disp_width = 128
        self.disp_height = 64
        self.disp = adafruit_ssd1306.SSD1306_I2C(
            self.disp_width,
            self.disp_height,
            self.i2c,
        )

        # Font for text display
        self.font = ImageFont.truetype("arial.ttf", 15)

        # Create the buttons
        # Default state is high (True)
        self.button_a = DigitalInOut(board.D5)
        self.button_b = DigitalInOut(board.D6)
        self.button_l = DigitalInOut(board.D27)
        self.button_r = DigitalInOut(board.D23)
        self.button_u = DigitalInOut(board.D17)
        self.button_d = DigitalInOut(board.D22)
        # Joystick center button
        self.button_c = DigitalInOut(board.D4)
        self.airbridge_input = DigitalInOut(PI_PIN_AIRBRIDGE)

        inputs = [
            self.button_a,
            self.button_b,
            self.button_l,
            self.button_r,
            self.button_u,
            self.button_d,
            self.button_c,
            self.airbridge_input,
        ]
        for inp in inputs:
            inp.direction = Direction.INPUT
            inp.pull = Pull.UP
            # Ground the pin to bring the value low (False)

        # Clear the display
        self.disp.fill(0)
        self.disp.show()

        # Clear the neopixels
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

        self.twpa_pump_power = 2.0
        self.twpa_pump_frequency = 7.0

    def _display_text_on_screen(
        self, text: str
    ) -> None:
        image = ImageDraw.text(
            (self.disp_width/2, self.disp_height/2),
            text,
            font=self.font,
            anchor="mm",
        ).convert("1")
        self.disp.image(image)
        self.disp.show()

    def initial_stage(self):
        # Display welcome text
        self._display_text_on_screen(
            "Welcome to your PhD hat\nPress A to start"
        )
        while True:
            # If A button pressed (value brought low)
            if not self.button_a.value:
                return
            else:
                time.sleep(FRAME_TIME)

    def airbridge_stage(self):
        # Display message
         self._display_text_on_screen(
            "Finish fabricating the airbridges"
        )
        while True:
            # If airbridge connection made (value brought low)
            if not self.airbridge_input.value:
                return
            # If A and B pressed (brought low)
            elif not self.button_a.value and not self.button_b_value:
                return
            else:
                time.sleep(FRAME_TIME)

    def twpa_stage(self):
        pass
    
    def surface_code_stage(self):
        pass
