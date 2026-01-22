# 📈 Live Trading GUI Platform - User Guide

## 🎯 Overview

A **professional multi-window trading platform** with:
- ✅ **Live candlestick charts** updating in real-time
- ✅ **Pattern-based algorithmic trading** with 23 research-backed patterns
- ✅ **Multi-stock monitoring** - open unlimited stocks side-by-side
- ✅ **Auto-trading** with optional human confirmation
- ✅ **Paper trading simulator** with $100,000 fake money
- ✅ **Draggable, resizable windows** like any desktop app
- ✅ **Compact analysis panel** showing all factors

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install pandas scipy scikit-learn matplotlib

# Run the trading platform
cd market_analysis
python trading_gui.py
```

### First Launch

When you launch the platform, you'll see:

```
┌────────────────────────────────────────────────────┐
│         📈 Live Trading Platform                   │
│    Pattern-Based Algorithmic Trading               │
├────────────────────────────────────────────────────┤
│  💼 Portfolio Summary                              │
│     Cash: $100,000.00                              │
│     Total Value: $100,000.00 (+$0.00)              │
├────────────────────────────────────────────────────┤
│  📊 Open Stock Monitor                             │
│     Enter Symbol: [______]  [Open Monitor]         │
│     ☐ Enable Auto-Trading                          │
│     ☑ Require Confirmation                         │
├────────────────────────────────────────────────────┤
│  ⭐ Watchlist                                       │
│  Quick Access: [AAPL] [NVDA] [TSLA] [MSFT] [GOOGL]│
│                                                     │
│  [Empty - No monitors open]                        │
└────────────────────────────────────────────────────┘
```

---

## 📺 Opening Stock Monitors

### Method 1: Type Symbol

1. Type stock symbol in the "Enter Symbol" field (e.g., `AAPL`)
2. Press Enter or click "Open Monitor"
3. A new window opens with live chart and analysis

### Method 2: Quick Access Buttons

- Click any of the quick access buttons: `AAPL`, `NVDA`, `TSLA`, `MSFT`, `GOOGL`
- Instantly opens that stock's monitor

### Multiple Stocks

- **Open as many as you want!** There's no limit
- Each stock gets its own independent window
- Drag windows around your screen
- Resize each window to your preference
- Each window has standard controls: ❌ Close, ➖ Minimize, ⬜ Maximize

---

## 🖥️ Stock Monitor Window Layout

Each stock monitor window shows:

```
┌─────────────────────────────────────────────────────────────────────┐
│ NVDA - Live Monitor                                    ❌ ➖ ⬜    │
├─────────────────────────────────────────────────────────────────────┤
│ Symbol: NVDA  ☐ Auto-Trade  ☑ Require Confirmation  Price: $1828.18│
├──────────────────────────┬──────────────────────────────────────────┤
│                          │  🎯 Prediction                           │
│   CANDLESTICK CHART      │    📈 BUY +7.2%                          │
│   (Live Updating)        │    Confidence: 65%                       │
│                          │                                          │
│   [Green/Red Candles]    │  ⭐ Active Patterns                      │
│   [Volume bars]          │    1. Momentum (+9.0%, 58%)              │
│   [Price axis]           │    2. January Effect (+5.5%, 68%)        │
│   [Time axis]            │    3. Earnings Drift (+2.4%, 62%)        │
│                          │    ... (scrollable)                      │
│                          │                                          │
│                          │  📊 Technicals                           │
│                          │    Current: $1828.18                     │
│                          │    SMA(20): $1750.32                     │
│                          │    SMA(50): $1680.45                     │
│                          │    Volatility: 35.2%                     │
│                          │                                          │
│                          │  🔍 Factor Scores                        │
│                          │    Pattern:    +7.2%                     │
│                          │    Confidence: 65%                       │
│                          │    Patterns:   8                         │
│                          │                                          │
│                          │  💡 Trading Signal                       │
│                          │    🟢 STRONG BUY                         │
│                          │                                          │
│                          │    [BUY]  [SELL]                         │
├──────────────────────────┴──────────────────────────────────────────┤
│ Position & P&L                                                      │
│ Position: 10 shares @ $1800.00          P&L: +$281.80              │
└─────────────────────────────────────────────────────────────────────┘
```

### Left Side: Live Chart

- **Candlestick chart** updates every second
- **Green candles** = price went up
- **Red candles** = price went down
- Shows last 100 bars
- Dark theme for easy viewing

### Right Side: Analysis Panel (Scrollable)

1. **🎯 Prediction**
   - Direction: BUY/SELL/HOLD
   - Expected return percentage
   - Confidence level

2. **⭐ Active Patterns**
   - List of detected patterns
   - Each shows expected return & confidence
   - Scrollable to see all patterns

3. **📊 Technicals**
   - Current price
   - Moving averages (20-day, 50-day)
   - Volatility percentage

4. **🔍 Factor Scores**
   - Overall pattern prediction
   - Confidence score
   - Number of active patterns

5. **💡 Trading Signal**
   - Real-time recommendation
   - Color-coded: 🟢 Green = Buy, 🔴 Red = Sell, ⚪ Gray = Hold

6. **Action Buttons**
   - `BUY` - Manually buy stock
   - `SELL` - Manually sell stock

### Bottom: Position Info

- Shows your current position (if any)
- Real-time P&L (Profit & Loss)
- Updates continuously

---

## 🤖 Auto-Trading Features

### Enable Auto-Trading

**Per-Stock Basis:**
1. Open a stock monitor
2. Check ☑ "Auto-Trade" at the top
3. System now automatically generates trades when patterns signal

**Default Setting:**
- In main window, check "Enable Auto-Trading"
- All NEW monitors will open with auto-trade enabled

### Human Verification

**With Confirmation (Recommended):**
- Check ☑ "Require Confirmation"
- When a trading signal is generated, you get a popup:

```
┌─────────────────────────────────┐
│     Confirm Trade               │
├─────────────────────────────────┤
│  Auto-Trade Signal              │
│                                 │
│  Symbol: NVDA                   │
│  Action: BUY                    │
│  Quantity: 10                   │
│  Price: $1828.18                │
│  Signal Strength: 65%           │
│  Expected Return: +7.2%         │
│                                 │
│  Execute this trade?            │
│                                 │
│     [Yes]      [No]             │
└─────────────────────────────────┘
```

- Click `Yes` to execute
- Click `No` to reject

**Without Confirmation (Fully Automatic):**
- Uncheck "Require Confirmation"
- Trades execute instantly when signals trigger
- ⚠️ **Use with caution!** No human oversight

### Trading Triggers

Auto-trades are generated when:
1. **Prediction > 3%** (or < -3% for sells)
2. **Confidence > 55%**
3. **Multiple patterns agree**

Example:
```
Momentum: +9.0%
January Effect: +5.5%
Earnings Drift: +2.4%
Combined: +7.2% with 65% confidence
→ BUY signal generated
```

---

## 💰 Paper Trading Simulator

### Starting Capital

- **$100,000 fake money** to start
- Practice trading with no real risk
- Perfect for testing strategies

### Making Trades

**Method 1: Manual Trades**
1. Open a stock monitor
2. Click `BUY` or `SELL` button
3. Confirm the trade
4. Position added to your portfolio

**Method 2: Auto-Trades**
1. Enable auto-trading
2. System trades automatically when patterns signal
3. View trades in Trade History

### Tracking Performance

**Portfolio Summary (Main Window):**
```
💼 Portfolio Summary
   Cash: $95,000.00
   Total Value: $103,500.00 (+$3,500.00)
