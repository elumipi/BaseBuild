#!/usr/bin/env python
#=========================================================================================================
#    Original script from Rachel
#    Modified for DEAN ElimuPI
#
#    Date        |By     | Desxcription
# ---------------+-------+----------------------------------------
#    2017-Apr-3  | PVe   | Initial fork 
#    2017-Jun-28 | PVe   | Updated base configuration
#    2018-Feb-28 | PVe   | Added more modular design
#    2018-Mar-15 | PBo   | Bug fixes
#    2018-Mar-26 | PVe   | Updated files handling
#=========================================================================================================
import sys
import os
import subprocess
import argparse
import shutil
import urllib
import argparse
import platform

#================================
# Settings for build
#================================
base_hostname       = "elimupi"                                     # Defaul hostname
base_user           = "pi"                                          # Default user name to use
base_passwd         = "elimupi"                                     # Default password for all services
base_ip_range       = "10.11.0"                                     # IP range (/24) for the WiFI interface
base_ip             = "10.11.0.1"                                   # Default IP address for the WiFi interface
base_build          = "ELIMUPI-20180326"                            # Date of build
base_git            = "https://github.com/elumipi/BaseBuild.git"    # Git location

installed_modules   = [];                   # Installed modules

#================================
# Command line arguments
#================================
argparser = argparse.ArgumentParser()
argparser.add_argument( "--khan-academy",
                       choices=["none", "ka-lite"],
                       default="ka-lite",
                       help="Select Khan Academy package to install (default = \"ka-lite\")")
argparser.add_argument("--no-wifi",
                       dest="install_wifi",
                       action="store_false",
                       help="Do not configure local wifi hotspot.")
args = argparser.parse_args()

#################################
# Installer functions
#################################

#================================
#    USB Content management 
#================================
def USB_automount():
    print "USB automount handling and web menu"
    return True

#================================
# Kahn Acadamy content (educational)
#================================
def install_kalite():
    sudo("apt-get install -y python-pip") or die("Unable to install pip.")
    sudo("pip install --no-cache-dir ka-lite-static") or die("Unable to install KA-Lite")   
    
    sudo("kalite manage setup --username=" + base_passwd + " --password=" + base_passwd + " --hostname=" + base_hostname + " --description=" + base_hostname) ### PBo 20180315 Removed unwanted confirmation  
    sudo("mkdir -p /etc/ka-lite") or die("Unable to create /etc/ka-lite configuration directory.")
    cp("files/init-functions", "/etc/default/ka-lite") or die("Unable to install KA-Lite configuration script.")
    cp("files/init-service", "/etc/init.d/ka-lite") or die("Unable to install KA-Lite service.")
    sudo("chmod +x /etc/init.d/ka-lite") or die("Unable to set permissions on KA-Lite service.")
    sudo("sh -c 'echo root >/etc/ka-lite/username'") or die("Unable to configure the userid of the KA-Lite process.")
    if exists("/etc/systemd"):
        sudo("mkdir -p /etc/systemd/system/ka-lite.service.d") or die("Unable to create KA-Lite service options directory.")
        cp("files/init-systemd-conf", "/etc/systemd/system/ka-lite.service.d/10-extend-timeout.conf") or die("Unable to increase KA-Lite service startup timeout.")
    sudo("update-rc.d ka-lite defaults") or die("Unable to register the KA-Lite service.")

    ##  PBo 20180313-06 Start with systemctl < sudo("service ka-lite start") or die("Unable to start the KA-Lite service.")
    sudo("systemctl restart ka-lite") or die("Unable to start the KA-Lite service.")
    sudo("sh -c '/usr/local/bin/kalite --version > /etc/kalite-version'") or die("Unable to record kalite version")
    return True

