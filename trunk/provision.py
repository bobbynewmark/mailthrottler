#import json
#import subprocess

import boto.ec2
from fabric.api import *
import time
import fabric.network
import os

region = "us-east-1"
image_id = "ami-51792c38"
instance_type = "t1.micro"
security_groups = ["echo-server-1"]
key_name = "echoserver"
key_location = os.path.abspath(os.path.expandvars("%HOME%\\Downloads\\echoserver.pem"))

class Dummy_Status(object):
    status = "unknown"


def getStatus(i_status):
    system_status = getattr(i_status, "system_status", Dummy_Status).status
    instance_status = getattr(i_status, "instance_status", Dummy_Status).status
    return (system_status, instance_status)


def launch_instance(conn):
    dummy = Dummy_Status() 
    #assume that we have the security_group setup already??
    #assume that we have the keypair already
    print "Launching instance"
    reservation = conn.run_instances(image_id,
                  max_count = 1,
                  key_name = key_name,
                  instance_type = instance_type,
                  security_groups = security_groups
                  )

    myinstance = reservation.instances[0]
    print "launched", myinstance.id 
    #wait for state to reach 
    t1 = time.time()
    while myinstance.state != "running":
        print "\tWaiting for instance to reach running state.  Current state:", myinstance.state
        time.sleep(30)
        myinstance.update()
        if time.time() - t1 > (5*60):
            break

    if myinstance.state != "running":
        print "Failed to start instance, please check AWS console"
        return (False, myinstance)
    
    print "\tInstance now running"
    time.sleep(10)
    #now we wait till it can be connected to
    i_status = conn.get_all_instance_status(myinstance.id)[0]
    t1 = time.time()
    while (getStatus(i_status) != ("ok", "ok")): 
        print "\tWaiting for instance to be reachable. System:%s Instance:%s" % getStatus(i_status)
        time.sleep(30)
        i_status = conn.get_all_instance_status(myinstance.id)[0]
        if time.time() - t1 > (5*60):
            break
        
    if (getStatus(i_status) != ("ok", "ok")):
        print "Instance not reachable, please check AWS console"
        return (False, myinstance)

    return (True, myinstance)

#assume that you have .boto config setup
print "Connecting to EC2 region:", region
conn = boto.ec2.connect_to_region(region)
launch_success , myinstance = launch_instance(conn)
if not launch_success:
    exit(0)
public_ip = myinstance.ip_address
public_dns = myinstance.public_dns_name

print "public ip:", public_ip
print "public dns:", public_dns

env.hosts = [ public_dns ]
env.host_string = public_dns
env.user = "ec2-user"
env.key_filename = key_location
sudo("yum install make automake gcc gcc-c++ kernel-devel git-core -y")
sudo("yum install python27-devel -y")
sudo("yum install subversion -y")
sudo("wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | sudo python27")
sudo("python27 -m easy_install pip")
sudo("python27 -m pip install twisted")
sudo("python27 -m pip install genshi")
run("svn checkout http://mailthrottler.googlecode.com/svn/trunk/ mailthrottler-read-only")
with cd("~/mailthrottler-read-only"):
    run("twistd -o -y mailThrottler.tac")
fabric.network.disconnect_all()









