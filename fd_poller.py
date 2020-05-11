import os
import sys
import time
import json
import datetime
import traceback

import pandas as pd
from lxml import html
from requests import Session
import messagebird

import logging

# TODO: Refactor these constants into config

# Your Fresh Direct login credentials
USERNAME = 'ilovegroceries@gmail.com'
PASSWORD = 'correcthorsebatterystaple'

# Your MessageBird api key
MESSAGE_BIRD_API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxx'

# Phone number to text on grocery availability
PHONE_NUMBER_TO_TEXT = '+12125555555'


def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('log.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


logger = setup_custom_logger('fresh-direct-poller')


class Alerter:
    def __init__(self, alert_interval=60):
        self.alert_interval = alert_interval
        self.last_alerted = datetime.datetime.fromtimestamp(0)

    def alert(self, message):
        if (datetime.datetime.now() - self.last_alerted).seconds > self.alert_interval:
            self.last_alerted = datetime.datetime.now()
            self.user_alert(message)

    def user_alert(self, message):
        pass  # Implement in subclass.


class TextAlerter(Alerter):
    client = messagebird.Client(MESSAGE_BIRD_API_KEY)

    def user_alert(self, message):
        message = self.client.message_create(
            'MessageBird',
            PHONE_NUMBER_TO_TEXT,
            message,
            {'reference': 'Foobar'}
        )


class FreshDirectClient:
    def __init__(self, logger):
        self.logger = logger
        self.auth_endpoint = 'https://www.freshdirect.com/api/login/'
        self.slots_endpoint = 'https://www.freshdirect.com/your_account/delivery_info_avail_slots.jsp'
        self.headers = {
            'User-Agent': 'PostmanRuntime/7.24.1',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = Session()

    def authenticate(self, user_id, password):
        # Need to query homepage first to get session cookies for for auth.
        self.logger.info("Authenticating Fresh Direct...")
        res1 = self.session.get('https://www.freshdirect.com/', timeout=(3, 5), headers=self.headers)
        res1.raise_for_status()

        credentials = json.dumps({'userId': user_id, 'password': password})
        res2 = self.session.post(self.auth_endpoint,
                                 timeout=(3, 5), headers=self.headers, data={'data': credentials})
        res2.raise_for_status()
        self.logger.info("Success!")

    def get_delivery_timeslots_html(self):
        res = self.session.get(self.slots_endpoint, headers=self.headers, timeout=10)
        res.raise_for_status()
        return res.text


def parse_timeslots(html_string):
    snapshot_time = datetime.datetime.utcnow()
    tree = html.fromstring(html_string)

    records = []
    time_slots_set = set()
    for col in range(7):
        day_name = tree.xpath('//*[@id="ts_d{col}_hE_content"]/div[1]/b'.format(col=col))[0].text
        mmm, dd = tree.xpath('//*[@id="ts_d{col}_hE_content"]/div[2]'.format(col=col))[0].text.split(' ')

        for row in range(7):
            time_slot = tree.xpath('//*[@id="ts_d{col}_ts{row}_time"]'.format(col=col, row=row))
            if not time_slot:
                continue

            time_slot_text = time_slot[0].text.strip()
            if not time_slot_text:
                continue

            time_slots_set.add(time_slot_text)
            time_slot_is_available = 'tsSoldoutC' not in list(time_slot[0].classes)

            record = (snapshot_time, day_name, mmm, dd, time_slot_text, time_slot_is_available)
            records.append(record)

    df = pd.DataFrame(records, columns=['snapshot_ts', 'weekday', 'month', 'day', 'timeslot', 'available'])
    return df


def poll_and_alert(client, alerter, poll_interval):
    while True:
        logger.info("Polling Fresh Direct for updates...")
        timeslots_html = client.get_delivery_timeslots_html()
        df = parse_timeslots(timeslots_html)
        available_slots = df[lambda x: x.available][['weekday', 'month', 'day', 'timeslot']]

        if len(available_slots) > 0:
            message = 'The following time slots are available on Fresh Direct:\n\n'
            for record in available_slots.to_records():
                timeslot_text = ' '.join(list(record)[1:])
                logger.info(timeslot_text)
                message += timeslot_text + '\n'
            alerter.alert(message)

        logger.info('{} of {} delivery time slots available.'.format(len(available_slots), len(df)))
        time.sleep(poll_interval)


def run_main(poll_interval, alert_interval):
    """ Main entry point.

    Args
        poll_interval (int)
            Number of seconds to wait between refreshes.

        alert_interval (int)
            Number of seconds to wait between subsequent alerts.
    """
    start_time = datetime.datetime.now()

    client = FreshDirectClient(logger)
    client.authenticate(USERNAME, PASSWORD)

    alerter = TextAlerter(alert_interval)

    is_running = True
    while is_running:
        try:
            message = 'Fresh direct polling started.'
            alerter.alert(message)
            logger.info(message)
            poll_and_alert(client, alerter, poll_interval)
        except KeyboardInterrupt:
            logger.info('Stopped.')
            is_running = False
        except Exception as e:
            alerter.alert('fd-poller error: {}'.format(str(e)))
            stacktrace = ''.join(traceback.format_exception(*sys.exc_info()))
            logger.error(stacktrace)
        finally:
            end_time = datetime.datetime.now()
            run_time = end_time - start_time
            message = 'Fresh direct poller finished running.'
            alerter.alert(message)
            logger.info(message)


if __name__ == '__main__':
    run_main(poll_interval=15, alert_interval=60)
