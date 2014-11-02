import os
from mcpi.minecraft import Minecraft
from mcpi.connection import Connection

# We can develop on one machine and test on another.  Using an
# ethernet cable can be a convenient way to do this.  Here's how.

# http://www.linuxcircle.com/2013/05/03/connecting-rpi-to-laptop-ethernet/

# $ less /etc/network/interfaces
# iface eth0 inet static
#    address 192.168.2.2
#    netmask 255.255.255.0
#    network 192.168.2.0

# $ sudo ifup eth0

# $ export RASPI="192.168.2.3"


def smoke_test(world):

    world.postToChat('smoke test')
    world.player.getPos()


if __name__ == '__main__':

    RASPI = os.environ.get('RASPI', 'localhost')
    conn = Connection(address=RASPI, port=4711)
    world = Minecraft(conn)

    smoke_test(world)
    print('OK')
