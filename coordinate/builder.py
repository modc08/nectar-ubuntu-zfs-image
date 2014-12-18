#!/usr/bin/env python

# pylint: disable=invalid-name,line-too-long,broad-except

"""Initiate and follow the progress of image creation. Post progress to Slack. Note: This is a fault-intolerant, quick-and-dirty prototype!"""

import datetime, json, os, random, socket, time

import glanceclient, swiftclient
import keystoneclient.v2_0.client as keystone
import novaclient.v1_1.client as nova

import requests, yaml

# Config

config = yaml.load(open("config.yaml", "r"))

# Slack

def slack(s):
    payload = { "text" : "image-builder: " + s }
    requests.post(config["slack"]["webhook"], data=json.dumps(payload))

# OpenStack

openstack = config["openstack"]

nova_client = nova.Client(username=openstack["username"], api_key=openstack["password"], project_id=openstack["tenant"], auth_url=openstack["auth_url"])
keystone_client = keystone.Client(username=openstack["username"], password=openstack["password"], tenant_name=openstack["tenant"], auth_url=openstack["auth_url"])
glance_url = keystone_client.service_catalog.url_for(service_type="image", endpoint_type="publicURL")
swift_url = keystone_client.service_catalog.url_for(service_type="object-store", endpoint_type="publicURL")
glance_client = glanceclient.Client(endpoint=glance_url, token=keystone_client.auth_token)

def initiate():
    """Boot the builder."""

    user_data = open("user-data.sh").read()
    flavor = nova_client.flavors.find(name=openstack["flavor"])
    builder = nova_client.servers.create(availability_zone=openstack["region"], name="image-builder", image=openstack["image"]["base"], flavor=flavor, userdata=user_data, security_groups=[openstack["security_group"]])

    slack("instantiated: " + builder.id)

    previous_status = ""
    while not builder.status == "ACTIVE":
        if builder.status != previous_status:
            slack("vm is %s" % builder.status)
            previous_status = builder.status
        time.sleep(2)
        builder.get()

    ip = builder.networks.values()[0][0]
    rip = socket.gethostbyaddr(ip)[0]

    slack("vm is %s at %s" % (builder.status, rip))

    return builder

def wait_for_completion(builder):
    """Wait around until the builder has powered down."""
    previous_status = builder.status

    while not builder.status == "SHUTOFF":
        if builder.status != previous_status:
            slack("vm is %s" % builder.status)
            previous_status = builder.status
        time.sleep(2)
        builder.get()

    slack("vm is %s" % builder.status)

def snapshot(builder):
    """Snapshot the now-powered-down builder."""

    image_name = openstack["image"]["prefix"] + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    image_id = builder.create_image(image_name)

    slack("creating image: %s" % image_name)

    image = glance_client.images.get(image_id)

    previous_status = ""
    while not image.status == "active":
        if image.status != previous_status:
            slack("image %s is %s" % (image_name, image.status))
            previous_status = image.status
        time.sleep(2)
        image.get()

    slack("image %s is %s" % (image_name, image.status))

    return image_id

def finish(builder, image_id):
    """Tidy up and record the image ID."""

    builder.delete()
    slack("vm deleted")

    swiftclient.client.put_object(swift_url, token=keystone_client.auth_token, container=openstack["swift"]["container"], name=openstack["swift"]["object"], contents=image_id)
    slack("swift: %s/%s = %s" % (openstack["swift"]["container"], openstack["swift"]["object"], image_id))

if __name__ == "__main__":
    builder = initiate()
    wait_for_completion(builder)
    image_id = snapshot(builder)
    finish(builder, image_id)
