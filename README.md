These are instructions on setting up your own website using Ghost,
AWS, and Namecheap.  It was used to set up [deitte.com](http://deitte.com/).

Before going any further, there are a few important things to understand:

1. These instructions are for those with unique Ghost requirements or
   who like tinkering around on AWS.  If I didn't fall into both those
   categories and wanted a professional Ghost blog, I would use one of
   the plans from [ghost.org](https://ghost.org/pricing/).
2. This guide was used to set up a modest personal blog.  If you are
   planning for something big, I would add in an ELB, a cluster in
   more than one availability zone, more analytics, and a bunch more below.  This
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
the Ubuntu Server 16 image instead.  As for the size of your instance,
I have found the tiny t2.nano works just fine for a low-traffic blog.

## Connect to the instance
[Connect to the
instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html),
using "ubuntu" for "my"instance-user-name". For instance, to connect on Mac or Linux, you would just do this:
```
ssh -i /path/my-key-pair.pem ubuntu@public_ip
```

Remember if you followed AWS' guidance on restriction access to port
22 (as you should), you may need to update in AWS later if your own IP
address changes.

## Follow Ghost's Guide

Now it's on to
[Ghost's standard Ubuntu guide](https://ghost.org/docs/install/ubuntu/).

Where it asks you to login as root and create a new user, I chose to
skip these steps and keep using the ubuntu user instead.

All of the optional set up steps (ghost MySQL user, nginx, SSL,
systemd) are a good idea to do.

## Create an Elastic IP
In order to make things easier in the future, head into the AWS UI for some setup:

1. In the navigation pane, choose Elastic IPs
2. Choose Allocate New Address, and then Yes, Allocate.
3. Select the Elastic IP address from the list, choose Actions, and then choose Associate Address.
4. In the dialog box, choose Instance from the Associate with list, and then select your instance from the Instance list. Choose Yes, Associate when you're done.
5. Copy down the Elastic IP, which is used below

Doing the above may change your "ssh" connection setup.  Look at the
instance in the AWS UI again to get updated details if you are
disconnected.

## Set up your domain
I chose Namecheap instead of Amazon's Route 53 for DNS because I was planning to use Namecheap's email hosting service as well (which I describe in the next section).  It also turns out that Namecheap is cheaper and generally easier to use.

To set up, go to [Namecheap](https://www.namecheap.com/) and register or transfer the domain you want.  The process is fairly straightforward.  When you get to setting up the domain, go into "Advanced DNS" for the domain and create an "A Record".  Set the "Host" as "@" and set the Value as the Elastic IP you set up above.  Save this, and this create a second "A Record"  Set the "Host" as "www" and set the Value as the same Elastic IP you set up above.

## Set up email (optional)
Amazon does not have email hosting for individuals, a painful point I found out in time.  I ended up using [Namecheap email hosting](https://www.namecheap.com/hosting/email.aspx) which I then forward on to Gmail.  The setup for this is pretty much automatic if you're using Namecheap for domain hosting as well.

If you have tons of time on your hands and like managing a mail server, you could [build something yourself](https://avix.co/blog/creating-your-own-mail-server-amazon-ec2-postfix-dovecot-postgresql-amavis-spamassassin-apache-and-squirrelmail-part-1/).  But that's even more overkill than the rest of this, especially for personal projects.

## Reserve your instance
Save some money and
[reserve your EC2 instance](https://aws.amazon.com/ec2/pricing/reserved-instances/buyer/).
Choose what you are running if you are sure this is the correct one
for the next year, or looking into their Savings Plans if you're not.
You can choose one with no upfront cost, which means it's just money
saved each month on your bill if you are going to keep running this blog.

## Set up EBS backup
Follow the steps in my separate guide on
[setup for scheduled EBS snapshots](https://github.com/bdeitte/scheduled-snapshots).
Or use AWS Backup.

## Set up billing alarm
Make sure that you don't spend more money than you're expecting.  Go
through [http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-alarms.html](free
tier alarms).

## Set up a basic monitor
There are some simple things you can do in AWS, but the most important thing to know is that your website is visible to the world.  This is easiest to do with a tool outside of AWS.

## Other things to think about

Think about your upgrade plans, how you plan to keep up to date with
both Ghost and what else is installed on your server.   To help with
this, I automatically have security updates installed for the server
with:

```
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

You should have a basic synthetic monitor setup to alert you if the
blog is up or down.  There's many good products that include this,
like Datadog, or you can look to use [Cloudwatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Synthetics_Canaries.html).

Many more things you could do to make things better, as noted in the
intro.  Feel free to open a PR if you see anything I've missed.
