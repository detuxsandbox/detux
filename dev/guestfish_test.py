
import sys
import guestfs

if len(sys.argv) < 2:
    print("inspect_vm: missing disk image to inspect", file=sys.stderr)
    sys.exit(1)
disk = sys.argv[1]

g = guestfs.GuestFS(python_return_dict=True)
g.add_drive_opts(disk, readonly=1)

g.launch()

roots = g.inspect_os()
if len(roots) == 0:
    print("inspect_vm: no operating systems found", file=sys.stderr)
    sys.exit(1)

for root in roots:
    print("Root device: %s" % root)

    print("  Product name: %s" % (g.inspect_get_product_name(root)))
    print("  Version:      %d.%d" %
          (g.inspect_get_major_version(root),
           g.inspect_get_minor_version(root)))
    print("  Type:         %s" % (g.inspect_get_type(root)))
    print("  Distro:       %s" % (g.inspect_get_distro(root)))

    mps = g.inspect_get_mountpoints(root)
    for device, mp in sorted(mps.items(), key=lambda k: len(k[0])):
        try:
            g.mount_ro(mp, device)
        except RuntimeError as msg:
            print("%s (ignored)" % msg)

    filename = "/etc/issue.net"
    if g.is_file(filename):
        print("--- %s ---" % filename)
        lines = g.cat(filename)
        print(lines)

    g.umount_all()