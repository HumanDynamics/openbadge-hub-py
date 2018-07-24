#!/bin/sh
echo "populating necessary cron env vars"
printenv | grep "TZ\|AWS\|HOSTNAME" >> /etc/environment
echo "creating crontab"
crontab -l 2>/dev/null | echo "$CRON_SCHEDULE /backup.sh > /tmp/testout 2>&1 \n" | crontab -
echo "verify crontab:"
crontab -l
echo "starting cron"
cron -f
