#!/bin/bash

# Note: this can mess up the Ethernet controller.

echo Disabling USB
echo 0 > /sys/devices/platform/soc/3f980000.usb/buspower
cat /sys/devices/platform/soc/3f980000.usb/buspower

sleep 5

echo Enabling USB
echo 1 > /sys/devices/platform/soc/3f980000.usb/buspower
cat /sys/devices/platform/soc/3f980000.usb/buspower

echo Done.
