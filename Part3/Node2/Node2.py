"""Node2"""

from MAC import *

Node2 = MAC("Node2")
Node2_Tx = Tx()
Node2_Rx = Rx()

Node2.start()
Node2_Tx.start()
Node2_Rx.start()

stream = set_stream()
stream.start()