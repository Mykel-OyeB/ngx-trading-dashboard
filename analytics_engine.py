# analytics_engine.py - Advanced Analytics Engine
# ✅ Real backtesting, Sharpe/Sortino/Calmar ratios, monthly P&L

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calculate_sharpe_ratio(returns, risk_free_rate=0.15/252):
    """
    Sharpe Ratio = (Portfolio Return - Risk Free) / Std Dev
    Nigeria risk-free rate: ~15% annual = 0.15/252 daily
    """
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    if returns.std() == 0:
        return 0
    return np.sqrt(252) * (excess_returns.mean() / returns.std())

def calculate_sortino_ratio(returns, risk_free_rate=0.15/252):
    """
    Sortino Ratio = (Portfolio Return - Risk Free) / Downside Deviation
    Only penalizes negative volatility
    """
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return np.sqrt(252) * (excess_returns.mean() / downside_returns.std())

def calculate_calmar_ratio(cumulative_returns):
    """
    Calmar Ratio = Annual Return / Max Drawdown
    Measures return per unit of worst drawdown
    """
    if len(cumulative_returns) < 2:
        return 0
    
    # Calculate total return
    total_return = cumulative_returns.iloc[-1] - 1
    
    # Calculate max drawdown
    rolling_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_drawdown = abs(drawdown.min())
    
    if max_drawdown == 0:
        return 0
    
    # Annualize (assume ~252 trading days)
    years = len(cumulative_returns) / 252
    if years == 0:
        return 0
    
    annual_return = (cumulative_returns.iloc[-1]) ** (1/years) - 1
    return annual_return / max_drawdown

def calculate_max_drawdown(equity_curve):
    """Calculate maximum peak-to-trough decline"""
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    return drawdown.min()

def calculate_win_rate(trades_df):
    """Calculate percentage of winning trades"""
    if trades_df.empty:
        return 0
    winning_trades = len(trades_df[trades_df['P&L ₦'] > 0])
    return winning_trades / len(trades_df) * 100

def calculate_profit_factor(trades_df):
    """Gross Wins / Gross Losses"""
    if trades_df.empty:
        return 0
    
    gross_wins = trades_df[trades_df['P&L ₦'] > 0]['P&L ₦'].sum()
    gross_losses = abs(trades_df[trades_df['P&L ₦'] < 0]['P&L ₦'].sum())
    
    if gross_losses == 0:
        return 0 if gross_wins == 0 else float('inf')
    
    return gross_wins / gross_losses

def backtest_strategy(prices_df, signals_df, initial_capital=10_000_000):
    """
    Backtests the strategy using historical signals
    Assumes:
    - Buy when Signal = BUY and Strength >= 75%
    - Sell when TP (30%) or SL (-7%) hit
    - T+2 settlement
    - 3% dealing costs (1.5% buy + 1.5% sell)
    """
    
    if prices_df.empty or signals_df.empty:
        return pd.DataFrame(), 0, []
    
    # Initialize
    capital = initial_capital
    position = 0
    entry_price = 0
    entry_date = None
    trades = []
    equity_curve = []
    
    # Sort by date
    prices_df = prices_df.sort_values('Date').reset_index(drop=True)
    
    for idx, row in prices_df.iterrows():
        date = row['Date']
        ticker = row['Ticker']
        price = row['Close']
        
        # Check if we have a signal for this stock on this date
        signal_row = signals_df[
            (signals_df['Ticker'] == ticker) & 
            (signals_df['Date'] == date.strftime('%Y-%m-%d'))
        ]
        
        # If no position and signal is BUY with strength >= 75%
        if position == 0 and not signal_row.empty:
            strength = signal_row['Strength(%)'].values[0]
            if strength >= 75:
                # Buy (T+2 settlement, but we'll simplify)
                shares = int((capital * 0.05) / (price * 1.015))  # 5% position, 1.5% buy cost
                if shares > 0:
                    position = shares
                    entry_price = price
                    entry_date = date
                    capital -= shares * price * 1.015  # Include buy cost
        
        # If we have a position, check for exit
        elif position > 0:
            # Calculate P&L
            pnl_pct = (price - entry_price) / entry_price * 100
            
            # Check TP (30%) or SL (-7%)
            if pnl_pct >= 30 or pnl_pct <= -7:
                # Sell
                exit_value = position * price * 0.985  # 1.5% sell cost
                pnl = exit_value - (position * entry_price * 1.015)
                
                trades.append({
                    'Ticker': ticker,
                    'Entry Date': entry_date,
                    'Exit Date': date,
                    'Entry Price': entry_price,
                    'Exit Price': price,
                    'Shares': position,
                    'P&L ₦': pnl,
                    'P&L %': pnl_pct,
                    'Exit Reason': 'TP' if pnl_pct >= 30 else 'SL'
                })
                
                capital += exit_value
                position = 0
                entry_price = 0
                entry_date = None
        
        # Update equity curve
        current_value = capital + (position * price if position > 0 else 0)
        equity_curve.append({
            'Date': date,
            'Equity': current_value,
            'Return': current_value / initial_capital - 1
        })
    
    equity_df = pd.DataFrame(equity_curve)
    trades_df = pd.DataFrame(trades)
    
    # Calculate final return
    final_return = (equity_df['Equity'].iloc[-1] / initial_capital - 1) * 100 if not equity_df.empty else 0
    
    return equity_df, final_return, trades_df

def generate_monthly_performance(equity_df):
    """Generate monthly P&L breakdown"""
    if equity_df.empty:
        return pd.DataFrame()
    
    equity_df = equity_df.copy()
    equity_df['Month'] = equity_df['Date'].dt.to_period('M')
    
    monthly = equity_df.groupby('Month')['Return'].agg(['first', 'last']).reset_index()
    monthly['Monthly_Return_%'] = (monthly['last'] - monthly['first']) * 100
    monthly['Month'] = monthly['Month'].astype(str)
    
    return monthly[['Month', 'Monthly_Return_%']]

def get_analytics_summary(equity_df, trades_df):
    """Generate comprehensive analytics summary"""
    if equity_df.empty:
        return {}
    
    # Calculate daily returns
    equity_df = equity_df.copy()
    equity_df['Daily_Return'] = equity_df['Return'].diff().fillna(0)
    
    # Metrics
    metrics = {
        'Total_Return_%': (equity_df['Return'].iloc[-1]) * 100,
        'Sharpe_Ratio': calculate_sharpe_ratio(equity_df['Daily_Return']),
        'Sortino_Ratio': calculate_sortino_ratio(equity_df['Daily_Return']),
        'Calmar_Ratio': calculate_calmar_ratio(1 + equity_df['Return']),
        'Max_Drawdown_%': calculate_max_drawdown(1 + equity_df['Return']) * 100,
        'Win_Rate_%': calculate_win_rate(trades_df) if not trades_df.empty else 0,
        'Profit_Factor': calculate_profit_factor(trades_df) if not trades_df.empty else 0,
        'Total_Trades': len(trades_df) if not trades_df.empty else 0,
        'Avg_Trade_P&L_₦': trades_df['P&L ₦'].mean() if not trades_df.empty else 0,
        'Best_Trade_%': trades_df['P&L %'].max() if not trades_df.empty else 0,
        'Worst_Trade_%': trades_df['P&L %'].min() if not trades_df.empty else 0,
    }
    
    return metrics
