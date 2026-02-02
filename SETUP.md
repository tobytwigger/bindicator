# FE compiling

`npx nuxi generate`

# Setup

Changes to be made from the raw raspberry pi lite image.


1. `nano /etc/hostname` and change to `bins`
2. If needed, set up `pi` user, add to sudo group etc
   3. sudo useradd -m -g users pi
   4. sudo passwd pi
   5. sudo adduser pi sudo
   6. sudo adduser pi gpio
3. STH AROUND download or copy script across (github?) that downloads and extracts the latest zip and runs setup.sh
   4. Simulated by copying entire repo except for gitattributes, frontend bar the output, and old-frontend
4. Run setup.sh
5. `touch /home/pi/database.sqlite`