# analytics_engine.py - Advanced Analytics Engine
# ✅ Clean syntax, no circular imports, safe for Streamlit

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def calculate_sharpe_ratio(returns, risk_free_rate=0.15/252):
    if len(returns) < 2: return 0
    excess = returns - risk_free_rate
    if returns.std() == 0: return 0
    return np.sqrt(252) * (excess.mean() / returns.std())

def calculate_sortino_ratio(returns, risk_free_rate=0.15/252):
    if len(returns) < 2: return 0
    excess = returns - risk_free_rate
    downside = returns[returns < 0]
    if len(downside) == 0 or downside.std() == 0: return 0
    return np.sqrt(252) * (excess.mean() / downside.std())

def calculate_calmar_ratio(cumulative_returns):
    if len(cumulative_returns) < 2: return 0
    total_ret = cumulative_returns.iloc[-1] - 1
    rolling_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_dd = abs(drawdown.min())
    if max_dd == 0: return 0
    years = len(cumulative_returns) / 252
    if years == 0: return 0
    annual_ret = (cumulative_returns.iloc[-1]) ** (1/years) - 1
    return annual_ret / max_dd

def calculate_max_drawdown(equity_curve):
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    return drawdown.min()

def calculate_win_rate(trades_df):
    if trades_df.empty: return 0
    return len(trades_df[trades_df['P&L ₦'] > 0]) / len(trades_df) * 100

def calculate_profit_factor(trades_df):
    if trades_df.empty: return 0
    wins = trades_df[trades_df['P&L ₦'] > 0]['P&L ₦'].sum()
    losses = abs(trades_df[trades_df['P&L ₦'] < 0]['P&L ₦'].sum())
    return wins / losses if losses > 0 else (0 if wins == 0 else float('inf'))

def backtest_strategy(prices_df, signals_df, initial_capital=10_000_000):
    if prices_df.empty or signals_df.empty:
        return pd.DataFrame(), 0, pd.DataFrame()
    
    capital = initial_capital
    positions = {}
    trades = []
    equity_curve = []
    
    prices_df = prices_df.copy()
    prices_df['Date'] = pd.to_datetime(prices_df['Date'])
    prices_df = prices_df.sort_values('Date').reset_index(drop=True)
    unique_dates = prices_df['Date'].unique()
    
    for current_date in unique_dates:
        day_prices = prices_df[prices_df['Date'] == current_date]
        
        for _, row in day_prices.iterrows():
            ticker = row['Ticker']
            price = row['Close']
            
            if ticker in positions:
                pos = positions[ticker]
                days_held = (current_date - pos['entry_date']).days
                
                if days_held >= 2:
                    pnl_pct = (price - pos['entry_price']) / pos['entry_price'] * 100
                    if pnl_pct >= 30 or pnl_pct <= -7:
                        shares = pos['shares']
                        sell_val = shares * price * 0.985
                        buy_cost = shares * pos['entry_price'] * 1.015
                        pnl = sell_val - buy_cost
                        
                        trades.append({
                            'Ticker': ticker, 'Entry Date': pos['entry_date'],
                            'Exit Date': current_date, 'Entry Price': pos['entry_price'],
                            'Exit Price': price, 'Shares': shares,
                            'P&L ₦': pnl, 'P&L %': pnl_pct,
                            'Exit Reason': 'TP' if pnl_pct >= 30 else 'SL',
                            'Days Held': days_held
                        })
                        capital += sell_val
                        del positions[ticker]
            
            if ticker not in positions:
                signal = signals_df[(signals_df['Ticker'] == ticker) & 
                                   (signals_df['Date'] == current_date.strftime('%Y-%m-%d'))]
                if not signal.empty and signal['Strength(%)'].values[0] >= 75:
                    shares = int((capital * 0.05) / (price * 1.015))
                    if shares > 0:
                        cost = shares * price * 1.015
                        if cost <= capital:
                            positions[ticker] = {'shares': shares, 'entry_price': price, 'entry_date': current_date}
                            capital -= cost
        
        pos_val = sum(pos['shares'] * day_prices[day_prices['Ticker'] == t]['Close'].values[0] 
                      for t, pos in positions.items() if t in day_prices['Ticker'].values)
        equity_curve.append({'Date': current_date, 'Equity': capital + pos_val, 'Return': (capital + pos_val) / initial_capital - 1})
    
    equity_df = pd.DataFrame(equity_curve)
    trades_df = pd.DataFrame(trades)
    final_ret = (equity_df['Equity'].iloc[-1] / initial_capital - 1) * 100 if not equity_df.empty else 0
    return equity_df, final_ret, trades_df

def generate_monthly_performance(equity_df):
    if equity_df.empty: return pd.DataFrame()
    eq = equity_df.copy()
    eq['Month'] = eq['Date'].dt.to_period('M')
    monthly = eq.groupby('Month')['Return'].agg(['first', 'last']).reset_index()
    monthly['Monthly_Return_%'] = (monthly['last'] - monthly['first']) * 100
    monthly['Month'] = monthly['Month'].astype(str)
    return monthly[['Month', 'Monthly_Return_%']]

def get_analytics_summary(equity_df, trades_df):
    if equity_df.empty: return {}
    eq = equity_df.copy()
    eq['Daily_Return'] = eq['Return'].diff().fillna(0)
    return {
        'Total_Return_%': eq['Return'].iloc[-1] * 100,
        'Sharpe_Ratio': calculate_sharpe_ratio(eq['Daily_Return']),
        'Sortino_Ratio': calculate_sortino_ratio(eq['Daily_Return']),
        'Calmar_Ratio': calculate_calmar_ratio(1 + eq['Return']),
        'Max_Drawdown_%': calculate_max_drawdown(1 + eq['Return']) * 100,
        'Win_Rate_%': calculate_win_rate(trades_df),
        'Profit_Factor': calculate_profit_factor(trades_df),
        'Total_Trades': len(trades_df),
        'Avg_Trade_P&L_₦': trades_df['P&L ₦'].mean() if not trades_df.empty else 0,
        'Best_Trade_%': trades_df['P&L %'].max() if not trades_df.empty else 0,
        'Worst_Trade_%': trades_df['P&L %'].min() if not trades_df.empty else 0,
    }
