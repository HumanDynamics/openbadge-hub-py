#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import os
import re
import shlex
import subprocess

import logging
import json
from time import time
from datetime import datetime as dt
from requests.exceptions import RequestException
import glob

from badge import *
from badge_discoverer import BadgeDiscoverer
from badge_manager_server import BadgeManagerServer
from badge_manager_standalone import BadgeManagerStandalone
import hub_manager 
from settings import DATA_DIR, LOG_DIR

log_file_name = LOG_DIR + 'server.log'
scans_file_name = DATA_DIR + 'scan.txt'

pending_file_prefix = DATA_DIR + 'pending_'
audio_archive_file_name = DATA_DIR + 'audio_archive.txt'
proximity_archive_file_name = DATA_DIR + 'proximity_archive.txt'

standalone_audio_file = DATA_DIR + 'audio_data.txt'
standalone_proximity_file = DATA_DIR + 'proximity_data.txt'

AUDIO = "audio"
PROXIMITY = "proximity"

SCAN_DURATION = 3  # seconds

#NOTE try to keep under 100MB or so due to memory constraints
MAX_PENDING_FILE_SIZE = 20000000 # in bytes, so 20MB

# create logger with 'badge_server'
logger = logging.getLogger('badge_server')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler(log_file_name)
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(mac)s] %(message)s')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def get_devices(device_file="device_macs.txt"):
    """
    Returns a list of devices included in device_macs.txt
    Format is device_mac<space>device_name
    :param device_file:
    :return:
    """
    if not os.path.isfile(device_file):
        logger.error("Cannot find devices file: {}".format(device_file))
        exit(1)
    logger.info("Reading whitelist:")

    regex = re.compile(r'^([A-Fa-f0-9]{2}(?::[A-Fa-f0-9]{2}){5}).*')

    with open(device_file, 'r') as devices_macs:
        devices = [regex.findall(line) for line in devices_macs]
        devices = filter(lambda x: x, map(lambda x: x[0] if x else False, devices))
        devices = [d.upper() for d in devices]

    for d in devices:
        logger.info("    {}".format(d))

    return devices


def round_float_for_log(x):
    return float("{0:.3f}".format(x))

def has_chunks(filename):
    """
    Returns true if there is data in the file, and false otherwise
    """
    return os.path.exists(filename) and os.path.getsize(filename) > 0
    
def offload_data():
    """
    Send pending files to server and move pending to archive
    
    Return True on success, False on failure
    """
    #TODO test with standalone
    #NOTE not currently doing anything with the True/False
    # return values, might decide to do something later
    pending_files = glob.glob(pending_file_prefix + "*")
    for pending_file_name in pending_files:
        
        if not has_chunks(pending_file_name):
            continue

        chunks = []
        with open(pending_file_name, "r") as pending_file:
            for line in pending_file:
                chunks.append(json.loads(line))

        # real quick grab the data type from the first data entry
        data_type = "audio" if "audio" in chunks[0]["type"] else "proximity"
        # fire away!
        try:
            chunks_written = hub_manager.send_data_to_server(logger, data_type, chunks)
            if chunks_written == len(chunks):
                logger.info("Successfully wrote {} data entries to server"
                    .format(len(chunks)))
            else:
                # this seems unlikely to happen but is good to keep track of i guess
                logger.error("Data mismatch: {} data entries were not written to server"
                    .format(len(chunks) - chunks_written))
                logger.error("Error sending data from file {} to server!"
                    .format(pending_file_name))
                return False
                
            # write to archive and erase pending file
            with open(get_archive_name(data_type), "a") as archive_file:
                for chunk in chunks:
                    archive_file.write(json.dumps(chunk) + "\n")
            os.remove(pending_file_name)
        except RequestException as e:
            logger.error("Error sending data from file {} to server!"
                .format(pending_file_name))
            logger.error(e)
            return False
    return True


def get_archive_name(data_type):
    """
    Return the name of the archive file for the passed data type
    """
    if data_type == AUDIO:
        return audio_archive_file_name
    else:
        return proximity_archive_file_name

def get_proximity_name(mode="server"):
    """
    return the name of the existing pending proximity file,
    or a new one if either one doesn't exist or if  
    the existing file is > MAX_PENDING_FILE_SIZE
    """
    if mode == "server":
        return _get_pending_file_name(PROXIMITY)
    else:
        return standalone_proximity_file

