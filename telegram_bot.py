"""
telegram_bot.py
Basit Telegram Bot - ETH analiz sonuçlarını gönderir
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
        logger.info("Telegram bot initialized")
        logger.info(f"Chat ID: {chat_id}")
    
    async def start_session(self):
        """HTTP session başlat"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """HTTP session kapat"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Telegram'a mesaj gönder"""
        if not self.session:
            await self.start_session()
        
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info("✅ Message sent to Telegram successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                    return False
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ HTTP error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending message: {e}")
            return False
    
    def format_analysis_message(self, analysis: Dict) -> str:
        """Analiz sonucunu Telegram mesajı formatına çevir"""
        
        # Direction emoji mapping
        direction_emoji = {
            "BULLISH": "🚀📈",
            "BEARISH": "📉🔻", 
            "SIDEWAYS": "↔️📊",
            "WEAK_BULLISH": "📈⬆️",
            "WEAK_BEARISH": "📊⬇️",
            "INSUFFICIENT_DATA": "❓📊"
        }
        
        direction = analysis.get('direction', 'UNKNOWN')
        emoji = direction_emoji.get(direction, "❓")
        
        # Strength emoji
        strength = analysis.get('trend_strength', 0)
        if strength >= 75:
            strength_emoji = "💪💪💪"
        elif strength >= 50:
            strength_emoji = "💪💪"
        elif strength >= 25:
            strength_emoji = "💪"
        else:
            strength_emoji = "😴"
        
        # Fibonacci level emoji
        fib_level = analysis.get('dominant_fib_level', 0)
        if fib_level == 0.382:
            fib_emoji = "🎯"  # Golden ratio
        elif fib_level == 0.618:
            fib_emoji = "🏆"  # Golden ratio
        elif fib_level == 0.5:
            fib_emoji = "⚖️"  # Middle
        else:
            fib_emoji = "📐"
        
        # Confidence
        confidence = analysis.get('confidence', 0)
        conf_emoji = "🔥" if confidence > 70 else "⚡" if confidence > 40 else "💭"
        
        # Format timestamp
        timestamp = analysis.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        else:
            time_str = datetime.now().strftime("%H:%M:%S")
        
        message = f"""
🎯 <b>ETH Trend Analysis</b>

💰 <b>Current Price:</b> ${analysis.get('current_price', 0):.2f}
📊 <b>Current Mum:</b> H: ${analysis.get('current_high', 0):.2f} | L: ${analysis.get('current_low', 0):.2f}

📈 <b>Direction:</b> {direction} {emoji}
{conf_emoji} <b>Confidence:</b> {confidence:.1f}%

{fib_emoji} <b>Fibonacci Analysis:</b>
   • Avg Retracement: <code>{analysis.get('avg_fibonacci_retracement', 0):.1f}%</code>
   • Dominant Level: <code>{fib_level}</code>

{strength_emoji} <b>Trend Strength:</b> {strength}/100"""

        # Swing point bilgileri ekle
        if analysis.get('swing_points_found', False):
            message += f"""

🎯 <b>Swing Levels:</b>
   🔺 <b>Last Swing High:</b> ${analysis['last_swing_high']:.2f} <i>({analysis['swing_high_age']} mum önce)</i>
   🔻 <b>Last Swing Low:</b> ${analysis['last_swing_low']:.2f} <i>({analysis['swing_low_age']} mum önce)</i>"""
        else:
            message += f"""

⚠️ <b>Swing Levels:</b> <i>Detecting...</i>"""

        message += f"""

📈 <b>Analysis Details:</b>
   • Window: {analysis.get('analysis_window', 20)} candles
   • Sample Size: {analysis.get('sample_size', 0)} valid pairs
   • Total Candles: {analysis.get('candles_analyzed', 0)}

⏰ <b>Time:</b> {time_str}
🔄 <b>Next Update:</b> {analysis.get('next_update_minutes', 5)} minutes

<i>ETH Trend Analyzer v2.0 - Swing Based</i>
        """
        
        return message.strip()
    
    async def send_analysis(self, analysis: Dict) -> bool:
        """Analiz sonucunu Telegram'a gönder"""
        try:
            message = self.format_analysis_message(analysis)
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"❌ Error formatting analysis message: {e}")
            return False
    
    async def send_startup_message(self) -> bool:
        """Sistem başlangıç mesajı"""
        message = f"""
🚀 <b>ETH Trend Analyzer Started</b>

✅ WebSocket connection established
📊 Historical data loaded
🔄 Real-time analysis active

<b>Settings:</b>
• Analysis Window: 20 candles
• Update Interval: 5 minutes
• Fibonacci-focused analysis

<i>System online and monitoring ETH/USDT...</i>

⏰ Started at: {datetime.now().strftime("%H:%M:%S")}
        """
        return await self.send_message(message.strip())
    
    async def send_error_message(self, error: str) -> bool:
        """Hata mesajı gönder"""
        message = f"""
⚠️ <b>ETH Analyzer Error</b>

❌ <code>{error}</code>

🔄 System will attempt to recover automatically...

⏰ {datetime.now().strftime("%H:%M:%S")}
        """
        return await self.send_message(message.strip())
    
    async def test_connection(self) -> bool:
        """Bot bağlantısını test et"""
        test_message = f"""
🧪 <b>Test Message</b>

✅ Telegram bot connection successful!
📱 Chat ID: <code>{self.chat_id}</code>
⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

<i>Ready to send ETH analysis updates...</i>
        """
        return await self.send_message(test_message.strip())

# Test fonksiyonu
async def test_telegram_bot():
    """Telegram bot test"""
    # Test için dummy credentials - gerçek kullanımda değiştir
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set real BOT_TOKEN and CHAT_ID in the test function")
        return
    
    bot = SimpleTelegramBot(BOT_TOKEN, CHAT_ID)
    
    try:
        # Test connection
        success = await bot.test_connection()
        if success:
            print("✅ Telegram bot test successful!")
            
            # Test analysis message
            test_analysis = {
                "timestamp": datetime.now().isoformat(),
                "current_price": 4659.83,
                "direction": "BULLISH",
                "confidence": 75.5,
                "avg_fibonacci_retracement": 38.2,
                "dominant_fib_level": 0.382,
                "trend_strength": 68,
                "next_update_minutes": 5,
                "candles_analyzed": 1000,
                "analysis_window": 20,
                "sample_size": 20
            }
            
            await bot.send_analysis(test_analysis)
            print("✅ Analysis message test successful!")
            
        else:
            print("❌ Telegram bot test failed!")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        await bot.close_session()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(test_telegram_bot())