#================================
#    KIWIX WiKi Offline 
#================================
def install_kiwix():
    sudo("mkdir -p /var/kiwix/bin") or die("Unable to make create kiwix directories")
    kiwix_version = "0.9"
    sudo("sh -c 'wget -O - http://downloads.sourceforge.net/project/kiwix/"+kiwix_version+"/kiwix-server-"+kiwix_version+"-linux-armv5tejl.tar.bz2 | tar xj -C /var/kiwix/bin'") or die("Unable to download kiwix-server")
    # the reason we have a sample zim file is so that if no modules
    # are installed you can still tell that kiwix is running
    cp("files/kiwix-sample.zim", "/var/kiwix/sample.zim") or die("Unable to install kiwix sample zim")
    cp("files/kiwix-sample-library.xml", "/var/kiwix/sample-library.xml") or die("Unable to install kiwix sample library")
    cp("files/dean-kiwix-start.pl", "/var/kiwix/bin/dean-kiwix-start.pl") or die("Unable to copy dean-kiwix-start wrapper")
    sudo("chmod +x /var/kiwix/bin/dean-kiwix-start.pl") or die("Unable to set permissions on dean-kiwix-start wrapper")
    cp("files/init-kiwix-service", "/etc/init.d/kiwix") or die("Unable to install kiwix service")
    sudo("chmod +x /etc/init.d/kiwix") or die("Unable to set permissions on kiwix service.")
    sudo("update-rc.d kiwix defaults") or die("Unable to register the kiwix service.")
    sudo("sed -i 's/dean-kiwix-start.pl/dean-kiwix-start.pl/g' /etc/init.d/kiwix") or die("Unable to change /etc/init.d/kiwix")    ## PBo 20180312-07
    sudo("systemctl daemon-reload") or die("systemctl daemon reload failed")
    sudo("systemctl start kiwix") or die("Unable to start the kiwix service")

    ## PBo 20180312-07 sudo("service kiwix start") or die("Unable to start the kiwix service.")
    sudo("sh -c 'echo "+kiwix_version+" >/etc/kiwix-version'") or die("Unable to record kiwix version.")
    return True

#================================
#    Citadel MAIL solutiuon 
#================================
def install_citadel():
    print "Installing CitaDel mail solution"
    ## PBo 20180313 Install with -y < sudo("sudo apt-get install citadel-suite")
    sudo("sudo apt-get install -y citadel-suite")
    # Installation steps
    return True

#================================
# WordPress installer
#================================
def install_wordpress():
    if installed_modules.index('apache'):
        sudo("cd /var/www/html/")   # check if this is OK!!!!!!
        sudo("rm *")
        # sudo("wget http://wordpress.org/latest.tar.gz")
        sudo("sh -c 'wget -O - http://wordpress.org/latest.tar.gz'") or die("Unable to download kiwix-server")  
        sudo("tar xzf latest.tar.gz")
        sudo("mv wordpress/* .")
        sudo("rm -rf wordpress latest.tar.gz")
        sudo("chown -R www-data: .")
        # Setup database for WordPress
        sudo("mysql --user=" + base_user + " --password=" + base_passwd + " <files/create_wordpress.sql" )

        # Add caching for performance reasons
        installed_modules.extend(['wordpress'])
        return True
    else:
        return False

#================================
# PHP Installation
#================================
def install_php():
    print "========================================="
    print "Installing PHP"
    print "========================================="
    sudo("sudo apt-get -y install libxml2-dev") or die("Unable to install libXml2.")
    sudo("sudo apt-get -y install php7.0") or die("Unable to install php7.0.")
    sudo("sudo apt-get -y install php7.0-common") or die("Unable to install php7.0-common.")
    sudo("sudo apt-get -y install php7.0-dev ") or die("Unable to install php7.0-dev.")
    sudo("sudo apt-get -y install php-pear ") or die("Unable to install php-pear.")
    #mysql related modules
    sudo("sudo apt-get -y install php7.0-mysql sqlite3 php7.0-sqlite3") or die("Unable to install web platform.")
    installed_modules.extend(['php'])
    return True

#================================
# MySQL installation
#================================                     
def install_mysql():
    print "========================================="
    print "Installing MySQL platform"
    print "========================================="
    sudo("sudo apt-get -y install mysql-server") or die("Unable to install mysql server.")
    sudo("sudo apt-get -y install mysql-client") or die("Unable to install mysql client.")
    sudo("sudo echo mysql-server mysql-server/root_password password " + base_passwd +  " | sudo debconf-set-selections") or die("Unable to set default MySQL password.")
    sudo("sudo echo mysql-server mysql-server/root_password_again password " + base_passwd + " | sudo debconf-set-selections") or die("Unable to set default MySQL password (again).")
    installed_modules.extend(['mysql'])

    ## PBo 20180313-02 From install_apache
    cp("files/my.cnf", "/etc/mysql/my.cnf") or die("Unable to copy MySQL server configuration.")

    return True

