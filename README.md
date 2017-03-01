= docker

== Development
For development, you can use the dev_ubuntu.yml (for linux, mac or windows) and dev_jessie.yml (if you are using raspberry pi). For exmaple:
docker-compose -f dev_ubuntu.yml up

By default, docker will start in standalone mode. However, you can override the default parameters using the run command:
docker-compose -f dev_ubuntu.yml run openbadge-hub-py -m server pull

For convenience, we mount the local data, logs and config directories as volumes in docker. This allows easier access to the data generated in this mode.

== Production
TBD. Use docker-compose.yml. Don't forget to populate .env (see .env.sample)

== Other useful commands
* Gaining shell: docker-compose -f dev_ubuntu.yml run --entrypoint /bin/bash openbadge-hub-py
