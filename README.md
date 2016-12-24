
= docker
Based on - https://github.com/don41382/docker-rpi-python3-with-bluetooth

make:
make build

run:
docker run  --privileged -a stdin -a stdout -i -t  -it --net host humandynamics/openbadge-hub-py
