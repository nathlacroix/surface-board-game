import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from PIL import ImageFont, ImageDraw, Image
import adafruit_ssd1306
import neopixel
import time
import numpy as np
import random

PI_PIN_NEOPIXELS = board.D18
PI_PIN_AIRBRIDGE = board.D10 #"TODO"
PI_NEOPIXEL_COUNT = 18
FONTPATH = "/home/ants/hat/src/surface_board_game/arial.ttf"
# Tick rate for sleeping between checking the buttons, 60 Hz
FRAME_TIME = 1.0/60.0

# surface code constants
N_DETERMINISTIC_SAMPLES = 3
DISTANCE = 3
N_AUX_QBS = DISTANCE**2 - 1  # Adjust this based on your actual number of auxiliary qubits
NEOPIXEL_COUNT = 17  # Adjust this based on your actual number of NeoPixels
TWPA_CALIBRATED = False
green_gradients = [
    (0, 255, 0),
    (4, 251, 0),
    (8, 247, 0),
    (12, 243, 0),
    (16, 239, 0),
    (20, 235, 0),
    (24, 231, 0),
    (28, 227, 0),
    (32, 223, 0),
    (36, 219, 0),

    (44, 211, 0),
    (48, 207, 0),
    (52, 203, 0),
    (56, 199, 0),
    (60, 195, 0),
    (64, 191, 0),
    (68, 187, 0),
    (72, 183, 0),
    (76, 179, 0),
    (80, 175, 0),
    (84, 171, 0),
    (88, 167, 0),
    (92, 163, 0),
    (96, 159, 0),
    (100, 155, 0),
    (104, 151, 0),
    (108, 147, 0),
    (112, 143, 0),
    (116, 139, 0),
    (120, 135, 0),
    (124, 131, 0),
    (128, 127, 0),
    (132, 123, 0),
    (136, 119, 0),
    (140, 115, 0),
    (144, 111, 0),
    (148, 107, 0),
    (152, 103, 0),
    (156, 99, 0),
    (160, 95, 0),
    (164, 91, 0),
    (168, 87, 0),
    (172, 83, 0),
    (176, 79, 0),
    (180, 75, 0),
    (184, 71, 0),
    (188, 67, 0),
    (192, 63, 0),
    (196, 59, 0),
    (200, 55, 0),
    (204, 51, 0),
    (208, 47, 0),
    (212, 43, 0),
    (216, 39, 0),
    (220, 35, 0),
    (224, 31, 0),
    (228, 27, 0),
    (232, 23, 0),
    (236, 19, 0),
    (240, 15, 0),
    (244, 11, 0),
    (248, 7, 0),
    (255, 3, 0)
]
blue_gradients = [
    (173, 216, 230), (176, 224, 230), (184, 233, 238), (188, 238, 243),
    (193, 240, 244), (197, 245, 249), (200, 249, 255), (202, 252, 255),
    (206, 253, 255), (210, 255, 255), (214, 255, 255), (178, 223, 238),
    (149, 206, 251), (120, 188, 255), (91, 171, 255), (62, 154, 255),
    (33, 136, 255), (4, 119, 255), (0, 104, 235), (0, 89, 204),
    (0, 74, 173), (0, 59, 143), (0, 44, 112), (0, 29, 81),
    (135, 206, 250), (127, 199, 242), (118, 192, 234), (110, 185, 226),
    (101, 178, 218), (93, 171, 210), (85, 164, 202), (76, 157, 194),
    (68, 150, 186), (59, 143, 178), (51, 136, 170), (43, 129, 162),
    (34, 122, 154), (26, 115, 146), (17, 108, 138), (9, 101, 130),
    (0, 94, 122), (0, 87, 114), (0, 80, 106), (0, 73, 98),
    (0, 66, 90), (0, 59, 82), (0, 52, 74), (0, 45, 66),
    (0, 38, 58), (0, 31, 50), (0, 24, 42), (0, 17, 34),
    (0, 10, 26), (0, 3, 18), (0, 0, 10), (0, 0, 20),
    (0, 0, 30), (0, 0, 40), (0, 0, 50), (0, 0, 60),
    (0, 0, 70), (0, 0, 80), (0, 0, 90), (0, 0, 100),
    (0, 0, 110), (0, 0, 120), (0, 0, 130), (0, 0, 140),
    (0, 0, 150), (0, 0, 160), (0, 0, 170), (0, 0, 180)
]
red_gradients = [(255//3, 0//4, 0//4)]*64
COLOR_Z_AUX_QB = green_gradients[10]
COLOR_X_AUX_QB = blue_gradients[20]
COLOR_DATA_QB = (255//3, 0//4, 0//4)
# Other global variables
current_frame = 0

class PhDHat:

    def __init__(self):
        # configure software bypass. Set to False to run in normal mode with the hat
        self.software_bypass = True

        self.state = "pre-initialize"
        self.pixels = neopixel.NeoPixel(
            PI_PIN_NEOPIXELS,
            PI_NEOPIXEL_COUNT,
            brightness=0.2,
            auto_write=False,
            pixel_order=neopixel.GRB
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
        self.draw = None
        self.image = None

        # Font for text display
        self.font =  ImageFont.truetype(FONTPATH, 15)

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


    def _display_text_on_screen(
        self, text: str, new_screen=True, font: ImageFont = None,
            font_size: None = None, position: tuple = None, anchor="mm",
            sleep: int = 0
    ) -> None:
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = self.disp.width
        height = self.disp.height
        if new_screen:
            self.image = Image.new("1", (width, height))

            # Get drawing object to draw on image.
            self.draw = ImageDraw.Draw(self.image)
            # Draw a black filled box to clear the image.
            self.draw.rectangle((0, 0, width, height), outline=1, fill=1)

        if font_size is not None:
            font = ImageFont.truetype(FONTPATH, font_size)
        elif font is None:
            font = self.font
        if position is None:
            position = (self.disp_width / 2, self.disp_height / 2)

        self.draw.text(
            position,
            text,
            font=font,
            anchor=anchor,
        )

        self.disp.image(self.image)
        self.disp.show()

        if sleep:
            time.sleep(sleep)

    def _display_surface_board_cycle(
            self, score: int, n_rounds: int, streak: int,
            cycle: int,
    ) -> None:
        text = f"Score: {score}/{n_rounds}      "\
                f"Streak: {streak}"
        position=(2, 2)
        self._display_text_on_screen(text, new_screen=True,
                                     font_size=10, position=position,
                                     anchor='lt')

        self._display_text_on_screen(f'Cycle: {cycle}', new_screen=False)
        # time.sleep(2)

    def initial_stage(self):
        print('Initial stage ...')
        # Display welcome text
        self._display_text_on_screen(
            "Welcome\nto your PhD hat\nPress #5 to start"
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
            "1. Finish fabricating\nthe airbridges"
        )
        while True:
            # If airbridge connection made (value brought low)
            if not self.airbridge_input.value:
                return
            # bypass If A and B pressed (brought low)
            elif self.check_bypasses():
                return
            else:
                time.sleep(FRAME_TIME)

    def twpa_stage(self):
        # Display message
        self._display_text_on_screen(
            "2. Tune the TWPA!", sleep=3,
        )
        power = 11
        frequency = 7.7
        gain = self.twpa_optimization(power, frequency)
        success = False
        while not success:
            text = f"Pump power (U/D): {power:.1f} dBm   Pump frequency (L/R): {frequency:.2f} GHz"
            self._display_text_on_screen(text, anchor="lt", position=(2, 2), font_size=12)
            gain = self.twpa_optimization(power, frequency)
            success = self.check_bypasses()



    def twpa_optimization(self, power, frequency):
        # Input: Frequency in GHz, power in dBm
        # Output: Gain Factor (between 0 and 10), bool for indicating too much noise
        # Optimal value at 7.91 GHz, 9.5 dBm
        # Too much noise above 9 dBm

        freqgain = 10 / (1 + (7.91 - frequency) ** 2 / 0.01)

        powergain = np.exp(-(power - 9.5) ** 2 / 0.5)

        gain = freqgain * powergain

        try:
            if power > 9:
                toomuchnoise = True
            else:
                toomuchnoise = False
        except:
            toomuchnoise = False
        return gain, toomuchnoise

    def surface_code_stage(self):
        print('Starting surface code game ...')
        self._display_text_on_screen(
            "Starting surface\nboard game..."
        )
        time.sleep(2)

        playing = True
        print('Loading samples...')
        # Assume your samples are loaded in the following format:
        # samples = {0: {'syndromes': [...], 'data_qubits': [...], 'log_op': ...}, 1: {...}, ...}
        samples = self.load_samples("samples.npz")
        current_round = 1
        self.score = 0
        self.streak = 0
        self.n_rounds = 3

        while playing:
            print(f'Game #{current_round}')
            self._display_text_on_screen(f'Game #{current_round}', sleep=2)
            sample = self.choose_sample(samples, current_round)
            self.display_syndrome(sample, current_round)
            # check logical operator
            success = self.check_logical_operator(sample['log_op'])
            current_round += 1
            self.score += success
            if success:
                self.streak += 1
                self.display_success_screen(self.score, self.streak)
            else:
                self.streak = 0
                self.display_failure_screen(self.score)

            if current_round > self.n_rounds:
                playing = False

        print('Game over.')

    def check_logical_operator(self, log_op):
        return True
    @staticmethod
    def load_samples(file_path, display=False):
        data = np.load(file_path, allow_pickle=True)
        samples = {int(seed): data[seed].item() for seed in data.files}
        if display:
            for seed, data in samples.items():
                print(f"Seed {seed}:")
                print("Syndromes:", data['syndromes'])
                print("Data qubits:", data['data_qubits'])
                print("Log op:", data['log_op'])
                print("\n")
        return samples

    @staticmethod
    def choose_sample(samples, current_round):
        global current_frame

        if current_frame < N_DETERMINISTIC_SAMPLES:
            # Return the n-th sample for the first N_DETERMINISTIC_SAMPLES rounds
            sample_index = current_frame
        else:
            # Return a random sample after the first N_DETERMINISTIC_SAMPLES rounds
            sample_index = random.randint(0, len(samples) - 1)

        current_frame += 1
        return samples[sample_index]

    def display_syndrome(self, sample, current_round, colors=None, bypass_buttons=False):
        if colors is None:
            colors = [COLOR_Z_AUX_QB] * 4 + [COLOR_X_AUX_QB] * 4

        cycle = 0
        exit = False
        while cycle < len(sample['syndromes']) / N_AUX_QBS  and not exit:
            syndrome_slice = sample['syndromes'][cycle*N_AUX_QBS: (cycle + 1) * N_AUX_QBS]
            print("Cycle:", cycle +1, syndrome_slice) # for display, cycles are 1-indexed
            self._display_surface_board_cycle(score=self.score, n_rounds=self.n_rounds,
                                              streak=self.streak, cycle=cycle+1) # for display, cycles are 1-indexed
            self.light_neopixels(syndrome_slice, colors)
            self.pixels.show()
            if bypass_buttons:
                cycle += 1
                time.sleep(2)
            else:
                frame_update = None
                while frame_update is None:
                    frame_update = self.check_buttons()
                    if frame_update == 'next':
                        cycle += 1
                    if frame_update == 'prev':
                        if cycle > 0:
                            cycle -= 1
                    if frame_update == 'exit':
                        exit = True
                time.sleep(0.5)

        #
        # return False  # Unsuccessful display
    def check_buttons(self):
        if not self.button_r.value:
            return 'next'
        elif not self.button_l.value:
            return 'prev'
        elif self.check_bypasses():
            return 'exit'

    def check_bypasses(self, button_bypass=True, software_bypass=True):
        if button_bypass not self.button_a.value and not self.button_b.value:
            return True
        elif software_bypass and self.software_bypass:
            print('software bypass will be activated in 2 sec!')
            time.sleep(2)
            return True
        else:
            return False

    def light_neopixels(self, syndrome_slice, colors):
        # Adjust this function based on your actual NeoPixel setup
        for i in range(min(len(syndrome_slice), NEOPIXEL_COUNT)):
            if syndrome_slice[i]:
                self.pixels[i] = colors[i]  # Turn on NeoPixel
            else:
                self.pixels[i] = (0, 0, 0)  # Turn off NeoPixel

    def display_logical_operator_prompt(self):
        print(
            "Do you want to flip the logical operator? (Press 'left' to decline, 'right' to accept)")



    def display_success_screen(self, score, streak):
        text = f"Success!\n New Score: {score}, Streak: {streak}"
        print(text)
        self._display_text_on_screen(text, font_size=12)
        time.sleep(2)

    def display_failure_screen(self, score):
        text = f"Incorrect :-(\nScore: {score}"
        print(text)
        self._display_text_on_screen(text, font_size=12)
        time.sleep(2)

