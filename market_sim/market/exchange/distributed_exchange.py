import time
from typing import Dict, List
from .consensus_order_book import ConsensusOrderBook, Order
from decimal import Decimal

class DistributedExchange:
    """Exchange that uses consensus for critical operations."""
    
    def __init__(self):
        self.order_books: Dict[str, ConsensusOrderBook] = {}
        self.active_symbols = ["AAPL", "GOOGL", "TSLA", "MSFT"]
        
        # Initialize order books for each symbol
        for symbol in self.active_symbols:
            self.order_books[symbol] = ConsensusOrderBook(symbol)
    
    def place_order(self, symbol: str, side: str, quantity: int, 
                   price: float, trader_id: str) -> bool:
        """Place an order on the exchange."""
        if symbol not in self.order_books:
            return False
            
        order = Order(
            order_id=f"O_{trader_id}_{int(time.time()*1000)}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=Decimal(str(price)),
            trader_id=trader_id,
            timestamp=time.time()
        )
        
        return self.order_books[symbol].add_order(order)
    
    def get_market_data(self) -> Dict:
        """Get market data for all symbols."""
        return {
            symbol: book.get_order_book_state() 
            for symbol, book in self.order_books.items()
        }
    
    def simulate_trading_session(self, num_orders: int = 20):
        """Simulate a trading session with random orders."""
        import random
        
        traders = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        
        for i in range(num_orders):
            symbol = random.choice(self.active_symbols)
            side = random.choice(["buy", "sell"])
            quantity = random.randint(10, 1000)
            base_price = {"AAPL": 150, "GOOGL": 2000, "TSLA": 800, "MSFT": 300}
            price = base_price[symbol] + random.uniform(-20, 20)
            trader = random.choice(traders)
            
            print(f"\nOrder {i+1}: {trader} wants to {side} {quantity} {symbol} @ ${price:.2f}")
            result = self.place_order(symbol, side, quantity, price, trader)
            print(f"Order result: {'Executed' if result else 'Added to book'}")
