import streamlit as st
import yfinance as yf
from textblob import TextBlob
import plotly.graph_objects as go
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io

# Page Config
st.set_page_config(page_title="Trade Smarter, Not Harder: Your Personal AI Stock Agent", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Glassmorphism cards */
    .metric-card {
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 215, 0, 0.2);
        margin-bottom: 15px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(255, 215, 0, 0.3);
    }
    
    /* Enhanced metrics */
    .stMetric {
        background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FFD700;
    }
    
    /* Bullish/Bearish badges */
    .bullish {
        color: #00FF88;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .bearish {
        color: #FF4444;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
    }
    
    /* Gold accent for headers */
    h1, h2, h3 {
        color: #FFD700 !important;
    }
    
    /* Smooth transitions */
    * {
        transition: all 0.3s ease;
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

def apply_scenario(base_sentiment, scenario):
    """Apply scenario adjustments to sentiment"""
    scenarios = {
        "None": 1.0,
        "Interest Rates +1%": 0.75,
        "Tech Acquisition Announced": 1.3,
        "Global Recession Fear": 0.5,
        "Earnings Beat Expectation": 1.4,
        "Supply Chain Disruption": 0.65
    }
    return base_sentiment * scenarios.get(scenario, 1.0)

def generate_certificate(ticker, price, recommendation, sentiment_score, pe_ratio, market_cap):
    """Generate a professional analysis certificate"""
    # Create image
    img = Image.new('RGB', (1200, 800), color='#0E1117')
    draw = ImageDraw.Draw(img)
    
    # Try to use default font, fallback to basic if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        body_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        title_font = header_font = body_font = small_font = ImageFont.load_default()
    
    # Gold border
    draw.rectangle([20, 20, 1180, 780], outline='#FFD700', width=5)
    draw.rectangle([30, 30, 1170, 770], outline='#FFD700', width=2)
    
    # Title
    draw.text((600, 80), "STOCK ANALYSIS CERTIFICATE", fill='#FFD700', font=title_font, anchor='mm')
    draw.text((600, 140), f"Analysis Report: {ticker}", fill='#FFFFFF', font=header_font, anchor='mm')
    
    # Divider line
    draw.line([(100, 180), (1100, 180)], fill='#FFD700', width=3)
    
    # Main recommendation
    rec_color = '#00FF88' if 'BUY' in recommendation else '#FF4444' if 'SELL' in recommendation else '#FFD700'
    draw.text((600, 260), f"RECOMMENDATION: {recommendation}", fill=rec_color, font=header_font, anchor='mm')
    
    # Metrics
    y_pos = 340
    metrics = [
        f"Current Price: ${price:.2f}",
        f"Sentiment Score: {sentiment_score:.2f}",
        f"P/E Ratio: {pe_ratio}",
        f"Market Cap: {market_cap}"
    ]
    
    for metric in metrics:
        draw.text((600, y_pos), metric, fill='#FFFFFF', font=body_font, anchor='mm')
        y_pos += 50
    
    # Footer
    draw.line([(100, 620), (1100, 620)], fill='#FFD700', width=2)
    draw.text((600, 670), "Analyzed by Abhi Bhardwaj - Stock Agent", fill='#888888', font=body_font, anchor='mm')
    draw.text((600, 720), f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill='#666666', font=small_font, anchor='mm')
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

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
    st.markdown("### ✨ Features")
    st.markdown("- 📊 **Multi-Stock Comparison**")
    st.markdown("- 💰 **Real-time Prices**")
    st.markdown("- 📰 **Sentiment Analysis**")
    st.markdown("- 📉 **Technical Indicators**")
    st.markdown("- 🔮 **Scenario Planning**")

# Main Page Title
st.title("📈 Trade Smarter, Not Harder: Your Personal AI Stock Agent")
st.markdown("---")

if not selected_tickers:
    st.info("👈 Select or enter a stock ticker to get started!")
    st.stop()

# URL Sharing Feature
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Share Analysis")
if selected_tickers:
    share_ticker = selected_tickers[0]
    share_url = f"?ticker={share_ticker}"
    st.sidebar.code(share_url, language=None)
    st.sidebar.caption("Share this URL parameter to link directly to this stock")

# Check for URL parameters on load
try:
    query_params = st.query_params
    if "ticker" in query_params:
        url_ticker = query_params["ticker"].upper()
        if url_ticker not in selected_tickers:
            selected_tickers = [url_ticker]
            st.info(f"📍 Loaded {url_ticker} from shared link!")
except:
    pass

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

# --- SMART STOCK ANALYSIS (Iterate through tickers) ---
st.markdown("---")
st.header("⚡ Smart Stock Analysis")

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
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        with col1: st.metric("Current Price", f"${current_price:.2f}")
        with col2: st.metric("Market Cap", format_large_number(info.get('marketCap')))
        with col3: st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        with col4: st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

        # Scenario Injector 🔮
        st.markdown("---")
        st.subheader("🔮 Scenario Planning")
        scenario_col1, scenario_col2 = st.columns([2, 1])
        
        with scenario_col1:
            selected_scenario = st.selectbox(
                "What if...",
                ["None", "Interest Rates +1%", "Tech Acquisition Announced", 
                 "Global Recession Fear", "Earnings Beat Expectation", "Supply Chain Disruption"],
                key=f"scenario_{ticker}"
            )
        
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
        
        # Apply scenario adjustment
        base_sentiment = avg_polarity
        adjusted_sentiment = apply_scenario(base_sentiment, selected_scenario)
        
        # Generate recommendation
        if adjusted_sentiment > 0.1:
            recommendation = "BUY"
        elif adjusted_sentiment < -0.1:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        with scenario_col2:
            if selected_scenario != "None":
                st.metric(
                    "Scenario Impact",
                    f"{(adjusted_sentiment - base_sentiment) * 100:.1f}%",
                    delta=f"Confidence: {abs(adjusted_sentiment) * 100:.0f}%"
                )
                st.caption(f"**Adjusted Rec:** {recommendation}")
            else:
                st.metric("Base Sentiment", f"{base_sentiment:.2f}")

        st.subheader("📰 News Sentiment Analysis")
        
        # News Sentiment Filter
        if analyzed_news:
            min_sentiment = st.slider(
                "Filter news by minimum sentiment score",
                -1.0, 1.0, -1.0, 0.1,
                key=f"filter_{ticker}"
            )
            filtered_news = [n for n in analyzed_news if n['polarity'] >= min_sentiment]
            st.caption(f"Showing {len(filtered_news)} of {len(analyzed_news)} articles")
        else:
            filtered_news = []
        
        s_col1, s_col2 = st.columns([1, 3])
        with s_col1:
            st.markdown(f"## {get_sentiment_label(adjusted_sentiment)}")
            st.progress((adjusted_sentiment + 1) / 2)
        
        with s_col2:
            # Certificate Download Button
            cert_buffer = generate_certificate(
                ticker, 
                current_price, 
                recommendation,
                adjusted_sentiment,
                info.get('trailingPE', 'N/A'),
                format_large_number(info.get('marketCap'))
            )
            
            st.download_button(
                label="📜 Download Analysis Certificate",
                data=cert_buffer,
                file_name=f"{ticker}_analysis_certificate.png",
                mime="image/png",
                use_container_width=True
            )
            
            with st.expander("Latest News & Sentiment Scores", expanded=False):
                for item in filtered_news[:10]:  # Use filtered_news instead of analyzed_news
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
    <p><strong>Built by: Abhi Bhardwaj</strong></p>
    <p>Data: <a href='https://github.com/ranaroussi/yfinance' target='_blank'>yfinance</a> | 
    Sentiment: <a href='https://textblob.readthedocs.io/' target='_blank'>TextBlob</a> | 
    <a href='https://github.com/AB0204/Stock-Agent' target='_blank'>View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
