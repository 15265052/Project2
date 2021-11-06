"""Node11"""

from MAC import *

Node1 = MAC("Node1")
Node1_Tx = Tx()
Node1_Rx = Rx()

Node1.start()
Node1_Tx.start()
Node1_Rx.start()

stream = set_stream()
stream.start()