#================================
# Install sqlite
#================================
def install_sqlite():
    ## PBo 20180313-04<    sudo("sudo apt-get -y sqlite3") or die("Unable to install sqlite3")
    sudo("sudo apt-get install -y sqlite3") or die("Unable to install sqlite3")
    return True 

#================================
# Apache installer
#================================
def install_apache():
    print "========================================="
    print "Installing Apache platform run #3 (PBo) "
    print "========================================="
    sudo("sudo apt-get -y install apache2 libxml2-dev") or die("Unable to install Apache.")
    sudo("sudo apt-get -y install libapache2-mod-php7.0") or die("Unable to install libapache2-mod-php7.0.")
    sudo("sudo apt-get -y install php7.0-cgi") or die("Unable to install php7.0-cgi.")
    sudo("yes '' | sudo pecl install -f stem") or die("Unable to install php stemmer")
    # Install stemming
    sudo("wget https://pecl.php.net/get/stem-1.5.1.tgz") or die("Unable to download kiwix-server")
    sudo("tar -xvf stem-1.5.1.tgz -C stem")
    sudo("wget -O patch.file https://bugs.php.net/patch-display.php?bug_id=71631&patch=update-for-php7&revision=1456823887&download=1")
    sudo("patch -p1 < patch.file")
    sudo("md5sum stem.c")
    ## check package.xml <file md5sum="ee8c88ec8b8f06f686fcebdffe744b08" name="stem.c" role="src" />
    # add the corrected checksum
    sudo("sed -i \"s/<file md5sum=\\\"*\\\" name=\\\"stem.c\\\" role=\\\"src\\\" \\/>/<file md5sum=\\\"ee8c88ec8b8f06f686fcebdffe744b08\\\" name=\\\"stem.c\\\" role=\\\"src\\\" \\/>/\" p.xml")
    sudo("sh -c 'echo \'extension=stem.so\' >> /etc/php/7.0/cli/php.ini'") or die("Unable to install stemmer CLI config")
    sudo("sh -c 'echo \'extension=stem.so\' >> /etc/php/7.0/apache2/php.ini'") or die("Unable to install stemmer Apache config")
    sudo("sh -c 'sed -i \"s/upload_max_filesize *= *.*/upload_max_filesize = 512M/\" /etc/php/7.0/apache2/php.ini'") or die("Unable to increase upload_max_filesize in apache2/php.ini")
    sudo("sh -c 'sed -i \"s/post_max_size *= *.*/post_max_size = 512M/\" /etc/php/7.0/apache2/php.ini'") or die("Unable to increase post_max_size in apache2/php.ini")
    sudo("service apache2 stop") or die("Unable to stop Apache2.")
    #cp("files/apache2.conf", "/etc/apache2/apache2.conf") or die("Unable to copy Apache2.conf")
    cp("files/default", "/etc/apache2/sites-available/contentshell.conf") or die("Unable to set default Apache site.")
    sudo("a2dissite 000-default") or die("Unable to disable default Apache site.")
    sudo("a2ensite contentshell.conf") or die("Unable to enable contenthell Apache site.")
    ## PBo 20180313-02 No /etc/mysql folder here, moved to install_mysqql<    cp("files/my.cnf", "/etc/mysql/my.cnf") or die("Unable to copy MySQL server configuration.")
    sudo("a2enmod php7.0 proxy proxy_html rewrite") or die("Unable to enable Apache2 dependency modules.")
    if exists("/etc/apache2/mods-available/xml2enc.load"):
        sudo("a2enmod xml2enc") or die("Unable to enable Apache2 xml2enc module.")
    sudo("service apache2 restart") or die("Unable to restart Apache2.")
    installed_modules.extend(['apache'])
    return True 

