############
vLab Gateway
############

This service enables users to have their own private network. It does this by
NATing the public network to the user's private vLANs.


The default configuration is to use a DHCP address for the WAN, and NAT to
192.168.1.1/24. Port forwarding rules are already configured for SSH and RDP; this
way you can access your jumpbox without additional configuration. The port forwarding
rules assume your jumpbox own IP 192.168.1.2.

The Firewall has a web GUI accessible over HTTPS on port 444.
