import requests
import argparse
import json

def set_headers(key):
    ''' Set headers for API calls.'''
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': f'Token token={key}'
        }
    return headers

def get_schedule(headers,id):
    ''' Get schedule and return the schedule with layers in reverse order.'''
    url = f'https://api.pagerduty.com/schedules/{id}'
    response = requests.get(url, headers=headers)
    data = response.json()
    print(f'Getting schedule {id}')
    if response.status_code != 200:
        print(response.status_code, data['error']['message'])
        return None
    print(f'Schedule {id} retrieved')
    reversed_layers = []
    layers = data['schedule']['schedule_layers']
    for layer in layers:
        reversed_layers.insert(0, layer)
    data['schedule']['schedule_layers'] = reversed_layers
    return json.dumps(data)

def write_to_file(payload, id):
    ''' Write schedule to file '''
    with open(f'{id}.json', 'w') as f:
        print('Writing to file')
        f.write(payload)

def main():
    ap = argparse.ArgumentParser(
        description='Get schedules and reverse the schedule layers for updating.'
    )
    ap.add_argument('-k',
        '--key',
        required=True,
        help='REST API key'
    )
    ap.add_argument('-i',
        '--ids',
        required=True,
        nargs='+',
        help='Schedule IDs'
    )
    args = ap.parse_args()
    for id in args.ids:
        payload = get_schedule(set_headers(args.key), id)
        if payload is not None:
            write_to_file(payload, id)

if __name__ == '__main__':
    main()