def get_audio_name(mode="server"):
    if mode == "server":
        return _get_pending_file_name(AUDIO)
    else:
        return standalone_audio_file

def _get_pending_file_name(data_type):
    """
    If there are no current pending files < MAX_PENDING_FILE_SIZE in size,
        return a new pending filename
    Else, return an existing one.
    """
    filenames = filter(
            lambda x: os.path.getsize(x) < MAX_PENDING_FILE_SIZE,
            glob.glob("{}*{}*".format(pending_file_prefix, data_type)))
    if len(filenames) == 0:
        return _create_pending_file_name(data_type)
    else:
        return filenames[0]
                
def _create_pending_file_name(data_type):
    """
    Create a pending file name for the given data_type
    
    Uses the current date/time to create a unique filename
    """
    now = dt.now().strftime("%Y%m%d%H%M%S")
    filename = "{}{}_{}.txt".format(pending_file_prefix, now, data_type)
    if os.path.exists(filename):
        # this seems unlikely to happen, but just in case :)
        # get the number of pending files that match this time and add one
        files = glob.glob("{}{}*{}*".format(pending_file_prefix, now, data_type))
        now = '_'.join((now, str(len(files) + 1)))
        filename =  "{}{}_{}.txt".format(pending_file_prefix, now, data_type)

    return filename 
     
def dialogue(bdg, activate_audio, activate_proximity, mode="server"):
    """
    Attempts to read data from the device specified by the address. Reading is handled by gatttool.
    :param bdg:
    :return:
    """
    ret = bdg.pull_data(activate_audio, activate_proximity)
    addr = bdg.addr
    if ret == 0:
        logger.info("Successfully pulled data")
        # if we were able to pull data, we saw the badge again
        bdg.last_seen_ts = time.time()
    else:
        logger.info("Errors pulling data.")

    if bdg.dlg.chunks:
        logger.info("Chunks received: {}".format(len(bdg.dlg.chunks)))
        logger.info("saving chunks to file")

        # store in JSON file
        with open(get_audio_name(mode), "a") as fout:
            for chunk in bdg.dlg.chunks:
                ts_with_ms = round_float_for_log(ts_and_fract_to_float(chunk.ts, chunk.fract))
                log_line = {
                    'type': "audio received",
                    'log_timestamp': round_float_for_log(time.time()),
                    'log_index': -1,  # need to find a good accumulator.
                    'data': {
                        'voltage': round_float_for_log(chunk.voltage),
                        'timestamp': ts_with_ms,
                        'sample_period': chunk.sampleDelay,
                        'num_samples': len(chunk.samples),
                        'samples': chunk.samples,
                        'badge_address': addr,
                        'member': bdg.key
                    }
                }

                logger.debug("Chunk timestamp: {0:.3f}, Voltage: {1:.3f}, Delay: {2}, Samples in chunk: {3}".format(
                    ts_with_ms, chunk.voltage, chunk.sampleDelay, len(chunk.samples)))
                #logger.debug(json.dumps(log_line))
                json.dump(log_line, fout)
                fout.write('\n')

            logger.info("done writing")

        # update badge object to hold latest timestamps
        last_chunk = bdg.dlg.chunks[-1]
        logger.debug("Setting last badge audio timestamp to {} {}".format(last_chunk.ts, last_chunk.fract))
        if bdg.is_newer_audio_ts(last_chunk.ts, last_chunk.fract):
            bdg.set_audio_ts(last_chunk.ts, last_chunk.fract)
            bdg.last_voltage = round_float_for_log(chunk.voltage)
        else:
            logger.debug("Keeping existing timestamp ({}.{}) for {}. Last chunk timestamp was: {}.{}"
                              .format(bdg.last_audio_ts_int,bdg.last_audio_ts_fract,bdg.addr, last_chunk.ts, last_chunk.fract))


    else:
        logger.info("No mic data ready")

    if bdg.dlg.scans:
        logger.info("Proximity scans received: {}".format(len(bdg.dlg.scans)))
        logger.info("saving proximity scans to file")
        with open(get_proximity_name(mode), "a") as fout:
            for scan in bdg.dlg.scans:
                ts_with_ms = round_float_for_log(scan.ts)
                log_line = {
                    'type': "proximity received",
                    'log_timestamp': round_float_for_log(time.time()),
                    'log_index': -1,  # need to find a good accumulator.
                    'data': {
                        'voltage': round_float_for_log(scan.voltage),
                        'timestamp': ts_with_ms,
                        'badge_address': addr,
                        'rssi_distances':
                            {
                                device.ID: {'rssi': device.rssi, 'count': device.count} for device in scan.devices
                                },
                        'member': bdg.key
                    }
                }

                logger.debug("SCAN: scan timestamp: {0:.3f}, voltage: {1:.3f}, Devices in scan: {2}".format(
                    ts_with_ms, scan.voltage, scan.numDevices))
                #logger.info(json.dumps(log_line))

                json.dump(log_line, fout)
                fout.write('\n')

        # update badge object to hold latest timestamps
        last_scan = bdg.dlg.scans[-1]
        logger.debug("Setting last badge proximity timestamp to {}".format(last_scan.ts))
        bdg.last_proximity_ts = last_scan.ts
    else:
        logger.info("No proximity scans ready")


