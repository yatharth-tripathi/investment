"""Integration test for market making scenario."""

import pytest
from datetime import timedelta
import numpy as np
from simulation.scenarios.market_making_scenario import create_market_making_scenario
from core.utils.time_utils import utc_now

def test_market_making_scenario():
    """Test basic market making scenario execution."""
    # Setup
    start_time = utc_now()
    duration = timedelta(minutes=5)  # Shorter duration for tests
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Create and run simulation
    sim = create_market_making_scenario(
        start_time=start_time,
        duration=duration,
        symbols=symbols,
        num_random_traders=5,
        include_market_events=True
    )
    results = sim.run()

    print("")
    print("###########################################################")
    print("Testing market making scenario...")
    print("Number of trades: ", len(results['trades']))
    print("###########################################################")
    
    # Basic assertions
    assert len(results['trades']) > 0, "No trades were executed"
    assert len(results['metrics']['market_metrics']) > 0, "No market metrics were collected"
    assert len(results['metrics']['agent_metrics']) > 0, "No agent metrics were collected"
    
    # Check market maker behavior
    market_maker_metrics = [
        m for m in results['metrics']['agent_metrics'] 
        if m['agent_id'] == "MM_001"
    ]
    assert len(market_maker_metrics) > 0, "No market maker metrics found"
    
    # Verify price continuity
    for symbol in symbols:
        symbol_trades = [t for t in results['trades'] if t.symbol == symbol]
        if symbol_trades:
            prices = [float(t.price) for t in symbol_trades]
            
            # Check price reasonableness
            assert min(prices) > 0, f"Invalid prices found for {symbol}"
            assert np.std(prices) > 0, f"No price variation for {symbol}"
            
            # Check spread maintenance
            market_metrics = [
                m for m in results['metrics']['market_metrics']
                if m['symbol'] == symbol
            ]
            spreads = [m['spread_pct'] for m in market_metrics]
            assert all(s > 0 for s in spreads), f"Zero or negative spreads found for {symbol}"
            
    # Verify market events were processed
    market_events = [
        e for e in sim.event_queue 
        if e.event_type == 'market_event'
    ]
    assert len(market_events) > 0, "No market events were scheduled" 