from .consensus_node import ConsensusNode
from .byzantine_broadcast import ByzantineBroadcast

def run_consensus_demo():
    """Demonstrate consensus mechanism working."""
    
    # Create 4 nodes (can tolerate 1 Byzantine fault)
    nodes = [ConsensusNode(i, 4) for i in range(4)]
    
    # Create consensus system
    consensus = ByzantineBroadcast(nodes)
    
    # Sample trades to validate
    sample_trades = [
        {"symbol": "AAPL", "quantity": 100, "price": 150.0, "value": 15000},
        {"symbol": "GOOGL", "quantity": 50, "price": 2000.0, "value": 100000},
        {"symbol": "TSLA", "quantity": 200, "price": 800.0, "value": 160000},
        {"symbol": "INVALID", "quantity": -100, "price": 0, "value": -1000},  # Should be rejected
    ]
    
    print("Running Byzantine Broadcast Consensus Demo")
    print("=" * 50)
    
    results = consensus.simulate_consensus_rounds(sample_trades)
    
    for round_num, result in results.items():
        trade = sample_trades[round_num - 1]
        status = "ACCEPTED" if result else "REJECTED"
        print(f"Round {round_num}: Trade {trade['symbol']} - {status}")
        
    return results

if __name__ == "__main__":
    run_consensus_demo()
