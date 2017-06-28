# BaseBuild
ElumiPi builder 

This is a fork of the Rachel image for DEAN. Purpose is to provide a classroom environment for educational project in Tanzania and Kenia. Its purpose it to provide full Android tablet support without any direct internet connectivity.

Please visit http://www.dean.ngo for more information

# Functions
This version of the ElumiPi build supports:
- Secured WiFi access point
- Local DHCP, DNS
- Android application store 
- Web pages for management of the sytem and content management
- WiKiPedia alike functions
- Mail and calender functionality   
 
# Installation
1. Install a base RaspBian image on a SD card and insert it into the RaspberryPi.

2. Powerup the RaspberryPi and wait for the initial boot process to complete

3. Logon with user pi (password: raspberry)
  
4. Expand your microSD card partition
`sudo raspi-config`
`sudo reboot`

5. paste in the following command after reboot.
`curl -fsS https://raw.githubusercontent.com/rachelproject/rachelpiOS/master/installer.py | python`

Please note that this will change the 'pi' user's password to: elumipi

All default username and passwords will be elumipi/elumipi unless noted differently.

*NOTE1: This install is tested to work with `2016-05-27-raspbian-jessie` and is known to have problems with newer versions*

*NOTE2: for WIFI to work on the RaspberryPi 2 unit, you must have the WIFI USB dongle inserted
during installation so that the install script can configure it properly. RaspberryPi 3 models have on board WiFi and don't need a WIFI USB dongle.
Last updated : 2017/6/28

Original source : https://github.com/rachelproject/rachelpios