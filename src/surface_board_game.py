import numpy as np
import time
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


# initialize pixels
# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 17

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

def display_sample(sample, current_round):


    print(f"Displaying sample {current_round}")
    # while True:
    #     pixels[0] = (255, 0, 0)
    #     pixels[1] = (0, 255, 0)
    #     pixels[2] = (0, 0, 255)
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
    for i in range(0, len(sample['syndromes']), N_AUX_QBS):
        syndrome_slice = sample['syndromes'][i:i + N_AUX_QBS]
        light_neopixels(syndrome_slice)
        pixels.show()
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

def light_neopixels(syndrome_slice):
    # Adjust this function based on your actual NeoPixel setup
    for i in range(min(len(syndrome_slice), NEOPIXEL_COUNT)):
        if syndrome_slice[i]:
            pixels[i] = (255, 255, 255)  # Turn on NeoPixel (white)
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
n_rounds = 1


while playing:
    print(f'Round {current_round}')
    sample = choose_sample(samples, current_round)
    success = display_sample(sample, current_round)
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




