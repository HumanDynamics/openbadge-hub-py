The hub supports two modes:
* standalone - no server needed. The hub will read a list of badges form the devices.txt file and data will be stored locally. This mode is useful for development, tests and small deployments
* server - the hub reads list of badges from a openbadge-server and sends data back to the server

= docker

== Standalone
To run the hub in standalone mode, first create devices.txt file with a list of MAC address, and then 
* on an Ubuntu machine: docker-compose -f standalone_ubuntu up
* on a Raspberry Pi with Jessie: docker-compose -f standalone_jessie up
* If you'd like to run in the background add "-d" to the commands above

Note - for convenience, we mount the local data, logs and config directories as volumes in docker. This allows easier access to the data generated in this mode.

== Server mode
TBD

== Other useful commands
* Gaining shell:  docker-compose -f standalone_ubuntu.yml run openbadge-hub-py /bin/bash
