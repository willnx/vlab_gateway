# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_gateway_api.lib.worker import vmware


class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""
    @classmethod
    def setUpClass(cls):
        vmware.logger = MagicMock()

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'vCenter')
    def test_show_gateway(self, fake_vCenter, fake_get_info):
        """``show_gateway`` returns a dictionary when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'defaultGateway'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'worked': True}

        output = vmware.show_gateway(username='alice')
        expected = {'worked': True}

        self.assertEqual(output, expected)

    @patch.object(vmware, 'vCenter')
    def test_show_gateway_nothing(self, fake_vCenter):
        """``show_gateway`` returns an empty dictionary no gateway is found"""
        output = vmware.show_gateway(username='alice')
        expected = {}

        self.assertEqual(output, expected)

    @patch.object(vmware, 'Ova')
    @patch.object(vmware, '_setup_gateway')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, '_create_network_map')
    @patch.object(vmware, 'vCenter')
    def test_create_gateway(self, fake_vCenter, fake_create_network_map, fake_deploy_from_ova, fake_get_info, fake_setup_gateway, fake_Ova):
        """``create_gateway`` returns the new gateway's info when everything works"""
        fake_get_info.return_value = {'worked' : True}
        fake_logger = MagicMock()

        output = vmware.create_gateway(username='alice',
                                       wan='someWAN',
                                       lan='someLAN',
                                       logger=fake_logger)
        expected = {'worked': True}

        self.assertEqual(output, expected)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'vCenter')
    def test_delete_gateway(self, fake_vCenter, fake_power, fake_consume_task):
        """``delete_gateway`` powers off the VM then deletes it"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'defaultGateway'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        vmware.delete_gateway(username='alice', logger=fake_logger)

        self.assertTrue(fake_power.called)
        self.assertTrue(fake_vm.Destroy_Task.called)

    def test_create_network_map(self):
        """``_create_network_map`` returns a List when everything works as expected"""
        fake_logger = MagicMock()
        fake_ova = MagicMock()
        fake_ova.networks = ['wan', 'lan']
        fake_vcenter = MagicMock()
        wan = vmware.vim.Network(moId='asdf')
        lan = vmware.vim.Network(moId='asdf')
        fake_vcenter.networks = {'someWAN' : wan, 'someLAN': lan}

        output = vmware._create_network_map(vcenter=fake_vcenter,
                                            ova=fake_ova,
                                            wan='someWAN',
                                            lan='someLAN',
                                            logger=fake_logger)

        self.assertTrue(isinstance(output, list))

    def test_create_network_map_bad_wan(self):
        """``_create_network_map`` raises ValueError when the supplied WAN doesn't exist"""
        fake_logger = MagicMock()
        fake_ova = MagicMock()
        fake_ova.networks = ['wan', 'lan']
        fake_vcenter = MagicMock()
        wan = vmware.vim.Network(moId='asdf')
        lan = vmware.vim.Network(moId='asdf')
        fake_vcenter.networks = {'someWAN' : wan, 'someLAN': lan}

        with self.assertRaises(ValueError):
            vmware._create_network_map(vcenter=fake_vcenter,
                                        ova=fake_ova,
                                        wan='dohWAN',
                                        lan='someLAN',
                                        logger=fake_logger)


    def test_create_network_map_bad_lan(self):
        """``_create_network_map`` raises ValueError when the supplied LAN doesn't exist"""
        fake_logger = MagicMock()
        fake_ova = MagicMock()
        fake_ova.networks = ['wan', 'lan']
        fake_vcenter = MagicMock()
        wan = vmware.vim.Network(moId='asdf')
        lan = vmware.vim.Network(moId='asdf')
        fake_vcenter.networks = {'someWAN' : wan, 'someLAN': lan}

        with self.assertRaises(ValueError):
            vmware._create_network_map(vcenter=fake_vcenter,
                                        ova=fake_ova,
                                        wan='someWAN',
                                        lan='dohLAN',
                                        logger=fake_logger)

    def test_create_network_map_bad_ova(self):
        """``_create_network_map`` raises RuntimeError when the supplied OVA has unexpected networks defined"""
        fake_logger = MagicMock()
        fake_ova = MagicMock()
        fake_ova.networks = ['wan', 'lan', 'doh']
        fake_vcenter = MagicMock()
        wan = vmware.vim.Network(moId='asdf')
        lan = vmware.vim.Network(moId='asdf')
        fake_vcenter.networks = {'someWAN' : wan, 'someLAN': lan}

        with self.assertRaises(RuntimeError):
            vmware._create_network_map(vcenter=fake_vcenter,
                                        ova=fake_ova,
                                        wan='someWAN',
                                        lan='someLAN',
                                        logger=fake_logger)

    @patch.object(vmware.virtual_machine, 'set_meta')
    @patch.object(vmware.time, 'sleep') # so unittests run faster
    @patch.object(vmware.virtual_machine, 'run_command')
    def test_setup_gateway_returns_none(self, fake_run_command, fake_sleep, fake_set_meta):
        """``_setup_gateway`` returns None"""
        fake_logger = MagicMock()
        fake_vcenter = MagicMock()
        fake_vm = MagicMock()
        fake_result = MagicMock()
        fake_result.exitCode = 1
        # one Mock for every setup cmd that gets ran
        fake_run_command.side_effect = [fake_result, MagicMock(), MagicMock(),
                                        MagicMock(),  MagicMock(), MagicMock(),
                                        MagicMock(), MagicMock(), MagicMock(),
                                        MagicMock(), MagicMock(), MagicMock(),
                                        MagicMock()]

        result = vmware._setup_gateway(vcenter=fake_vcenter,
                                       the_vm=fake_vm,
                                       username='jane',
                                       gateway_version='1.0.0',
                                       logger=fake_logger)

        self.assertTrue(result is None)

if __name__ == '__main__':
    unittest.main()
