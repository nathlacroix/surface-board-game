# Surface-board-game

## Installation

Install prerequisites

```
sudo apt-get install -y i2c-tools libgpiod-dev python3-smbus python3-pil
```

Enable [I2C](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c) and SPI

Enable linger for the `hat` user:

```
sudo systemctl enable-linger hat
```

Create a virtual environment

```
python3 -m venv ~/phdhatenv
```

Clone this repository to `/home/hat`

## Running

For testing

```
sudo /home/hat/phdhatenv/bin/python /home/hat/surface-code-game/src/main.py
```

As a systemd service

```
sudo cp phd-hat.service /etc/systemd/system/phd-hat.service
sudo systemctl daemon-reload
sudo systemctl enable phd-hat.service
sudo systemctl start phd-hat.service
```