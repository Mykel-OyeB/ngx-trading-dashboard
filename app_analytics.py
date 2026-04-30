# Add this as TAB 4 in your existing app.py
# Place it after tab3 (Risk & Settings)

with tab4:
    st.subheader("📊 Strategy Performance Analytics")
    
    # Load historical data
    prices_df = fetch_prices_from_sheet()
    signals_df, _ = generate_ngx_signals()
    
    if prices_df.empty:
        st.warning("⚠️ No price data available. Ensure LivePrices has 60+ days of history.")
    else:
        # Run backtest
        with st.spinner("Running backtest..."):
            equity_df, total_return, trades_df = backtest_strategy(prices_df, signals_df)
            
            if equity_df.empty:
                st.warning("⚠️ No trades executed. Check signal thresholds.")
            else:
                # Calculate metrics
                metrics = get_analytics_summary(equity_df, trades_df)
                monthly_perf = generate_monthly_performance(equity_df)
                
                # Display metrics
                st.subheader("📈 Key Performance Metrics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Return", f"{metrics['Total_Return_%']:.1f}%", 
                         f"vs NGX ASI benchmark")
                c2.metric("Sharpe Ratio", f"{metrics['Sharpe_Ratio']:.2f}", 
                         "Target: >1.0")
                c3.metric("Sortino Ratio", f"{metrics['Sortino_Ratio']:.2f}", 
                         "Target: >1.5")
                c4.metric("Calmar Ratio", f"{metrics['Calmar_Ratio']:.2f}", 
                         "Target: >3.0")
                
                st.divider()
                
                c5, c6, c7, c8 = st.columns(4)
                c5.metric("Max Drawdown", f"{metrics['Max_Drawdown_%']:.1f}%", 
                         "Peak-to-trough decline")
                c6.metric("Win Rate", f"{metrics['Win_Rate_%']:.1f}%", 
                         "Target: >55%")
                c7.metric("Profit Factor", f"{metrics['Profit_Factor']:.2f}", 
                         "Target: >1.5")
                c8.metric("Total Trades", f"{metrics['Total_Trades']:.0f}", 
                         "Executed trades")
                
                st.divider()
                
                # Equity Curve
                st.subheader("📊 Equity Curve (Real Backtest)")
                fig = px.line(equity_df, x='Date', y='Equity', 
                             title="Strategy Equity vs Initial Capital")
                fig.add_hline(y=10_000_000, line_dash="dash", line_color="gray",
                             annotation_text="Initial Capital")
                fig.update_layout(height=500, hovermode="x unified")
                st.plotly_chart(fig, width="stretch")
                
                # Monthly Performance
                st.subheader("📅 Monthly Performance")
                if not monthly_perf.empty:
                    fig = px.bar(monthly_perf, x='Month', y='Monthly_Return_%',
                                title="Monthly Returns (%)",
                                color=monthly_perf['Monthly_Return_%'] > 0,
                                color_discrete_map={True: 'green', False: 'red'})
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, width="stretch")
                
                # Drawdown Chart
                st.subheader("⚠️ Drawdown Analysis")
                equity_df['Drawdown'] = (equity_df['Equity'] - equity_df['Equity'].cummax()) / equity_df['Equity'].cummax() * 100
                fig = px.area(equity_df, x='Date', y='Drawdown',
                             title="Strategy Drawdown (%)")
                fig.update_layout(height=300)
                st.plotly_chart(fig, width="stretch")
                
                # Trade Analysis
                st.subheader("📋 Trade Analysis")
                if not trades_df.empty:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Average Trade P&L", f"₦{metrics['Avg_Trade_P&L_₦']:,.0f}")
                        st.metric("Best Trade", f"+{metrics['Best_Trade_%']:.1f}%")
                    with c2:
                        st.metric("Worst Trade", f"{metrics['Worst_Trade_%']:.1f}%")
                    
                    st.dataframe(trades_df[['Ticker', 'Entry Date', 'Exit Date', 
                                           'P&L ₦', 'P&L %', 'Exit Reason']], 
                               use_container_width=True)
