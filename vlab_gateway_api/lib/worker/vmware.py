# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import socket
import random
import os.path

import ujson
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_gateway_api.lib import const


COMPONENT_NAME='defaultGateway'


def show_gateway(username):
    """Obtain basic information about the defaultGateway

    :Returns: Dictionary

    :param username: The user requesting info about their defaultGateway
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for vm in folder.childEntity:
            if vm.name == COMPONENT_NAME:
                info = virtual_machine.get_info(vcenter, vm, username)
                break
    return info


def create_gateway(username, wan, lan, logger, image_name='defaultgateway-IPAM.ova'):
    """Deploy the defaultGateway from an OVA

    :Returns: None

    :param username: The user who wants to create a new defaultGateway
    :type username: String

    :param wan: The name of the network to use in vCenter for the WAN network
    :type wan: String

    :param lan: The name of the network to use in vCenter for the LAN network
    :type lan: String

    :param image_name: The of the OVA to deploy
    :type image_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        ova = Ova(os.path.join(const.VLAB_GATEWAY_IMAGES_DIR, image_name))
        try:
            network_map = _create_network_map(vcenter, ova, wan, lan, logger)
            the_vm = virtual_machine.deploy_from_ova(vcenter, ova, network_map,
                                                     username, COMPONENT_NAME, logger)
        finally:
            ova.close()
        _setup_gateway(vcenter, the_vm, username, gateway_version='1.0.0', logger=logger)
        return virtual_machine.get_info(vcenter, the_vm, username, ensure_ip=True)


def delete_gateway(username, logger):
    """Unregister and destroy the defaultGateway virtual machine

    :Returns: None

    :param username: The user who wants to delete their defaultGateway
    :type username: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == COMPONENT_NAME:
                logger.debug('powering off VM')
                virtual_machine.power(entity, state='off')
                delete_task = entity.Destroy_Task()
                logger.debug('blocking while VM is being destroyed')
                consume_task(delete_task)


def _create_network_map(vcenter, ova, wan, lan, logger):
    """Map the OVA networks to available networks in vCenter

    :Returns: List

    :param vcenter: The instantiated connection to vCenter
    :type vcenter: vlab_inf_common.vmware.vCenter

    :param ova: The instantiated OVA object
    :type ova: vlab_inf_common.vmware.Ova

    :param wan: The name of the network to use in vCenter for the WAN network
    :type wan: String

    :param lan: The name of the network to use in vCenter for the LAN network
    :type lan: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    network_map = []
    ova_networks = ova.networks
    for network in ova_networks:
        a_map = vim.OvfManager.NetworkMapping()
        if network.lower() == 'wan':
            a_map.name = network
            try:
                a_map.network = vcenter.networks[wan]
            except KeyError:
                error = 'No such network for WAN: {}'.format(wan)
                raise ValueError(error)
            network_map.append(a_map)
        elif network.lower() == 'lan':
            a_map.name = network
            try:
                a_map.network = vcenter.networks[lan]
            except KeyError:
                error = 'No such network for LAN: {}'.format(lan)
                raise ValueError(error)
            network_map.append(a_map)
        else:
            error = "Unexpected network found defined in OVA: {}".format(network)
            raise RuntimeError(error)
    logger.debug('Created network map: {}'.format(network_map))
    return network_map


def resolve_name(name):
    """Resolve a DNS name into an IP address

    :Returns: String

    :param name: The FQDN to resolve
    :type name: String
    """
    hostname, aliases, addr = socket.gethostbyname_ex(name)
    return addr[0]


