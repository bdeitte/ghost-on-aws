#!/usr/bin/env python3
#
# Creates a new snapshot for all passed volumes deletes old snapshots
# Originally from https://www.flynsarmy.com/2015/06/how-to-schedule-daily-rolling-ebs-snapshots/
#
# Usage:
# python3 ssbackup.py --volume-ids=vol-1a23bcd4 --volume-ids=vol-2b34cde5 --expiry-days=7
#

import argparse
import subprocess
import json
import logging
import time, datetime, dateutil.parser

profile = 'ssbackup'       # Your AWS CLI profile

def bash(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    return process.communicate()[0].decode('utf-8')

def getOurSnapshots():
    """
    Return a list of snapshot Dicts created with this plugin.
    """
    return json.loads(bash([
                "aws", "ec2", "describe-snapshots",
                "--filters", "Name=tag-key,Values=Group", "Name=tag-value,Values=ssbackup",
                "--profile", profile
                ]))['Snapshots']

def createSnapshots(volumeIds):
    """
    Return True if snapshots of the given volumes are created, else False

    Keyword arguments:
    volumeIds -- List of EBS volume IDs
    """
    # Create the snapshots
    snapshots = []
    for volumeId in volumeIds:
        snapshots.append(createSnapshotForVolume(volumeId))

        # Add Name and Group tags to the snapshot
        if len(snapshots):
            snapshotIds = []
date = time.strftime("%Y-%m-%d")

for snapshot in snapshots:
    snapshotIds.append(snapshot['SnapshotId'])

response = json.loads(bash([
            "aws", "ec2", "create-tags",
            "--resources", ' '.join(snapshotIds),
            "--tags", "Key=Name,Value='Backup "+date+"'", "Key=Group,Value=ssbackup",
            "--profile", profile
            ]))

if response['return'] == 'true':
    return True

return False

def createSnapshotForVolume(volumeId):
    """
    Return a Dict of a created snapshot for the given EBS volume

    Keyword arguments:
    volumeId -- An EBS volume ID
    """

    date = time.strftime("%Y-%m-%d")
    message = "Creating snapshot for volume "+volumeId+"..."
    response = json.loads(bash([
                "aws", "ec2", "create-snapshot",
                "--volume-id", volumeId,
                "--description", "Backup "+date,
                "--profile", profile
                ]))
    message += response['SnapshotId']
    logging.info(message)

    return response

def deleteOldSnapshots(snapshots, max_age):
    """
    Delete all listed snapshots older than max_age
    """
    snapshotIds = []
    date = datetime.datetime.now()

    for snapshot in snapshots:
        snapshotDate = dateutil.parser.parse(snapshot['StartTime']).replace(tzinfo=None)
dateDiff = date - snapshotDate

if dateDiff.days >= max_age:
    message = "Deleting snapshot "+snapshot['SnapshotId']+" ("+str(dateDiff.days)+" days old)..."
    response = json.loads(bash([
                "aws", "ec2", "delete-snapshot",
                "--snapshot-id", snapshot['SnapshotId'],
                "--profile", profile
                ]))
    message += "done"
    logging.info(message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ADD YOUR DESCRIPTION HERE')
    parser.add_argument('-i','--volume-ids', help='EBS volume ID', required=True)
    parser.add_argument('-d','--delete-old', help='Delete old snapshots?', required=False, type=bool, default=True)
    parser.add_argument('-x','--expiry-days', help='Number of days to keep snapshots', required=False, type=int, default=7)
    args = parser.parse_args()

    logging.basicConfig(filename='ssbackup.log', level=logging.DEBUG, format='%(asctime)s:  %(message)s', datefmt='%Y-%m-%d %I:%M:%S%p')

    # Get all active volumes
    volumeIds = args.volume_ids.split(',')
    # Create the snapshots
    if len(volumeIds):
        snapshots = createSnapshots(volumeIds)
pass

# Delete snapshots older than expiry-days
if args.delete_old:
    deleteOldSnapshots(getOurSnapshots(), args.expiry_days)
