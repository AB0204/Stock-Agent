# SentiStock Analytics 📈

A powerful AI-driven tool that analyzes stock prices and news sentiment.

## Features
- **Real-time Data**: Fetches live stock prices using `yfinance`.
- **Sentiment Analysis**: Uses NLP (`TextBlob`) to determine if news is Bullish or Bearish.
- **Web Dashboard**: Built with **Streamlit** for interactive charts and data visualization.
- **CLI Mode**: Also includes a command-line interface for quick checks.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AB0204/SentiStock-Analytics.git
    cd SentiStock-Analytics
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Web App (Recommended)
```bash
streamlit run app.py
```

### CLI Tool
```bash
python3 main.py analyze TSLA
```