#================================
# Setup WiFi
#================================
def install_wifi():
    sudo("apt-get -y install hostapd udhcpd") or die("Unable install hostapd and udhcpd.")
    # PVe correctly write the udhcp config file
    # cp("files/udhcpd.conf", "/etc/udhcpd.conf") or die("Unable to copy uDHCPd configuration (udhcpd.conf)")
    
    sudo("sh -c 'echo \"# Sample udhcpd configuration file (/etc/udhcpd.conf)\" >/etc/udhcpd.conf'")                                    or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The start and end of the IP lease block\" >>/etc/udhcpd.conf'")                                               or die("Unable to write to udhcpd.conf") 
    sudo("sh -c 'echo \"start        " + base_ip_range + ".11    #default: 192.168.0.20\" >>/etc/udhcpd.conf'")                         or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"end        " + base_ip_range + ".199    #default: 192.168.0.254\" >>/etc/udhcpd.conf'")                         or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The interface that udhcpd will use\" >>/etc/udhcpd.conf'")                                                    or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"interface    wlan0        #default: eth0\" >>/etc/udhcpd.conf'")                                                or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#     \" >>/etc/udhcpd.conf'")                                                                                  or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The maximim number of leases (includes addressesd reserved\" >>/etc/udhcpd.conf'")                            or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# by OFFER's, DECLINE's, and ARP conficts\" >>/etc/udhcpd.conf'")                                               or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#     \" >>/etc/udhcpd.conf'")                                                                                  or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#     #max_leases    254        #default: 254\" >>/etc/udhcpd.conf'")                                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#     \" >>/etc/udhcpd.conf'")                                                                                  or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#     \" >>/etc/udhcpd.conf'")                                                                                  or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# If remaining is true (default), udhcpd will store the time\" >>/etc/udhcpd.conf'")                            or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# remaining for each lease in the udhcpd leases file. This is\" >>/etc/udhcpd.conf'")                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# for embedded systems that cannot keep time between reboots.\" >>/etc/udhcpd.conf'")                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# If you set remaining to no, the absolute time that the lease\" >>/etc/udhcpd.conf'")                          or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# expires at will be stored in the dhcpd.leases file.\" >>/etc/udhcpd.conf'")                                   or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"remaining    yes        #default: yes\" >>/etc/udhcpd.conf'")                                                   or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The time period at which udhcpd will write out a dhcpd.leases\" >>/etc/udhcpd.conf'")                         or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# file. If this is 0, udhcpd will never automatically write a\" >>/etc/udhcpd.conf'")                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# lease file. (specified in seconds)\" >>/etc/udhcpd.conf'")                                                    or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#auto_time    7200        #default: 7200 (2 hours)\" >>/etc/udhcpd.conf'")                                      or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The amount of time that an IP will be reserved (leased) for if a\" >>/etc/udhcpd.conf'")                      or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# DHCP decline message is received (seconds).\" >>/etc/udhcpd.conf'")                                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#decline_time    3600        #default: 3600 (1 hour)\" >>/etc/udhcpd.conf'")                                    or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The amount of time that an IP will be reserved (leased) for if an\" >>/etc/udhcpd.conf'")                     or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# ARP conflct occurs. (seconds\" >>/etc/udhcpd.conf'")                                                          or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#conflict_time    3600        #default: 3600 (1 hour)\" >>/etc/udhcpd.conf'")                                   or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# How long an offered address is reserved (leased) in seconds\" >>/etc/udhcpd.conf'")                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#offer_time    60        #default: 60 (1 minute)\" >>/etc/udhcpd.conf'")                                        or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# If a lease to be given is below this value, the full lease time is\" >>/etc/udhcpd.conf'")                    or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# instead used (seconds).\" >>/etc/udhcpd.conf'")                                                               or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#min_lease    60        #defult: 60\" >>/etc/udhcpd.conf'")                                                     or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The location of the leases file\" >>/etc/udhcpd.conf'")                                                       or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#lease_file    /var/lib/misc/udhcpd.leases    #defualt: /var/lib/misc/udhcpd.leases\" >>/etc/udhcpd.conf'")     or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The location of the pid file\" >>/etc/udhcpd.conf'")                                                          or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#pidfile    /var/run/udhcpd.pid    #default: /var/run/udhcpd.pid\" >>/etc/udhcpd.conf'")                        or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# Everytime udhcpd writes a leases file, the below script will be called.\" >>/etc/udhcpd.conf'")               or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# Useful for writing the lease file to flash every few hours.\" >>/etc/udhcpd.conf'")                           or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#notify_file                #default: (no script)\" >>/etc/udhcpd.conf'")                                       or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#notify_file    dumpleases    # <--- useful for debugging\" >>/etc/udhcpd.conf'")                               or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The following are bootp specific options, setable by udhcpd.\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#siaddr        192.168.0.22        #default: 0.0.0.0\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#sname        zorak            #default: (none)\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#boot_file    /var/nfs_root        #default: (none)\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# The remainer of options are DHCP options and can be specifed with the\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# keyword 'opt' or 'option'. If an option can take multiple items, such\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# as the dns option, they can be listed on the same line, or multiple\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# lines. The only option with a default is 'lease'.\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"opt    dns    8.8.8.8 8.8.4.4 # Google Public DNS servers\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \" option    subnet    255.255.255.0\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"opt    router    " + base_ip + "\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt    wins    192.168.10.10\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"option    domain    local\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"option    lease    864000        # 10 days of seconds\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"# Currently supported options, for more info, see options.c\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt subnet\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt timezone\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt router\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt timesrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt namesrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt dns\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt logsrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt cookiesrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt lprsrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt bootsize\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt domain\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt swapsrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt rootpath\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt ipttl\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt mtu\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt broadcast\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt wins\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt lease\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt ntpsrv\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt tftp\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt bootfile\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#opt wpad\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
