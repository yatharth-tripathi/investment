from typing import List, Dict, Optional
from .consensus_node import ConsensusNode
from .message_types import Proposal, Vote

class ByzantineBroadcast:
    def __init__(self, nodes: List[ConsensusNode]):
        self.nodes = nodes
        self.total_nodes = len(nodes)
        self.current_round = 0
        self.round_results: Dict[int, bool] = {}
        
    def propose_trade(self, proposer_id: int, trade_data: dict) -> int:
        """Start consensus process for a trade."""
        self.current_round += 1
        round_num = self.current_round
        
        # Step 1: Proposer creates proposal
        proposer = self.nodes[proposer_id]
        proposal = proposer.create_proposal(trade_data, round_num)
        
        # Step 2: Broadcast proposal to all nodes
        for node in self.nodes:
            node.received_proposals[round_num] = proposal
            
        # Step 3: Each node votes
        votes = []
        for node in self.nodes:
            if node.is_honest:  # Only honest nodes participate
                vote = node.vote_on_proposal(proposal)
                votes.append(vote)
        
        # Step 4: Broadcast votes to all nodes
        for node in self.nodes:
            for vote in votes:
                node.receive_vote(vote)
                
        # Step 5: Check for consensus
        consensus_result = self.nodes[0].check_consensus(round_num)
        if consensus_result is not None:
            self.round_results[round_num] = consensus_result
            
        return round_num
    
    def get_consensus_result(self, round_num: int) -> Optional[bool]:
        """Get consensus result for specific round."""
        return self.round_results.get(round_num)
    
    def simulate_consensus_rounds(self, trades_data: List[dict]) -> Dict[int, bool]:
        """Simulate multiple consensus rounds."""
        results = {}
        
        for i, trade_data in enumerate(trades_data):
            proposer_id = i % self.total_nodes
            round_num = self.propose_trade(proposer_id, trade_data)
            result = self.get_consensus_result(round_num)
            results[round_num] = result
            
        return results
