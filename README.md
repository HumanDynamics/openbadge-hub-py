The (python) hub is used for controlling, monitoring, and communicating with the badges. The code was tested mainly on
Ubuntu (14 & 16) and Raspbian. In this document, we mostly assume Ubuntu for a development environment, and Raspberry Pi
(Raspbian and HypriotOS) for deployment.

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
To use the hub in standalone mode, you need to create two files under the config folder
* devices.txt - list of member badges. These badges will collect proximity and audio data
* devices_beacon.txt - list of beacons badges. These badges will only broadcast their IDs

You can refer to "devices.txt.example" and "devices_beacons.txt.example" as a reference for the file structure.
Important notes:
* Make sure you provide all members and beacons with the same project id (otherwise they will not see each other)
* By convention, member badges should have an id between 1 and 15999. Beacon ids should be between 16000 and 32000
* Choose different project ids for different projects that are running at the same time. This will prevent id conflicts
* For project id, pick a number between 1 and 254. Avoid using project id 0 since this is the default value for ibeacons

Next, use docker-compose to run the hub itself. You can either use the dev_ubuntu.yml (for linux, mac or windows) or
dev_jessie.yml (if you are using raspberry pi). For example:
```
docker-compose -f dev_ubuntu.yml build
docker-compose -f dev_ubuntu.yml up
```

For convenience, we mount the local source files, data, logs and config directories as volumes in docker. This allows
faster builds and easier access to the data generated in this mode.

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

## Setting up Raspberry Pi (with Hypriot)
(Might not work well with Raspberry Pi Zero W. Bluetooth has issues)
For convenience, we will be using HypriotOS instead of Raspbian. It is easier to configure, and comes with docker
pre-installed.

Download the latest HypriotOS - https://blog.hypriot.com/downloads/ . To make things easy, you should download a version
that matches the Docker you are running on your own machine.

The default username and password for Hypriot are pirate/hypriot (instead of pi/raspberry)

Next, you need to flash the image to a SD card. We will use the flash tool (developed by Hypriot). It supports Mac and
Linux. Download and install it:
```
curl -O https://raw.githubusercontent.com/hypriot/flash/master/$(uname -s)/flash
chmod +x flash
sudo mv flash /usr/local/bin/flash
```

If it's not working, please follow the more detailed explaination here -
https://github.com/hypriot/flash/blob/master/README.md

Now we use flash to write the image to your SD card. If you are using Ubuntu, the SD card will likely be /dev/mmcblk0.
If you are not sure, you can omit the --device flash, and it will show you a list of devices. Also, note that we are
setting the hostname of the machine using this command
```
flash --device /dev/mmcblk0 --hostname badgepi-xx hypriotos-rpi-v1.4.0.img
```

Note - the flash tool also provides an easy way to setup your wifi. You can read more about it here -
https://github.com/hypriot/flash/blob/master/README.md

After the flash util is done, place the SD card in your raspberry pi and power it up.

Copy your SSH public key to the raspberry pi. If you don't have a public one, follow these instructions
https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#generating-a-new-ssh-key
```
ssh-copy-id -oStrictHostKeyChecking=no -oCheckHostIP=no pirate@badgepi-xx
```

Run the following command to change the id of the operating system (this is required for docker-machine):
```
ssh pirate@badgepi-xx sudo sed -i \'s/ID=raspbian/ID=debian/g\' /etc/os-release
```

Connect to raspberry pi, and run the following commands:
* ssh pirate@badgepi-xx
* change your password using passwd
* change the timezone using sudo dpkg-reconfigure tzdata
* DO NOT RUN update & upgrade before installting docker. It causes issues (sudo apt-get update && sudo apt-get upgrade -y)

Double check that your hubs sync their time with a NTP server. Unsync clocks will lead to data corruption and loss