#     
    sudo("sh -c 'echo \"# Static leases map\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#static_lease 00:60:08:11:CE:4E 192.168.0.54\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    sudo("sh -c 'echo \"#static_lease 00:60:08:11:CE:3E 192.168.0.44\" >>/etc/udhcpd.conf'") or die("Unable to write to udhcpd.conf")
    # End of writing config
    
    cp("files/udhcpd", "/etc/default/udhcpd") or die("Unable to copy UDHCPd configuration (udhcpd)")
    cp("files/hostapd", "/etc/default/hostapd") or die("Unable to copy hostapd configuration (hostapd)")
    cp("files/hostapd.conf", "/etc/hostapd/hostapd.conf") or die("Unable to copy hostapd configuration (hostapd.conf)")
    sudo("sh -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'") or die("Unable to set ipv4 forwarding")
    cp("files/sysctl.conf", "/etc/sysctl.conf") or die("Unable to copy sysctl configuration (sysctl.conf)")
    sudo("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE") or die("Unable to set iptables MASQUERADE on eth0.")
    sudo("iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT") or die("Unable to forward wlan0 to eth0.")
    sudo("iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT") or die("Unable to forward wlan0 to eth0.")
    sudo("sh -c 'iptables-save > /etc/iptables.ipv4.nat'") or die("Unable to save iptables configuration.")
    sudo("ifconfig wlan0 " + base_ip ) or die("Unable to set wlan0 IP address (" + base_ip + ")")
    sudo("service hostapd start") or die("Unable to start hostapd service.")
    sudo("service udhcpd start") or die("Unable to start udhcpd service.")
    sudo("update-rc.d hostapd enable") or die("Unable to enable hostapd on boot.")
    sudo("update-rc.d udhcpd enable") or die("Unable to enable UDHCPd on boot.")
    # udhcpd wasn't starting properly at boot (probably starting before interface was ready)
    # for now we we just force it to restart after setting the interface
    sudo("sh -c 'sed -i \"s/^exit 0//\" /etc/rc.local'") or die("Unable to remove exit from end of /etc/rc.local")
    sudo("sh -c 'echo ifconfig wlan0 "+ base_ip + " >> /etc/rc.local; echo service udhcpd restart >> /etc/rc.local;'") or die("Unable to setup udhcpd reset at boot.")
    sudo("sh -c 'echo exit 0 >> /etc/rc.local'") or die("Unable to replace exit to end of /etc/rc.local")
    #sudo("ifdown eth0 && ifdown wlan0 && ifup eth0 && ifup wlan0") or die("Unable to restart network interfaces.")
    return True
#################################
# Support functions
#################################
#================================
# Check if file exists
#================================
def yes_or_no(question):
    while "the answer is invalid":
        reply = str(raw_input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False
        
#================================
# Check if file exists
#================================
def exists(p):
    return os.path.isfile(p) or os.path.isdir(p)

#================================
# cmd run
#================================
def cmd(c):
    result = subprocess.Popen(c, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    try:
        result.communicate()
    except KeyboardInterrupt:
        pass
    return (result.returncode == 0)

#================================
# run command via sudo
#================================
def sudo(s):
    return cmd("sudo DEBIAN_FRONTEND=noninteractive %s" % s)

#================================
# Exit installer script
#================================
def die(d):
    print "Error: " + str(d)
    sys.exit(1)

#================================
# check if is virtual environment 
#================================
def is_vagrant():
    return os.path.isfile("/etc/is_vagrant_vm")

#================================
# base directory
#================================
def basedir():
    bindir = os.path.dirname(os.path.realpath(sys.argv[0]))     # Should be initial folder where install is started 
    if not bindir:
        bindir = "."
    else:
        return bindir           

#================================
# Home directory
#================================
def homedir():
    home = os.path.expanduser("~")
    return home

#================================
# Are we running a local installer
#================================
def localinstaller():
    if exists( basedir() + "/files"):
        print "Local installer"
        return True
    else:
        print "GIT installer"
        return False 
    
#================================
# Copy command
#================================    
def cp(s, d):
    return sudo("cp %s/%s %s" % (basedir(), s, d))

#================================
# Install the USB automounter functionality
#================================
def install_usb_mounter():
    sudo("apt-get -y install usbmount") or die("Unable install usbmount.")
    return True

#================================
# Check if we have a WiFi device
#================================
def wifi_present():
    if is_vagrant():
        return False
    return exists("/sys/class/net/wlan0")


############################################
# PHASE 0 install
############################################
def PHASE0():
    #================================
    # Check if on Linux and debian (requirement for ElimuPi)
    #================================
    if platform.system() != 'Linux': 
        die('Incorrect OS [' + platform.system() + ']')
    
    if platform.linux_distribution().index('debian'):
        die('Incorrect distribution [' + platform.linux_distribution() + ']')
    
    #================================
    # Get latest updates 
    #================================
    sudo("apt-get update -y") or die("Unable to update.")
    
    #================================
    # Get latest GIT
    #================================
    sudo("apt-get install -y git") or die("Unable to install Git.")
    
    #================================
    # Vargrant
    #================================
    if is_vagrant():
        sudo("mv /vagrant/sources.list /etc/apt/sources.list")
    
    #================================
    # Update and upgrade OS
    #================================
    sudo("apt-get update -y") or die("Unable to update.")
    sudo("apt-get dist-upgrade -y") or die("Unable to upgrade Raspbian.")
    
    #================================
    # Fix 'strange behaviour in vim (PBo 20180315)
    #================================
    sudo("sed -i  's/set compatible/set nocompatible/g' /etc/vim/vimrc.tiny") or die("Unable to fix vimrc.tiny")
    
    #================================
    # Clone the GIT repo.
    #================================
    if localinstaller():
        print "Using local files "
    else:
        print "Fetching files from GIT to " + basedir() 
        sudo("rm -fr " + basedir() + "/files")  
        # NOTE GIT is still old name; needs rebranding
        cmd("git clone --depth 1 " + base_git + " " + basedir() ) or die("Unable to clone Elimu installer repository.")
            
    #================================
    # Make installer autorun
    #================================
    if not basedir() + '/ElimuPi_installer.py' in open(homedir() + '/.bashrc').read():
        # Add to startup
        file = open(homedir() + '/.bashrc', 'a')
        file.write( basedir() + '/ElimuPi_installer.py')       # Enable autostart on logon
        file.close()
        print "Autostart enabled"
    else:
        print "Autostart already enabled"

    #================================
    # Write install status to file
    #================================
    file = open(base_build + '_install', 'w')
    file.write('1')                                                     # Write phase to file
    file.close()
    
    #================================
    # Reboot
    #================================
    print "---------------------------------------------------------"    
    print "Rebooting sytem required to enable all updates"
    print "Press enter to reboot"
    print "---------------------------------------------------------"
    raw_input('')
    sudo("reboot") or die("Unable to reboot Raspbian.")

############################################
# PHASE 1 install
############################################
def PHASE1():
    #================================
    # Update Raspi firmware
    #================================
    if not is_vagrant():
        sudo("yes | sudo rpi-update") or die("Unable to upgrade Raspberry Pi firmware")
    
    #================================
    # Install USB automounter
    #================================
    install_usb_mounter() or die("Unable to install automounter.")
    
    #================================
    # Setup wifi hotspot
    #================================
    if wifi_present() and args.install_wifi:
        install_wifi() or die("Unable to install WiFi.")
    
    #================================
    # Setup LAN
    #================================
    if not is_vagrant():
        cp("files/interfaces", "/etc/network/interfaces") or die("Unable to copy network interface configuration (interfaces)")
    
    #================================
    # Extra wifi driver configuration
    #================================
    if wifi_present() and args.install_wifi:
        cp("files/hostapd_RTL8188CUS", "/etc/hostapd/hostapd.conf.RTL8188CUS") or die("Unable to copy RTL8188CUS hostapd configuration.")
        cp("files/hostapd_realtek.conf", "/etc/hostapd/hostapd.conf.realtek") or die("Unable to copy realtek hostapd configuration.")
        
    
    #================================
    # Install components 
    #================================
    install_php() or die("Unable to install php.")
    install_apache() or die("Unable to install Apache.")
    install_mysql() or die("Unable to install mysql.")
    install_sqlite() or die("Unable to install sqlite.")
    install_citadel() or die("Unable to install Citadel.")
    
    #================================
    # Install web frontend (For now Rachel!!!)
    #================================
    #sudo("rm -fr /var/www") or die("Unable to delete existing default web application (/var/www).")
    #sudo("git clone --depth 1 https://github.com/rachelproject/contentshell /var/www") or die("Unable to download RACHEL web application.")
    #sudo("chown -R www-data.www-data /var/www") or die("Unable to set permissions on RACHEL web application (/var/www).")
    #sudo("sh -c \"umask 0227; echo 'www-data ALL=(ALL) NOPASSWD: /sbin/shutdown' >> /etc/sudoers.d/www-shutdown\"") or die("Unable to add www-data to sudoers for web shutdown")
    #sudo("usermod -a -G adm www-data") or die("Unable to add www-data to adm group (so stats.php can read logs)")
    
    #================================
    # KAHN academy (optional)
    #================================
    if args.khan_academy == "ka-lite":
            install_kalite() or die("Unable to install KA-Lite.")
    
    #================================
    # install the kiwix server (but not content)
    #================================
    install_kiwix()
    
    #================================
    # Change pi user login password 
    #================================
    if not is_vagrant():
        sudo("sh -c 'echo pi:" + base_passwd + "| chpasswd'") or die("Unable to change 'pi' password.")
    
    #================================
    # Update hostname (LAST!)
    #================================
    if not is_vagrant():
        cp("files/hosts", "/etc/hosts") or die("Unable to copy hosts file.")
        cp("files/hostname", "/etc/hostname") or die("Unable to copy hostname file.")
    
    #================================
    # record the version of the installer we're using - this must be manually
    # updated when you tag a new installer
    #================================
    sudo("sh -c 'echo " + base_build + " > /etc/elimupi-installer-version'") or die("Unable to record ELIMUPI version.")
    
    #================================
    # Final messages
    #================================
    print "ELIMUPI image has been successfully created."
    print "It can be accessed at: http://" + base_ip + "/"

############################################
#    Main code start
############################################
if os.path.isfile(base_build + '_install'):
    print "Continue install after reboot"
    # get phase
    install_phase = open(base_build + '_install').read()
     
else: 
    install_phase = 0

print '--------------------------------------------------------------------------'
print 'ElimuPi build : ' + base_build                   # Build version
print 'Platform      : ' + platform.platform()          # Platform : Linux-4.9.41-v7+-armv7l-with-debian-9.1
print 'System        : ' + platform.system()            # System   : Linux
print 'OS Release    : ' + platform.release()           # Release  : 4.9.41-v7+
print 'OS Version    : ' + platform.version()           # Version  : #1023 SMP Tue Aug 8 16:00:15 BST 2017
print "Install phase : (" + str(install_phase) + ")"    # Installer phase
print '--------------------------------------------------------------------------'
if install_phase == 0:
    if not yes_or_no("Do you want to install the ElimuPi build"):
        die('Installation aborted')
    PHASE0()
elif install_phase == 1:
    if not yes_or_no("Do you want to continue the ElimuPi build"):
        die('Installation aborted')
    PHASE1()
else: 
    print "Invallid installer state"
    die('Installation aborted')