# FE compiling

`npx nuxi generate`

# Flashing SD card
- PI Device: Raspberry Pi Zero 2 W
- OS: Raspberry Pi OS Lite (64-bit)
- Storage: Choose SD card

- Click next, then 'Edit Settings'
	- Set Hostname (bins)
	- Set username and password (toby and a password)
	- Set up wifi (for development only)
	- Enable SSH (feel free to add key here)

For headless setup, I think it requires a later version of rasppi imager. 

# Setup

## Should already be done

Changes to be made from the raw raspberry pi lite image (most of this is done with the flashing stage).


1. `nano /etc/hostname` and change to `bins`
2. If needed, set up `toby` user, add to sudo group etc
   3. sudo useradd -m -g users toby
   4. sudo passwd toby
   5. sudo adduser toby sudo
   6. sudo adduser toby gpio


## To do

### Install git
`sudo apt install git`

### Clone the repository

`git clone git@github.com:tobytwigger/bindicator`

### Set up the database

`mkdir /home/toby/data`
`touch /home/toby/data/database.sqlite`

### Run setup.sh

This will install the required dependencies and services, and set up/start nginx

3. STH AROUND download or copy script across (github?) that downloads and extracts the latest zip and runs setup.sh
   4. Simulated by copying entire repo except for gitattributes, frontend bar the output, and old-frontend
4. Run setup.sh


# Migration for fastapi

`alembic revision --autogenerate -m "initial migration"` to create migration file
`alembic upgrade head` to apply migration