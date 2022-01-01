# In Development // Not Working

![Logo](detux.png)
## The Multiplatform Linux Sandbox


### Introduction:
DetuxNG is a sandbox developed to do magic


### Setup:

1: Create Virtual Machines
 - Bash scripts will do net installs
 - power off vm
 - take snapshot

(Win10):
    Enable SSH server
    https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse
    https://winaero.com/enable-openssh-server-windows-10/
    
2: Verify working
 - virsh list --all              # List VMs
 - virsh net-dhcp-leases default # Get IPs of hosts

3: Auto-generate config?








### Contributers / Thanks:
Following is a list of early developers and contributors that we'd like to thank for their help.
- Vikas Iyengar - The brain ( [dudeintheshell](https://github.com/dudeintheshell) , email: iyengar.vikas@gmail.com ) 
- Muslim Koser - Technichal thought works (muslimk@gmail.com)
- Rahul Binjve - Help in pcap parsing ([@c0dist](https://github.com/c0dist), [twitter](https://twitter.com/c0dist))
- Amey Gat - Help in pcap parsing ([ameygat](https://github.com/ameygat), ameygat@gmail.com )
- Thanks to Aurélien Jarno (@aurel32) (https://www.aurel32.net/) for the pre-built VM images.
- Joe Stewart (@joestewart71) for developing Truman years ago and the immeasurable amount he's done. 