```

- **Cash**: Available buying power
- **Total Value**: Cash + positions value
- **P&L**: Profit/Loss (green if positive, red if negative)

**Per-Stock P&L (Monitor Windows):**
```
Position: 10 shares @ $1800.00          P&L: +$281.80
```

### View All Positions

Click "View All Positions" to see detailed breakdown:

```
OPEN POSITIONS
======================================================================

Symbol: NVDA
  Quantity:      10
  Entry Price:   $1800.00
  Current Price: $1828.18
  Unrealized P&L: +$281.80

Symbol: AAPL
  Quantity:      20
  Entry Price:   $185.00
  Current Price: $188.50
  Unrealized P&L: +$70.00
```

### Trade History

Click "Trade History" to see all executed trades:

```
TRADE HISTORY
================================================================================

2025-01-21 10:35:42 | BUY  | NVDA   |   10 @ $1800.00 [PATTERN]
2025-01-21 10:30:15 | BUY  | AAPL   |   20 @ $185.00  [PATTERN]
2025-01-21 09:45:23 | SELL | TSLA   |   15 @ $245.00
```

- `[PATTERN]` = Trade generated by pattern detection
- Blank = Manual trade

### Reset Simulator

- Click "Reset Simulator" to start over
- Resets capital to $100,000
- Clears all positions and history

---

## 🎨 Window Management

### Multiple Stocks Side-by-Side

**Tile Windows:**
1. Open multiple stocks (e.g., NVDA, AAPL, TSLA, MSFT)
2. Drag each window to different screen positions
3. Resize to fit your screen layout
4. Watch all stocks simultaneously!

**Example 2x2 Grid:**
```
┌─────────────┬─────────────┐
│   NVDA      │   AAPL      │
│   Monitor   │   Monitor   │
│             │             │
├─────────────┼─────────────┤
│   TSLA      │   MSFT      │
│   Monitor   │   Monitor   │
│             │             │
└─────────────┴─────────────┘
```

### Window Controls

Each window has standard controls (top-right):

- **❌ Close**: Close this stock monitor
- **➖ Minimize**: Minimize to taskbar
- **⬜ Maximize**: Full screen this window

### Dragging & Resizing

- **Drag**: Click title bar and drag to move
- **Resize**: Drag window edges/corners to resize
- **Snap**: Drag to screen edges to snap (OS-dependent)

### Focus Management

**From Watchlist:**
1. Main window shows list of open monitors
2. Double-click any item to bring that window to front

**From Taskbar:**
- Each monitor appears in your taskbar
- Click to switch between them

---

## 📊 Understanding the Analysis

### Pattern Detection

The system scans **23 research-backed patterns** every 10 seconds:

**Seasonal Patterns:**
- January Effect (small-caps in January)
- Santa Claus Rally (year-end)
- September Weakness
- FOMC Drift (before Fed announcements)

**Technical Patterns:**
- Momentum (winners keep winning)
- Mean Reversion (oversold bounces)
- 52-Week High breakouts
- Gap Fades

**Fundamental Patterns:**
- Value Premium (low P/E)
- Earnings Drift (post-earnings pop)
- Insider Buying
- Dividend Initiations

**Behavioral Patterns:**
- Overreaction Reversals
- VIX Spike bottoms
- Short Squeezes
- Lottery Stock underperformance

**Macro Patterns:**
- Fed Model (earnings yield vs bonds)
- Yield Curve Inversion
- Dollar Strength effects

### Factor Scores

Each pattern contributes to the prediction:

```
Pattern:    +7.2%   ← Combined prediction from all patterns
Confidence: 65%     ← How confident (based on pattern quality)
Patterns:   8       ← Number of active patterns detected
```

**How It's Calculated:**
1. Each pattern has a **signal strength** (0-1)
2. Each pattern has a **win rate** (historical probability)
3. System weights by strength × win rate × Sharpe ratio
4. Combines into unified prediction

**Example:**
```
Momentum:        +9.0% × 0.85 strength × 0.58 win rate = Heavy weight
January Effect:  +5.5% × 0.70 strength × 0.68 win rate = Heavy weight
Earnings Drift:  +2.4% × 0.75 strength × 0.62 win rate = Medium weight
────────────────────────────────────────────────────────────────────
Combined:        +7.2% with 65% confidence
```

### Technical Indicators

**Moving Averages:**
- SMA(20): 20-day simple moving average
- SMA(50): 50-day simple moving average
- If Current > SMA(20) > SMA(50) → Strong uptrend

**Volatility:**
- Annualized price volatility
- Higher = more risk, more opportunity
- Used for position sizing

### Trading Signals

**🟢 STRONG BUY:**
- Prediction > +10%
- Confidence > 60%

**🟢 BUY:**
- Prediction > +5%
- Confidence > 60%

**⚪ HOLD:**
- Prediction between -5% and +5%
- OR Confidence < 60%

**🔴 SELL:**
- Prediction < -5%
- Confidence > 60%

---

## ⚙️ Advanced Settings

### Position Sizing

Currently fixed at 10 shares per trade. To customize:

Edit `trading_gui.py` line ~585:
```python
quantity = 10  # Change this number
```

### Signal Thresholds

To adjust when auto-trades trigger:

Edit lines ~580-585:
```python
if abs(self.current_prediction) < 0.03:  # Change 0.03 (3%)
    return

