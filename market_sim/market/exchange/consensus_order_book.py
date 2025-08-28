
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from blockchain.consensus import ByzantineBroadcast, ConsensusNode
import time

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: int
    price: Decimal
    trader_id: str
    timestamp: float

@dataclass
class Trade:
    trade_id: str
    symbol: str
    quantity: int
    price: Decimal
    buyer_id: str
    seller_id: str
    timestamp: float
    consensus_validated: bool = False

class ConsensusOrderBook:
    """Order book that uses consensus for large trade validation."""
    
    def __init__(self, symbol: str, consensus_threshold: Decimal = Decimal('100000')):
        self.symbol = symbol
        self.consensus_threshold = consensus_threshold
        
        # Consensus system
        self.consensus_nodes = [ConsensusNode(i, 4) for i in range(4)]
        self.consensus_system = ByzantineBroadcast(self.consensus_nodes)
        
        # Order book data
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.executed_trades: List[Trade] = []
        
    def add_order(self, order: Order) -> bool:
        """Add order to book and attempt matching."""
        if order.side == "buy":
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda x: x.price, reverse=True)  # Highest price first
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda x: x.price)  # Lowest price first
            
        return self._try_match_orders()
    
    def _try_match_orders(self) -> bool:
        """Attempt to match buy and sell orders."""
        if not self.buy_orders or not self.sell_orders:
            return False
            
        buy_order = self.buy_orders[0]
        sell_order = self.sell_orders[0]
        
        # Check if prices cross
        if buy_order.price >= sell_order.price:
            trade_price = sell_order.price  # Use ask price
            trade_quantity = min(buy_order.quantity, sell_order.quantity)
            trade_value = trade_price * trade_quantity
            
            # Create potential trade
            potential_trade = Trade(
                trade_id=f"T_{len(self.executed_trades)+1}",
                symbol=self.symbol,
                quantity=trade_quantity,
                price=trade_price,
                buyer_id=buy_order.trader_id,
                seller_id=sell_order.trader_id,
                timestamp=time.time()
            )
            
            # Use consensus for large trades
            if trade_value >= self.consensus_threshold:
                return self._consensus_validate_trade(potential_trade)
            else:
                return self._execute_trade(potential_trade)
                
        return False
    
    def _consensus_validate_trade(self, trade: Trade) -> bool:
        """Validate trade through consensus mechanism."""
        trade_data = {
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "price": float(trade.price),
            "value": float(trade.price * trade.quantity),
            "buyer": trade.buyer_id,
            "seller": trade.seller_id
        }
        
        round_num = self.consensus_system.propose_trade(0, trade_data)
        consensus_result = self.consensus_system.get_consensus_result(round_num)
        
        if consensus_result:
            trade.consensus_validated = True
            return self._execute_trade(trade)
        else:
            print(f"Trade {trade.trade_id} rejected by consensus")
            return False
    
    def _execute_trade(self, trade: Trade) -> bool:
        """Execute the validated trade."""
        # Remove/update orders
        buy_order = self.buy_orders[0]
        sell_order = self.sell_orders[0]
        
        buy_order.quantity -= trade.quantity
        sell_order.quantity -= trade.quantity
        
        if buy_order.quantity == 0:
            self.buy_orders.pop(0)
        if sell_order.quantity == 0:
            self.sell_orders.pop(0)
            
        # Record trade
        self.executed_trades.append(trade)
        print(f"Executed trade: {trade.trade_id} - {trade.quantity} {trade.symbol} @ {trade.price}")
        return True
    
    def get_order_book_state(self) -> Dict:
        """Get current order book state."""
        return {
            "symbol": self.symbol,
            "bids": [(o.price, o.quantity) for o in self.buy_orders[:5]],
            "asks": [(o.price, o.quantity) for o in self.sell_orders[:5]],
            "last_trades": self.executed_trades[-10:]
        }
