# Pull base image
FROM resin/rpi-raspbian:jessie
MAINTAINER Felix Eckhardt felix.e@gmx.de

# Install dependencies
RUN apt-get update && apt-get install -y \
    python \
    python-dev \
    python-pip \
    gcc \
    build-essential \
    libglib2.0-dev \
    bluez \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

ENV DATA_DIR /data
RUN mkdir $DATA_DIR

ENV LOG_DIR /logs
RUN mkdir $LOG_DIR

COPY ./src /app

RUN pip install -r /app/requirements.txt

# Define working directory
WORKDIR /app

# Define default command
#CMD ["bash"]
ENTRYPOINT ["./badge_hub.py"]