if self.current_confidence < 0.55:  # Change 0.55 (55%)
    return
```

### Update Frequency

- **Chart**: Updates every 1 second
- **Analysis**: Runs every 10 seconds
- **Portfolio**: Updates every 1 second

To change analysis frequency, edit line ~638:
```python
if int(time.time()) % 10 == 0:  # Change 10 to desired seconds
```

---

## 🔒 Safety Features

### Built-in Safeguards

1. **Paper Trading Only**: Uses fake money, no real risk
2. **Human Confirmation**: Optional approval for all trades
3. **Insufficient Funds Check**: Can't trade more than you have
4. **Position Validation**: Can't sell what you don't own
5. **Signal Quality Filter**: Only high-confidence signals trigger trades

### Risk Management

**Per-Trade Risk:**
- Fixed position size (10 shares)
- No leverage
- No margin

**Portfolio Risk:**
- Track total exposure
- Monitor P&L in real-time
- Can close all positions instantly

---

## 🐛 Troubleshooting

### "Module Not Found" Errors

```bash
# Install missing dependencies
pip install pandas scipy scikit-learn matplotlib
```

### Window Not Opening

- Check if symbol is valid (e.g., `AAPL` not `Apple`)
- Close and reopen if stuck

### No Data Showing

- Wait 10 seconds for first analysis
- Chart updates every second
- Check if data feed is running

### Auto-Trade Not Working

1. Verify ☑ "Auto-Trade" is checked
2. Wait for signal conditions to be met
3. Check if confidence > 55% and prediction > 3%

### Reset Everything

Click "Reset Simulator" to start fresh:
- Clears all positions
- Resets capital to $100,000
- Clears trade history

---

## 📈 Example Workflow

### Day Trading Setup

1. **Launch Platform**
   ```bash
   python market_analysis/trading_gui.py
   ```

2. **Open Multiple Stocks**
   - Click quick access: `NVDA`, `AAPL`, `TSLA`
   - Arrange windows side-by-side

3. **Enable Auto-Trading**
   - Check ☑ "Auto-Trade" in each window
   - Keep ☑ "Require Confirmation" for safety

4. **Monitor All Day**
   - Watch candlestick charts update
   - See patterns detected in real-time
   - Approve trades when signals appear

5. **Review Performance**
   - Check "View All Positions"
   - Review "Trade History"
   - Track P&L

---

## 🎯 Tips for Best Results

### Pattern Quality

- **More patterns = better**: 5-8 active patterns is ideal
- **High confidence**: Look for >60% confidence
- **Multiple categories**: Best when seasonal + technical + fundamental agree

### Timing

- **Market hours**: Patterns work best during active trading
- **Earnings season**: Watch for earnings drift patterns
- **Month start**: January Effect strongest first week

### Risk Management

- **Start small**: Test with 10 shares per trade
- **Diversify**: Open 4-5 different stocks
- **Monitor closely**: Watch P&L regularly
- **Use confirmation**: Don't disable human verification until confident

---

## 🚀 Future Enhancements

**Coming Soon:**
- Real-time data from APIs (currently simulated)
- Custom position sizing
- Stop-loss automation
- Multiple timeframes (1min, 5min, 1hour)
- More technical indicators (RSI, MACD, Bollinger Bands)
- Alert notifications
- Export trade history to CSV
- Portfolio analytics dashboard

---

## 📞 Support

**Issues?**
- Check PATTERN_DATABASE_GUIDE.md for pattern details
- Check MARKET_ANALYSIS_README.md for system architecture
- See code comments in trading_gui.py

**Want Real Data?**
Replace `LiveDataFeed` class with real API:
- Alpha Vantage
- IEX Cloud
- Yahoo Finance (yfinance)
- Interactive Brokers

---

## ⚖️ Disclaimer

**EDUCATIONAL USE ONLY**

This is a **paper trading simulator** for learning and testing strategies.

- No real money involved
- Simulated data (not live market data)
- Past performance doesn't guarantee future results
- Always test thoroughly before live trading
- Never risk more than you can afford to lose

---

**Built with**: Python, tkinter, matplotlib, our 23-pattern detection system

**Author**: Market Analysis Team

**Last Updated**: 2026-01-21

---

Enjoy your live trading platform! 📈🚀
