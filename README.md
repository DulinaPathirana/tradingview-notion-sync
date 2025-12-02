# TradingView to Notion Sync

🚀 Automated synchronization of TradingView paper trading CSV exports to your Notion trading journal.

## Features

- ✅ Parse TradingView paper trading CSV exports
- ✅ Intelligently match Buy/Sell orders into complete trades
- ✅ Automatic P/L calculations (dollars & percentage)
- ✅ Direct sync to Notion database via API
- ✅ Support for multiple symbols and partial fills
- ✅ FIFO (First-In-First-Out) trade matching logic

## Prerequisites

- Python 3.7+
- TradingView paper trading account
- Notion account with API access

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/DulinaPathirana/tradingview-notion-sync.git
cd tradingview-notion-sync
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Setup

### Step 1: Get Your Notion API Key

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Give it a name (e.g., "TradingView Sync")
4. Select your workspace
5. Copy the "Internal Integration Token" (starts with `secret_`)

### Step 2: Get Your Notion Database ID

1. Open your Notion trading logger database
2. Click "Share" in the top right
3. Click "Invite" and add your integration
4. Copy the database ID from the URL:
   ```
   https://www.notion.so/{workspace}/{DATABASE_ID}?v={view_id}
   ```

### Step 3: Export Your TradingView Trades

1. Open TradingView Paper Trading
2. Go to your account/order history
3. Export as CSV
4. Save the file as `trades.csv` in this project directory

### Step 4: Set Environment Variables

#### On Windows:
```bash
set NOTION_API_KEY=secret_your_api_key_here
set NOTION_DATABASE_ID=your_database_id_here
set CSV_FILE_PATH=trades.csv
```

#### On Mac/Linux:
```bash
export NOTION_API_KEY="secret_your_api_key_here"
export NOTION_DATABASE_ID="your_database_id_here"
export CSV_FILE_PATH="trades.csv"
```

**Or create a `.env` file:**
```
NOTION_API_KEY=secret_your_api_key_here
NOTION_DATABASE_ID=your_database_id_here
CSV_FILE_PATH=trades.csv
```

## Usage

### Run the Sync Script

```bash
python sync.py
```

### Expected Output

```
=== TradingView to Notion Sync ===

Parsed 45 filled orders from CSV
Matched 12 complete trades
✓ Synced: COINBASE:SOLUSD | P/L: $15.43
✓ Synced: COINBASE:ETHUSD | P/L: -$8.20
✓ Synced: ASX:CBA | P/L: $42.50
...

Synced 12/12 trades to Notion

Sync complete!
```

## CSV Format

The script expects TradingView CSV exports with these columns:
- Symbol
- Side (Buy/Sell)
- Type
- Qty
- Limit Price
- Stop Price
- Fill Price
- Status
- Placing Time
- Closing Time
- Order ID

## Notion Database Structure

Your Notion database should have these properties:

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Trade identifier |
| Date | Date | Entry date |
| Symbol | Text | Stock/crypto ticker |
| Direction | Select | Long/Short |
| Entry Price | Number | Entry price |
| Exit Price | Number | Exit price |
| Position Size | Number | Quantity traded |
| P/L ($) | Number | Profit/Loss in dollars |
| P/L (%) | Number | Profit/Loss percentage |
| Result | Select | Win/Loss/Breakeven |

## Troubleshooting

### "Configuration Error: NOTION_API_KEY environment variable not set"
- Make sure you've set the environment variables correctly
- Check for typos in variable names
- On Windows, use `set` instead of `export`

### "No orders found in CSV file"
- Verify the CSV file path is correct
- Ensure the CSV contains filled orders
- Check that the CSV format matches TradingView exports

### "Failed to sync: 401 Unauthorized"
- Your Notion API key may be invalid
- Make sure your integration has access to the database
- Check that you've invited the integration to your database

### "Failed to sync: 400 Bad Request"
- Your database structure may not match the expected properties
- Verify all property names match exactly (case-sensitive)

## How It Works

1. **Parse CSV**: Reads and validates the TradingView CSV export
2. **Filter Filled Orders**: Only processes orders with "Filled" status
3. **Match Trades**: Groups orders by symbol and matches Buy→Sell pairs chronologically
4. **Calculate P/L**: Computes profit/loss in both dollars and percentage
5. **Sync to Notion**: Creates database entries via the Notion API

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please open an issue on GitHub.

---

**Made with ❤️ for traders who love data**
