from pathlib import Path
import random
import time

import adafruit_ssd1306
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import numpy as np
from PIL import ImageFont, ImageDraw, Image


PI_PIN_NEOPIXELS = board.D18
PI_PIN_AIRBRIDGE = board.D25
PI_NEOPIXEL_COUNT = 21
FONTPATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
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
# COLOR_Z_AUX_QB = green_gradients[10]
# COLOR_X_AUX_QB = blue_gradients[20]
# COLOR_DATA_QB = red_gradients[0]
COLOR_Z_AUX_QB = (0, 128, 0)
COLOR_X_AUX_QB = (0, 0, 128)
COLOR_DATA_QB = (128, 0, 0)
# Other global variables
current_frame = 0

class PhDHat:

    def __init__(self):
        # configure software bypass. Set to False to run in normal mode with the hat
        self.software_bypass = False

        self.state = "pre-initialize"
        self.pixels = neopixel.NeoPixel(
            PI_PIN_NEOPIXELS,
            PI_NEOPIXEL_COUNT,
            brightness=0.2,
            # auto_write=False,
            pixel_order=neopixel.GRB,
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
        # self.pixels.show()

        self.led_indices = {
            "d1":  1,
            "d2":  5,
            "d3":  7,
            "d4":  3,
            "d5":  9,
            "d6": 15,
            "d7": 11,
            "d8": 13,
            "d9": 17,
            "x1":  6,
            "x2":  4,
            "x3": 14,
            "x4": 12,
            "z1": 2,
            "z2": 10,
            "z3":  8,
            "z4": 16,
            "twpa1": 18,
            "twpa2": 19,
            "twpa3": 20,
        }


    def _display_text_on_screen(
        self, text: str, new_screen=True, font: ImageFont = None,
            font_size: None = None, position: tuple = None, anchor="mm",
            sleep: int = 0
    ) -> None:
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = self.disp.width
        height = self.disp.height
        print(text)
        if new_screen:
            # Fill with black by default
            self.image = Image.new("1", (width, height), color=0)

            # Get drawing object to draw on image.
            self.draw = ImageDraw.Draw(self.image)
            # Draw a black filled box to clear the image.
            # self.draw.rectangle((0, 0, width, height), outline=1, fill=1)

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
            fill=1,  # white text
        )

        self.disp.image(self.image)
        self.disp.show()

        if sleep:
            time.sleep(sleep)

    def _display_surface_board_cycle(
            self, score: int, n_rounds: int, streak: int,
            cycle: int,
    ) -> None:
        text = f"Score: {score}/{n_rounds}\nStreak: {streak}"
        position=(40, 18)
        self._display_text_on_screen(
            text, new_screen=True,
            font_size=11, position=position,
        )

        self._display_text_on_screen(
            f'Cycle: {cycle}', new_screen=False,
            position=(64, 40)
        )
        self._display_text_on_screen(
            'L/R to scroll',
            new_screen=False,
            anchor=("lb"),
            font_size=11,
            position=(2, 64-2)
        )
        # time.sleep(2)

    def _led_test(self):
        self.pixels.fill((255, 0, 0))
        # self.pixels.show()
        time.sleep(2)
        self.pixels.fill((0, 255, 0))
        # self.pixels.show()
        time.sleep(2)
        self.pixels.fill((0, 0, 255))
        # self.pixels.show()
        time.sleep(2)
        for led_key in self.led_indices:
            self.pixels.fill((0, 0, 0))
            if led_key[0] == 'd':
                # red
                color = (255, 0, 0)
            elif led_key[0] == 'x':
                # blue
                color = (0, 0, 255)
            elif led_key[0] == 'z':
                # green
                color = (0, 255, 0)
            else:
                color = (128, 128, 128)
            # for pix_idx in range(len(self.pixels)):
            #     self.pixels[pix_idx] = (0, 0, 0)
            print(f"LED {led_key}, index {self.led_indices[led_key]}")
            self.pixels[self.led_indices[led_key]] = color
            # self.pixels.show()
            # mask = PI_NEOPIXEL_COUNT * [False]
            # colors = PI_NEOPIXEL_COUNT * [(0, 0, 0)]
            # mask[self.led_indices[led_key]] = True
            # colors[self.led_indices[led_key]] = color
            # self.light_neopixels(mask, colors)
            time.sleep(3)

    def initial_stage(self):
        print('Initial stage ...')
        # Display welcome text
        self._display_text_on_screen(
            "Welcome\nto your PhD hat\nPress #5 to start",
            sleep=1,
        )
        self.pixels.fill((0, 0, 0))
        # self._led_test()
        while True:
            # If A button pressed (value brought low)
            if not self.button_a.value:
                return
            elif self.check_bypasses():
                return
            else:
                time.sleep(FRAME_TIME)

    def airbridge_stage(self):
        # Display message
        self._display_text_on_screen(
            "1. Finish\nfabricating\nthe airbridges",
            sleep=3
        )
        self.pixels.fill((0, 0, 0))
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
        # Light all LEDs yellow to match the figure
        for led_key in self.led_indices:
            self.pixels[self.led_indices[led_key]] = (128, 128, 0)
        # Display message
        self._display_text_on_screen(
            "2. Tune\nthe TWPA", sleep=3,
        )
        # Optional: light up LEDs of data qubits in a dim way on readout line
        # with the twpa.

        # twpa optimization
        # params = dict(power=8.5, freq=7.90)  # easy ones
        params = dict(power=8.0, freq=8.03)  # hard ones
        target_gain = 20
        fact = 40/12.13
        success = False
        while not success:
            text = (f"Pump parameters\n"
                    f"Power (U/D): {params['power']:.1f} dBm\n"
                    f"Freq.   (L/R): {params['freq']:.2f} GHz")
            gain, toomuchnoise = self.twpa_optimization(
                params['power'], params['freq'])
            self.pixels.fill((0, 0, 0))
            if not toomuchnoise:
                color = (int(15*gain), int(15*gain), 0)
                self.pixels.fill(color)
            else:
                for i in range(len(self.pixels)):
                    color = [random.randrange(255) for i in range(3)]
                    self.pixels[i] = color
            self._display_text_on_screen(
                text, position=(64, 20), font_size=11)
            # multiplicative factor such that 20 dB at "optimal" twpa parameters i.e. 9 dbm and 7.91 GHz
            text = f"Gain: {gain * fact:.2f} dB"
            self._display_text_on_screen(
                text,
                position=(64, 50),
                new_screen=False,
            )
            mapping = [
                 (self.button_l, ('freq', -0.01), ),
                 (self.button_r, ('freq', 0.01), ),
                 (self.button_d, ('power', -0.1), ),
                 (self.button_u, ('power', 0.1),)
             ]
            action = self.check_buttons(
                button_action_mapping=mapping, bypass_value=('power', 0.1))
            if isinstance(action, tuple):
                params[action[0]] += action[1]
            if not toomuchnoise and np.abs(gain * fact - target_gain) < 0.5:
                success = True

            if toomuchnoise:
                pass # optionally  implement crazy mode
                #self._display_text_on_screen("Too much noise!", new_screen=False)


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

    def play_again(self):
        print('Play again?')
        # Display welcome text
        self._display_text_on_screen(
            "Play again?\nPress #5 to start",
            sleep=1,
        )
        self.pixels.fill((0, 0, 0))
        # self._led_test()
        while True:
            # If A button pressed (value brought low)
            if not self.button_a.value:
                N_DETERMINISTIC_SAMPLES = 0
                return True
            elif self.check_bypasses():
                N_DETERMINISTIC_SAMPLES = 0
                return True
            else:
                time.sleep(FRAME_TIME)

    def surface_code_stage(self):
        self._display_text_on_screen(
            "3. Win\nthe surface\nboard game"
        )
        playing = True
        
        # Assume your samples are loaded in the following format:
        # samples = {0: {'syndromes': [...], 'data_qubits': [...], 'log_op': ...}, 1: {...}, ...}
        sample_path = Path(__file__).parent.joinpath("samples.npz")
        print(f'Loading samples from {sample_path}')
        samples = self.load_samples(sample_path)
        current_round = 1
        self.score = 0 # amount of successes
        self.streak = 0 # amount of consecutive successes
        self.n_rounds = 3 # number of games of decoding to program

        # light up data qubits
        self.pixels.fill((0, 0, 0))
        colors = [COLOR_DATA_QB] * 9 + [COLOR_Z_AUX_QB] * 4 + [COLOR_X_AUX_QB] * 4 
        keys = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "z1", "z2", "z3", "z4", "x1", "x2", "x3", "x4"]
        self.light_neopixels(
            [True] * (DISTANCE**2 * 2 - 1), colors=colors,
            keys=keys,
        )
        time.sleep(2)
        # self.light_neopixels([True] * DISTANCE**2, colors=[COLOR_DATA_QB] * DISTANCE**2,
        #                      keys=[f"d{i}" for i in range(1,  DISTANCE**2 +1) ]) # currently assumes data qubits are after aux.
        while playing:
            self._display_text_on_screen(f'Game #{current_round}', sleep=2)
            self.light_neopixels([True] * DISTANCE**2, colors=[COLOR_DATA_QB] * DISTANCE**2,
                                 keys=[f"d{i}" for i in range(1,  DISTANCE**2 +1) ])
            sample = self.choose_sample(samples)
            success = self.display_syndrome(sample)

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

        if self.score/self.n_rounds > 0.5:
            text = (f"Congratulations!\nDecoding\nSuccess Prob. {self.score/self.n_rounds*100:.1f}%")
            self._display_text_on_screen(text, font_size=11, sleep=3)
            text = (f"This is enough to\n"
                    f"correctly project onto\n"
                    f"the Massachusetts State\n"
                    f"without errors.")
            self._display_text_on_screen(text, font_size=10, sleep=10)
        else:
            text = (f"Decoding\nSuccess Prob. {self.score / self.n_rounds*100:.1f}%")
            self._display_text_on_screen(text, font_size=10, sleep=2)
            text = (f"Make sure to train\n"
                    f"again before projecting\n"
                    f"onto the Massachusetts\nState.")
            self._display_text_on_screen(text, font_size=10, sleep=10)
        print('Game over.')

    def check_logical_operator(self, sample, flip):
        print(sample)
        log_op = sample['log_op']
        initial_state = sample['log_op_init']
        print(f'Checking logical operator: initial state {initial_state}, log op {log_op}, flip {flip}')
        if flip:
            log_op = not log_op
        if log_op == initial_state:
            return True
        else:
            return False

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
    def choose_sample(samples):
        global current_frame

        if current_frame < N_DETERMINISTIC_SAMPLES:
            # Return the n-th sample for the first N_DETERMINISTIC_SAMPLES rounds
            sample_index = current_frame
        else:
            # Return a random sample after the first N_DETERMINISTIC_SAMPLES rounds
            sample_index = random.randint(0, len(samples) - 1)

        current_frame += 1
        return samples[sample_index]

    def display_syndrome(self, sample, colors=None, bypass_buttons=False):
        if colors is None:
            colors = [COLOR_Z_AUX_QB] * 4 + [COLOR_X_AUX_QB] * 4 #+ [COLOR_DATA_QB] * 9

        cycle = 0
        exit = False
        while cycle < len(sample['syndromes']) / N_AUX_QBS + 1  and not exit:
            if cycle == len(sample['syndromes']) / N_AUX_QBS:
                # this is the last frame, but it needs to still be in the while
                # loop just in case the decision is taken to go back to the previous cycle
                self.display_logical_operator_prompt()

                action = self.check_buttons(button_action_mapping=[(self.button_l, 'prev'),
                                                                   (self.button_u, 'yes'),
                                                                   (self.button_d, 'no')],
                                            bypass_value="yes")
                if action == "prev": # go back to previous cycle
                    cycle -= 1
                elif action == "yes": # check logical operator and return success/failure
                    return self.check_logical_operator(sample, flip=True)
                elif action == "no":
                    return self.check_logical_operator(sample, flip=False)

            else:
                syndrome_slice = sample['syndromes'][cycle*N_AUX_QBS: (cycle + 1) * N_AUX_QBS]
                print("Cycle:", cycle +1, syndrome_slice) # for display, cycles are 1-indexed
                self._display_surface_board_cycle(score=self.score, n_rounds=self.n_rounds,
                                                  streak=self.streak, cycle=cycle+1) # for display, cycles are 1-indexed
                # self.light_neopixels(9*[True], colors[8:], keys=["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9"])
                self.light_neopixels(syndrome_slice, colors, keys=["z1", "z2", "z3", "z4",
                                                                   "x1", "x2", "x3", "x4"])

                if bypass_buttons:
                    cycle += 1
                    time.sleep(2)
                else:
                    frame_update = None
                    while frame_update is None:
                        frame_update = self.check_buttons(bypass_value="next")
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
    def check_buttons(self, button_action_mapping=None, bypass_value="exit"):
        if button_action_mapping is None:
            button_action_mapping = [(self.button_r, 'next'), (self.button_l, 'prev')]
        for b, action in button_action_mapping:
            if not b.value:
                return action
        if self.check_bypasses():
            return bypass_value

    def check_bypasses(self, button_bypass=True, software_bypass=False):
        if button_bypass and not self.button_a.value and not self.button_b.value:
            return True
        elif software_bypass and self.software_bypass:
            print('software bypass will be activated in 2 sec!')
            time.sleep(2)
            return True
        else:
            return False

    def light_neopixels(self, mask, colors, indices=None, keys=None):
        """
        :param mask: list of booleans, if True, turn on pixel, if False, turn off
        :param colors: colors for each pixel. must be same length as mask
        :param indices: optional list of indices in the self.pixels list addressed by mask.
        must be same length as mask and colors
        :return:
        """
        # self.pixels.fill((0, 0, 0))
        if keys is not None:
            for k, m, c in zip(keys, mask, colors):
                if m:
                    self.pixels[self.led_indices[k]] = c  # Turn on NeoPixel
                else:
                    self.pixels[self.led_indices[k]] = (0, 0, 0)  # Turn off NeoPixel
        else:
            if indices is None:
                indices = np.arange(len(mask))
            for i, m, c in zip(indices, mask, colors):
                if m:
                    self.pixels[i] = c  # Turn on NeoPixel
                else:
                    self.pixels[i] = (0, 0, 0)  # Turn off NeoPixel

    def display_logical_operator_prompt(self, op="Z"):
        txt = f"Flip {op}_L?\n(Up/Down: Yes/No)"
        self._display_text_on_screen(txt, font_size=12)

    def display_success_screen(self, score, streak):
        text = f"Success!\nNew Score: {score}\nStreak: {streak}"
        self._display_text_on_screen(text, font_size=12)
        self.light_neopixels([False] + 17*[True], [(0, 0, 0)] + 17*[(0, 255, 0)])  # green
        time.sleep(2)

    def display_failure_screen(self, score):
        text = f"Incorrect :-(\nScore: {score}"
        self._display_text_on_screen(text, font_size=12)
        self.light_neopixels([False] + 17*[True], [(0, 0, 0)] + 17*[(255, 0, 0)])  # red
        time.sleep(2)

