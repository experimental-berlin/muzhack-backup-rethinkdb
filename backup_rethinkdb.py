#!/usr/bin/env python3
"""Script to back up RethinkDB either locally or remotely to S3."""
import subprocess
import argparse
import os.path
import sys
from datetime import datetime
import boto3
import logging


_logger = logging.getLogger('backup_rethinkdb')


def _error(msg):
    _logger.error(msg)
    sys.exit(1)


def get_environment_value(key):
    value = (os.environ.get(key) or '').strip()
    if not value:
        _error('You must define environment value \'{}\''.format(key))
    return value


def backup_rethinkdb(rethinkdb_host, s3_bucket, remove_local_backup):
    date_time_str = datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
    filename = 'rethinkdb-dump-{}.tar.gz'.format(date_time_str)
    if os.path.exists(filename):
        os.remove(filename)

    command = ['rethinkdb', 'dump', '-c', rethinkdb_host, '-f', filename]
    auth_key = os.environ.get('RETHINKDB_AUTH_KEY')
    if auth_key:
        _logger.info('Using RethinkDB authentication key')
        command.extend(['-a', auth_key, ])
    else:
        _logger.info('Not using any RethinkDB authentication key')
    _logger.info('Backing up database at {} to {}...'.format(rethinkdb_host, filename))
    subprocess.check_call(command, stdout=subprocess.PIPE)
    _logger.debug('Finished making backup file')

    if s3_bucket:
        _logger.info('Uploading \'{}\' to S3 bucket \'{}\'...'.format(filename,
              s3_bucket))
        access_key_id = get_environment_value('AWS_ACCESS_KEY_ID')
        secret = get_environment_value('AWS_SECRET_ACCESS_KEY')
        _logger.debug('Using AWS ACCESS KEY ID {}'.format(access_key_id)) 
        s3_client = boto3.client('s3', region_name='eu-central-1',
                                 aws_access_key_id=access_key_id,
                                 aws_secret_access_key=secret)
        s3_client.upload_file(filename, s3_bucket, filename)
        # TODO: Implement deleting backups that are older than 100 days

    if remove_local_backup:
        os.remove(filename)

    _logger.info('Success!')


def _main():
    logging.getLogger().setLevel(logging.WARNING)
    _logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

    parser = argparse.ArgumentParser(
        description='Back up local RethinkDB instance')
    parser.add_argument('--host', default='localhost', help='Specify RethinkDB host')
    parser.add_argument('--s3-bucket', default=None, help='Specify S3 bucket')
    parser.add_argument('--remove', action='store_true', default=False,
                        help='Remove backup archive when done?')
    args = parser.parse_args()

    backup_rethinkdb(host, args.s3_bucket, args.remove)


if __name__ == '__main__':
    _main()
