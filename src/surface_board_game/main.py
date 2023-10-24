import phdhat

# Set up system
hat = phdhat.PhDHat()

hat.initial_stage()
hat.airbridge_stage()
hat.twpa_stage()
hat.surface_code_stage()
keep_playing = hat.play_again()
while keep_playing:
    hat.surface_code_stage()
