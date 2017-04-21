# docker

## Development
For development, you can use the dev_ubuntu.yml (for linux, mac or windows) and dev_jessie.yml (if you are using raspberry pi). For exmaple:
docker-compose -f dev_ubuntu.yml up

By default, docker will start the hub in standalone mode. However, you can override the default parameters using the run command:
docker-compose -f dev_ubuntu.yml run openbadge-hub-py -m server pull

For convenience, we mount the local data, logs and config directories as volumes in docker. This allows easier access to the data generated in this mode.

## Production
For production, we use docker volumes to store the data (rather than using the host's dicrectories). It also automatically starts in server mode.

To set it up, create a .env file (use env.example as a template), and change the server address, port and key. 

Next, run docker-compose (it will use docker-compose.yml as default) :
docker-compose up -d


## Other useful commands
* Gaining shell: docker-compose -f dev_ubuntu.yml run --entrypoint /bin/bash openbadge-hub-py
* Checking is the hub is running: docker-compose ps
