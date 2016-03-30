# Overview
Testing is done using Selenium and Chrome Driver running in a container. These tests make a use of smoothie-simulator container which OKs every command received back to the driver and outputs the command to stdout. Connecting to this contianer log output from the test, gives us access to the stream of commands going to the smoothie. The main goal of tests is to ensure that actions on a frontend result in correct commands going to smoothie.

# Installation
1. Download and install OT.one containers from otone_docker
2. Pull this repository
3. Build smoothie simulator: ```docker build -t smoothie-simulator .```
4. Run device software overriding docker-compose.yml to add smoothie-simulator into the mix: ```docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd)/conf/docker-compose.yml:/home/docker-compose.yml bootstrap```
5. Install test requirements ```pip3 install -r requirements.txt```
6. Run tests: ```py.test -s smote_tests.py```