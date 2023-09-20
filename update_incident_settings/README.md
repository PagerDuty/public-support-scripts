# PagerDuty Update Services
This script will update all the services provided in the CVS file to enable the following setting:

```
alert_creation: create_alerts_and_incidents
```


## Installation

First, have python3 installed. Then:

    python3 -m venv pdupdateservice              # create a virtual environment
    . pdupdateservice/bin/activate               # activate it
    pip install -r requirements.txt              # install dependencies. use pip3 if no pip

## Usage

    python3 update_services.py -k API_Token -f CSV_File

    optional arguments:
    -h, --help            show this help message and exit
    -k API, --api API     pagerduty api token
    -f FILE, --file FILE  csv filename with the services
                          Obfuscated ID. Each ID on a new line


    You can find or add a new API Token by following these instructions https://support.pagerduty.com/docs/generating-api-keys
    You can find Service Features to change under Request Schema https://api-reference.pagerduty.com/#!/Services/put_services_id
