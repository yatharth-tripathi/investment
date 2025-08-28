from blockchain.consensus import ByzantineBroadcast, ConsensusNode

class ConsensusOrderBook:
    def __init__(self):
        self.nodes = [ConsensusNode(i, 4) for i in range(4)]
        self.consensus = ByzantineBroadcast(self.nodes)
    
    def validate_large_trade(self, trade_data):
        round_num = self.consensus.propose_trade(0, trade_data)
        return self.consensus.get_consensus_result(round_num)
