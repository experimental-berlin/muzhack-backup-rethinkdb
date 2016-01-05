#!/usr/bin/env python3
"""Script to schedule RethinkDB backup."""
import asyncio
import subprocess
from datetime import datetime, date, timedelta
import sys
import logging
import contextlib


def _configure_logging():
    logging.getLogger().setLevel(logging.WARNING)
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

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
    now = datetime.now()
    _logger.info('Backing up at {}...'.format(
        now.strftime('%Y-%m-%d %H:%M:%S')))
    _logger.info('Backed up successfully!')
    _logger.debug('Scheduling next backup')
    _schedule_backup(loop)


def _main():
    with contextlib.closing(asyncio.get_event_loop()) as loop:
        _schedule_backup(loop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _logger.info('Interrupted')
            sys.exit(0)


if __name__ == '__main__':
    _main()
