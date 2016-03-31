#!/usr/bin/env python3
from docker import Client
from selenium import webdriver
import docker.errors
import pytest
import time

# address of docker0 interface on the host machine
# all ports exposed in containers running are
# mapped to this address
docker_host_ip = '172.17.0.1'


@pytest.fixture(scope='module')
def attach_to_smoothie():
    """Find smoothie-simulator container.
    When OT.one is started from bootstrap container with
    docker-compose, it creates home_smoothie_1 container
    which receives G-code from the driver and sends it to stdout
    Returns instance of docker cli and container id of home_smoothie_1.
    """
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
    """Starts selenium container, connects to it and returns a driver"""
    cli = Client(base_url='unix://var/run/docker.sock')
    try:
        cli.remove_container('selenium', force=True)
    except docker.errors.NotFound:
        print("Couldn't remove selenium container: not found")
    # docker-py doesn't automatically pull a container
    # you should run docker pull selenium/standalone-chrome-debug
    # before running the test
    # Use selenium/standalone-chrome-debug with port 5900 mapped
    # to view test session using VNC
    # use selenium/standalone-chrome for normal operations
    cli.create_container(image='selenium/standalone-chrome-debug',
                         name='selenium',
                         ports=[4444, 5900],
                         host_config=cli.create_host_config(
                            port_bindings={
                                4444: ('127.0.0.1', 4444),
                                5900: 5900
                            },
                            extra_hosts={
                                 'otone.local': docker_host_ip
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
    """Click ALL, X, Y, Z and listen to corresponding G-code commands
    coming from smoothie simulator
    """
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
