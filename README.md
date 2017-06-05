The (python) hub is used for controlling, monitoring, and communicating with the badges. The code was tested mainly on
Ubuntu (14 & 16) and Raspbian. In this document, we mostly assume Ubuntu for a development environment, and Raspberry Pi
(Raspbian) for deployment.

In order to simplify setup and deployment, the hub code can now be wrapped in a Docker container.

There are two main modes of operation -
1. Standalone - in this mode, the hub loads a list of badges from a static files and writes data to local files. This
mode is useful for testing, development, and when you only need a single hub
2. Server - in server mode, the hub communicates with a server (openbadge-server). It will read the list of badges,
and send back information such as badge health and collected data

Important notes:
* When using multiple hubs, it's important to set up NTP properly so that the time on the hubs is synchronized.
Unsynchronized clocks will lead to significant data loss and data corruption
* When running the hub on Raspberry Pi, the hub will modify system parameters in order to (significantly) speed up
Bluetooth communication. These settings might affect the communication with other Bluetooth devices, and therefore we
do not apply these changes to non-raspberry pi machines
* Docker uses different base images for Ubuntu and Raspbian, and therefore there are different .yml files for different
operating systems

# Development / Standalone mode
To use the hub in standalone mode, create a files called "devices.txt" under the config directory and add the MAC
addresses of your badges. You can use the "devices.txt.example" as a reference for the file structure.

Next, use docker-compose to run the hub itself. You can either use the dev_ubuntu.yml (for linux, mac or windows) or
dev_jessie.yml (if you are using raspberry pi). For example:
```
docker-compose -f dev_ubuntu.yml build
docker-compose -f dev_ubuntu.yml up
```

For convenience, we mount the local data, logs and config directories as volumes in docker. This allows easier access
to the data generated in this mode.

Note - by default, docker will start the hub in standalone mode. However, you can override the command parameters:
```
docker-compose -f dev_ubuntu.yml run openbadge-hub-py -m server pull
```

If you choose to run the hub in server more, remember to create a .env file and set the parameters accordingly. See the
next section for more information.

In order to get an interactive shell for the hub container, you need to overwrite the entrypoint:
```
docker-compose -f dev_ubuntu.yml run --entrypoint /bin/bash openbadge-hub-py
```

# Deployment
For deployment, we are going to assume Raspberry Pi as a platform. The following sections explain how to setup the
raspberry pi, and then how run the hub code using Docker.

## Setting up Raspberry Pi
* Make sure hubs synchronize their dates using NTP (preferably the same NTP server). **No, seriously. Make sure that the
 time on all of your hubs and servers is synchronized**
* Download the Raspbian lite (2017-04-10-raspbian-jessie-lite.img) and install
   * On most operating systems, you can use Etcher (https://etcher.io/)
   * If you are using a Linux command line for installation, you can do the following :
      * unmount SD card volumes (if there are existing volumes, some machines will auto-mount them)
      * sudo dd bs=4M if=2017-04-10-raspbian-jessie-lite.img of=/dev/mmcblk0
      * sync
   * More insturctions can be found [here](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md).
* Create private and public keys:
```
ssh-keygen -t rsa -b 2048 -C "badgepi-key" -f badgepi-key
chmod 600 badgepi-key
```
* The command will generate two files::
   * badgepi-key - this one you keep on your computer
   * badgepi-key.pub - this file will be placed on each of your hubs

* Alter files on SD card before placing it in the raspberry Pi:
```
# turn on ssh
sudo mkdir -p /media/temp_boot ; sudo mount /dev/mmcblk0p1 /media/temp_boot/
sudo touch /media/temp_boot/ssh
sudo umount /media/temp_boot

sudo mkdir -p /media/temp_vol ; sudo mount /dev/mmcblk0p2 /media/temp_vol/
# Change hostname
sudo sh -c 'echo badgepi-xx > /media/temp_vol/etc/hostname'
# Setup SSH keys
sudo mkdir -p /media/temp_vol/home/pi/.ssh
sudo cp badgepi-key.pub /media/temp_vol/home/pi/.ssh/authorized_keys
sudo chmod 750 /media/temp_vol/home/pi/.ssh
sudo chmod 600 /media/temp_vol/home/pi/.ssh/authorized_keys
sudo chown -R 1000:1000 /media/temp_vol/home/pi/.ssh
# Disable connection using password (use keys instead)
sudo sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/g" /media/temp_vol/etc/ssh/sshd_config
sudo umount /media/temp_vol
sync
```
* Connect to raspberry pi. You'll need to use the (private) key file you created since we disabled the password login:
   * ssh -i badgepi-key pi@badgepi-xx
* run config tool: sudo raspi-config
   * Expand space
   * Change password
* sudo apt-get update
* sudo apt-get upgrade
* sudo dpkg-reconfigure tzdata
* Double check that your hubs sync their time with a NTP server. Have I mentioned how important that is?

## Deployment with docker-machine
Create a .env file (use env.example as a template), and change the server address, port and key:
* BADGE_SERVER_ADDR : server address (e.g. my.server.com)
* BADGE_SERVER_PORT : port
* APPKEY : application authentication key (needs to match APPKEY in your server configuration)


Use docker-machine to setup Docker on your raspberry pi:
'''
docker-machine create --driver generic --generic-ssh-user <username> --generic-ssh-key <ssh-key-location>
--generic-ip-address <ip-address> <machine-name>
'''

Next, run docker-compose (it will use docker-compose.yml as default) :
```
docker-compose build
docker-compose up
```

## Deployment as a swarm
TBD

# MISC
## Updating BlueZ
One of the main requirements for the hub is the BlueZ library. Raspbian and Ubuntu already have BlueZ installed, but it
 is very old. While it seems to

### Ubuntu
For Ubuntu, you are likely to need to install it from the source. Here's the procedure we have been using. It's been
tested on  Ubuntu 14.04 and seems to be working well.

Install dependencies:
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get -y install libdbus-1-dev libdbus-glib-1-dev libglib2.0-dev libical-dev libreadline-dev libudev-dev libusb-dev make
```

Download and install [BlueZ](http://www.bluez.org/download/) version 5.29 or higher:
```
wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.37.tar.xz
tar xf bluez-5.37.tar.xz
cd bluez-5.37
mkdir release
./configure --disable-systemd
make -j4
sudo make install
```

### Raspbian
For Raspbian, you can follow the procedure described in [stackexchange](http://raspberrypi.stackexchange.com/questions/39254/updating-bluez-5-23-5-36)
 and install a newer version of BlueZ from the stretch sources
