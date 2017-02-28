The hub supports two modes:
* standalone - no server needed. The hub will read a list of badges form the devices.txt file and data will be stored locally. This mode is useful for development, tests and small deployments
* server - the hub reads list of badges from a openbadge-server and sends data back to the server

= docker
Note - docker image is based on - https://github.com/don41382/docker-rpi-python3-with-bluetooth

Commands:
* To run the hub in standalone mode, on an Ubuntu machine: docker-compose -f standalone_ubuntu up
* To run the hub in standalone mode, on a Raspberry Pi with Jessie: docker-compose -f standalone_jessie up

Other useful commands:
* Gaining shell:  docker-compose -f standalone_ubuntu.yml run openbadge-hub-py /bin/bash
