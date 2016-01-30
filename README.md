These are instructions on setting up your own website using Ghost, nginx, and Node 4.x on AWS and Namecheap.  See [my article on the subject](http://deitte.com/ghost-on-aws/) for the blog where this setup is used.

Before going any further, there are a few important things to understand:

1. These instructions are for those with unique Ghost requirements or who like tinkering around on AWS.  If I didn't fall into both those categories and wanted a Ghost blog, I would use one of the plans on https://ghost.org/pricing/. It's nearly the same price as setting up on AWS, or perhaps less expensive in some cases.  It's a whole lot simpler, and then you're supporting the non-profit that works on Ghost. 
2. This guide was used to set up a modest personal blog.  If you are planning for something big, I would add in an ELB, a cluster in more than one availability zone, and a bunch more below.  This isn't a bad starting point, but don't think this is all you need for your big site!  I would also automate a lot of the below.  It would be wonderful to use CloudFormation or Elastic Beanstalk and some more bash scripts to automate most of the below.  Or Ansible/Chef/Docker/etc.  If you end up doing any shortening of the steps, I'll incorporate these details in the instructions below.
3. AWS, Ghost, and all the rest below is always changing.  If instructions aren't working, and you figure out how to get things to work again, PRs are welcome to fix this up.

**Table of Contents**

- [Initial Amazon setup](#initial-amazon-setup)
- [EC2 Setup](#ec2-setup)
- [Connect to the instance](#connect-to-the-instance)
- [Prep Ubuntu](#prep-ubuntu)
- [Setup Node.js and related tools](#setup-nodejs-and-related-tools)
- [Install Ghost](#install-ghost)
- [Set up PM2 and startup script](#set-up-pm2-and-startup-script)
- [Create an Elastic IP](#create-an-elastic-ip)
- [Setup nginx](#setup-nginx)
- [Reboot and test](#reboot-and-test)
- [Create domain on Namecheap (optional)](#create-domain-on-namecheap-optional)
- [Set up email (optional)](#set-up-email-optional)
- [Set up CloudFront and SSL (optional)](#set-up-cloudfront-and-ssl-optional)
- [More application tinkering](#more-application-tinkering)
- [Set up EBS backup](#set-up-ebs-backup)
- [Set up billing alarm](#set-up-billing-alarm)
- [Set up a basic monitor](#set-up-a-basic-monitor)
- [Future updates](#future-updates)

## Initial Amazon setup
If you don't have an AWS account, go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html. You can skip "Create A Virtual Private Cloud" on this page since you'll have a default VPC.

## EC2 Setup
Go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance_linux.html. Following everything other than choosing Amazon Machine Image (step #3). Choose the Ubuntu Server image instead. You could choose the Amazon Image, but these instructions are written for Ubuntu.

## Connect to the instance
Go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-connect-to-instance-linux.html. Follow everything except use "ubuntu" instead of "ec2-user". For instance, to connect on Mac or Linux, you would just do this:
```
ssh -i /path/my-key-pair.pem ubuntu@public_dns_name
```

## Prep Ubuntu
Run the following to ensure Ubuntu is up to date. This will take a few minutes.
```
sudo apt-get update && sudo apt-get upgrade -y
```
You will likely be asked the following: "A new version of /boot/grub/menu.lst is available, but the version installed currently has been locally modified.  What would you like to do about menu.lst?"  Just press enter and choose the default, "keep the local version currently installed".

Install some needed libraries. Add to the list anything you may want (like emacs).
```
sudo apt-get install -y unzip build-essential libssl-dev git nginx
```

## Setup Node.js and related tools
Install nvm to help wtih Node.js installations.
```
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.26.1/install.sh | bash
source ~/.profile
```

Then install the latest Node.js. The first command lists out the versions, so you can check to see if you want to install something even newer.
```
nvm ls-remote
nvm install v4.2.4
nvm alias default v4.2.4
nvm use default
```

## Install Ghost
Time to install Ghost. 
```
sudo mkdir /var/www
sudo chown -R ubuntu:ubuntu /var/www
curl -L https://ghost.org/zip/ghost-latest.zip -o ghost.zip
unzip -uo ghost.zip -d /var/www/ghost
cd /var/www/ghost
npm install --production
```

## Set up PM2 and startup script
We will use PM2 to keep Ghost going.
```
npm install -g pm2
pm2 startup ubuntu -u ubuntu
```
The output of the second command above will tell you to run something.  Do this now.  Then continue on with the PM2 setup.
```
pm2 start /var/www/ghost/index.js --name ghost
pm2 status
```
If you see an error in the status call above, look at the logs in $HOME/.pm2/logs for details. If things look fine, save what has been done so PM2 will start up properly on restart.
```
pm2 save
````

Now you can make sure that Ghost is up and running.
```
curl http://localhost:2368
```

## Create an Elastic IP
Head into the AWS UI for some setup:

1. In the navigation pane, choose Elastic IPs
2. Choose Allocate New Address, and then Yes, Allocate. 
3. Select the Elastic IP address from the list, choose Actions, and then choose Associate Address.
4. In the dialog box, choose Instance from the Associate with list, and then select your instance from the Instance list. Choose Yes, Associate when you're done.
5. Copy down the Elastic IP, which is used below

Doing the above may change your "ssh" connection setup.  Look at the instance in the AWS UI again to get updated details if you are disconnected.

## Setup nginx
Some people like to use port forwarding to port 80 instead of this, but I use nginx to also allow for some old static files from a previous website to be served.  nginx was already installed above, and we just need to configure it now.

```
sudo vi /etc/nginx/sites-available/default
```

Replace the existing server section with the following.  Substitute in your Elastic IP for x.x.x.x
```
server {
    listen 80;
    server_name x.x.x.x localhost;

    location / {
        proxy_pass http://127.0.0.1:2368;
    }
}
```

If you have any additional files to serve, you can add these in now too.  For instance, I have an old blog where I still want to serve up most of the files from their original location.  This was a Movable Type blog, with the bulk of the files in /archive.  So I added this in too in the server block:
```
    # optional, just an example
    location /archives {
        root /var/www;
    }
```

Reload nginx to pick up the configuration changes.
```
sudo nginx -s reload
```

Now you should be able to see the same page you saw above, now through nginx on port 80.
```
curl http://localhost
```

## Reboot and test
sudo reboot.  Wait a minute for the instance to come back up, then log in again.  Then make sure the instance is still running:
```
curl http://localhost
```

## Create domain on Namecheap (optional)
I chose Namecheap instead of Amazon's Route 53 because I was planning to use Namecheap's email hosting service as well (which I describe in the next section).  It also turns out that Namecheap is cheaper and generally easier to use.

To set up, go to [Namecheap](https://www.namecheap.com/) and register or transfer the domain you want.  The process is fairly straightforward.  When you get to setting up the domain, go into "Advanced DNS" for the domain and create an "A Record".  Set the "Host" as "@" and set the Value as the Elastic IP you set up above.  Save this, and this create a second "A Record"  Set the "Host" as "www" and set the Value as the same Elastic IP you set up above.

After the domain started resolving, I did not need to change anything in nginx.  You do though need to make a small edit to the Ghost config.
```
vi /var/www/ghost/config.js
```
You may be using the dev mode, as I am accidentily (and which you are too if you followed these instructions exactly) so make sure to switch the domain in the correct section.

## Set up email (optional)
Amazon does not have email hosting for individuals, a painful point I found out in time.  I ended up using [Namecheap email hosting](https://www.namecheap.com/hosting/email.aspx) which I then forward on to Gmail.  The setup for this is pretty much automatic if you're using Namecheap for domain hosting as well.

If you have tons of time on your hands and like managing a mail server, you could [build something yourself](https://avix.co/blog/creating-your-own-mail-server-amazon-ec2-postfix-dovecot-postgresql-amavis-spamassassin-apache-and-squirrelmail-part-1/).  But that's even more overkill than the rest of this, especially for personal projects.

## Set up CloudFront and SSL (optional)
I haven't done this part, but it makes sense to use Amazon's CDN in front of your EC2 instance, both for faster response times and to use a smaller instance that will handle load better.  Using CloudFront also gives you HTTPS for free, with the [AWS Certificate Manager](https://aws.amazon.com/certificate-manager/).

## More application tinkering
Need to add info about adding in comments (Disqus), log rotation (if needed, haven't looked), and seeing traffic (through Google Analytics).

## Set up EBS backup
Follow the steps in my separate guide on [setup for scheduled EBS snapshots](https://github.com/bdeitte/scheduled-snapshots).  

## Set up billing alarm
Make sure that you don't spend more money than you're expecting.  Go through http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-alarms.html

## Set up a basic monitor
There are some simple things you can do in AWS, but the most important thing to know is that your website is visible to the world.  This is easiest to do with a tool outside of AWS.  I prefer RunScope for this, and there is a simple free account you can sign up for.  To set up:
- [Sign up](https://www.runscope.com/signup) for an account
- Under "Monitor API Performance & Uptime", click "Get Started"
- Enter the base URL for your website, or whatever page you want to set out for uptime.  Fill in the rest of the form however you'd like.
- Next click on Tests, and then Skip Tutorial.  You should see your test.
- Click on Manage Shared Environements, then Bucket-wide Settings, then Notifications.  Select your email address, and then select "Notify after the test fails in a location" and "and again after the test returns to passing.".

There is a whole lot more you can do with RunScope, or with monitoring in general.  But this will at least start things off and let you know when your website has issues.

## Future updates
I haven't gone through this myself, but at some point I will want to update Ghost, or Node.js, or other things on the server.  It's to do this on a newly-created snapshot where you can test this out to ensure basic functionality works.  And then you can move over the Elastic IP to flip things over.  Ghost also has some docs here in http://support.ghost.org/how-to-upgrade/
Things to update occasionally:
- sudo apt-get update && sudo apt-get upgrade -y
- Node upgrade with nvm
- npm install -g pm2 && pm2 updatePM2
