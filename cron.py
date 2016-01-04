import subprocess
import os


crontab_filename = '/etc/cron.d/crontab'
with open(crontab_filename, 'rb') as f:
    crontab = f.readlines()
for k in [k for k in os.environ if k.startswith('CRONVAR_')]:
    cron_vars.append((k, os.environ[k],))

crontab = cron_vars + ['',] + crontab
with open(crontab_filename, 'wb') as f:
    f.write('\n'.join(crontab))
subprocess.check_call(['crond', '-L', '15',])
