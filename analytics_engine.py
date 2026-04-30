def backtest_strategy(prices_df, signals_df, initial_capital=10_000_000):
    """
    Backtests the strategy using historical signals
    Rules:
    - Buy when Signal = BUY and Strength >= 75%
    - Hold until TP (30%) or SL (-7%) hit
    - T+2 settlement (can't sell same day)
    - 3% total dealing costs (1.5% buy + 1.5% sell)
    - Max 5% position size per stock
    """
    
    if prices_df.empty or signals_df.empty:
        return pd.DataFrame(), 0, pd.DataFrame()
    
    # Initialize
    capital = initial_capital
    positions = {}  # Track open positions: {ticker: {'shares': X, 'entry_price': Y, 'entry_date': Z}}
    trades = []
    equity_curve = []
    
    # Ensure dates are datetime objects
    prices_df = prices_df.copy()
    prices_df['Date'] = pd.to_datetime(prices_df['Date'])
    
    # Sort by date
    prices_df = prices_df.sort_values('Date').reset_index(drop=True)
    
    # Get unique dates
    unique_dates = prices_df['Date'].unique()
    
    for current_date in unique_dates:
        # Get all prices for this date
        day_prices = prices_df[prices_df['Date'] == current_date]
        
        # Check each stock
        for _, row in day_prices.iterrows():
            ticker = row['Ticker']
            price = row['Close']
            
            # If we have an OPEN position in this stock
            if ticker in positions:
                pos = positions[ticker]
                entry_price = pos['entry_price']
                entry_date = pos['entry_date']
                
                # Calculate days held (must be >= 2 for T+2)
                days_held = (current_date - entry_date).days
                
                if days_held >= 2:  # Can only exit after T+2
                    # Calculate P&L
                    pnl_pct = (price - entry_price) / entry_price * 100
                    
                    # Check TP (30%) or SL (-7%)
                    if pnl_pct >= 30 or pnl_pct <= -7:
                        # EXIT the position
                        shares = pos['shares']
                        sell_value = shares * price * 0.985  # 1.5% sell cost
                        buy_cost = shares * entry_price * 1.015  # 1.5% buy cost
                        pnl = sell_value - buy_cost
                        
                        trades.append({
                            'Ticker': ticker,
                            'Entry Date': entry_date,
                            'Exit Date': current_date,
                            'Entry Price': entry_price,
                            'Exit Price': price,
                            'Shares': shares,
                            'P&L ₦': pnl,
                            'P&L %': pnl_pct,
                            'Exit Reason': 'TP' if pnl_pct >= 30 else 'SL',
                            'Days Held': days_held
                        })
                        
                        capital += sell_value
                        del positions[ticker]  # Remove position
            
            # If NO position and we have a BUY signal
            if ticker not in positions:
                # Find signal for this stock on this date
                signal_row = signals_df[
                    (signals_df['Ticker'] == ticker) & 
                    (signals_df['Date'] == current_date.strftime('%Y-%m-%d'))
                ]
                
                if not signal_row.empty:
                    strength = signal_row['Strength(%)'].values[0]
                    
                    # BUY if strength >= 75%
                    if strength >= 75:
                        # Calculate position size (5% of capital)
                        position_value = capital * 0.05
                        shares = int(position_value / (price * 1.015))  # Include 1.5% buy cost
                        
                        if shares > 0:
                            total_cost = shares * price * 1.015
                            if total_cost <= capital:  # Ensure we have enough cash
                                positions[ticker] = {
                                    'shares': shares,
                                    'entry_price': price,
                                    'entry_date': current_date
                                }
                                capital -= total_cost
        
        # Update equity curve (end of day)
        current_positions_value = sum(
            pos['shares'] * day_prices[day_prices['Ticker'] == ticker]['Close'].values[0]
            for ticker, pos in positions.items()
            if ticker in day_prices['Ticker'].values
        )
        
        total_equity = capital + current_positions_value
        equity_curve.append({
            'Date': current_date,
            'Equity': total_equity,
            'Return': total_equity / initial_capital - 1
        })
    
    equity_df = pd.DataFrame(equity_curve)
    trades_df = pd.DataFrame(trades)
    
    final_return = (equity_df['Equity'].iloc[-1] / initial_capital - 1) * 100 if not equity_df.empty else 0
    
    return equity_df, final_return, trades_df
