"""Node2"""

from MAC import *

Node1 = MAC("Node2")
Node1_Tx = Tx()
Node1_Rx = Rx()

Node1.start()
Node1_Tx.start()
Node1_Rx.start()

stream = set_stream()
stream.start()