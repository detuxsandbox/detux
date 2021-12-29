# Example showing how to inspect a virtual machine disk.

import sys
import guestfs

if len(sys.argv) < 3:
    print("inspect_vm: missing disk image to inspect", file=sys.stderr)
    sys.exit(1)
disk = sys.argv[1]
payload = sys.argv[2]


g = guestfs.GuestFS(python_return_dict=True)
g.add_drive_opts(disk, readonly=1)
g.launch()

# Ask libguestfs to inspect for operating systems.
roots = g.inspect_os()
if len(roots) == 0:
    print("inspect_vm: no operating systems found", file=sys.stderr)
    sys.exit(1)

for root in roots:
    print("Root device: %s" % root)
    mps = g.inspect_get_mountpoints(root)
    for device, mp in sorted(mps.items(), key=lambda k: len(k[0])):
        try:
            g.mount(mp, device)
        except RuntimeError as msg:
            print("%s (ignored)" % msg)




    # If /etc/issue.net file exists, print up to 3 lines.
    filename = "/etc/issue.net"
    if g.is_file(filename):
        print("--- %s ---" % filename)
        lines = g.head_n(3, filename)
        for line in lines:
            print(line)

    # Unmount everything.
    g.umount_all()