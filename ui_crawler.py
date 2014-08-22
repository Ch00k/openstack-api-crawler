import argparse
import re
import time

import requests


XML = '<?xml version="1.0"?>\n' \
      '<pingdom_http_custom_check>\n' \
      '  <status>{}</status>\n' \
      '  <response_time>{}</response_time>\n' \
      '</pingdom_http_custom_check>'

TIMEOUT = 28


def login(url, username, password):
    start = time.time()

    session = requests.Session()
    try:
        sess_resp = session.get(url, timeout=TIMEOUT)
        real_url = sess_resp.url
        if sess_resp.status_code >= 400:
            return {'status': 'DOWN', 'time': 0}

        for line in sess_resp.text.splitlines():
            if 'id_region' in line:
                match = re.match('^\s+<input.*value="(http.*)" \/>$', line)
                if match is None:
                    exit('Could not find region in page source')
                region = match.group(1)

        csrftoken = session.cookies['csrftoken']
        payload = {'username': username, 'password': password,
                   'csrfmiddlewaretoken': csrftoken, 'region': region}

        resp = session.post(real_url + '/auth/login/',
                            data=payload, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return {'status': 'TIMEOUT', 'time': 0}

    end = time.time()

    if 'Logged in as: {}'.format(username) in resp.text:
        status = 'OK'
        time_taken = (end - start) * 1000
    else:
        status = 'DOWN'
        time_taken = 0
    return {'status': status, 'time': time_taken}


def generate_xml(status, response_time):
    return XML.format(status, '%.3f' % response_time)


def write_report(report):
    with open('{}.xml'.format('ui'), 'w') as f:
        f.write(report)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True,
                        help='Username of the account used for API check')
    parser.add_argument('-p', '--password', required=True,
                        help='Password of the account used for API check')
    parser.add_argument('-l', '--url', required=True,
                        help='Control Panel URL')
    args = parser.parse_args()

    result = login(args.url, args.username, args.password)
    report = generate_xml(result['status'], result['time'])
    write_report(report)


if __name__ == '__main__':
    main()
