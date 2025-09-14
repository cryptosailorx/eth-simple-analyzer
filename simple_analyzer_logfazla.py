"""
simple_analyzer_FINAL.py
ETH Trend Analyzer - Debug Eklenmiş Final Versiyon
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleFibAnalyzer:
    def __init__(self):
        self.HISTORICAL_LIMIT = 1000  # Geriye dönük veri
        self.ANALYSIS_WINDOW = 20     # Analiz penceresi
        self.UPDATE_INTERVAL = 5      # 5 dakikada bir güncelle
        self.last_update = None
        self.current_analysis = {}
        
        logger.info("SimpleFibAnalyzer initialized")
        logger.info(f"Analysis window: {self.ANALYSIS_WINDOW} candles")
        logger.info(f"Update interval: {self.UPDATE_INTERVAL} minutes")
    
    def find_swing_points(self, candles: List[Dict], lookback: int = 10, lookforward: int = 10) -> Dict:
        """Swing High ve Swing Low noktalarını tespit et"""
        swing_highs = []
        swing_lows = []
        
        total_needed = lookback + lookforward + 1
        if len(candles) < total_needed:
            logger.warning(f"Not enough candles for swing detection: {len(candles)} < {total_needed}")
            return {"swing_highs": [], "swing_lows": []}
        
        logger.info(f"🔍 Starting swing detection on {len(candles)} candles...")
        logger.info(f"📊 Swing parameters: lookback={lookback}, lookforward={lookforward}")
        
        search_end = len(candles) - lookforward
        logger.info(f"🎯 Searching swings in range {lookback} to {search_end}")
        
        for i in range(lookback, search_end):
            try:
                current_high = float(candles[i]['high'])
                current_low = float(candles[i]['low'])
                
                # Swing High kontrolü
                is_swing_high = True
                for j in range(i - lookback, i + lookforward + 1):
                    if j != i:
                        compare_high = float(candles[j]['high'])
                        if compare_high >= current_high:
                            is_swing_high = False
                            break
                
                if is_swing_high:
                    swing_highs.append({
                        "index": i,
                        "price": current_high,
                        "timestamp": candles[i]['timestamp']
                    })
                
                # Swing Low kontrolü
                is_swing_low = True
                for j in range(i - lookback, i + lookforward + 1):
                    if j != i:
                        compare_low = float(candles[j]['low'])
                        if compare_low <= current_low:
                            is_swing_low = False
                            break
                
                if is_swing_low:
                    swing_lows.append({
                        "index": i,
                        "price": current_low,
                        "timestamp": candles[i]['timestamp']
                    })
                    
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Error processing candle {i}: {e}")
                continue
        
        logger.info(f"✅ Swing detection completed: {len(swing_highs)} highs, {len(swing_lows)} lows found")
        
        if swing_highs:
            logger.info(f"🔺 Latest swing high: ${swing_highs[-1]['price']:.2f} at index {swing_highs[-1]['index']}")
        if swing_lows:
            logger.info(f"🔻 Latest swing low: ${swing_lows[-1]['price']:.2f} at index {swing_lows[-1]['index']}")
        
        return {
            "swing_highs": swing_highs,
            "swing_lows": swing_lows
        }
    
    def analyze_trend_direction(self, candles: List[Dict]) -> tuple[str, float]:
        """Swing point based trend direction analysis"""
        if len(candles) < 50:
            logger.warning(f"Insufficient candles for swing analysis: {len(candles)} < 50")
            return "INSUFFICIENT_DATA", 0
        
        # Swing noktalarını tespit et
        swing_data = self.find_swing_points(candles, lookback=10, lookforward=10)
        swing_highs = swing_data["swing_highs"]
        swing_lows = swing_data["swing_lows"]
        
        logger.info(f"🔍 Swing Detection Results: {len(swing_highs)} highs, {len(swing_lows)} lows")
        
        if not swing_highs or not swing_lows:
            logger.warning("⚠️ No swing points found, falling back to simple analysis")
            # Fallback: Simple price analysis
            recent_candles = candles[-20:]
            closes = [float(c['close']) for c in recent_candles]
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            
            if price_change > 0.5:
                return "WEAK_BULLISH", 60
            elif price_change < -0.5:
                return "WEAK_BEARISH", 60  
            else:
                return "SIDEWAYS", 70
        
        # En son swing high ve low'ları al
        last_swing_high = swing_highs[-1]
        last_swing_low = swing_lows[-1]
        
        logger.info(f"🔺 Last Swing High: ${last_swing_high['price']:.2f} (Index: {last_swing_high['index']})")
        logger.info(f"🔻 Last Swing Low: ${last_swing_low['price']:.2f} (Index: {last_swing_low['index']})")
        
        # Şu anki mumun high/low değerleri
        current_candle = candles[-1]
        current_high = float(current_candle['high'])
        current_low = float(current_candle['low'])
        current_close = float(current_candle['close'])
        
        logger.info(f"📊 Current Mum: High=${current_high:.2f}, Low=${current_low:.2f}, Close=${current_close:.2f}")
        
        # Trend belirleme mantığı
        broke_swing_high = current_high > last_swing_high["price"]
        broke_swing_low = current_low < last_swing_low["price"]
        
        logger.info(f"🎯 Breakout Check: High broke={broke_swing_high}, Low broke={broke_swing_low}")
        
        # Confidence hesaplama için mesafeler
        swing_high_distance = abs(current_high - last_swing_high["price"]) / last_swing_high["price"] * 100
        swing_low_distance = abs(current_low - last_swing_low["price"]) / last_swing_low["price"] * 100
        
        if broke_swing_high and not broke_swing_low:
            direction = "BULLISH"
            confidence = min(95, 70 + swing_high_distance * 10)
            logger.info(f"🚀 BULLISH: Swing high broken by ${current_high - last_swing_high['price']:.2f}")
            
        elif broke_swing_low and not broke_swing_high:
            direction = "BEARISH"
            confidence = min(95, 70 + swing_low_distance * 10)
            logger.info(f"📉 BEARISH: Swing low broken by ${last_swing_low['price'] - current_low:.2f}")
            
        elif broke_swing_high and broke_swing_low:
            if last_swing_high["index"] > last_swing_low["index"]:
                direction = "BULLISH"
                confidence = min(90, 60 + swing_high_distance * 10)
                logger.info(f"🔥 BULLISH: Both broken, swing high more recent")
            else:
                direction = "BEARISH"  
                confidence = min(90, 60 + swing_low_distance * 10)
                logger.info(f"🔥 BEARISH: Both broken, swing low more recent")
                
        else:
            direction = "SIDEWAYS"
            
            swing_range = last_swing_high["price"] - last_swing_low["price"]
            if swing_range > 0:
                position_ratio = (current_close - last_swing_low["price"]) / swing_range
                center_distance = abs(position_ratio - 0.5)
                confidence = max(50, 100 - center_distance * 100)
                logger.info(f"↔️ SIDEWAYS: No breakouts, position in range: {position_ratio:.2f}")
            else:
                confidence = 50
        
        return direction, confidence
    
    def calculate_fibonacci_retracement(self, prev_candle: Dict, current_candle: Dict) -> Dict:
        """İki mumlu Fibonacci düzeltme analizi"""
        try:
            prev_high = float(prev_candle['high'])
            prev_low = float(prev_candle['low'])
            prev_open = float(prev_candle.get('open', prev_candle['close']))
            prev_close = float(prev_candle['close'])
            
            current_high = float(current_candle['high'])
            current_low = float(current_candle['low'])
            
            prev_range = prev_high - prev_low
            
            if prev_range <= 0:
                return {"fib_level": 0, "retracement_pct": 0, "range_size": 0, "direction": "invalid"}
            
            fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
            
            prev_is_bullish = prev_close > prev_open
            
            if prev_is_bullish:
                retracement_ratio = (prev_high - current_low) / prev_range
                direction = "pullback_after_bullish"
            else:
                retracement_ratio = (current_high - prev_low) / prev_range
                direction = "recovery_after_bearish"
            
            retracement_ratio = max(0, min(1, retracement_ratio))
            
            closest_fib = min(fib_levels, key=lambda x: abs(x - retracement_ratio))
            
            return {
                "fib_level": closest_fib,
                "retracement_pct": retracement_ratio * 100,
                "range_size": prev_range,
                "direction": direction,
                "prev_was_bullish": prev_is_bullish
            }
            
        except Exception as e:
            logger.error(f"Fibonacci calculation error: {e}")
            return {"fib_level": 0, "retracement_pct": 0, "range_size": 0, "direction": "error"}
    
    def calculate_average_retracement(self, candles: List[Dict]) -> Dict:
        """Son 20 mumun ortalama Fibonacci düzeltme analizi"""
        if len(candles) < self.ANALYSIS_WINDOW:
            return {"avg_retracement": 0, "dominant_fib_level": 0, "sample_size": 0}
        
        recent_candles = candles[-self.ANALYSIS_WINDOW:]
        retracements = []
        fib_levels = []
        
        for i in range(1, len(recent_candles)):
            prev_candle = recent_candles[i-1]
            current_candle = recent_candles[i]
            
            fib_data = self.calculate_fibonacci_retracement(prev_candle, current_candle)
            
            if fib_data['range_size'] > 0 and fib_data['direction'] != 'error':
                retracements.append(fib_data['retracement_pct'])
                fib_levels.append(fib_data['fib_level'])
        
        if not retracements:
            return {"avg_retracement": 0, "dominant_fib_level": 0, "sample_size": 0}
        
        avg_retracement = np.mean(retracements)
        dominant_fib = max(set(fib_levels), key=fib_levels.count) if fib_levels else 0
        
        return {
            "avg_retracement": avg_retracement,
            "dominant_fib_level": dominant_fib,
            "sample_size": len(retracements),
            "retracement_std": np.std(retracements) if len(retracements) > 1 else 0
        }
    
    def should_update_analysis(self) -> bool:
        """5 dakikada bir güncelleyip güncellememesi gerektiğini kontrol et"""
        if self.last_update is None:
            print("🔄 First analysis - updating...")
            return True
            
        time_diff = datetime.now() - self.last_update
        should_update = time_diff >= timedelta(minutes=self.UPDATE_INTERVAL)
        
        print(f"⏰ Time since last update: {time_diff}")
        print(f"🔄 Should update: {should_update}")
        
        return should_update
    
    def calculate_trend_strength(self, candles: List[Dict], direction: str) -> float:
        """Trend gücü hesaplama (0-100)"""
        if len(candles) < self.ANALYSIS_WINDOW:
            return 0
        
        recent_candles = candles[-self.ANALYSIS_WINDOW:]
        closes = [float(c['close']) for c in recent_candles]
        
        price_volatility = np.std(closes) / np.mean(closes) * 100
        
        volumes = [float(c.get('volume', 1)) for c in recent_candles]
        volume_trend = np.mean(volumes[-5:]) / np.mean(volumes[-15:]) if len(volumes) >= 15 else 1
        
        price_momentum = abs((closes[-1] - closes[0]) / closes[0] * 100)
        
        base_strength = min(100, price_momentum * 5)
        volatility_penalty = min(50, price_volatility * 2)
        volume_bonus = min(20, (volume_trend - 1) * 20) if volume_trend > 1 else 0
        
        strength = max(0, base_strength - volatility_penalty + volume_bonus)
        
        if direction in ["SIDEWAYS"]:
            strength *= 0.3
        elif direction in ["WEAK_BULLISH", "WEAK_BEARISH"]:
            strength *= 0.7
        
        return min(100, strength)
    
    def perform_analysis(self, candles: List[Dict]) -> Optional[Dict]:
        """Ana analiz fonksiyonu"""
        print(f"🔄 PERFORM_ANALYSIS CALLED with {len(candles)} candles")
        
        if not self.should_update_analysis():
            print("⏰ Not time for update yet, returning None")
            return None
        
        if len(candles) < self.ANALYSIS_WINDOW:
            logger.warning(f"Insufficient data: {len(candles)} < {self.ANALYSIS_WINDOW}")
            return None
        
        try:
            # DEBUG: Raw data kontrol
            print(f"🔄 PERFORM_ANALYSIS STARTED with {len(candles)} candles")
            print(f"📊 Raw current candle: {candles[-1]}")
            logger.info(f"🔄 Performing new analysis with {len(candles)} candles...")
            logger.info(f"📊 Raw current candle: {candles[-1]}")
            
            # ÖNCE swing detection'u manual çağır
            print("🎯 Manual swing detection starting...")
            logger.info("🎯 Manual swing detection starting...")
            swing_data = self.find_swing_points(candles, lookback=10, lookforward=10)
            swing_highs = swing_data["swing_highs"] 
            swing_lows = swing_data["swing_lows"]
            print(f"✅ Manual swing detection completed: {len(swing_highs)} highs, {len(swing_lows)} lows")
            
            # Ana analizler
            print("🔄 Calling analyze_trend_direction...")
            direction, confidence = self.analyze_trend_direction(candles)
            print(f"✅ Direction: {direction}, Confidence: {confidence}")
            
            fib_data = self.calculate_average_retracement(candles)
            trend_strength = self.calculate_trend_strength(candles, direction)
            
            # Current price ve mum bilgileri
            current_candle = candles[-1]
            current_price = float(current_candle['close'])
            current_high = float(current_candle['high'])
            current_low = float(current_candle['low'])
            
            # Sonuçları kaydet - Swing bilgileri ile birlikte
            self.current_analysis = {
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "current_high": current_high,
                "current_low": current_low,
                "direction": direction,
                "confidence": round(confidence, 1),
                "avg_fibonacci_retracement": round(fib_data['avg_retracement'], 1),
                "dominant_fib_level": fib_data['dominant_fib_level'],
                "trend_strength": round(trend_strength, 0),
                "next_update_minutes": self.UPDATE_INTERVAL,
                "candles_analyzed": len(candles),
                "analysis_window": self.ANALYSIS_WINDOW,
                "sample_size": fib_data['sample_size'],
                # Swing point bilgileri - MANUEL OLARAK EKLIYORUZ
                "last_swing_high": None,
                "last_swing_low": None,
                "swing_high_age": 0,
                "swing_low_age": 0,
                "swing_points_found": False,
                "total_swing_highs": len(swing_highs),
                "total_swing_lows": len(swing_lows)
            }
            
            # Swing point bilgilerini ekle - FULL DEBUG
            print(f"🔧 Attempting to save swing data...")
            print(f"   swing_highs length: {len(swing_highs)}")
            print(f"   swing_lows length: {len(swing_lows)}")
            
            if swing_highs and swing_lows:
                try:
                    last_swing_high = swing_highs[-1]
                    last_swing_low = swing_lows[-1]
                    
                    print(f"🔺 Processing swing high: {last_swing_high}")
                    print(f"🔻 Processing swing low: {last_swing_low}")
                    
                    swing_high_age = len(candles) - 1 - last_swing_high["index"]
                    swing_low_age = len(candles) - 1 - last_swing_low["index"]
                    
                    print(f"📊 Calculated ages: high={swing_high_age}, low={swing_low_age}")
                    
                    self.current_analysis.update({
                        "last_swing_high": last_swing_high["price"],
                        "last_swing_low": last_swing_low["price"],
                        "swing_high_age": swing_high_age,
                        "swing_low_age": swing_low_age,
                        "swing_points_found": True
                    })
                    
                    print(f"✅ Swing data saved to analysis:")
                    print(f"   High: ${last_swing_high['price']:.2f} ({swing_high_age} mum önce)")
                    print(f"   Low: ${last_swing_low['price']:.2f} ({swing_low_age} mum önce)")
                    
                except Exception as e:
                    print(f"❌ Error saving swing data: {e}")
                    print(f"   Type: {type(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ No swing data to save")
            
            print(f"💾 Analysis data saved:")
            print(f"   current_high: {self.current_analysis['current_high']}")
            print(f"   current_low: {self.current_analysis['current_low']}")
            print(f"   swing_points_found: {self.current_analysis['swing_points_found']}")
            
            # FULL DEBUG - Dictionary contents
            print(f"💾 ANALYSIS DICTIONARY CONTENTS:")
            for key, value in self.current_analysis.items():
                print(f"   {key}: {value}")
            
            self.last_update = datetime.now()
            
            # Detaylı log
            logger.info(f"✅ Analysis completed: {direction} (Conf: {confidence:.1f}%)")
            logger.info(f"📊 Current Mum - High: ${current_high:.2f}, Low: ${current_low:.2f}, Close: ${current_price:.2f}")
            logger.info(f"🔍 Swing Detection - Highs: {len(swing_highs)}, Lows: {len(swing_lows)}")
            
            if self.current_analysis["swing_points_found"]:
                logger.info(f"🔺 Last Swing High: ${self.current_analysis['last_swing_high']:.2f} ({self.current_analysis['swing_high_age']} mum önce)")
                logger.info(f"🔻 Last Swing Low: ${self.current_analysis['last_swing_low']:.2f} ({self.current_analysis['swing_low_age']} mum önce)")
            else:
                logger.warning(f"⚠️ Swing points not found. Total candles: {len(candles)}")
            
            logger.info(f"📈 Fibonacci Avg: {fib_data['avg_retracement']:.1f}% | Trend Strength: {trend_strength:.0f}")
            
            return self.current_analysis
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_last_analysis(self) -> Dict:
        """Son analiz sonucunu döndür"""
        return self.current_analysis
    
    def format_analysis_summary(self, analysis: Dict) -> str:
        """Konsol için detaylı özet"""
        if not analysis:
            return "No analysis available"
        
        summary = f"""
