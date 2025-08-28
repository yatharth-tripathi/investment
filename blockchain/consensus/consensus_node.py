import random
from typing import Dict, List, Set, Optional
from .message_types import Message, Vote, Proposal, MessageType

class ConsensusNode:
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.is_honest = True
        self.received_votes: Dict[int, List[Vote]] = {}  # round -> votes
        self.received_proposals: Dict[int, Proposal] = {}  # round -> proposal
        self.decisions: Dict[int, bool] = {}  # round -> final decision
        
    def create_proposal(self, trade_data: dict, round_num: int) -> Proposal:
        """Create a new trade proposal."""
        return Proposal(self.node_id, trade_data, round_num)
    
    def vote_on_proposal(self, proposal: Proposal) -> Vote:
        """Vote on a received proposal."""
        # Simple voting logic - accept if trade value is reasonable
        trade_value = proposal.trade_data.get('value', 0)
        decision = trade_value > 0 and trade_value < 1000000  # Basic validation
        
        return Vote(self.node_id, decision, proposal.round_number)
    
    def receive_vote(self, vote: Vote):
        """Process received vote."""
        round_num = vote.round_number
        if round_num not in self.received_votes:
            self.received_votes[round_num] = []
        self.received_votes[round_num].append(vote)
    
    def check_consensus(self, round_num: int) -> Optional[bool]:
        """Check if consensus reached for given round."""
        if round_num not in self.received_votes:
            return None
            
        votes = self.received_votes[round_num]
        if len(votes) < (2 * self.total_nodes // 3) + 1:  # Need 2f+1 votes
            return None
            
        accept_votes = sum(1 for vote in votes if vote.decision)
        reject_votes = len(votes) - accept_votes
        
        return accept_votes > reject_votes
