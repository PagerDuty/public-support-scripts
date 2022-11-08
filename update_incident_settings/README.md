# PDupdateServices

Update PagerDuty Services contained within a user provided csv or which do not match the "change" to be made. Default functionality is to enable creating Alerts and Notifications, but any Service Features found in Request Schema https://api-reference.pagerduty.com/#!/Services/put_services_id can be changed (see example under Usage, -c argument). Contact pkennard@pagerduty.com with any questions.

## Installation

First, have python 3 installed. Then:

    python3 -m venv venv              # create a virtual environment
    . venv/bin/activate               # activate it
    pip install -r requirements.txt   # install dependencies. use pip3 if no pip

## Usage

    ./updateService.py -a API_Token -f CSV_File -o service -c Change_to_Make > output.txt

    optional arguments:
    -h, --help            show this help message and exit
    -a API, --api API     pagerduty api token
    -f FILE, --file FILE  csv filename with Services Name and Services
                          Obfuscated ID fields
    -o Object, --object   The PD object to be modified, defaults to Service, eg
                          'service' or 'escalation_policy'
    -c CHANGE, --change CHANGE
                          change to service 'feature:setting', eg
                          'alert_creation:create_incidents' or
                          'acknowledgement_timeout:10'

    API_Token can be hardcoded to line 23 of updateService.py
    Service IDs can be hardcoded to line 26 of updateService.py instead of CSV_File
    Change_to_Make is hardcoded to 'alert_creation:create_alerts_and_incidents'
      but can be overridden with -c argument to something like 'acknowledgement_timeout:1'

    You can find or add a new API Token by following these instructions https://support.pagerduty.com/docs/generating-api-keys
    You can find Service Features to change under Request Schema https://api-reference.pagerduty.com/#!/Services/put_services_id 
    
## Sample Output
    ./updateService.py -a API_Token -c 'acknowledgement_timeout:100'

    Current service settings:
    PBUDURC : Customer Support Service -> acknowledgement_timeout = None
    PDPL21H : Shopping API -> acknowledgement_timeout = None
    P3KP8PJ : Shopping Cart - App Server -> acknowledgement_timeout = None
    P7WA929 : Shopping Cart - Database -> acknowledgement_timeout = None
    PR1POT7 : Test Service -> acknowledgement_timeout = None
    
    Making changes to these services:
    PBUDURC -> Customer Support Service
    PDPL21H -> Shopping API
    P3KP8PJ -> Shopping Cart - App Server
    P7WA929 -> Shopping Cart - Database
    PR1POT7 -> Test Service

    Continue? y


    Updating service id: PBUDURC -> Customer Support Service
    Status Code: 200
    Changed ['Customer Support Service'] acknowledgement_timeout to [100]
    -----------------------------------------------
