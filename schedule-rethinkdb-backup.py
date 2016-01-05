#!/usr/bin/env python3
"""Script to schedule RethinkDB backup."""
import asyncio
import subprocess
from datetime import datetime, date, timedelta
import sys
import logging
import contextlib
import time
import datadog.api

from backup_rethinkdb import backup_rethinkdb, get_environment_value


def _configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    logger = logging.getLogger('app')
    log_level = logging.DEBUG
    logger.setLevel(log_level)
    logging.getLogger('backup_rethinkdb').setLevel(log_level)

    return logger


_logger = _configure_logging()


def _schedule_backup(loop):
    hour = 18

    now = datetime.now()
    today = date.today()
    desired_time = datetime(today.year, today.month, today.day, hour=hour)
    if now.hour >= hour:
        _logger.debug(
            'Delaying until {} next day since we\'re already at {}'.format(
                hour, now.hour))
        desired_time = desired_time + timedelta(days=1)
    else:
        _logger.debug('Delaying until {} same day'.format(hour))
    desired_seconds = (desired_time - now).seconds

    _logger.debug(
        'Delaying for {} second(s) before backup'.format(desired_seconds))
    loop.call_later(desired_seconds, _backup, loop)


def _backup(loop):
    """Perform actual backup."""
    def post_datadog_event(title, text, alert_type):
        datadog.api.Event.create(title=title, text=text, alert_type=alert_type)


    success = False
    error = None
    for attempt in range(1, 4):
        now = datetime.now()
        _logger.info('Backup attempt #{} at {}...'.format(
            attempt, now.strftime('%Y-%m-%d %H:%M:%S')))
        try:
            backup_rethinkdb(
                get_environment_value('RETHINKDB_HOST'),
                get_environment_value('RETHINKDB_BACKUP_S3_BUCKET'), True)
        except Exception as err:
            error = err
            import traceback
            traceback.print_exc()
            _logger.warn('Backup attempt #{} failed'.format(attempt))
            time.sleep(1)
        else:
            success = True
            break
    if success:
        _logger.info('Backed up successfully!')
        post_datadog_event(
            'RethinkDB Backup Success',
            'RethinkDB was successfully backed up', 'success')
    else:
        _logger.error('Failed to back up!')
        post_datadog_event(
            'RethinkDB Backup Failure',
            'Failed to back up RethinkDB: {}'.format(error), 'error')

    _logger.debug('Scheduling next backup')
    _schedule_backup(loop)


def _main():
    datadog.initialize(
        api_key=get_environment_value('DATADOG_API_KEY'),
        app_key=get_environment_value('DATADOG_APP_KEY')
    )

    with contextlib.closing(asyncio.get_event_loop()) as loop:
        _schedule_backup(loop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _logger.info('Interrupted')
            sys.exit(0)


if __name__ == '__main__':
    _main()
