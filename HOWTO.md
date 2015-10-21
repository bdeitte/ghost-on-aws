Instructions on setting up your own website using Ghost on AWS

Before you begin
----------------
1. This is a horribly-rough draft. Still setting things up myself and iterating on it. Still setting things up myself. User beware. Please fix up if you can.
2. You should probably just use (https://ghost.org/).  They have good prices, it's a whole lot simpler, and then you're supporting the non-profit that works on Ghost.  These instructions are for those with unique requirements or who like tinkering around on AWS.  (I just happen to fall into both categories.)
3. This is a very manual process.  Why not docker, chef, or your favorite install/deploy tool?  Perhaps later I try to something better, or at the very least I'll be adding some kind of scripting for updates.  I first wanted to  understand the basics of what's going on here.  (See the previous point about tinkering.)

Initial Amazon setup
----------------
http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html
You can skip "Create A Virtual Private Cloud" on this page.

EC2 Setup
----------------
Following everything other than choosing Amazon Machine Image (step #3).  Choose the Ubuntu Server image instead.
http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance_linux.html

Connect to the instance
----------------
Follow everything except use "ubuntu" instead of "ec2-user"
http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-connect-to-instance-linux.html
For instance, to connect on Mac or Linux, you would just do:
ssh -i /path/my-key-pair.pem ubuntu@public_dns_name

Prep Ubuntu
----------------
Run the following, which will take a few minutes: "sudo apt-get update && sudo apt-get upgrade -y"
You will likely be asked the following: "A new version of /boot/grub/menu.lst is available, but the version installed currently has been locally modified.  What would you like to do about menu.lst?"  Just press enter and choose the default, "keep the local version currently installed"
sudo apt-get install -y unzip build-essential libssl-dev git

Setup Node.js and related tools
----------------
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.26.1/install.sh | bash
log in again, or run "source ~/.profile"

nvm install v4.1.2
nvm alias default v4.1.2
nvm use default

Install Ghost
----------------
sudo mkdir /var/www
sudo chown -R ubuntu:ubuntu /var/www
curl -L https://ghost.org/zip/ghost-latest.zip -o ghost.zip
unzip -uo ghost.zip -d /var/www/ghost
cd /var/www/ghost
perl -pi -e 's/3.0.8/3.1.0/g' package.json
perl -pi -e 's/~0.12.0/~0.12.0 || ^4.0.0/g' package.json
rm npm-shrinkwrap.json
(above three lines are done for Node 4.x support)
npm install --production
(ignore the warnings on the install)

Set up pm2 and startup script
----------------
npm install -g pm2
pm2 startup ubuntu -u ubuntu
(and run the command pm2 tells you to run in the text)
pm2 start /var/www/ghost/index.js --name ghost
pm2 status
(if you see an error above, look at the logs in $HOME/.pm2/logs for details)
pm2 save

Make sure now that nginx is running.  This return some html to the screen:
curl http://localhost:2368

Create an Elastic IP
----------------
In the navigation pane in the AWS UI, choose Elastic IPs.
Choose Allocate New Address, and then Yes, Allocate.
Note
Select the Elastic IP address from the list, choose Actions, and then choose Associate Address.
In the dialog box, choose Instance from the Associate with list, and then select your instance from the Instance list. Choose Yes, Associate when you're done.
Copy down the Elastic IP, which is used below
Doing this may change your "ssh" connection setup.  Look at the instance in the AWS UI again to get updated details if you are disconnected.

Setup nginx
----------------
Some people like to use port forwarding to port 80 instead of this, but I use nginx to also allow for some old static files from a previous website to be served.

sudo apt-get install nginx -y

sudo vi /etc/nginx/sites-available/default

Replace the existing server section with:

server {
    listen 80;
    server_name x.x.x.x localhost;

    location / {
        proxy_pass http://127.0.0.1:2368;
    }
}

If you have any additional files to serve, you can add these in now too.  For instance, I have an old blog where I still want to serve up most of the files from their original location.  This was a Movable Type blog, with the bulk of the files in /archive.  So I added this in too in the server block:

# optional, just an example
    location /archives {
        root /var/www;
    }

Reload nginx:
sudo nginx -s reload

Try out:
curl http://localhost

Reboot and test
----------------
sudo reboot.  Wait a minute for the instance to come back up, then log in again.  Then make sure the instance is still running:
curl http://localhost
(And this isn't working.  PM2 doesn't save as it should.)

Create Route 53 route (optional)
----------------
http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-transfer-to-route-53.html
remember a www cname
switch domain in ghost/config.js.  You may be using the dev mode, as I am accidentily, so make sure to switch in the correct section

Set up email (optional)
----------------
set up mail, connect to gmail.  Try https://avix.co/blog/creating-your-own-mail-server-amazon-ec2-postfix-dovecot-postgresql-amavis-spamassassin-apache-and-squirrelmail-part-1/

Set up EBS backup
----------------
Just doing this manually in the UI right now.  Need to automate.

Set up billing alarm:
http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-alarms.html

Set up basic monitor(s)
----------------
Fill in, not doing yet. Lots of options here.

Future updates
----------------
(try on a new instance from a newly-created snapshot)
http://support.ghost.org/how-to-upgrade/
Things to update occasionally:
- sudo apt-get update && sudo apt-get upgrade -y
- Node upgrade with nvm
- npm install -g pm2 && pm2 update