def scan_for_devices(devices_whitelist):
    bd = BadgeDiscoverer(logger)
    try:
        all_devices = bd.discover(scan_duration=SCAN_DURATION)
    except Exception as e: # catch *all* exceptions
        logger.error("Scan failed,{}".format(e))
        all_devices = {}

    scanned_devices = []
    for addr,device_info in all_devices.iteritems():
        if addr in devices_whitelist:
            logger.debug("\033[1;7m\033[1;32mFound {}, added. Device info: {}\033[0m".format(addr, device_info))
            scanned_devices.append({'mac':addr,'device_info':device_info})
        else:
            #logger.debug("Found {}, but not on whitelist. Device info: {}".format(addr, device_info))
            pass

    time.sleep(2)  # requires sometimes to prevent connection from failing
    return scanned_devices


def create_badge_manager_instance(mode,timestamp):
    if mode == "server":
        mgr = BadgeManagerServer(logger=logger)
    else:
        mgr = BadgeManagerStandalone(logger=logger,timestamp=timestamp)
    return mgr


def reset():
    '''
    Resets and reconfigures Bluetooth parameters. The specific parameters affect connection speed negotiation. It's
    not pretty, but safer to change the conn params this way
    :return:
    '''

    # Resets BLE hci
    logger.info("Resetting bluetooth")
    reset_command = "hciconfig hci0 reset"
    args = shlex.split(reset_command)
    p = subprocess.Popen(args)

    # israspberry pi?
    logger.info("Setting bluetooth connection parameters")
    if os.uname()[4][:3] == 'arm':
        logger.info("Raspberry Pi detected, changing bluetooth connection parameters")
        with open("/sys/kernel/debug/bluetooth/hci0/conn_min_interval", "w") as connparam:
            connparam.write("16")
        with open("/sys/kernel/debug/bluetooth/hci0/conn_max_interval", "w") as connparam:
            connparam.write("17")
    else:
        logger.warn("Not a Raspberry Pi, Bluetooth connection parameters remain untouched (communication may be slower)")

    time.sleep(2)  # requires sleep after reset
    logger.info("Done resetting bluetooth")


def pull_devices(mgr, start_recording):
    logger.info('Started pulling')
    activate_audio = False
    activate_proximity = False

    if start_recording is None or start_recording == "both":
        activate_audio = True
        activate_proximity = True
    elif start_recording == "audio":
        activate_audio = True
    elif start_recording == "proximity":
        activate_proximity = True
    elif start_recording == "none":
        activate_audio = False
        activate_proximity = False

    logger.info("Start recording: Audio = {}, Proximity = {}".format(activate_audio,activate_proximity))
    mode = "server" if isinstance(mgr, BadgeManagerServer) else "standalone"

    while True:
        mgr.pull_badges_list()
        # When we refactor we can change this, but for now:
        if mode == "server":
            logger.info("Attempting to offload data to server")
            offload_data()
        logger.info("Scanning for devices...")
        scanned_devices = scan_for_devices(mgr.badges.keys())
        # iterate before the actual data collection loop just to offload
        # voltages to the server (and update heartbeat on server)
        for device in scanned_devices:
            b = mgr.badges.get(device['mac'])
            # i don't think adv_payload is ever supposed to be empty, 
            # but sometimes it is. and when it is, it breaks
            if device['device_info']['adv_payload'] is not None:
                b.last_voltage = device['device_info']['adv_payload']['voltage']
            b.last_seen_ts = time.time()
            mgr.send_badge(device['mac'])

        # now the actual data collection 
        for device in scanned_devices:
            b = mgr.badges.get(device['mac'])
            # try to update latest badge timestamps from the server
            mgr.pull_badge(b.addr)
            # pull data
            dialogue(b, activate_audio, activate_proximity, mode)

            # update timestamps on server
            mgr.send_badge(device['mac'])

            time.sleep(2)  # requires sleep between devices


