from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

class MessageType(Enum):
    PROPOSAL = "proposal"
    VOTE = "vote"
    DECISION = "decision"

@dataclass
class Message:
    sender_id: int
    message_type: MessageType
    content: Any
    round_number: int
    signature: Optional[str] = None
    
class Vote:
    def __init__(self, voter_id: int, decision: bool, round_num: int):
        self.voter_id = voter_id
        self.decision = decision  # True = accept, False = reject
        self.round_number = round_num
        
class Proposal:
    def __init__(self, proposer_id: int, trade_data: dict, round_num: int):
        self.proposer_id = proposer_id
        self.trade_data = trade_data
        self.round_number = round_num
