from surface_board_game.phdhat import PhDHat

if __name__ == "__main__":

    # Set up system
    hat = phdhat.PhDHat()

    hat.initial_stage()
    hat.airbridge_stage()
    hat.twpa_stage()
    hat.surface_code_stage()
