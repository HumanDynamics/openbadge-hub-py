from __future__ import absolute_import, division, print_function
import requests
import time

from badge import *
from server import BADGE_ENDPOINT, BADGES_ENDPOINT, BEACON_ENDPOINT, BEACONS_ENDPOINT, request_headers
from settings import APPKEY, HUB_UUID
import traceback

class BadgeManagerServer:
    def __init__(self, logger):
        self._badges = None
        self.logger = logger

    def _jason_badge_to_object(self, d):
        conv = lambda x: int(float(x))
        return Badge(d.get('badge'),
                    self.logger,
                    d.get('key'),
                    badge_id = d.get('id'),
                    project_id = d.get('advertisement_project_id'),
                    init_audio_ts_int=conv(d.get('last_audio_ts')),
                    init_audio_ts_fract=conv(d.get('last_audio_ts_fract')),
                    init_proximity_ts=conv(d.get('last_proximity_ts')),
                    init_voltage=d.get('last_voltage'),
                    init_contact_ts = d.get('last_contacted_ts'),
                    init_unsync_ts = d.get('last_unsync_ts')

        )

    def _read_badges_list_from_server(self, retry=True, retry_delay_sec=5):
        """
        Reads badges info from the server
        :param retry: if blocking is set, hub will keep retrying
        :return:
        """
        server_badges = {}
        done = False

        while not done:
            try:
                self.logger.info("Requesting devices from server...")
                response = requests.get(BADGES_ENDPOINT, headers=request_headers())
                if response.ok:
                    self.logger.info("Updating devices list ({})...".format(len(response.json())))
                    for d in response.json():
                        if(d.get('active')==True):
                            server_badges[d.get('badge')] = self._jason_badge_to_object(d)

                    done = True
                else:
                    raise Exception('Got a {} from the server'.format(response.status_code))

            except (requests.exceptions.ConnectionError, Exception) as e:
                s = traceback.format_exc()
                self.logger.error("Error reading badges list from server : {}, {}".format(e,s))
                if not retry:
                    done = True
                else:
                    self.logger.info("Sleeping for {} seconds before retrying".format(retry_delay_sec))
                    time.sleep(retry_delay_sec)

        return server_badges

    def _read_badge_from_server(self, badge_key, retry=False, retry_delay_sec=5):
        """
        Reads given badge info from the server
        :param retry: if blocking is set, hub will keep retrying
        :return:
        """
        done = False

        while not done:
            try:
                self.logger.info("Requesting device {} from server...".format(badge_key))
                response = requests.get(BADGE_ENDPOINT(badge_key), headers=request_headers())
                if response.ok:
                    #self.logger.debug("Received ({})...".format(response.json()))
                    return self._jason_badge_to_object(response.json())
                else:
                    raise Exception('Got a {} from the server'.format(response.status_code))

            except (requests.exceptions.ConnectionError, Exception) as e:
                self.logger.error("Error reading badge from server : {}".format(e))
                if not retry:
                    done = True
                else:
                    self.logger.info("Sleeping for {} seconds before retrying".format(retry_delay_sec))
                    time.sleep(retry_delay_sec)

        return None

    def _update_badge_with_server_badge(self,badge,server_badge):
        """
        Updates the timestamp of the given badge if the given server badge has more recent timestamps
        When running multiple hubs in the same project, a different hub might have updated these values
        already. Therefore, we need to pull the latest values.
        :param badge:
        :param server_badge:
        :return:
        """
        mac = badge.addr
        server_ts_int = server_badge.last_audio_ts_int
        server_ts_fract = server_badge.last_audio_ts_fract
        server_ts_last_contacted = server_badge.last_contacted_ts
        server_ts_last_unsync = server_badge.last_unsync_ts
        if badge.is_newer_audio_ts(server_ts_int, server_ts_fract):
            #self.logger.debug("Updating {} with new audio timestamp: {} {}"
            #                  .format(mac, server_ts_int, server_ts_fract))
            badge.set_audio_ts(server_ts_int, server_ts_fract)
        else:
            #self.logger.debug("Keeping existing timestamp for {}. Server values were: {} {}"
            #                  .format(mac, server_ts_int, server_ts_fract))
            pass

        # proximity
        server_proximity_ts = server_badge.last_proximity_ts
        if server_proximity_ts > badge.last_proximity_ts:
            #self.logger.debug("Updating {} with new proximity timestamp: {}".format(mac, server_proximity_ts))
            badge.last_proximity_ts = server_proximity_ts

        else:
            #self.logger.debug("Keeping existing proximity timestamp for {}. Server value was: {}"
            #                  .format(mac, server_proximity_ts))
            pass

        if server_ts_last_contacted > badge.last_contacted_ts:
            badge.last_contacted_ts = server_ts_last_contacted
        else:
            pass

        if server_ts_last_unsync > badge.last_unsync_ts:
            badge.last_unsync_ts = server_ts_last_unsync
        else:
            pass

        # updates project id and badge id
        badge.badge_id = server_badge.badge_id
        badge.project_id = server_badge.project_id

    def pull_badges_list(self):
        # first time we read from server
        if self._badges is None:
            server_badges = self._read_badges_list_from_server(retry=True)
            self._badges = server_badges
        else:
            # update list
            server_badges = self._read_badges_list_from_server(retry=False)
            for mac in server_badges:
                if mac not in self._badges:
                    # new badge
                    self._badges[mac] = server_badges[mac]
                else:
                    # existing badge. Update if needed
                    # audio
                    badge = self._badges[mac]
                    server_badge = server_badges[mac]
                    self._update_badge_with_server_badge(badge,server_badge)

    def pull_badge(self, mac):
        """
        Contacts to server (if responding) and updates the given badge data
        :param mac:
        :return:
        """
        badge = self._badges[mac]
        server_badge = self._read_badge_from_server(badge.key)
        if server_badge is None:
            self.logger.warn("Could not find device {} in server, or communication problem".format(badge.key))
        else:
            # update timestamps if more recent
            self._update_badge_with_server_badge(badge, server_badge)

    def send_badge(self, mac):
        """
        Sends timestamps of the given badge to the server
        :param mac:
        :return:
        """
        try:
            badge = self._badges[mac]
            data = {            
                'observed_id': badge.observed_id,
                'last_audio_ts': badge.last_audio_ts_int,
                'last_audio_ts_fract': badge.last_audio_ts_fract,
                'last_proximity_ts': badge.last_proximity_ts,
                'last_voltage': badge.last_voltage,
                'last_seen_ts': badge.last_seen_ts,
                'last_contacted_ts': badge.last_contacted_ts,
                'last_unsync_ts': badge.last_unsync_ts
            }

            self.logger.debug("Sending update badge data to server, badge {} : {}".format(badge.key, data))
            response = requests.patch(BADGE_ENDPOINT(badge.key), data=data, headers=request_headers())
            if response.ok is False:
                if response.status_code == 400:
                    self.logger.debug("Server had more recent date, badge {} : {}".format(badge.key, response.text))
                else:
                    raise Exception('Server sent a {} status code instead of 200: {}'.format(response.status_code,
                                                                                         response.text))
        except Exception as e:
            self.logger.error('Error sending updated badge into to server: {}'.format(e))

    def create_badge(self, name, email, mac ):
        """
        Creates a badge using the giving information
        :param name: user name
        :param email: user email
        :param mac: badge mac
        :return:
        """
        try:
            data = {
                'name': name,
                'email': email,
                'badge': mac,
            }

            self.logger.info("Creating new badge : {}".format(data))
            response = requests.post(BADGES_ENDPOINT, data=data, headers=request_headers())
            if response.ok is False:
                s = traceback.format_exc()
                raise Exception('Error creating badge {}. Status: {}, Error: {}, {}'.format(data, response.status_code,
                                                                                             response.text, s))
        except Exception as e:
            s = traceback.format_exc()
            self.logger.error('Error creating new badge. Error: {} ,{}'.format(e,s))



    @property
    def badges(self):
        if self._badges is None:
            raise Exception('Badges list has not been initialized yet')
        return self._badges


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger('badge_server')
    logger.setLevel(logging.DEBUG)
    
    mgr = BadgeManagerServer(logger=logger)
    mgr.pull_badges_list()
    print(mgr.badges)
    mgr.pull_badges_list()
    print(mgr.badges)
    for mac in mgr.badges:
        print("Updating: {}".format(mac))
        mgr.send_badge(mac)

    b1 = mgr.pull_badge(mac)
    print(b1)
