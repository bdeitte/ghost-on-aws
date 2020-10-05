These are instructions on setting up your own website using Ghost, nginx, and Node 4.x on AWS and Namecheap.  See [my article on the subject](http://deitte.com/ghost-on-aws/) for the blog where this setup is used.

Before going any further, there are a few important things to understand:

1. These instructions are for those with unique Ghost requirements or who like tinkering around on AWS.  If I didn't fall into both those categories and wanted a Ghost blog, I would use one of the plans on https://ghost.org/pricing/.
2. This guide was used to set up a modest personal blog.  If you are
   planning for something big, I would add in an ELB, a cluster in
   more than one availability zone, and a bunch more below.  This
   isn't a bad starting point, but don't think this is all you need
   for your big site.  I would also automate a lot of the below-
   infrastructure as code pays dividends.
3. AWS, Ghost, and all the rest below is always changing.  If
   instructions aren't working, and you figure out how to get things
   to work again, PRs are welcome to fix this up.

## EC2 setup
If you don't have an AWS account, go through [the AWS guide for EC2 setup](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html).

Then go through step #1 in
[the AWS guide for EC2 launching](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance_linux.html). Follow
everything other than choosing Amazon Machine Image (step #3). Choose
the Ubuntu Server 16 image instead.

## Connect to the instance
[Connect to the
instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html),
using "ubuntu" for "my"instance-user-name". For instance, to connect on Mac or Linux, you would just do this:
```
ssh -i /path/my-key-pair.pem ubuntu@public_ip
```

## Follow Ghost's Guide

Now it's on to
[Ghost's standard Ubuntu guide](https://ghost.org/docs/install/ubuntu/)

Where it asks you to login as root and create a new user, I chose to
skip these steps and keep using the ubuntu user instead.

## Create an Elastic IP
Head into the AWS UI for some setup:

1. In the navigation pane, choose Elastic IPs
2. Choose Allocate New Address, and then Yes, Allocate.
3. Select the Elastic IP address from the list, choose Actions, and then choose Associate Address.
4. In the dialog box, choose Instance from the Associate with list, and then select your instance from the Instance list. Choose Yes, Associate when you're done.
5. Copy down the Elastic IP, which is used below

Doing the above may change your "ssh" connection setup.  Look at the instance in the AWS UI again to get updated details if you are disconnected.

## Create domain on Namecheap (optional)
I chose Namecheap instead of Amazon's Route 53 because I was planning to use Namecheap's email hosting service as well (which I describe in the next section).  It also turns out that Namecheap is cheaper and generally easier to use.

To set up, go to [Namecheap](https://www.namecheap.com/) and register or transfer the domain you want.  The process is fairly straightforward.  When you get to setting up the domain, go into "Advanced DNS" for the domain and create an "A Record".  Set the "Host" as "@" and set the Value as the Elastic IP you set up above.  Save this, and this create a second "A Record"  Set the "Host" as "www" and set the Value as the same Elastic IP you set up above.

After the domain started resolving, I did not need to change anything in nginx.  You do though need to make a small edit to the Ghost config.
```
vi /var/www/ghost/config.production.json
```

## Set up email (optional)
Amazon does not have email hosting for individuals, a painful point I found out in time.  I ended up using [Namecheap email hosting](https://www.namecheap.com/hosting/email.aspx) which I then forward on to Gmail.  The setup for this is pretty much automatic if you're using Namecheap for domain hosting as well.

If you have tons of time on your hands and like managing a mail server, you could [build something yourself](https://avix.co/blog/creating-your-own-mail-server-amazon-ec2-postfix-dovecot-postgresql-amavis-spamassassin-apache-and-squirrelmail-part-1/).  But that's even more overkill than the rest of this, especially for personal projects.

## Set up CloudFront and SSL (optional)
I haven't done this part, but it makes sense to use Amazon's CDN in front of your EC2 instance, both for faster response times and to use a smaller instance that will handle load better.  Using CloudFront also gives you HTTPS for free, with the [AWS Certificate Manager](https://aws.amazon.com/certificate-manager/).

## More application tinkering
Need to add info about adding in comments (Disqus), log rotation (if needed, haven't looked), and seeing traffic (through Google Analytics).

## Set up EBS backup
Follow the steps in my separate guide on
[setup for scheduled EBS snapshots](https://github.com/bdeitte/scheduled-snapshots).

## Set up billing alarm
Make sure that you don't spend more money than you're expecting.  Go through http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-alarms.html

## Set up a basic monitor
There are some simple things you can do in AWS, but the most important thing to know is that your website is visible to the world.  This is easiest to do with a tool outside of AWS.  I used to suggest RunScope in this section, but they are shutting down their free tier.  Feel free to fill this in with a better suggestion!

## Other things to think about

Plenty more to do as things go forward!  Make sure you think about how
you do updates, to the server pieces and Ghost.  Pay attention
