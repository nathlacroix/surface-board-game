import numpy as np
import time

import buttons
import twpa
import pygame
import board
import neopixel
import time
import random

# Constants
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
    (40, 215, 0),
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


# initialize pixels
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 64

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

# Other global variables
current_frame = 0

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

def display_syndrome(sample, current_round, colors=None, bypass_buttons=False):
    if colors is None:
        colors = [COLOR_Z_AUX_QB]*4 + [COLOR_X_AUX_QB]*4

    print(f"Displaying sample {current_round}")
    # while True:
    #     for i in range(num_pixels):
    #         pixels[i] = red_gradients[i]
    #     pixels.show()
    #     time.sleep(2)
    # global current_frame
    #
    # pygame.init()
    #
    # # Initialize OLED display and joystick
    # pygame.display.init()
    # pygame.joystick.init()
    # joystick = pygame.joystick.Joystick(0)
    # joystick.init()
    #
    # # Display syndromes on NeoPixels
    frame = 0
    for i in range(0, len(sample['syndromes']), N_AUX_QBS):
        syndrome_slice = sample['syndromes'][i:i + N_AUX_QBS]
        light_neopixels(syndrome_slice, colors)
        pixels.show()
        # if bypass_buttons:
        #     frame_update = 'next'
        # else:
        #     frame_update = None
        #     while frame_update is None:
        #         frame_update = buttons.check_buttons()
        #         if frame_update == 'next':
        #             frame +=1
        #         if frame_update == 'prev':
        #             frame -=1
        #         if frame_update == 'exit':
        #             pass
    #
    #     pygame.event.pump()
        time.sleep(2)  # Adjust the delay based on your preference
    #
    #     # Check for joystick input
    #     for event in pygame.event.get():
    #         if event.type == pygame.JOYBUTTONDOWN and event.button == 7:  # "right" button
    #             if i + N_AUX_QBS >= len(sample['syndromes']):
    #                 display_logical_operator_prompt()
    #                 return True  # Successful display
    #         elif event.type == pygame.JOYBUTTONDOWN and event.button == 6:  # "left" button
    #             if i - N_AUX_QBS >= 0:
    #                 i -= 2 * N_AUX_QBS  # Go back two frames
    #
    # return False  # Unsuccessful display

def light_neopixels(syndrome_slice, colors):
    # Adjust this function based on your actual NeoPixel setup
    for i in range(min(len(syndrome_slice), NEOPIXEL_COUNT)):
        if syndrome_slice[i]:
            pixels[i] = colors[i]  # Turn on NeoPixel
        else:
            pixels[i] = (0, 0, 0)  # Turn off NeoPixel

def display_logical_operator_prompt():
    print("Do you want to flip the logical operator? (Press 'left' to decline, 'right' to accept)")

    pygame.event.pump()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 7:  # "right" button
                return True  # User wants to flip the logical operator
            elif event.type == pygame.JOYBUTTONDOWN and event.button == 6:  # "left" button
                return False  # User declines to flip the logical operator

def display_success_screen(score, streak):
    print(f"Success! Score: {score}, Streak: {streak}")

def display_failure_screen(score):
    print(f"Failure! Score: {score}")

# if __name__ == '__main__':


    # check airbridge process completed (no code needed?)

    # tune twpa
while not (TWPA_CALIBRATED or twpa.check_twpa_bypass()):
    # add twpa code here
    print("Tuning up TWPA...")
    time.sleep(2)
    pass

# start surface code game
# Start the game
print('Starting surface code game...')
playing = True
print('Loading samples...')
# Assume your samples are loaded in the following format:
# samples = {0: {'syndromes': [...], 'data_qubits': [...], 'log_op': ...}, 1: {...}, ...}
samples = load_samples("samples.npz")
current_round = 1
score = 0
streak = 0
n_rounds = 15


while playing:
    print(f'Round {current_round}')
    sample = choose_sample(samples, current_round)
    success = display_syndrome(sample, current_round)
    current_round += 1
    # score += success
    # if success:
    #     streak += 1
    #     display_success_screen(score, streak)
    # else:
    #     streak = 0
    #     display_failure_screen(score)

    if current_round > n_rounds:
        playing = False

print('Game over.')




