#!/usr/bin/env python3.5
from __future__ import print_function
from docker import Client
from selenium import webdriver
import docker.errors
import itertools
import logging
import pytest
import time


def tail_log_lines(logs):
    while True:
        yield ''.join(itertools.takewhile(lambda c: c != '\n', logs))


@pytest.fixture(scope='module')
def attach_to_smoothie():
    cli = Client(base_url='unix://var/run/docker.sock')
    # cli.containers() is expected to return a list with only one container
    # we can unpack it into a variable as a tuple with one element
    # ex: a, = tuple([1])
    c, = filter(
        lambda a: '/home_smoothie_1' in a['Names'],
        cli.containers())
    smoothie_id = c['Id']

    print('Smoothie container ID: {0}'.format(smoothie_id))
    return cli, smoothie_id


@pytest.fixture(scope='module')
def start_selenium(request):
    cli = Client(base_url='unix://var/run/docker.sock')
    try:
        cli.remove_container('selenium', force=True)
    except docker.errors.NotFound:
        print('Couldn''t remove selenium container: not found')
    cli.create_container(image='selenium/standalone-chrome-debug',
                         name='selenium',
                         ports=[4444, 5900],
                         host_config=cli.create_host_config(
                            port_bindings={
                                4444: ('127.0.0.1', 4444),
                                5900: 5900
                            },
                            extra_hosts={
                                 'otone.local': '172.17.0.1'
                            }
                            )
                         )
    cli.start('selenium')
    time.sleep(5)
    driver = webdriver.Remote(
        'http://localhost:4444/wd/hub',
        desired_capabilities=webdriver.DesiredCapabilities.CHROME)

    def fin():
        driver.quit()
        cli.stop('selenium')
        cli.remove_container(container='selenium')
    request.addfinalizer(fin)
    return driver


def test_home(attach_to_smoothie, start_selenium):
    cli, smoothie_id = attach_to_smoothie
    driver = start_selenium
    driver.get('http://otone.local:5000')
    time.sleep(5)
    test_set = {
        'ALL': b'G28\r\n',
        'X': b'G28 X\r\n',
        'Y': b'G28 Y\r\n',
        'Z': b'G28 Z\r\n'
    }

    def logs():
        return cli.logs(smoothie_id, stdout=True).splitlines()

    for key, value in test_set.items():
        log = len(logs())
        driver.find_element_by_link_text(key).click()
        time.sleep(1)
        res, = logs()[log:]
        assert eval(res) == value