def sync_all_devices(mgr):
    logger.info('Syncing all badges recording.')
    mgr.pull_badges_list()
    for mac in mgr.badges:
        bdg = mgr.badges.get(mac)
        bdg.sync_timestamp()
        time.sleep(2)  # requires sleep between devices

    time.sleep(2)  # allow BLE time to disconnect


def devices_scanner(mgr):
    logger.info('Scanning for badges')
    mgr.pull_badges_list()
    while True:
        logger.info("Scanning for devices...")
        scanned_devices = scan_for_devices(mgr.badges.keys())
        with open(scans_file_name, "a") as fout:
            for device in scanned_devices:
                mac = device['mac']
                scan_date = device['device_info']['scan_date']
                rssi = device['device_info']['rssi']
                if device['device_info']['adv_payload']:
                    voltage = device['device_info']['adv_payload']['voltage']
                else:
                    voltage = 0.0
                logger.debug("{},{},{:.2f},{:.2f}".format(scan_date, mac, rssi, voltage))
                fout.write("{},{},{:.2f},{:.2f}\n".format(scan_date, mac, rssi, voltage))
        time.sleep(5)  # give time to Ctrl-C


def start_all_devices(mgr):
    logger.info('Starting all badges recording.')
    while True:
        mgr.pull_badges_list()

        logger.info("Scanning for devices...")
        scanned_devices = scan_for_devices(mgr.badges.keys())
        for device in scanned_devices:
            dev_info = device['device_info']
            if dev_info ['adv_payload']:
                sync = dev_info ['adv_payload']['sync_status']
                audio = dev_info ['adv_payload']['audio_status']
                proximity = dev_info ['adv_payload']['proximity_status']

                if sync == 0 or audio == 0 or proximity == 0:
                    logger.info("Starting {}".format(device['mac']))
                    bdg = mgr.badges.get(device['mac'])
                    bdg.start_recording()
                    time.sleep(2)  # requires sleep between devices

                else:
                    logger.info("No need to start {}".format(device['mac']))


        time.sleep(2)  # allow BLE time to disconnect


def add_pull_command_options(subparsers):
    pull_parser = subparsers.add_parser('pull', help='Continuously pull data from badges')
    pull_parser.add_argument('-r','--start_recording'
                             , choices=('audio', 'proximity', 'both','none'), required=False
                             , default='both'
                             , dest='start_recording',help='data recording option')

def add_scan_command_options(subparsers):
    pull_parser = subparsers.add_parser('scan', help='Continuously scan for badges')


def add_sync_all_command_options(subparsers):
    sa_parser = subparsers.add_parser('sync_all', help='Send date to all devices in whitelist')


def add_start_all_command_options(subparsers):
    st_parser = subparsers.add_parser('start_all', help='Start recording on all devices in whitelist')


if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser(description="Run scans, send dates, or continuously pull data")
    parser.add_argument('-dr','--disable_reset_ble', action='store_true', default=False, help="Do not reset BLE")
    parser.add_argument('-m','--hub_mode', choices=('server', 'standalone')
                        , default='standalone', dest='hub_mode'
                        , help="Operation mode - standalone (using a configuration file) or a server")
    parser.add_argument('-t', '--timestamp'
                             , type=int, required=False
                             , dest='timestamp', help='UTC timestamp to start pulling data from (int)')

    subparsers = parser.add_subparsers(help='Program mode (e.g. Scan, send dates, pull, scan etc.)', dest='mode')
    add_pull_command_options(subparsers)
    add_scan_command_options(subparsers)
    add_sync_all_command_options(subparsers)
    add_start_all_command_options(subparsers)

    args = parser.parse_args()

    mgr = create_badge_manager_instance(args.hub_mode, args.timestamp)

    if not args.disable_reset_ble:
        reset()

    if args.mode == "sync_all":
        sync_all_devices(mgr)

    # scan for devices
    if args.mode == "scan":
        devices_scanner(mgr)

    # pull data from all devices
    if args.mode == "pull":
        pull_devices(mgr, args.start_recording)

    if args.mode == "start_all":
        start_all_devices(mgr)

    exit(0)
