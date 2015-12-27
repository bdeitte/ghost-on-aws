Instructions on setting up your own website using Ghost, nginx, and Node 4.x on AWS

Cavaets
----------------
1. This is a rough draft. As you'll see in the notes below, I'm still setting things up and iterating on the guide. User beware. PRs welcome.
2. You should probably stop reading and use https://ghost.org/ instead. They have good prices, it's a whole lot simpler, and then you're supporting the non-profit that works on Ghost. These instructions are for those with unique requirements or who like tinkering around on AWS.
3. This is a fairly manual process.  It would be wonderful, at the very least, to use CloudFormation and some bash scripts to automate more of the below.  If you end up doing this, I would be more than happy to incorporate it in the below.

Initial Amazon setup
----------------
If you don't have an AWS account, go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html. You can skip "Create A Virtual Private Cloud" on this page since you'll have a default VPC.

EC2 Setup
----------------
Go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance_linux.html. Following everything other than choosing Amazon Machine Image (step #3). Choose the Ubuntu Server image instead. You could choose the Amazon Image, but these instructions are written for Ubuntu.

Connect to the instance
----------------
Go through http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-connect-to-instance-linux.html. Follow everything except use "ubuntu" instead of "ec2-user". For instance, to connect on Mac or Linux, you would just do this:
```
ssh -i /path/my-key-pair.pem ubuntu@public_dns_name
```

Prep Ubuntu
----------------
Run the following to ensure Ubuntu is up to date. This will take a few minutes.
```
sudo apt-get update && sudo apt-get upgrade -y
```
You will likely be asked the following: "A new version of /boot/grub/menu.lst is available, but the version installed currently has been locally modified.  What would you like to do about menu.lst?"  Just press enter and choose the default, "keep the local version currently installed".

Install some needed libraries. Add to the list anything you may want (like emacs).
```
sudo apt-get install -y unzip build-essential libssl-dev git nginx
```

Setup Node.js and related tools
----------------
Install nvm to help wtih Node.js installations.
```
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.26.1/install.sh | bash
source ~/.profile
```

Then install the latest Node.js. The first command lists out the versions, so you can check to see if you want to install something even newer.
```
nvm ls-remote
nvm install v4.1.2
nvm alias default v4.1.2
nvm use default
```

Install Ghost
----------------
Time to install Ghost. 
```
sudo mkdir /var/www
sudo chown -R ubuntu:ubuntu /var/www
curl -L https://ghost.org/zip/ghost-latest.zip -o ghost.zip
unzip -uo ghost.zip -d /var/www/ghost
cd /var/www/ghost
npm install --production
```

Set up PM2 and startup script
----------------
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

Create an Elastic IP
----------------
Head into the AWS UI for some setup:

1. In the navigation pane, choose Elastic IPs
2. Choose Allocate New Address, and then Yes, Allocate. 
3. Select the Elastic IP address from the list, choose Actions, and then choose Associate Address.
4. In the dialog box, choose Instance from the Associate with list, and then select your instance from the Instance list. Choose Yes, Associate when you're done.
5. Copy down the Elastic IP, which is used below

Doing the above may change your "ssh" connection setup.  Look at the instance in the AWS UI again to get updated details if you are disconnected.

Setup nginx
----------------
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

Reboot and test
----------------
sudo reboot.  Wait a minute for the instance to come back up, then log in again.  Then make sure the instance is still running:
```
curl http://localhost
```

Create Route 53 route (optional)
----------------
(See the Set up email section... I will be switching off of Route 53 to simplify email setup.)

If you want your own domain, Route 53 is a great way to go.  Needs to fill in more details here... I used http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-transfer-to-route-53.html and some other docs.  

If you're new to DNS setups, it's easy to forget a www CNAME. Make sure to include this if you want www.yourdomainname.com to work. This doesn't by default: only yourdomainname.com (without the www) will resolve.

I did not need to change anything in nginx after this, but you do need to edit the Ghost config.
```
vi /var/www/ghost/config.js
```
You may be using the dev mode, as I am accidentily (and which you are too if you followed these instructions exactly) so make sure to switch in the correct section.

Set up email (optional)
----------------
I am likely going to do this by moving off of Route 53 and switching to Namecheap for DNS and email hosting.  If you have tons of time on your hands and like managing a mail server, you could instead use
https://avix.co/blog/creating-your-own-mail-server-amazon-ec2-postfix-dovecot-postgresql-amavis-spamassassin-apache-and-squirrelmail-part-1/

More application tinkering
----------------
Need to add info about adding in comments, log rotation (if needed, haven't looked), and seeing traffic (through log grepping for now).

Set up EBS backup
----------------
Just doing this manually in the UI right now.  Need to automate. Lots of scripts out there for this.

Set up billing alarm
----------------
Make sure that you don't spend more money than you're expecting.  Go through http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-alarms.html

Set up a basic monitor
----------------
There are some simple things you can do in AWS, but the most important thing to know is that your website is visible to the world.  This is easiest to do with a tool outside of AWS.  I prefer RunScope for this, and there is a simple free account you can sign up for.  To set up:
- [Sign up](https://www.runscope.com/signup) for an account
- Under "Monitor API Performance & Uptime", click "Get Started"
- Enter the base URL for your website, or whatever page you want to set out for uptime.  Fill in the rest of the form however you'd like.
- Next click on Tests, and then Skip Tutorial.  You should see your test.  
- Click on Manage Shared Environements, then Bucket-wide Settings, then Notifications.  Select your email address, and then select "Notify only when a test run fails".

There is a whole lot more you can do with RunScope, or with monitoring in general.  But this will at least start things off and let you know when your website has issues.

Future updates
----------------
I haven't gone through this myself, but at some point I will want to update Ghost, or Node.js, or other things on the server.  It's to do this on a newly-created snapshot where you can test this out to ensure basic functionality works.  And then you can move over the Elastic IP to flip things over.  Ghost also has some docs here in http://support.ghost.org/how-to-upgrade/
Things to update occasionally:
- sudo apt-get update && sudo apt-get upgrade -y
- Node upgrade with nvm
- npm install -g pm2 && pm2 updatePM2
