
= docker
Based on - https://github.com/don41382/docker-rpi-python3-with-bluetooth

make:
make build

run:
docker run  --privileged --net host  -e BADGE_SERVER_ADDR=localhost -e BADGE_SERVER_PORT=8000 APPKEY=secret -v /sys/kernel/debug:/sys/kernel/debug humandynamics/openbadge-hub-py -m standalone -dr scan

run an interactive shell:
docker run  --privileged -a stdin -a stdout -it --net host  --entrypoint=bash -v /sys/kernel/debug:/sys/kernel/debug humandynamics/openbadge-hub-py 
