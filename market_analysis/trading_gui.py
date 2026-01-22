"""
Live Trading GUI Platform

Real-time multi-window stock monitoring with:
- Live candlestick charts
- Pattern detection
- Algorithmic trading (auto/manual)
- Paper trading simulator
- Multi-stock monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import queue
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
from pathlib import Path

# Import our analysis modules
sys.path.append(str(Path(__file__).parent))
from core.pattern_detector import PatternDetector, PatternSignal
from data.pattern_database import PatternDatabase
from core.black_scholes_merton import BlackScholesMerton
from core.behavioral_factors import BehavioralFactorAnalyzer
from utils.risk_management import RiskManager


@dataclass
class TradeOrder:
    """Trading order"""
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    timestamp: datetime
    signal_strength: float
    pattern_based: bool
    requires_confirmation: bool = True
    confirmed: bool = False


@dataclass
class Position:
    """Open position"""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0


class TradingSimulator:
    """Paper trading simulator with fake money"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.pending_orders: List[TradeOrder] = []

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.current_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value

    def execute_trade(self, order: TradeOrder) -> bool:
        """Execute a trade in simulator"""
        if order.action == 'BUY':
            cost = order.quantity * order.price
            if cost > self.cash:
                return False

            self.cash -= cost

            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                # Average up
                total_qty = pos.quantity + order.quantity
                avg_price = (pos.entry_price * pos.quantity + order.price * order.quantity) / total_qty
                pos.quantity = total_qty
                pos.entry_price = avg_price
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    entry_price=order.price,
                    current_price=order.price,
                    entry_time=order.timestamp
                )

        elif order.action == 'SELL':
            if order.symbol not in self.positions:
                return False

            pos = self.positions[order.symbol]
            if order.quantity > pos.quantity:
                return False

            proceeds = order.quantity * order.price
            self.cash += proceeds

            # Record realized P&L
            pnl = (order.price - pos.entry_price) * order.quantity

            pos.quantity -= order.quantity
            if pos.quantity == 0:
                del self.positions[order.symbol]

        # Record trade
        self.trade_history.append({
            'timestamp': order.timestamp,
            'symbol': order.symbol,
            'action': order.action,
            'quantity': order.quantity,
            'price': order.price,
            'pattern_based': order.pattern_based
        })

        return True

    def update_positions(self, current_prices: Dict[str, float]):
        """Update position values"""
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                pos.current_price = current_prices[symbol]
                pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity


class LiveDataFeed:
    """Simulated live data feed (replace with real API)"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data_queue = queue.Queue()
        self.running = False
        self.thread = None

        # Initialize with some data
        self.current_price = 100.0
        self.ohlcv_data = []

    def start(self):
        """Start live data feed"""
        self.running = True
        self.thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop data feed"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _fetch_loop(self):
        """Simulate fetching live data"""
        while self.running:
            # Simulate price movement
            change = np.random.randn() * 0.005 * self.current_price
            self.current_price += change

            # Create OHLC bar (1-minute)
            high = self.current_price * (1 + abs(np.random.randn()) * 0.002)
            low = self.current_price * (1 - abs(np.random.randn()) * 0.002)
            open_price = self.current_price + np.random.randn() * 0.001 * self.current_price
            volume = np.random.randint(100000, 1000000)

            bar = {
                'timestamp': datetime.now(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': self.current_price,
                'volume': volume
            }

            self.data_queue.put(bar)
            self.ohlcv_data.append(bar)

            # Keep last 1000 bars
            if len(self.ohlcv_data) > 1000:
                self.ohlcv_data.pop(0)

            time.sleep(1)  # Update every second

    def get_latest_data(self) -> Optional[Dict]:
        """Get latest data bar"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None

    def get_ohlcv_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame for analysis"""
        if not self.ohlcv_data:
            return pd.DataFrame()

        df = pd.DataFrame(self.ohlcv_data)
        df.set_index('timestamp', inplace=True)
        return df


class StockMonitorWindow(tk.Toplevel):
    """Individual stock monitoring window"""

    def __init__(self, parent, symbol: str, simulator: TradingSimulator,
                 auto_trade: bool = False, require_confirmation: bool = True):
        super().__init__(parent)

        self.symbol = symbol
        self.simulator = simulator
        self.auto_trade = auto_trade
        self.require_confirmation = require_confirmation

        # Window setup
        self.title(f"{symbol} - Live Monitor")
        self.geometry("1200x800")

        # Analysis modules
        self.pattern_detector = PatternDetector()
        self.bs_model = BlackScholesMerton()
        self.behav_analyzer = BehavioralFactorAnalyzer()

        # Live data feed
        self.data_feed = LiveDataFeed(symbol)

        # Current analysis
        self.current_signals = []
        self.current_prediction = 0.0
        self.current_confidence = 0.0

        # Setup UI
        self._setup_ui()

        # Start data feed
        self.data_feed.start()

        # Start update loop
        self.update_display()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_ui(self):
        """Setup window UI"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top bar with controls
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        # Symbol label
        ttk.Label(top_bar, text=f"Symbol: {self.symbol}",
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=5)

        # Auto-trade toggle
        self.auto_trade_var = tk.BooleanVar(value=self.auto_trade)
        ttk.Checkbutton(top_bar, text="Auto-Trade",
                       variable=self.auto_trade_var,
                       command=self.toggle_auto_trade).pack(side=tk.LEFT, padx=5)

        # Confirmation toggle
        self.confirm_var = tk.BooleanVar(value=self.require_confirmation)
        ttk.Checkbutton(top_bar, text="Require Confirmation",
                       variable=self.confirm_var).pack(side=tk.LEFT, padx=5)

        # Current price
        self.price_label = ttk.Label(top_bar, text="Price: $0.00",
                                     font=('Arial', 12, 'bold'))
        self.price_label.pack(side=tk.RIGHT, padx=5)

        # Split into left (chart) and right (analysis)
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left: Chart
        chart_frame = ttk.Frame(paned)
        paned.add(chart_frame, weight=2)

        # Create matplotlib chart
        self.fig = Figure(figsize=(8, 6), facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111, facecolor='#2d2d2d')

        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Right: Analysis panel
        analysis_frame = ttk.Frame(paned)
        paned.add(analysis_frame, weight=1)

        # Analysis sections
        self._setup_analysis_panel(analysis_frame)

        # Bottom: Position info
        bottom_frame = ttk.LabelFrame(main_frame, text="Position & P&L", padding=5)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        self.position_text = tk.StringVar(value="No position")
        ttk.Label(bottom_frame, textvariable=self.position_text).pack(side=tk.LEFT, padx=5)

        self.pnl_text = tk.StringVar(value="P&L: $0.00")
        ttk.Label(bottom_frame, textvariable=self.pnl_text,
                 font=('Arial', 10, 'bold')).pack(side=tk.RIGHT, padx=5)

    def _setup_analysis_panel(self, parent):
        """Setup compact analysis panel"""
        # Make scrollable
        canvas = tk.Canvas(parent, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Prediction summary
        pred_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Prediction", padding=5)
        pred_frame.pack(fill=tk.X, padx=5, pady=5)

        self.pred_label = ttk.Label(pred_frame, text="Analyzing...",
                                    font=('Arial', 12, 'bold'))
        self.pred_label.pack()

        self.confidence_label = ttk.Label(pred_frame, text="Confidence: --")
        self.confidence_label.pack()

        # Active patterns
        patterns_frame = ttk.LabelFrame(scrollable_frame, text="⭐ Active Patterns", padding=5)
        patterns_frame.pack(fill=tk.X, padx=5, pady=5)

        self.patterns_text = scrolledtext.ScrolledText(patterns_frame, height=8, width=30,
                                                       font=('Courier', 8))
        self.patterns_text.pack(fill=tk.BOTH, expand=True)

        # Technical indicators
        tech_frame = ttk.LabelFrame(scrollable_frame, text="📊 Technicals", padding=5)
        tech_frame.pack(fill=tk.X, padx=5, pady=5)

        self.tech_text = tk.Text(tech_frame, height=6, width=30, font=('Courier', 8))
        self.tech_text.pack(fill=tk.BOTH)

        # Factors
        factors_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Factor Scores", padding=5)
        factors_frame.pack(fill=tk.X, padx=5, pady=5)

        self.factors_text = tk.Text(factors_frame, height=8, width=30, font=('Courier', 8))
        self.factors_text.pack(fill=tk.BOTH)

        # Trading signals
        signal_frame = ttk.LabelFrame(scrollable_frame, text="💡 Trading Signal", padding=5)
        signal_frame.pack(fill=tk.X, padx=5, pady=5)

        self.signal_label = ttk.Label(signal_frame, text="No signal",
                                      font=('Arial', 10, 'bold'))
        self.signal_label.pack()

        # Action buttons
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="BUY", command=lambda: self.manual_trade('BUY')).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="SELL", command=lambda: self.manual_trade('SELL')).pack(side=tk.RIGHT, expand=True, padx=2)

    def update_chart(self):
        """Update candlestick chart"""
        df = self.data_feed.get_ohlcv_dataframe()

        if len(df) < 2:
            return

        # Clear and redraw
        self.ax.clear()

        # Plot last 100 candles
        plot_df = df.tail(100).copy()
        plot_df['index'] = range(len(plot_df))

        # Candlesticks
        for idx, row in plot_df.iterrows():
            i = row['index']
            color = '#00ff00' if row['close'] >= row['open'] else '#ff0000'

            # High-low line
            self.ax.plot([i, i], [row['low'], row['high']], color=color, linewidth=1)

            # Body
            height = abs(row['close'] - row['open'])
            bottom = min(row['open'], row['close'])
            rect = Rectangle((i - 0.4, bottom), 0.8, height,
                           facecolor=color, edgecolor=color)
            self.ax.add_patch(rect)

        # Style
        self.ax.set_facecolor('#2d2d2d')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.ax.set_title(f'{self.symbol} - Live Chart', color='white', fontsize=12)
        self.ax.set_xlabel('Time', color='white')
        self.ax.set_ylabel('Price ($)', color='white')
        self.ax.grid(True, alpha=0.2, color='white')

        self.canvas.draw()

    def run_analysis(self):
        """Run pattern detection and analysis"""
        df = self.data_feed.get_ohlcv_dataframe()

        if len(df) < 50:
            return

        # Detect patterns
        additional_data = {
            'market_cap': 50e9,
            'pe_ratio': 25,
            'vix': 18,
            'short_interest_pct': 0.05
        }

        try:
            signals = self.pattern_detector.detect_all_patterns(
                symbol=self.symbol,
                price_data=df,
                current_date=datetime.now(),
                market_type='stocks',
                additional_data=additional_data
            )

            self.current_signals = signals

            # Combine signals
            if signals:
                combined = self.pattern_detector.combine_pattern_signals(signals)
                self.current_prediction = combined['prediction']
                self.current_confidence = combined['confidence']
            else:
                self.current_prediction = 0.0
                self.current_confidence = 0.0

            # Check for trading signal
            if self.auto_trade_var.get():
                self.check_trading_signal()

        except Exception as e:
            print(f"Analysis error: {e}")

    def check_trading_signal(self):
        """Check if we should generate trading signal"""
        if abs(self.current_prediction) < 0.03:  # Less than 3%
            return

        if self.current_confidence < 0.55:  # Less than 55% confidence
            return

        # Generate order
        action = 'BUY' if self.current_prediction > 0 else 'SELL'
        quantity = 10  # Fixed for demo

        order = TradeOrder(
            symbol=self.symbol,
            action=action,
            quantity=quantity,
            price=self.data_feed.current_price,
            timestamp=datetime.now(),
            signal_strength=self.current_confidence,
            pattern_based=True,
            requires_confirmation=self.confirm_var.get()
        )

        if order.requires_confirmation:
            # Show confirmation dialog
            self.show_trade_confirmation(order)
        else:
            # Execute immediately
            self.execute_order(order)

    def show_trade_confirmation(self, order: TradeOrder):
        """Show trade confirmation dialog"""
        msg = f"Auto-Trade Signal\n\n"
        msg += f"Symbol: {order.symbol}\n"
        msg += f"Action: {order.action}\n"
        msg += f"Quantity: {order.quantity}\n"
        msg += f"Price: ${order.price:.2f}\n"
        msg += f"Signal Strength: {order.signal_strength:.1%}\n"
        msg += f"Expected Return: {self.current_prediction:+.1%}\n\n"
        msg += "Execute this trade?"

        result = messagebox.askyesno("Confirm Trade", msg)

        if result:
            self.execute_order(order)

    def execute_order(self, order: TradeOrder):
        """Execute trading order"""
        success = self.simulator.execute_trade(order)

        if success:
            messagebox.showinfo("Trade Executed",
                              f"{order.action} {order.quantity} {order.symbol} @ ${order.price:.2f}")
        else:
            messagebox.showerror("Trade Failed",
                               f"Could not execute {order.action} order")

    def manual_trade(self, action: str):
        """Manual trade button"""
        quantity = 10  # Could make this configurable

        order = TradeOrder(
            symbol=self.symbol,
            action=action,
            quantity=quantity,
            price=self.data_feed.current_price,
            timestamp=datetime.now(),
            signal_strength=0.0,
            pattern_based=False,
            requires_confirmation=True
        )

        self.show_trade_confirmation(order)

    def update_display(self):
        """Update all display elements"""
        try:
            # Get latest data
            latest = self.data_feed.get_latest_data()

            if latest:
                # Update price
                price = latest['close']
                self.price_label.config(text=f"Price: ${price:.2f}")

                # Update chart
                self.update_chart()

                # Run analysis every 10 seconds
                if int(time.time()) % 10 == 0:
                    self.run_analysis()
                    self.update_analysis_display()

                # Update position
                self.update_position_display()

            # Schedule next update
            self.after(1000, self.update_display)

        except Exception as e:
            print(f"Update error: {e}")
            self.after(1000, self.update_display)

    def update_analysis_display(self):
        """Update analysis panels"""
        # Prediction
        direction = "📈 BUY" if self.current_prediction > 0 else "📉 SELL" if self.current_prediction < -0.02 else "⚪ HOLD"
        self.pred_label.config(text=f"{direction} {self.current_prediction:+.1%}")
        self.confidence_label.config(text=f"Confidence: {self.current_confidence:.0%}")

        # Patterns
        self.patterns_text.delete('1.0', tk.END)
        for i, signal in enumerate(self.current_signals[:5], 1):
            self.patterns_text.insert(tk.END, f"{i}. {signal.pattern.name}\n")
            self.patterns_text.insert(tk.END, f"   {signal.expected_return:+.1%} ({signal.confidence:.0%})\n")

        # Technicals
        df = self.data_feed.get_ohlcv_dataframe()
        if len(df) >= 50:
            self.tech_text.delete('1.0', tk.END)

            # Calculate indicators
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else 0
            current = df['close'].iloc[-1]

            self.tech_text.insert(tk.END, f"Current: ${current:.2f}\n")
            self.tech_text.insert(tk.END, f"SMA(20): ${sma_20:.2f}\n")
            if sma_50 > 0:
                self.tech_text.insert(tk.END, f"SMA(50): ${sma_50:.2f}\n")

            vol = df['close'].pct_change().std() * np.sqrt(252)
            self.tech_text.insert(tk.END, f"Volatility: {vol:.1%}\n")

        # Factors
        self.factors_text.delete('1.0', tk.END)
        self.factors_text.insert(tk.END, f"Pattern:    {self.current_prediction:+.1%}\n")
        self.factors_text.insert(tk.END, f"Confidence: {self.current_confidence:.0%}\n")
        self.factors_text.insert(tk.END, f"Patterns:   {len(self.current_signals)}\n")

        # Signal
        if abs(self.current_prediction) > 0.05 and self.current_confidence > 0.60:
            action = "STRONG BUY" if self.current_prediction > 0.10 else "BUY" if self.current_prediction > 0 else "SELL"
            self.signal_label.config(text=f"🟢 {action}", foreground='green' if self.current_prediction > 0 else 'red')
        else:
            self.signal_label.config(text="⚪ HOLD", foreground='gray')

    def update_position_display(self):
        """Update position and P&L display"""
        if self.symbol in self.simulator.positions:
            pos = self.simulator.positions[self.symbol]
            self.position_text.set(f"Position: {pos.quantity} shares @ ${pos.entry_price:.2f}")

            pnl = pos.unrealized_pnl
            color = 'green' if pnl >= 0 else 'red'
            self.pnl_text.set(f"P&L: ${pnl:+,.2f}")
        else:
            self.position_text.set("No position")
            self.pnl_text.set("P&L: $0.00")

    def toggle_auto_trade(self):
        """Toggle auto-trading"""
        self.auto_trade = self.auto_trade_var.get()
        status = "enabled" if self.auto_trade else "disabled"
        messagebox.showinfo("Auto-Trade", f"Auto-trading {status} for {self.symbol}")

    def on_close(self):
        """Clean up when closing"""
        self.data_feed.stop()
        self.destroy()


