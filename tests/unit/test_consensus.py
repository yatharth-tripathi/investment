import pytest
from blockchain.consensus.consensus_node import ConsensusNode
from blockchain.consensus.byzantine_broadcast import ByzantineBroadcast

def test_node_creation():
    node = ConsensusNode(0, 4)
    assert node.node_id == 0
    assert node.total_nodes == 4
    assert node.is_honest == True

def test_consensus_basic():
    nodes = [ConsensusNode(i, 3) for i in range(3)]
    consensus = ByzantineBroadcast(nodes)
    
    trade_data = {"symbol": "TEST", "value": 1000}
    round_num = consensus.propose_trade(0, trade_data)
    
    result = consensus.get_consensus_result(round_num)
    assert result is not None
