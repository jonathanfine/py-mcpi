'''Record and replay

We can record behaviour and play it back again.  This provides a form
of testing, without needing a real server.  It also provides
reproducibility of testing.  This is, if you like, a simple form of
mock objects.

This is a proof-of-concept implementation.  It requires refinement.
The key thing is that at the end we record interaction with a real
Minecraft server, and then replay that interaction back, without using
a real Minecraft server.

This code needs a refactor, and then it might be possible to start
running and accumulating test scripts. This approach should be
particularly good for backwards compatibility.

'''

from __future__ import print_function

import os
from mcpi.minecraft import Minecraft
from mcpi.connection import Connection
import operator

__metaclass__ = type


# The names of the methods we will be testing.
CONNECTION_NAMES = ['drain', 'send', 'receive', 'sendReceive']

MINECRAFT_NAMES = [

    # Object itself methods.
    'getBlock',
    'getBlockWithData',
    'getBlocks',
    'setBlock',
    'setBlocks',
    'getHeight',
    'getPlayerEntityIds',
    'saveCheckpoint',
    'restoreCheckpoint',
    'postToChat',
    'setting',

    # Camera methods.
    'camera.setNormal',
    'camera.setFixed',
    'camera.setFollow',
    'camera.setPos',

    # Entity methods - inherited from CmdPositioner.
    'entity.getPos',
    'entity.setPos',
    'entity.getTilePos',
    'entity.setTilePos',
    'entity.setting',

    # Event methods.
    'events.clearAll',
    'events.pollBlockHits',

    # Player methods.
    'player.getPos',
    'player.setPos',
    'player.getTilePos',
    'player.setTilePos',
    'player.setting',
]


class Bunch:
    pass


class Logger:

    def __init__(self, log):
        self.log = log


    def _enter(self, key, name, args, kwargs):
        self.log.append(('enter', key, name, args, kwargs))


    def _exit(self, key, name, value):
        self.log.append(('exit', key, name, value))


    def wrap_fn(self, key, name, fn):

        def fn_wrapped(*args, **kwargs):

            self._enter(key, name, args, kwargs)
            value = fn(*args, **kwargs)
            self._exit(key, name, value)
            return value

        return fn_wrapped


    def wrap(self, obj, key, names):

        wrapped = Bunch()

        for name in names:

            # This will fetch obj.first.second etc.
            fn = operator.attrgetter(name)(obj)

            # Prepare to deal with segmented names.
            segs = name.split('.')
            curr = wrapped
            for seg in segs[:-1]:

                # Track down through the segments.
                if not hasattr(curr, seg):
                    setattr(curr, seg, Bunch())
                curr = getattr(curr, seg)

            # Add the wrapped function at the end of the chain.
            setattr(curr, segs[-1], self.wrap_fn(key, name, fn))

        return wrapped


# This is related to Minecraft.
def logged_connect(log, conn):

    logger = Logger(log)
    conn = logger.wrap(conn, 'conn', CONNECTION_NAMES)
    world = Minecraft(conn)
    world = logger.wrap(world, 'world', MINECRAFT_NAMES)

    return world


# A connection that responds according to a script.
class DummyConn:

    def __init__(self, log, live):
        self.log = log
        self.live = live

    def drain(self, *args, **kwargs):

        locn = len(self.live)
        return self.log[locn][-1]

    receive = drain
    send = drain
    sendReceive = drain


# Script + connection --> log / transcript.
# TODO: Should this be a method of log?
def record(log, script, conn):

    world = logged_connect(log, conn)
    script(world)


# Here's a test script we can run on a world.
def script(world):

    world.postToChat('hi')
    pos = world.player.getPos()
    world.camera.setPos(36, 40, 14)


if __name__ == '__main__':

    # Create a connection to a real Minecraft server.
    RASPI = os.environ.get('RASPI', 'localhost')
    conn = Connection(address=RASPI, port=4711)

    # Create a log of our interaction with the real server.
    log = []
    record(log, script, conn)

    for item in log:
        print(item)
    print()


    # Create a replaying connection object, which has access to what
    # will be the live log.
    live = []
    conn = DummyConn(log, live)

    # Create a log of interactions, but through a replaying connection.
    record(live, script, conn)

    for item in live:
        print(item)
    print()

    assert live == log
