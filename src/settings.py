from __future__ import absolute_import, division, print_function
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
import os
import socket
import sys

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BADGE_SERVER_ADDR = os.environ.get("BADGE_SERVER_ADDR")
if BADGE_SERVER_ADDR is None:
    print("BADGE_SERVER_ADDR is not set")
    sys.exit(1)

BADGE_SERVER_PORT = os.environ.get("BADGE_SERVER_PORT")
if BADGE_SERVER_PORT is None:
    print("BADGE_SERVER_PORT is not set")
    sys.exit(1)

BEACON_SERVER_ADDR = os.environ.get("BADGE_SERVER_ADDR")
if BEACON_SERVER_ADDR is None:
    print("BADGE_SERVER_ADDR is not set")
    sys.exit(1)

BEACON_SERVER_PORT = os.environ.get("BADGE_SERVER_PORT")
if BADGE_SERVER_PORT is None:
    print("BADGE_SERVER_PORT is not set")
    sys.exit(1)

APPKEY = os.environ.get("APPKEY")
if APPKEY is None:
    print("APPKEY is not set")
    sys.exit(1)

if os.environ.get("LOG_DIR").endswith("/"):
    LOG_DIR = os.environ.get("LOG_DIR")
else:
    LOG_DIR = os.environ.get("LOG_DIR") + "/"
if LOG_DIR is None:
    print("LOG_DIR is not set")
    sys.exit(1)

if os.environ.get("DATA_DIR").endswith("/"):
    DATA_DIR = os.environ.get("DATA_DIR")
else:
    DATA_DIR = os.environ.get("DATA_DIR") + "/"
if DATA_DIR is None:
    print("DATA_DIR is not set")
    sys.exit(1)

if os.environ.get("CONFIG_DIR").endswith("/"):
    CONFIG_DIR = os.environ.get("CONFIG_DIR")
else:
    CONFIG_DIR = os.environ.get("CONFIG_DIR") + "/"
if CONFIG_DIR is None:
    print("CONFIG_DIR is not set")
    sys.exit(1)

HUB_UUID = socket.gethostname()
