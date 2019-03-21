#!/bin/bash

## This script is designed to be run via a cron job with the MAILTO variable set to generate an email when output occurs (an IP is added/removed/changed)

if [ -f "webhooks_result.txt" ]; then
  mv webhooks_result.txt webhooks_result.txt.old
fi

for ip in $(curl https://app.pagerduty.com/webhook_ips |sed 's/","/ /g;s/\["//g;s/"\]//g'); do
    echo $ip;
done | sort > webhooks_result.txt

if [ -f "webhooks_result.txt.old" ]; then
  DIFF=$(diff -q 'webhooks_result.txt.old' 'webhooks_result.txt' > /dev/null)
  if [ $? -ne 0 ]; then
    echo "Changes detected! New IPs are:"
    cat webhooks_result.txt
  fi
  rm webhooks_result.txt.old
fi
