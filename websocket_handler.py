"""
websocket_handler_NEW.py
Real-time Fibonacci Tracking WebSocket Handler
"""

import asyncio
import websockets
import json
import requests
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleWebSocketHandler:
    def __init__(self, analyzer, telegram_bot=None):
        self.analyzer = analyzer
        self.telegram_bot = telegram_bot
        
        # WebSocket ayarları
        self.ws_url = "wss://fstream.binance.com/ws/ethusdt@kline_1m"
        self.rest_url = "https://fapi.binance.com/fapi/v1/klines"
        
        # Veri buffer - son 1000 mum
        self.candle_buffer = deque(maxlen=1000)
        
        # Bağlantı durumu
        self.running = False
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        logger.info("WebSocket handler initialized")
    
    async def fetch_historical_candles(self, limit: int = 1000) -> bool:
        """Başlangıç için historical kline verilerini çek"""
        logger.info(f"📥 Fetching last {limit} historical candles...")
        
        params = {
            "symbol": "ETHUSDT",
            "interval": "1m",
            "limit": min(limit, 1000)
        }
        
        try:
            response = requests.get(self.rest_url, params=params, timeout=15)
            response.raise_for_status()
            klines = response.json()
            
            if not klines:
                logger.error("❌ No historical data received")
                return False
            
            # Kline verisini standart formata çevir
            candles = []
            for kline in klines:
                candle = {
                    "timestamp": kline[0],
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "is_closed": True
                }
                candles.append(candle)
            
            # Buffer'a ekle
            self.candle_buffer.extend(candles)
            
            latest_price = candles[-1]['close']
            logger.info(f"✅ Loaded {len(candles)} historical candles")
            logger.info(f"📊 Latest price: ${latest_price:.2f}")
            logger.info(f"💾 Buffer size: {len(self.candle_buffer)}")
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"❌ HTTP error fetching historical data: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching historical data: {e}")
            return False
    
    async def process_websocket_message(self, message: str) -> None:
        """WebSocket mesajını işle ve real-time Fibonacci analizi yap"""
        try:
            data = json.loads(message)
            kline_data = data.get('k')
            
            if not kline_data:
                return
            
            # Sadece kapalı mumları işle (x=True)
            is_closed = kline_data.get('x', False)
            if not is_closed:
                return
            
            # Yeni mumu oluştur
            candle = {
                "timestamp": int(kline_data['t']),
                "open": float(kline_data['o']),
                "high": float(kline_data['h']),
                "low": float(kline_data['l']),
                "close": float(kline_data['c']),
                "volume": float(kline_data['v']),
                "is_closed": True
            }
            
            # Real-time Fibonacci analizi - Her yeni mum vs önceki mum
            if len(self.candle_buffer) > 0:
                prev_candle = self.candle_buffer[-1]
                fib_result = self.analyzer.calculate_fibonacci_retracement(prev_candle, candle)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # Log'a yaz
                logger.info(f"🕯️  [{current_time}] New candle: ${candle['close']:.2f} | Vol: {candle['volume']:.0f}")
                logger.info(f"📊 Fibonacci vs Previous: {fib_result['retracement_pct']:.1f}% ({fib_result['fib_level']}) | {fib_result['direction']}")
                
                # Console'da detaylı göster
                prev_range = prev_candle['high'] - prev_candle['low']
                print(f"🔍 REAL-TIME FIBONACCI ANALYSIS [{current_time}]:")
                print(f"   Previous Candle: High=${prev_candle['high']:.2f}, Low=${prev_candle['low']:.2f}, Range=${prev_range:.2f}")
                print(f"   Current Candle: High=${candle['high']:.2f}, Low=${candle['low']:.2f}, Close=${candle['close']:.2f}")
                print(f"   📐 Fibonacci Level: {fib_result['fib_level']} ({fib_result['retracement_pct']:.1f}%)")
                print(f"   📊 Direction: {fib_result['direction']}")
                
                # Fibonacci seviye analizi
                fib_level = fib_result['fib_level']
                if fib_level in [0.382, 0.618]:
                    print(f"   🎯 GOLDEN RATIO LEVEL!")
                elif fib_level == 0.5:
                    print(f"   ⚖️  MIDDLE LEVEL")
                elif fib_result['retracement_pct'] > 80:
                    print(f"   ⚠️  STRONG RETRACEMENT")
                elif fib_result['retracement_pct'] < 20:
                    print(f"   💪 WEAK RETRACEMENT")
                
                print("-" * 70)
                
                # Real-time Fibonacci sonucunu Telegram'a gönder
                if self.telegram_bot and fib_result['range_size'] > 0:
                    await self.telegram_bot.send_realtime_fibonacci(prev_candle, candle, fib_result)
                
            else:
                current_time = datetime.now().strftime("%H:%M:%S")
                logger.info(f"🕯️  [{current_time}] First candle: ${candle['close']:.2f} | Volume: {candle['volume']:.0f}")
            
            # Buffer'a ekle
            self.candle_buffer.append(candle)
            
            # Ana swing analizi yap (5 dakikada bir)
            analysis_result = self.analyzer.perform_analysis(list(self.candle_buffer))
            
            if analysis_result:
                logger.info("📊 5-minute swing analysis completed!")
                
                # Konsol'da göster
                summary = self.analyzer.format_analysis_summary(analysis_result)
                print("\n" + "="*50)
                print("🔄 5-MINUTE SWING ANALYSIS UPDATE")
                print(summary)
                print("="*50 + "\n")
                
                # Telegram'a swing analizi gönder
                if self.telegram_bot:
                    await self.send_analysis_to_telegram(analysis_result)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in WebSocket message: {e}")
        except KeyError as e:
            logger.error(f"❌ Missing key in WebSocket message: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing WebSocket message: {e}")
    
    async def send_analysis_to_telegram(self, analysis: dict) -> None:
        """Swing analiz sonucunu Telegram'a gönder"""
        if not self.telegram_bot:
            logger.warning("⚠️  Telegram bot not configured")
            return
        
        try:
            await self.telegram_bot.send_analysis(analysis)
        except Exception as e:
            logger.error(f"❌ Error sending swing analysis to Telegram: {e}")
    
    async def connect_websocket(self) -> None:
        """WebSocket bağlantısını kur ve dinle"""
        logger.info(f"🔌 Connecting to WebSocket: {self.ws_url}")
        
        try:
            async with websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                
                self.connected = True
                self.reconnect_attempts = 0
                logger.info("✅ WebSocket connected successfully!")
                
                # İlk swing analiz yap
                if len(self.candle_buffer) >= self.analyzer.ANALYSIS_WINDOW:
                    initial_analysis = self.analyzer.perform_analysis(list(self.candle_buffer))
                    if initial_analysis:
                        logger.info("📊 Initial swing analysis completed")
                        summary = self.analyzer.format_analysis_summary(initial_analysis)
                        print("\n" + "="*50)
                        print("🚀 INITIAL SWING ANALYSIS")
                        print(summary)
                        print("="*50 + "\n")
                        
                        if self.telegram_bot:
                            await self.send_analysis_to_telegram(initial_analysis)
                
                # Real-time mesajları dinle
                async for message in websocket:
                    if not self.running:
                        break
                    await self.process_websocket_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.warning("⚠️  WebSocket connection closed")
        except websockets.exceptions.InvalidURI:
            self.connected = False
            logger.error(f"❌ Invalid WebSocket URI: {self.ws_url}")
        except Exception as e:
            self.connected = False
            logger.error(f"❌ WebSocket connection error: {e}")
    
    async def start_with_reconnect(self) -> None:
        """Yeniden bağlanma ile WebSocket'i başlat"""
        self.running = True
        
        while self.running:
            try:
                await self.connect_websocket()
                
            except Exception as e:
                logger.error(f"❌ WebSocket error: {e}")
            
            if not self.running:
                break
            
            # Yeniden bağlanma mantığı
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts <= self.max_reconnect_attempts:
                wait_time = min(60, 5 * self.reconnect_attempts)
                logger.info(f"🔄 Reconnecting in {wait_time} seconds... (attempt {self.reconnect_attempts})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached")
                self.stop()
    
    async def start(self) -> bool:
        """Ana başlatma fonksiyonu"""
        logger.info("🚀 Starting ETH Real-time Fibonacci WebSocket handler...")
        
        # Historical data yükle
        if not await self.fetch_historical_candles(1000):
            logger.error("❌ Failed to load historical data. Cannot start.")
            return False
        
        # WebSocket'i başlat
        await self.start_with_reconnect()
        return True
    
    def stop(self) -> None:
        """WebSocket handler'ı durdur"""
        logger.info("🛑 Stopping WebSocket handler...")
        self.running = False
        self.connected = False
    
    def get_status(self) -> dict:
        """Handler durumunu döndür"""
        return {
            "running": self.running,
            "connected": self.connected,
            "buffer_size": len(self.candle_buffer),
            "reconnect_attempts": self.reconnect_attempts,
            "last_candle": self.candle_buffer[-1] if self.candle_buffer else None
        }
    
    def get_latest_price(self) -> float:
        """En son fiyatı döndür"""
        if self.candle_buffer:
            return self.candle_buffer[-1]['close']
        return 0.0
