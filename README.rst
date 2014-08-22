=====================
OpenStack API Crawler
=====================

How it works
------------

The script queries the *list* API resource of each supported OpenStack service (e.g. for Nova it queries list of instances, for Neutron - list of networks), gets the response code (which should be 200 in 100% of times :-) ) and calculates the time it takes for the server to respond to the *list* request. Then it writes the response code and the time into an XML file of the format Pingdom can consume.

Supported OpenStack services
----------------------------

* Keystone
* Nova
* Glance
* Cinder
* Neutron

Installation
------------

To install the dependencies run the following::

    ~$ sudo apt-get install python-pip
    ~$ sudo pip install -r requirements.txt

Running
-------

To run the script you will need username, password and tenant name of the OpenStack user you intend to use to query the APIs, as well as the endpoint of Identity API, aka Keystone. Currently the script supports Keyston API v2 only::

    ~$ python crawler.py --help
    usage: crawler.py [-h] -u USERNAME -p PASSWORD -t TENANT -i IDENTITY_URL -s
                      SERVICE

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Username of the account used for API check
      -p PASSWORD, --password PASSWORD
                            Password of the account used for API check
      -t TENANT, --tenant TENANT
                            Tenant name of the account used for API check
      -i IDENTITY_URL, --identity-url IDENTITY_URL
                            Identity service endpoint URL
      -s SERVICE, --service SERVICE
                            Service to check. Supported services are: keystone,
                            nova, glance, cinder, neutron, swift, heat

Run the script as follows::

    ~$ python crawler.py -u <crawler_user> -p <crawler_password> -t <crawler_tenant> -i <keystone_url> -s nova

The script will generate XML files for each service it checks in the following format::

    <?xml version="1.0"?>
    <pingdom_http_custom_check>
      <status>OK</status>
      <response_time>0.260</response_time>
    </pingdom_http_custom_check>


    <?xml version="1.0"?>
    <pingdom_http_custom_check>
      <status>DOWN</status>
      <response_time>0.260</response_time>
    </pingdom_http_custom_check>

XMLs are put into the same directory where the script is and are overwritten each time the script runs.

Timeouts
--------

Default timeout value for the API response is 28 seconds. If a timeout occurs the resulting XML will look like this::

    <?xml version="1.0"?>
    <pingdom_http_custom_check>
      <status>TIMEOUT</status>
      <response_time>0.000</response_time>
    </pingdom_http_custom_check>

Identity API failure
--------------------

Keystone has it's own check that is triggered by passing a :code:`-s keystone` option to the script. However, we also use Keystone in all the other checks to obtain a token to use in X-Auth-Token header. If obtaining a token fails for whatever reason the script generates a failure report for Keystone and exits immediately (i.e. it does not run the subsequent service check)

UI crawler
----------

There is a separate crawler that emulates login to UI (OpenStack Horizon) and calculates time it takes::

    ~$ python ui_crawler.py --help
    usage: ui_crawler.py [-h] -u USERNAME -p PASSWORD -l URL -r REGION

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            Username of the account used for API check
      -p PASSWORD, --password PASSWORD
                            Password of the account used for API check
      -l URL, --url URL     Control Panel URL

Run the script like this::

    ~$ python ui_crawler.py -u <crawler_user> -p <crawler_password> -l <horizon_login_page_url>

The script will generate the same kind of XML report as described previously.
