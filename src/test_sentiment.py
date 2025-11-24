import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.services.sentiment_service import get_sentiment_data, calculate_pump_score

def test_diy_sentiment():
    print("🚀 Testing Sentiment Analysis (CoinGecko)...")
    
    symbol = "SOL"
    
    print(f"\n📊 Fetching sentiment data for {symbol}...")
    sentiment_data = get_sentiment_data(symbol)
    print(f"Social Data: {json.dumps(sentiment_data, indent=2)}")
    
    print("\n🧮 Calculating Pump Score...")
    
    tech_metrics = {
        "volume_change_1h": 150,
        "rsi": 65
    }
    
    result = calculate_pump_score(sentiment_data, tech_metrics)
    
    print("\n✅ Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_diy_sentiment()
