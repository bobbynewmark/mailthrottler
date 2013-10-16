*Commands to Run to get instance up*

*Variables*
* image_id = ami-51792c38  #32bit-linux
* security_group = echo-server-1
* key-name = echoserver

*Launch Instance*
    
	aws ec2 run-instances --image-id ami-51792c38 --count 1 --instance-type t1.micro --key-name echoserver --security-groups echo-server-1

*Above returns Json with variables*
* Reservations[0].Instances[0].PublicDnsName
* Reservations[0].Instances[0].InstanceId
* Reservations[0].Instances[0].State.Name

*wait till running*

    aws ec2 describe-instances

*ssh to instance*
    
	ssh -i \users\acox.SSG\Downloads\echoserver.pem ec2-user@ec2-54-227-32-37.compute-1.amazonaws.com

*run to get packages installed*
    
	sudo yum install make automake gcc gcc-c++ kernel-devel git-core -y 
    sudo yum install python27-devel -y 
    sudo yum install subversion -y
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | sudo python27  
    sudo python27 -m easy_install pip
    sudo python27 -m pip install twisted
    sudo python27 -m pip install genshi

*run to get mailthrottler installed*
    
	svn checkout http://mailthrottler.googlecode.com/svn/trunk/ mailthrottler-read-only

*configure mailthrottler*
????

*run mailthrottler*
    
	cd mailthrottler-read-only
    python27 mailThrottler &

*terminate instance*

    aws ec2 terminate-instances --instance-ids i-67fdf003
