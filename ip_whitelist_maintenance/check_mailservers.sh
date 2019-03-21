#!/bin/bash

## This script is designed to be run via a cron job with the MAILTO variable set to generate an email when output occurs (an IP is added/removed/changed)

if [ -f "mailservers_result.txt" ]; then
  mv mailservers_result.txt mailservers_result.txt.old
fi

dig +short mx acme.pagerduty.com | sed 's/.$//g' | sed 's/^[0-9][0-9]* //g' | xargs dig +short | sort > mailservers_result.txt

if [ -f "mailservers_result.txt.old" ]; then
  DIFF=$(diff -q 'mailservers_result.txt.old' 'mailservers_result.txt' > /dev/null)
  if [ $? -ne 0 ]; then
    echo "Changes detected! New IPs are:"
    cat mailservers_result.txt
  fi
  rm mailservers_result.txt.old
fi