def _setup_gateway(vcenter, the_vm, username, gateway_version, logger):
    """Initialize the new gateway for the user

    :Returns: None

    :param vcenter: The instantiated connection to vCenter
    :type vcenter: vlab_inf_common.vmware.vCenter

    :param the_vm: The new gateway
    :type the_vm: vim.VirtualMachine
    """
    time.sleep(120) # Let the VM fully boot
    vlab_ip = resolve_name(const.VLAB_URL.replace('https://', '').replace('http://', ''))
    cmd1 = '/usr/bin/sudo'
    args1 = '/usr/bin/hostnamectl set-hostname {}'.format(username)
    result1 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd1,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args1)
    if result1.exitCode:
        logger.error('Failed to set hostname to {}'.format(username))

    # Updating hostname fixes SPAM when SSH into box about "failure to resolve <host>"
    cmd2 = '/usr/bin/sudo'
    args2 = "/bin/sed -i -e 's/ipam/{}/g' /etc/hosts".format(username)
    result2 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd2,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args2)
    if result2.exitCode:
        logger.error('Failed to fix hostname SPAM')

    # Fix the env var for the log_sender
    cmd3 = '/usr/bin/sudo'
    args3 = "/bin/sed -i -e 's/VLAB_LOG_TARGET=localhost:9092/VLAB_LOG_TARGET={}/g' /etc/environment".format(const.VLAB_IPAM_BROKER)
    result3 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd3,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args3)
    if result3.exitCode:
        logger.error('Failed to set IPAM log-sender address')

    # Set the encryption key for log_sender
    cmd4 = '/usr/bin/sudo'
    args4 = "/bin/sed -i -e 's/changeME/{}/g' /etc/vlab/log_sender.key".format(const.VLAB_IPAM_KEY)
    result4 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd4,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args4)
    if result4.exitCode:
        logger.error('Failed to set IPAM encryption key')
        logger.error('CMD: {} {}'.format(cmd4, args4))
        logger.error('Result: \n{}'.format(result4))

    cmd5 = '/usr/bin/sudo'
    args5 = "/bin/sed -i -e 's/VLAB_URL=https:\/\/localhost/VLAB_URL={}/g' /etc/environment".format(const.VLAB_URL.replace('/', '\/'))
    result5 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd5,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args5)
    if result5.exitCode:
        logger.error('Failed to set VLAB_URL environment variable')


    cmd6 = '/usr/bin/sudo'
    args6 = "/bin/sed -i -e 's/PRODUCTION=false/PRODUCTION=beta/g' /etc/environment"
    result6 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd6,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args6)
    if result6.exitCode:
        logger.error('Failed to set PRODUCTION environment variable')

    cmd7 = '/usr/bin/sudo'
    args7 = "/bin/sed -i -e 's/1.us.pool.ntp.org/{}/g' /etc/chrony/chrony.conf".format(vlab_ip)
    result7 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd7,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args7)
    if result7.exitCode:
        logger.error('Failed to set NTP server')

    cmd8 = '/usr/bin/sudo'
    args8 = "/bin/sed -i -e 's/VLAB_DDNS_KEY=aabbcc/VLAB_DDNS_KEY={}/g' /etc/environment".format(const.VLAB_DDNS_KEY)
    result8 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd8,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args8)
    if result8.exitCode:
        logger.error('Failed to configure DDNS settings')

    cmd9 = '/usr/bin/sudo'
    args9 = "sed -i -e 's/8.8.8.8/{}/g' /etc/bind/named.conf".format(vlab_ip)
    result9 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd9,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args9)
    if result9.exitCode:
        logger.error('Failed to configure DNS forwarder')

    # *MUST* happen after setting up the hostname otherwise the salt-minion will
    # use the default hostname when registering with the salt-master
    cmd10 = '/usr/bin/sudo'
    args10 = "/bin/systemctl enable salt-minion.service"
    result10 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd10,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args10)
    if result10.exitCode:
        logger.error('Failed to enable Config Mgmt Software')


    cmd11 = '/usr/bin/sudo'
    args11 = "/bin/sed -i -e 's/#master: salt/master: {}/g' /etc/salt/minion".format(vlab_ip)
    result11 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd11,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args11)
    if result11.exitCode:
        logger.error('Failed to configure Config Mgmt Software')


    cmd12 = '/usr/bin/sudo'
    args12 = "/bin/sed -i -e 's/$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat/#$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat/g' /etc/rsyslog.conf"
    result12 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd12,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args12)
    if result12.exitCode:
        logger.error('Failed to set kern.log timestamp format')

    cmd13 = '/usr/bin/sudo'
    args13 = '/sbin/reboot'
    result13 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd13,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args13,
                                          one_shot=True)
    if result13.exitCode:
        logger.error('Failed to reboot IPAM server')

    meta_data = {'component': 'defaultGateway',
                 'created': time.time(),
                 'version': gateway_version,
                 'configured': True,
                 'generation': 1}
    virtual_machine.set_meta(the_vm, meta_data)
    time.sleep(60) # Give the box time to power cycles
