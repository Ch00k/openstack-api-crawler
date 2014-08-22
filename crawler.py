import json
import argparse
import time

import requests


HEADERS = {'Accept': 'application/json', 'Content-type': 'application/json'}

XML = '<?xml version="1.0"?>\n' \
      '<pingdom_http_custom_check>\n' \
      '  <status>{}</status>\n' \
      '  <response_time>{}</response_time>\n' \
      '</pingdom_http_custom_check>'

TIMEOUT = 28


def service_request(service_endpoint, method, path, headers, body=None):
    start = time.time()
    try:
        if body:
            resp = getattr(requests, method)('{}/{}'.format(service_endpoint,
                                                            path),
                                             json.dumps(body), headers=headers,
                                             timeout=TIMEOUT)
        else:
            resp = getattr(requests, method)('{}/{}'.format(service_endpoint,
                                                            path),
                                             headers=headers, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return {'status': 'TIMEOUT', 'time': 0}

    end = time.time()
    try:
        resp_body = resp.json()
    except ValueError:
        resp_body = resp.text
    if resp.status_code < 400:
        status = 'OK'
        time_taken = (end - start) * 1000
    else:
        status = 'DOWN'
        time_taken = 0
    return {'status': status, 'headers': resp.headers,
            'body': resp_body, 'time': time_taken}


def auth_headers(token):
    headers = HEADERS
    headers['X-Auth-Token'] = token
    return headers


def get_auth(endpoint, usermame, password, tenant_name):
    body = {
        'auth': {
            'tenantName': tenant_name,
            'passwordCredentials': {
                'username': usermame,
                'password': password
            }
        }
    }
    return service_request(endpoint, 'post', '/tokens', HEADERS, body)


def get_endpoint(auth, service_name):
    for service in auth['body']['access']['serviceCatalog']:
        if service['name'] == service_name:
            return service['endpoints'][0]['publicURL']


def list_instances(endpoint, token):
    return service_request(endpoint, 'get', '/servers', auth_headers(token))


def list_images(endpoint, token):
    return service_request(endpoint, 'get', '/v2/images', auth_headers(token))


def list_volumes(endpoint, token):
    return service_request(endpoint, 'get', '/volumes', auth_headers(token))


def list_networks(endpoint, token):
    return service_request(endpoint, 'get', '/v2.0/networks',
                           auth_headers(token))


def list_containers(endpoint, token):
    return service_request(endpoint, 'get', '', auth_headers(token))


def list_stacks(endpoint, token):
    return service_request(endpoint, 'get', '/stacks', auth_headers(token))


keystone_check = get_auth
nova_check = list_instances
glance_check = list_images
cinder_check = list_volumes
neutron_check = list_networks
swift_check = list_containers
heat_check = list_stacks


def generate_xml(status, response_time):
    return XML.format(status, '%.3f' % response_time)


def write_report(service, report):
    with open('{}.xml'.format(service), 'w') as f:
        f.write(report)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True,
                        help='Username of the account used for API check')
    parser.add_argument('-p', '--password', required=True,
                        help='Password of the account used for API check')
    parser.add_argument('-t', '--tenant', required=True,
                        help='Tenant name of the account used for API check')
    parser.add_argument('-i', '--identity-url', required=True,
                        help='Identity service endpoint URL')
    parser.add_argument('-s', '--service', required=True,
                        help='Service to check. Supported services are: '
                             'keystone, nova, glance, '
                             'cinder, neutron, swift, heat, all')
    args = parser.parse_args()

    # Try to authenticate
    auth = get_auth(args.identity_url, args.username, args.password,
                    args.tenant)

    # If we did not manage to authenticate successfully, generate a failure
    # report for Keystone and exit immediately
    if auth['status'] == 'DOWN' or auth['status'] == 'TIMEOUT':
        keystone_report = generate_xml('DOWN', auth['time'])
        if args.service == 'all':
            write_report('all', keystone_report)
        else:
            write_report('keystone', keystone_report)
            write_report(args.service, keystone_report)
        exit()

    token = auth['body']['access']['token']['id']
    if args.service == 'all':
        times = []
        for service in ('nova', 'glance', 'cinder',
                        'neutron'):
            endpoint = get_endpoint(auth, service)
            service_response = globals()['{}_check'.format(service)](endpoint,
                                                                     token)
            if service_response['status'] == 'DOWN':
                report = generate_xml('DOWN', service_response['time'])
                write_report('all', report)
                exit()
            elif service_response['status'] == 'TIMEOUT':
                report = generate_xml('TIMEOUT', service_response['time'])
                write_report('all', report)
                exit()
            times.append(service_response['time'])
        time_avg = sum(times) / len(times)
        report = generate_xml('OK', time_avg)
        write_report('all', report)
    else:
        endpoint = get_endpoint(auth, args.service)
        if args.service == 'keystone':
            service_response = \
                globals()['{}_check'.format(args.service)](endpoint,
                                                           args.username,
                                                           args.password,
                                                           args.tenant)
        else:
            service_response = \
                globals()['{}_check'.format(args.service)](endpoint, token)
        report = generate_xml(service_response['status'],
                              service_response['time'])
        write_report(args.service, report)


if __name__ == '__main__':
    main()
