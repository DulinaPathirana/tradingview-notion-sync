#!/usr/bin/env python3
"""
TradingView to Notion Sync
Parse TradingView paper trading CSV exports and sync completed trades to Notion.
"""

import csv
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
import requests

# Configuration
class Config:
    NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID', '')
    CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', 'trades.csv')
    
    @classmethod
    def validate(cls):
        if not cls.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY environment variable not set")
        if not cls.NOTION_DATABASE_ID:
            raise ValueError("NOTION_DATABASE_ID environment variable not set")

class TradeOrder:
    """Represents a single order from TradingView CSV"""
    def __init__(self, row: Dict):
        self.symbol = row.get('Symbol', '').strip()
        self.side = row.get('Side', '').strip()  # Buy or Sell
        self.order_type = row.get('Type', '').strip()
        self.qty = float(row.get('Qty', 0) or 0)
        self.limit_price = float(row.get('Limit Price', 0) or 0)
        self.stop_price = float(row.get('Stop Price', 0) or 0)
        self.fill_price = float(row.get('Fill Price', 0) or 0)
        self.status = row.get('Status', '').strip()
        self.placing_time = row.get('Placing Time', '').strip()
        self.closing_time = row.get('Closing Time', '').strip()
        self.order_id = row.get('Order ID', '').strip()
        
    def is_filled(self) -> bool:
        return self.status == 'Filled'
    
    def is_buy(self) -> bool:
        return self.side == 'Buy'
    
    def is_sell(self) -> bool:
        return self.side == 'Sell'

class Trade:
    """Represents a completed trade (Buy + Sell pair)"""
    def __init__(self, symbol: str, buy_order: TradeOrder, sell_order: TradeOrder):
        self.symbol = symbol
        self.buy_order = buy_order
        self.sell_order = sell_order
        
    @property
    def entry_price(self) -> float:
        return self.buy_order.fill_price
    
    @property
    def exit_price(self) -> float:
        return self.sell_order.fill_price
    
    @property
    def position_size(self) -> float:
        return min(self.buy_order.qty, self.sell_order.qty)
    
    @property
    def pnl_dollars(self) -> float:
        return (self.exit_price - self.entry_price) * self.position_size
    
    @property
    def pnl_percent(self) -> float:
        if self.entry_price == 0:
            return 0
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def result(self) -> str:
        if self.pnl_dollars > 0:
            return 'Win'
        elif self.pnl_dollars < 0:
            return 'Loss'
        return 'Breakeven'
    
    @property
    def entry_date(self) -> str:
        return self.buy_order.closing_time
    
    @property
    def exit_date(self) -> str:
        return self.sell_order.closing_time

def parse_csv(file_path: str) -> List[TradeOrder]:
    """Parse TradingView CSV file"""
    orders = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order = TradeOrder(row)
                if order.is_filled():
                    orders.append(order)
        print(f"Parsed {len(orders)} filled orders from CSV")
        return orders
    except FileNotFoundError:
        print(f"Error: CSV file not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}")
        return []

def match_trades(orders: List[TradeOrder]) -> List[Trade]:
    """Match Buy and Sell orders to create complete trades"""
    # Group orders by symbol
    by_symbol = defaultdict(lambda: {'buys': [], 'sells': []})
    
    for order in orders:
        if order.is_buy():
            by_symbol[order.symbol]['buys'].append(order)
        elif order.is_sell():
            by_symbol[order.symbol]['sells'].append(order)
    
    # Match buys with sells
    trades = []
    for symbol, orders_dict in by_symbol.items():
        buys = sorted(orders_dict['buys'], key=lambda x: x.closing_time)
        sells = sorted(orders_dict['sells'], key=lambda x: x.closing_time)
        
        # Simple FIFO matching
        for buy in buys:
            for sell in sells:
                # Match if sell happened after buy and quantities are compatible
                if sell.closing_time > buy.closing_time and sell.qty > 0 and buy.qty > 0:
                    trade = Trade(symbol, buy, sell)
                    trades.append(trade)
                    
                    # Reduce quantities for partial fills
                    matched_qty = min(buy.qty, sell.qty)
                    buy.qty -= matched_qty
                    sell.qty -= matched_qty
                    
                    if buy.qty == 0:
                        break
    
    print(f"Matched {len(trades)} complete trades")
    return trades

def create_notion_page(trade: Trade) -> Dict:
    """Create Notion database entry for a trade"""
    return {
        "parent": {"database_id": Config.NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"{trade.symbol} - {trade.entry_date[:10]}"
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": parse_notion_date(trade.entry_date)
                }
            },
            "Symbol": {
                "rich_text": [
                    {
                        "text": {
                            "content": trade.symbol
                        }
                    }
                ]
            },
            "Direction": {
                "select": {
                    "name": "Long"
                }
            },
            "Entry Price": {
                "number": trade.entry_price
            },
            "Exit Price": {
                "number": trade.exit_price
            },
            "Position Size": {
                "number": trade.position_size
            },
            "P/L ($)": {
                "number": round(trade.pnl_dollars, 2)
            },
            "P/L (%)": {
                "number": round(trade.pnl_percent, 2)
            },
            "Result": {
                "select": {
                    "name": trade.result
                }
            }
        }
    }

def parse_notion_date(date_str: str) -> str:
    """Convert TradingView date format to Notion ISO format"""
    try:
        # TradingView format: "2025-10-30 142210"
        dt = datetime.strptime(date_str, "%Y-%m-%d %H%M%S")
        return dt.isoformat()
    except:
        return datetime.now().isoformat()

def sync_to_notion(trades: List[Trade]):
    """Sync trades to Notion database"""
    headers = {
        "Authorization": f"Bearer {Config.NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    success_count = 0
    for trade in trades:
        try:
            page_data = create_notion_page(trade)
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=page_data
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"✓ Synced: {trade.symbol} | P/L: ${trade.pnl_dollars:.2f}")
            else:
                print(f"✗ Failed: {trade.symbol} | Error: {response.text}")
        except Exception as e:
            print(f"✗ Error syncing {trade.symbol}: {str(e)}")
    
    print(f"\nSynced {success_count}/{len(trades)} trades to Notion")

def main():
    print("=== TradingView to Notion Sync ===")
    print()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease set the following environment variables:")
        print("  NOTION_API_KEY - Your Notion integration token")
        print("  NOTION_DATABASE_ID - Your Notion database ID")
        print("  CSV_FILE_PATH - Path to TradingView CSV file (optional)")
        return
    
    # Parse CSV
    orders = parse_csv(Config.CSV_FILE_PATH)
    if not orders:
        print("No orders found in CSV file")
        return
    
    # Match trades
    trades = match_trades(orders)
    if not trades:
        print("No complete trades found")
        return
    
    # Sync to Notion
    sync_to_notion(trades)
    print("\nSync complete!")

if __name__ == "__main__":
    main()