📊 ETH Analysis Summary
Current Price: ${analysis['current_price']:.2f}
Current Mum - High: ${analysis.get('current_high', 0):.2f} | Low: ${analysis.get('current_low', 0):.2f}

Direction: {analysis['direction']} (Confidence: {analysis['confidence']}%)
Avg Fibonacci Retracement: {analysis['avg_fibonacci_retracement']}%
Dominant Fib Level: {analysis['dominant_fib_level']}
Trend Strength: {analysis['trend_strength']}/100
Sample Size: {analysis['sample_size']} pairs"""

        # Swing point bilgileri ekle
        if analysis.get('swing_points_found', False):
            summary += f"""

🔺 Last Swing High: ${analysis['last_swing_high']:.2f} ({analysis['swing_high_age']} mum önce)
🔻 Last Swing Low: ${analysis['last_swing_low']:.2f} ({analysis['swing_low_age']} mum önce)
📊 Swing Count: {analysis.get('total_swing_highs', 0)} highs, {analysis.get('total_swing_lows', 0)} lows"""
        else:
            summary += f"""

⚠️ Swing points: Insufficient data for detection"""

        summary += f"""

Next Update: {analysis['next_update_minutes']} minutes"""
        
        return summary.strip()

# Test fonksiyonu
def test_analyzer():
    """Test fonksiyonu"""
    analyzer = SimpleFibAnalyzer()
    
    # Test data
    test_candles = []
    base_price = 2000
    
    for i in range(25):
        price_change = np.random.normal(0, 10)
        base_price += price_change
        
        open_price = base_price
        high = base_price + abs(np.random.normal(5, 2))
        low = base_price - abs(np.random.normal(5, 2))
        close = base_price + np.random.normal(0, 3)
        
        candle = {
            "timestamp": datetime.now().timestamp() * 1000 + i * 60000,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.uniform(1000, 5000)
        }
        test_candles.append(candle)
    
    result = analyzer.perform_analysis(test_candles)
    
    if result:
        print("✅ Test successful!")
        print(analyzer.format_analysis_summary(result))
    else:
        print("❌ Test failed!")

if __name__ == "__main__":
    test_analyzer()