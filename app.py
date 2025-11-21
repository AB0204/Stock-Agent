import streamlit as st
import yfinance as yf
from textblob import TextBlob
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="Stock Sentiment Agent", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    .stMetric {
        background-color: #0e1117;
        padding: 10px;
        border-radius: 5px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: #888;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        border-top: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def get_sentiment_color(score):
    if score > 0.1: return "green"
    elif score < -0.1: return "red"
    else: return "orange"

def get_sentiment_label(score):
    if score > 0.1: return "BULLISH 🚀"
    elif score < -0.1: return "BEARISH 📉"
    else: return "NEUTRAL 😐"

def format_large_number(num):
    if num is None: return "N/A"
    if num >= 1_000_000_000_000: return f"${num/1_000_000_000_000:.2f}T"
    if num >= 1_000_000_000: return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000: return f"${num/1_000_000:.2f}M"
    return f"${num:.2f}"

# Sidebar
with st.sidebar:
    st.title("🤖 Stock Agent")
    
    # Analysis Mode
    analysis_mode = st.radio(
        "Analysis Mode",
        ["Quick Scan (1Y)", "Deep Dive (3Y)", "Technical (6M)"],
        index=0
    )
    
    # Period mapping
    period_map = {
        "Quick Scan (1Y)": "1y",
        "Deep Dive (3Y)": "3y",
        "Technical (6M)": "6mo"
    }
    selected_period = period_map[analysis_mode]
    
    st.markdown("---")
    
    # Market Selection
    market = st.radio(
        "Select Market",
        ["🇺🇸 US Stocks", "🇮🇳 Indian Stocks"],
        index=0
    )
    
    # Stock Selection based on market
    if market == "🇺🇸 US Stocks":
        popular_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
        additional_tickers = ["AMD", "INTC", "NFLX", "SPY", "QQQ"]
        default_ticker = ["TSLA"]
        custom_hint = "e.g. COIN, DIS"
    else:  # Indian Stocks
        popular_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS"]
        additional_tickers = ["WIPRO.NS", "LT.NS", "BHARTIARTL.NS", "NIFTY50.NS"]
        default_ticker = ["RELIANCE.NS"]
        custom_hint = "e.g. TATAMOTORS.NS"
    
    selected_tickers = st.multiselect(
        "Select Stocks", 
        options=popular_tickers + additional_tickers,
        default=default_ticker
    )
    
    custom_ticker = st.text_input(f"Or type a ticker ({custom_hint})")
    if custom_ticker:
        custom_ticker = custom_ticker.upper()
        # Auto-add .NS suffix for Indian stocks if not present
        if market == "🇮🇳 Indian Stocks" and not custom_ticker.endswith(('.NS', '.BO')):
            custom_ticker = f"{custom_ticker}.NS"
        if custom_ticker not in selected_tickers:
            selected_tickers.append(custom_ticker)
    
    st.markdown("---")
    
    # Technical Indicator Controls
    st.subheader("Technical Indicators")
    show_indicators = st.checkbox("Show Technical Indicators", value=True)
    
    if show_indicators:
        rsi_period = st.slider("RSI Period", min_value=5, max_value=30, value=14)
        ma_short = st.number_input("Short MA Period", min_value=5, max_value=50, value=20)
        ma_long = st.number_input("Long MA Period", min_value=20, max_value=200, value=50)
        show_macd = st.checkbox("Show MACD", value=True)
    
    st.markdown("---")
    st.markdown("### Features")
    st.markdown("- **Multi-Stock Comparison**")
    st.markdown("- **Real-time Prices**")
    st.markdown("- **Sentiment Analysis**")
    st.markdown("- **Technical Indicators**")

if not selected_tickers:
    st.info("👈 Select or enter a stock ticker to get started!")
    st.stop()

# Data Fetching with Progress
data = {}
progress_text = "Fetching market data..."
progress_bar = st.progress(0)

for i, ticker in enumerate(selected_tickers):
    with st.spinner(f"Loading {ticker}..."):
        data[ticker] = yf.Ticker(ticker)
    progress_bar.progress((i + 1) / len(selected_tickers))
    
progress_bar.empty()

# --- COMPARISON MODE (If > 1 ticker) ---
if len(selected_tickers) > 1:
    st.header("📊 Market Comparison")
    
    # Metrics Table
    cols = st.columns(len(selected_tickers))
    comparison_data = []
    
    for idx, ticker in enumerate(selected_tickers):
        stock = data[ticker]
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', current_price)
        delta = current_price - previous_close
        delta_percent = (delta / previous_close) * 100 if previous_close else 0
        
        comparison_data.append({
            'Ticker': ticker,
            'Price': f"${current_price:.2f}",
            'Change %': f"{delta_percent:.2f}%",
            'Market Cap': format_large_number(info.get('marketCap')),
            'P/E': f"{info.get('trailingPE', 'N/A')}"
        })
        
        with cols[idx]:
            st.metric(
                label=ticker, 
                value=f"${current_price:.2f}", 
                delta=f"{delta_percent:.2f}%"
            )
    
    # Data Editor for Comparison
    with st.expander("📊 Detailed Comparison Table", expanded=False):
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    # Comparison Chart
    st.subheader("Price History Comparison")
    fig = go.Figure()
    for ticker in selected_tickers:
        hist = data[ticker].history(period=selected_period)
        if not hist.empty:
            start_price = hist['Close'].iloc[0]
            normalized_close = ((hist['Close'] - start_price) / start_price) * 100
            fig.add_trace(go.Scatter(x=hist.index, y=normalized_close, mode='lines', name=ticker))
    
    fig.update_layout(
        yaxis_title="Change (%)", 
        hovermode="x unified",
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# --- DEEP DIVE MODE (Iterate through tickers) ---
st.markdown("---")
st.header("🔎 Deep Dive Analysis")

tabs = st.tabs(selected_tickers)

for i, ticker in enumerate(selected_tickers):
    with tabs[i]:
        with st.status(f"Analyzing {ticker}...", expanded=True) as status:
            st.write("Fetching fundamentals...")
            stock = data[ticker]
            info = stock.info
            
            st.write("Analyzing news sentiment...")
            news = stock.news
            
            st.write("Calculating technical indicators...")
            hist = stock.history(period=selected_period)
            
            status.update(label=f"Analysis complete for {ticker}!", state="complete", expanded=False)
        
        # Fundamentals
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Market Cap", format_large_number(info.get('marketCap')))
        with col2: st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        with col3: st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
        with col4: st.metric("Volume", format_large_number(info.get('volume')))

        # Sentiment
        total_polarity = 0
        analyzed_news = []
        
        if news:
            for item in news:
                title = item.get('title', '')
                if not title and 'content' in item: title = item['content'].get('title', '')
                link = item.get('link', '')
                publisher = item.get('publisher', 'Unknown')
                
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                total_polarity += polarity
                analyzed_news.append({'title': title, 'link': link, 'publisher': publisher, 'polarity': polarity})
            
            avg_polarity = total_polarity / len(news)
        else:
            avg_polarity = 0

        st.subheader("Sentiment Analysis")
        s_col1, s_col2 = st.columns([1, 3])
        with s_col1:
            st.markdown(f"## {get_sentiment_label(avg_polarity)}")
            st.progress((avg_polarity + 1) / 2)
        
        with s_col2:
            with st.expander("Latest News & Sentiment Scores", expanded=False):
                for item in analyzed_news[:5]:
                    p_score = item['polarity']
                    p_emoji = "🟢" if p_score > 0.1 else "🔴" if p_score < -0.1 else "🟡"
                    st.markdown(f"{p_emoji} **[{item['title']}]({item['link']})**")
                    st.caption(f"Source: {item['publisher']} | Score: {p_score:.2f}")

        # Price Chart with Technical Indicators
        st.subheader("Price Chart & Technical Analysis")
        
        if not hist.empty and show_indicators:
            # Calculate indicators
            hist['RSI'] = ta.rsi(hist['Close'], length=rsi_period)
            hist['SMA_Short'] = ta.sma(hist['Close'], length=ma_short)
            hist['SMA_Long'] = ta.sma(hist['Close'], length=ma_long)
            
            if show_macd:
                macd = ta.macd(hist['Close'])
                hist['MACD'] = macd['MACD_12_26_9']
                hist['MACD_signal'] = macd['MACDs_12_26_9']
            
            # Create subplots
            from plotly.subplots import make_subplots
            
            num_rows = 3 if show_macd else 2
            fig = make_subplots(
                rows=num_rows, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.5, 0.25, 0.25] if show_macd else [0.7, 0.3],
                subplot_titles=(f'{ticker} Price', 'RSI', 'MACD') if show_macd else (f'{ticker} Price', 'RSI')
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            # Moving Averages
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['SMA_Short'], name=f'SMA {ma_short}', line=dict(color='orange', width=1)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['SMA_Long'], name=f'SMA {ma_long}', line=dict(color='blue', width=1)),
                row=1, col=1
            )
            
            # RSI
            fig.add_trace(
                go.Scatter(x=hist.index, y=hist['RSI'], name='RSI', line=dict(color='purple')),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            if show_macd:
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist['MACD'], name='MACD', line=dict(color='blue')),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Scatter(x=hist.index, y=hist['MACD_signal'], name='Signal', line=dict(color='red')),
                    row=3, col=1
                )
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=800,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Raw Data Expander
            with st.expander("📊 View Raw Price Data", expanded=False):
                st.dataframe(hist[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA_Short', 'SMA_Long']].tail(50))
        
        elif not hist.empty:
            # Simple chart without indicators
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close'])])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No price history available.")

# Attribution Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>Built by Abhi Bhardwaj</strong></p>
    <p>Data: <a href='https://github.com/ranaroussi/yfinance' target='_blank'>yfinance</a> | 
    Sentiment: <a href='https://textblob.readthedocs.io/' target='_blank'>TextBlob</a> | 
    <a href='https://github.com/AB0204/Stock-Agent' target='_blank'>View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