## Setting up Raspberry Pi using Raspian (For Raspberry Pi Zero W)
It seems that Hypriot has some issues with Pi Zero W (Bluetooth won't start). Therefore, it's better to use Raspbian
until they fix the problem.

Download the latest Jessie lite.

The default username and password for Hypriot are pi/raspberry

Now we use flash to write the image to your SD card. If you are using Ubuntu, the SD card will likely be /dev/mmcblk0.
If you are not sure, you can omit the --device flash, and it will show you a list of devices. Also, note that we are
setting the hostname of the machine using this command
```
flash --device /dev/mmcblk0 2017-04-10-raspbian-jessie-lite.img
```

Now, we'll need to turn on SSH and change the hostname. We'll do that by altering the following files on the SD card:
* First, mount the boot partition and main partition
* Create a file call "ssh" under the boot partition
* Edit /etc/hostname in the main partition and replace "raspberrypi" with your hostname
* Unmonut both partitions

Place the SD card in your raspberry pi and power it up.

Copy your SSH public key to the raspberry pi. If you don't have a public one, follow these instructions
https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#generating-a-new-ssh-key
```
ssh-copy-id -oStrictHostKeyChecking=no -oCheckHostIP=no pi@badgepi-xx
```

Run the following command to change the id of the operating system (this is required for docker-machine):
```
ssh pi@badgepi-xx sudo sed -i \'s/ID=raspbian/ID=debian/g\' /etc/os-release
```

Connect to raspberry pi, and run the following commands:
* ssh pi@badgepi-xx
* change your password using passwd
* extend the file system (sudo raspi-config --expand-rootfs), then reboot
* change the timezone (sudo dpkg-reconfigure tzdata)
* DO NOT RUN update & upgrade before installting docker. It causes issues (sudo apt-get update && sudo apt-get upgrade -y)

Double check that your hubs sync their time with a NTP server. Unsync clocks will lead to data corruption and loss

Now, latest versions os docker-machine has some issues with raspbian - docker-machine will fail without an obvious error. To fix it, you'll need to do the following:

```
ssh pi@badgepi-xx sudo sed -i \'s/ID=debian/ID=raspbian/g\' /etc/os-release
ssh pi@badgepi-xx sudo 'curl -sSL https://get.docker.com | sh'
ssh pi@badgepi-xx sudo sed -i \'s/ID=raspbian/ID=debian/g\' /etc/os-release
```

Then follow the instructions below for setting up with docker-machine.


## Deployment with docker-machine
Create a .env file (use the env.example file from the root directory as a template) and change the server address, port
and key:
* BADGE_SERVER_ADDR : server address (e.g. my.server.com)
* BADGE_SERVER_PORT : port
* APPKEY : application authentication key (needs to match APPKEY in your server configuration)

Use docker-machine to setup Docker on your raspberry pi (it will use your SSH key to connect):
'''
docker-machine create --engine-storage-driver=overlay --driver generic --generic-ssh-user pi  --generic-ip-address badgepi-xx.yourdomain.com badgepi-xx
'''

Note - in the latest docker version (true for 2017/07/07), there's a bug. Try adding the following to the create command:
'''
--engine-install-url=https://web.archive.org/web/20170623081500/https://get.docker.com
'''

Make the new machine the active machine:
```
eval $(docker-machine env badgepi-xx)
```

Make sure you are in the openbadge-hub-py directoy, and run docker-compose (it will use docker-compose.yml as default) :
```
docker-compose build
docker-compose up -d
```

## Deployment as a swarm
TBD

# Other useful commands
## Loading badges from a CSV files
This feature is no longer available as a hub command. Instead, use the django admin tool to import badges.

# MISC
## Notes on BlueZ
One of the main requirements for the hub is the BlueZ library. Newer version of Ubuntu and Raspbian include a somewhat
new version of BlueZ, so just make sure you use a recent release and ensure BlueZ version is >= 5.29. To check which
version you are using, type:
```
bluetoothd --version
```

## How to set the keyboard to a English-US layout
Go to Localization options, then:

Locale -> remove en_GB, add en_US.UTF-8, then choose enUS.UTF-8 as default

Keyboard layout -> choose a generic keyboard -> in the next list you'll see only UK keyboards. Go down and choose "other" -> Choose English (US) -> Choose English (US) agian

## Notes on how to create an image and copying it on multiple hubs
Ingeneral, follow the instructions on how to setup a regular hub, except:
* Do not expand the file system. It seems that HypriotOS and Jessie both expand it automatically. So in order to turn it off, edit /boot/boot/cmdline.txt and remove the call to init=/usr/lib/raspi-config/init_resize.sh
* Istead, use fdisk to extend it to a smaller partition. You can find more infomration here - http://www.raspberry-projects.com/pi/pi-operating-systems/raspbian/troubleshooting/expand-filesystem-issues . In general:
  * sudo fdisk /dev/mmcblk0
  * Then press 'p' to see the current partitions on the disk
  * Now delete the 2nd partition (it won't actually delete the data on it)
  * Press 'd' > Enter
  * Press '2' > Enter
  * Now re-create it:
  * Press 'n' > Enter
  * Press 'p' > Enter
  * Press '2' > Enter
  * Enter the First sector and the same value as the original /dev/mmcblk0p2 partition
  * Set the new size. I used +3G to create a 3GB partition (you'll need some space for building the hub images)
  * Now press 'p' > Enter to see the new partition setup.
  * Finally press 'w' > Enter to write it
  * Now reboot: sudo shutdown -r now
  * Once its back do the resize: sudo resize2fs /dev/mmcblk0p2
* Use docker-machine to install docker dependencies, etc
* Then run update & upgrade

Then save the image
* See this post for information - https://raspberrypi.stackexchange.com/questions/8305/how-to-make-an-image-img-from-whats-on-the-sd-card-but-as-compact-as-the-or 
* make sure partitions are unmounted
* sudo fdisk -l /dev/mmcblk0
* sudo dd if=/dev/mmcblk0 of=openbadge-hub-py.img bs=512 count=<END of second partition + 1>

Burn image into a new SD card
* Use dd, flash or Etcher.io

After you create a copy, make sure to:
* Change the hostname
* Extend the filesystem

## Old instructions on setting up a Raspberry Pi with Raspbian
Download the Raspbian lite (e.g. 2017-04-10-raspbian-jessie-lite.img) the the offical site.

Install the image on a SD card
* On most operating systems, you can use Etcher (https://etcher.io/)
* More instructions can be found here - https://www.raspberrypi.org/documentation/installation/installing-images/linux.md

Turn on ssh on raspberry pi
* Mount the boot partition of the SD Card
* Create an empty file called ssh
* Unmount

Change the hostname
* Mount the main volume
* Change /etc/hostname
* Unmount

Copy your SSH public key to the raspberry pi. If you don't have one, follow these instructions
 - https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#generating-a-new-ssh-key
```
ssh-copy-id -oStrictHostKeyChecking=no -oCheckHostIP=no pi@badgepi-xx
```

Run the following command to change the id of the operating system (this is required for docker-machine):
```
ssh pi@badgepi-xx sudo sed -i \'s/ID=raspbian/ID=debian/g\' /etc/os-release
```

Connect to raspberry pi, and run the following commands:
* ssh pi@badgepi-xx
* sudo raspi-config
   * Expand space
   * Change password
* sudo apt-get update
* sudo apt-get upgrade
* sudo dpkg-reconfigure tzdata

Double check that your hubs sync their time with a NTP server. Unsync clocks will lead to data corruption and loss