class TradingPlatformGUI(tk.Tk):
    """Main trading platform GUI"""

    def __init__(self):
        super().__init__()

        self.title("Live Trading Platform - Pattern-Based Algorithmic Trading")
        self.geometry("600x500")

        # Trading simulator
        self.simulator = TradingSimulator(initial_capital=100000)

        # Open windows
        self.open_windows: Dict[str, StockMonitorWindow] = {}

        # Watchlist
        self.watchlist = []

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup main UI"""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(title_frame, text="📈 Live Trading Platform",
                 font=('Arial', 16, 'bold')).pack()
        ttk.Label(title_frame, text="Pattern-Based Algorithmic Trading",
                 font=('Arial', 10)).pack()

        # Portfolio summary
        portfolio_frame = ttk.LabelFrame(self, text="💼 Portfolio Summary", padding=10)
        portfolio_frame.pack(fill=tk.X, padx=10, pady=5)

        self.portfolio_text = tk.StringVar(value=f"Cash: ${self.simulator.cash:,.2f}")
        ttk.Label(portfolio_frame, textvariable=self.portfolio_text,
                 font=('Arial', 12, 'bold')).pack()

        self.total_value_text = tk.StringVar(value="Total Value: $100,000.00")
        ttk.Label(portfolio_frame, textvariable=self.total_value_text,
                 font=('Arial', 11)).pack()

        # Stock selector
        selector_frame = ttk.LabelFrame(self, text="📊 Open Stock Monitor", padding=10)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(selector_frame, text="Enter Symbol:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.symbol_entry = ttk.Entry(selector_frame, width=15)
        self.symbol_entry.grid(row=0, column=1, padx=5)
        self.symbol_entry.bind('<Return>', lambda e: self.open_stock_monitor())

        ttk.Button(selector_frame, text="Open Monitor",
                  command=self.open_stock_monitor).grid(row=0, column=2, padx=5)

        # Auto-trade settings
        settings_frame = ttk.LabelFrame(selector_frame, text="Settings", padding=5)
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)

        self.default_auto_trade = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Enable Auto-Trading",
                       variable=self.default_auto_trade).pack(side=tk.LEFT, padx=5)

        self.default_confirmation = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Require Confirmation",
                       variable=self.default_confirmation).pack(side=tk.LEFT, padx=5)

        # Watchlist
        watchlist_frame = ttk.LabelFrame(self, text="⭐ Watchlist", padding=10)
        watchlist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Quick access buttons for common stocks
        quick_frame = ttk.Frame(watchlist_frame)
        quick_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(quick_frame, text="Quick Access:").pack(side=tk.LEFT, padx=5)

        for symbol in ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL']:
            ttk.Button(quick_frame, text=symbol, width=8,
                      command=lambda s=symbol: self.quick_open(s)).pack(side=tk.LEFT, padx=2)

        # Open windows list
        self.windows_listbox = tk.Listbox(watchlist_frame, height=8)
        self.windows_listbox.pack(fill=tk.BOTH, expand=True)
        self.windows_listbox.bind('<Double-Button-1>', self.focus_window)

        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="View All Positions",
                  command=self.show_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Trade History",
                  command=self.show_trade_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset Simulator",
                  command=self.reset_simulator).pack(side=tk.RIGHT, padx=5)

        # Start update loop
        self.update_portfolio()

    def open_stock_monitor(self):
        """Open stock monitor window"""
        symbol = self.symbol_entry.get().strip().upper()

        if not symbol:
            messagebox.showwarning("Input Required", "Please enter a stock symbol")
            return

        if symbol in self.open_windows:
            # Focus existing window
            self.open_windows[symbol].lift()
            return

        # Create new monitor window
        window = StockMonitorWindow(
            self,
            symbol=symbol,
            simulator=self.simulator,
            auto_trade=self.default_auto_trade.get(),
            require_confirmation=self.default_confirmation.get()
        )

        self.open_windows[symbol] = window

        # Add to watchlist
        self.windows_listbox.insert(tk.END, f"{symbol} - Live Monitor")

        # Clear entry
        self.symbol_entry.delete(0, tk.END)

        # Handle window close
        def on_window_close():
            if symbol in self.open_windows:
                del self.open_windows[symbol]
                self.update_windows_list()
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_window_close)

    def quick_open(self, symbol: str):
        """Quick open from button"""
        self.symbol_entry.delete(0, tk.END)
        self.symbol_entry.insert(0, symbol)
        self.open_stock_monitor()

    def focus_window(self, event):
        """Focus window from list"""
        selection = self.windows_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        symbols = list(self.open_windows.keys())

        if idx < len(symbols):
            self.open_windows[symbols[idx]].lift()

    def update_windows_list(self):
        """Update windows listbox"""
        self.windows_listbox.delete(0, tk.END)
        for symbol in self.open_windows.keys():
            self.windows_listbox.insert(tk.END, f"{symbol} - Live Monitor")

    def update_portfolio(self):
        """Update portfolio display"""
        # Update positions with current prices
        current_prices = {}
        for symbol, window in self.open_windows.items():
            current_prices[symbol] = window.data_feed.current_price

        self.simulator.update_positions(current_prices)

        # Update display
        self.portfolio_text.set(f"Cash: ${self.simulator.cash:,.2f}")

        total_value = self.simulator.get_portfolio_value(current_prices)
        pnl = total_value - self.simulator.initial_capital
        color = 'green' if pnl >= 0 else 'red'

        self.total_value_text.set(f"Total Value: ${total_value:,.2f} ({pnl:+,.2f})")

        # Schedule next update
        self.after(1000, self.update_portfolio)

    def show_positions(self):
        """Show all open positions"""
        win = tk.Toplevel(self)
        win.title("Open Positions")
        win.geometry("600x400")

        text = scrolledtext.ScrolledText(win, font=('Courier', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text.insert(tk.END, "OPEN POSITIONS\n")
        text.insert(tk.END, "=" * 70 + "\n\n")

        if not self.simulator.positions:
            text.insert(tk.END, "No open positions\n")
        else:
            for symbol, pos in self.simulator.positions.items():
                text.insert(tk.END, f"Symbol: {symbol}\n")
                text.insert(tk.END, f"  Quantity:      {pos.quantity}\n")
                text.insert(tk.END, f"  Entry Price:   ${pos.entry_price:.2f}\n")
                text.insert(tk.END, f"  Current Price: ${pos.current_price:.2f}\n")
                text.insert(tk.END, f"  Unrealized P&L: ${pos.unrealized_pnl:+,.2f}\n")
                text.insert(tk.END, "\n")

    def show_trade_history(self):
        """Show trade history"""
        win = tk.Toplevel(self)
        win.title("Trade History")
        win.geometry("700x500")

        text = scrolledtext.ScrolledText(win, font=('Courier', 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text.insert(tk.END, "TRADE HISTORY\n")
        text.insert(tk.END, "=" * 80 + "\n\n")

        if not self.simulator.trade_history:
            text.insert(tk.END, "No trades executed\n")
        else:
            for trade in reversed(self.simulator.trade_history[-50:]):  # Last 50
                text.insert(tk.END, f"{trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | ")
                text.insert(tk.END, f"{trade['action']:4s} | ")
                text.insert(tk.END, f"{trade['symbol']:6s} | ")
                text.insert(tk.END, f"{trade['quantity']:4d} @ ${trade['price']:8.2f}")
                if trade['pattern_based']:
                    text.insert(tk.END, " [PATTERN]")
                text.insert(tk.END, "\n")

    def reset_simulator(self):
        """Reset trading simulator"""
        result = messagebox.askyesno("Confirm Reset",
                                     "This will reset your portfolio and clear all positions. Continue?")

        if result:
            self.simulator = TradingSimulator(initial_capital=100000)
            messagebox.showinfo("Reset Complete", "Simulator has been reset to $100,000")


def main():
    """Launch trading platform"""
    app = TradingPlatformGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
