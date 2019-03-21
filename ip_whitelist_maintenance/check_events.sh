#!/bin/bash

## This script is designed to be run via a cron job with the MAILTO variable set to generate an email when output occurs (an IP is added/removed/changed)

if [ -f "events_result.txt" ]; then
  mv events_result.txt events_result.txt.old
fi

dig +short events.pagerduty.com | sort > events_result.txt

if [ -f "events_result.txt.old" ]; then
  DIFF=$(diff -q 'events_result.txt.old' 'events_result.txt' > /dev/null)
  if [ $? -ne 0 ]; then
    echo "Changes detected! New IPs are:"
    cat events_result.txt
  fi
  rm events_result.txt.old
fi
