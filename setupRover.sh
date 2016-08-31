#!/bin/bash
sudo pigpiod
gpsd  /var/run/gpsd.sock /dev/ttyACM0
