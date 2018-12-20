# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
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
                info = virtual_machine.get_info(vcenter, vm)
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
        return virtual_machine.get_info(vcenter, the_vm)


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


def _setup_gateway(vcenter, the_vm, username, gateway_version, logger):
    """Initialize the new gateway for the user

    :Returns: None

    :param vcenter: The instantiated connection to vCenter
    :type vcenter: vlab_inf_common.vmware.vCenter

    :param the_vm: The new gateway
    :type the_vm: vim.VirtualMachine
    """
    time.sleep(120) # Let the VM fully boot
    cmd1 = '/usr/bin/sudo'
    the_hostname = '{}.vlab.{}'.format(username, const.VLAB_DOMAIN)
    args1 = '/usr/bin/hostnamectl set-hostname {}'.format(the_hostname)
    result1 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd1,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args1)
    if result1.exitCode:
        logger.error('Failed to set hostname to {}'.format(the_hostname))

    # Fix the env var for the log_sender
    cmd2 = '/usr/bin/sudo'
    args2 = "/bin/sed -i -e 's/VLAB_LOG_TARGET=localhost:9092/VLAB_LOG_TARGET={}/g' /etc/environment".format(const.VLAB_IPAM_BROKER)
    result2 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd2,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args2)
    if result2.exitCode:
        logger.error('Failed to set IPAM log-sender address')

    # Set the encryption key for log_sender
    cmd3 = '/usr/bin/sudo'
    args3 = "/bin/sed -i -e 's/changeME/{}/g' /etc/vlab/log_sender.key".format(const.VLAB_IPAM_KEY)
    result3 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd3,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args3)
    if result3.exitCode:
        logger.error('Failed to set IPAM encryption key')
        logger.error('CMD: {} {}'.format(cmd3, args3))
        logger.error('Result: \n{}'.format(result3))

    # Restart log sender; should work now
    cmd4= '/usr/bin/sudo'
    args4 = '/bin/systemctl restart vlab-log-sender'
    result4 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd4,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args4)
    if result4.exitCode:
        logger.error('Failed to restart vlab-log-sender')

    cmd5 = '/usr/bin/sudo'
    args5 = "/bin/sed -i -e 's/VLAB_URL=https:\/\/localhost/VLAB_LOG_TARGET={}/g' /etc/environment".format(const.VLAB_URL.replace('/', '\/'))
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
    args7 = '/sbin/reboot'
    result7 = virtual_machine.run_command(vcenter,
                                          the_vm,
                                          cmd6,
                                          user=const.VLAB_IPAM_ADMIN,
                                          password=const.VLAB_IPAM_ADMIN_PW,
                                          arguments=args7,
                                          one_shot=True)
    if result7.exitCode:
        logger.error('Failed to reboot IPAM server')

    meta_data = {'component': 'defaultGateway',
                 'created': time.time(),
                 'version': gateway_version,
                 'configured': True,
                 'generation': 1}
    virtual_machine.set_meta(the_vm, meta_data)
    time.sleep(60) # Give the box time to power cycles
