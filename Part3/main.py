"""node1: Transmitter"""

from MAC import *

Node1 = MAC("Receiver")
Node1_Tx = Tx()
Node1_Rx = Rx()

Node1.start()
Node1_Tx.start()
Node1_Rx.start()
