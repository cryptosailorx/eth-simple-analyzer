"""
Swing Detection Test
Direkt olarak swing detection'u test et
"""

import requests
import json
from simple_analyzer_logfazla import SimpleFibAnalyzer

def test_swing_detection():
    """Manuel swing detection test"""
    print("🔍 Testing swing detection...")
    
    # Historical data al
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "limit": 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        klines = response.json()
        
        print(f"📊 Loaded {len(klines)} klines")
        
        # Convert to candle format
        candles = []
        for kline in klines:
            candle = {
                "timestamp": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5])
            }
            candles.append(candle)
        
        print(f"✅ Converted to {len(candles)} candles")
        print(f"📊 Sample candle: {candles[-1]}")
        
        # Test swing detection
        analyzer = SimpleFibAnalyzer()
        swing_data = analyzer.find_swing_points(candles, lookback=10, lookforward=10)
        
        swing_highs = swing_data["swing_highs"]
        swing_lows = swing_data["swing_lows"]
        
        print(f"\n🎯 SWING DETECTION RESULTS:")
        print(f"Swing Highs: {len(swing_highs)}")
        print(f"Swing Lows: {len(swing_lows)}")
        
        if swing_highs:
            print(f"\n🔺 Last 3 Swing Highs:")
            for sh in swing_highs[-3:]:
                age = len(candles) - 1 - sh["index"]
                print(f"   ${sh['price']:.2f} - {age} mum önce (index {sh['index']})")
        
        if swing_lows:
            print(f"\n🔻 Last 3 Swing Lows:")
            for sl in swing_lows[-3:]:
                age = len(candles) - 1 - sl["index"]
                print(f"   ${sl['price']:.2f} - {age} mum önce (index {sl['index']})")
        
        # Current mum vs swing levels
        current = candles[-1]
        current_high = current['high']
        current_low = current['low']
        
        print(f"\n📊 Current Mum:")
        print(f"High: ${current_high:.2f}")
        print(f"Low: ${current_low:.2f}")
        print(f"Close: ${current['close']:.2f}")
        
        if swing_highs and swing_lows:
            last_high = swing_highs[-1]['price']
            last_low = swing_lows[-1]['price']
            
            print(f"\n🎯 Breakout Analysis:")
            print(f"Current High > Last Swing High: {current_high} > {last_high} = {current_high > last_high}")
            print(f"Current Low < Last Swing Low: {current_low} < {last_low} = {current_low < last_low}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_swing_detection()