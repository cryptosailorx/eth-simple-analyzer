"""
telegram_bot_UPDATED.py
Telegram Bot - Real-time Fibonacci + Swing Analysis
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
    
    async def send_realtime_fibonacci(self, prev_candle: dict, current_candle: dict, fib_result: dict) -> bool:
        """Real-time Fibonacci analiz sonucunu Telegram'a gönder"""
        try:
            # Fibonacci seviye emoji
            fib_level = fib_result['fib_level']
            if fib_level in [0.382, 0.618]:
                fib_emoji = "🎯"  # Golden ratio
            elif fib_level == 0.5:
                fib_emoji = "⚖️"  # Middle
            elif fib_level in [0.236, 0.786]:
                fib_emoji = "📐"  # Other levels
            elif fib_level == 0:
                fib_emoji = "📊"  # Low level
            elif fib_level == 1.0:
                fib_emoji = "🔴"  # Full retracement
            else:
                fib_emoji = "📊"  # Default
            
            # Retracement strength
            retracement_pct = fib_result['retracement_pct']
            if retracement_pct > 80:
                strength_emoji = "🔥"  # Strong
            elif retracement_pct > 60:
                strength_emoji = "💪"  # Medium
            elif retracement_pct > 30:
                strength_emoji = "📈"  # Weak
            else:
                strength_emoji = "📊"  # Very weak
            
            # Direction emoji
            direction_emoji = {
                "pullback_after_bullish": "📉 Pullback",
                "recovery_after_bearish": "📈 Recovery",
                "invalid": "❓ Invalid"
            }
            dir_text = direction_emoji.get(fib_result['direction'], "↔️ Neutral")
            
            prev_range = prev_candle['high'] - prev_candle['low']
            current_time = datetime.now().strftime("%H:%M:%S")
            
            message = f"""
🕯️ <b>Real-time Fibonacci</b> | {current_time}

{fib_emoji} <b>Fibonacci:</b> <code>{fib_level}</code> ({retracement_pct:.1f}%) {strength_emoji}
{dir_text}

📊 <b>Previous Candle:</b>
   High: ${prev_candle['high']:.2f} | Low: ${prev_candle['low']:.2f} 
   Range: ${prev_range:.2f}

🕯️ <b>Current Candle:</b> 
   High: ${current_candle['high']:.2f} | Low: ${current_candle['low']:.2f}
   <b>Close: ${current_candle['close']:.2f}</b>

<i>Live tracking every minute...</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"❌ Error sending real-time fibonacci: {e}")
            return False
    
    def format_swing_analysis_message(self, analysis: Dict) -> str:
        """Swing analizi sonucunu Telegram mesajı formatına çevir"""
        
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
🎯 <b>5-Min Swing Analysis</b> | {time_str}

💰 <b>Current Price:</b> ${analysis.get('current_price', 0):.2f}
📊 <b>Current Candle:</b> H: ${analysis.get('current_high', 0):.2f} | L: ${analysis.get('current_low', 0):.2f}

📈 <b>Direction:</b> {direction} {emoji}
{conf_emoji} <b>Confidence:</b> {confidence:.1f}%

{fib_emoji} <b>Fibonacci (20-candle avg):</b>
   • Avg Retracement: <code>{analysis.get('avg_fibonacci_retracement', 0):.1f}%</code>
   • Dominant Level: <code>{fib_level}</code>

{strength_emoji} <b>Trend Strength:</b> {strength}/100"""

        # Swing point bilgileri ekle
        if analysis.get('swing_points_found', False):
            message += f"""

🎯 <b>Swing Levels:</b>
   🔺 <b>Last Swing High:</b> ${analysis['last_swing_high']:.2f} <i>({analysis['swing_high_age']} mum önce)</i>
   🔻 <b>Last Swing Low:</b> ${analysis['last_swing_low']:.2f} <i>({analysis['swing_low_age']} mum önce)</i>
   📊 <b>Count:</b> {analysis.get('total_swing_highs', 0)} highs, {analysis.get('total_swing_lows', 0)} lows"""
        else:
            message += f"""

⚠️ <b>Swing Levels:</b> <i>Detecting...</i>"""

        # SIDEWAYS durumunda ek bilgi ekle
        if direction == "SIDEWAYS" and analysis.get('swing_points_found', False):
            swing_high = analysis['last_swing_high']
            swing_low = analysis['last_swing_low']
            current_price = analysis.get('current_price', 0)
            
            # Current price'ın swing range'deki pozisyonu
            swing_range = swing_high - swing_low
            position_pct = ((current_price - swing_low) / swing_range * 100) if swing_range > 0 else 50
            
            if position_pct > 70:
                sideways_detail = f"📊 <b>Range Position:</b> Upper area ({position_pct:.0f}%) - Near swing high"
            elif position_pct < 30:
                sideways_detail = f"📊 <b>Range Position:</b> Lower area ({position_pct:.0f}%) - Near swing low"
            else:
                sideways_detail = f"📊 <b>Range Position:</b> Middle area ({position_pct:.0f}%)"
            
            message += f"""

{sideways_detail}
💡 <b>Breakout Levels:</b> Above ${swing_high:.2f} (Bullish) or Below ${swing_low:.2f} (Bearish)"""

        message += f"""

📈 <b>Analysis Details:</b>
   • Window: {analysis.get('analysis_window', 20)} candles
   • Sample Size: {analysis.get('sample_size', 0)} pairs
   • Total Candles: {analysis.get('candles_analyzed', 0)}

🔄 <b>Next Update:</b> {analysis.get('next_update_minutes', 5)} minutes

<i>Real-time Fibonacci + 5-min Swing Analysis</i>
        """
        
        return message.strip()
    
    async def send_analysis(self, analysis: Dict) -> bool:
        """Swing analiz sonucunu Telegram'a gönder"""
        try:
            message = self.format_swing_analysis_message(analysis)
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"❌ Error formatting swing analysis message: {e}")
            return False
    
    async def send_startup_message(self) -> bool:
        """Sistem başlangıç mesajı"""
        message = f"""
🚀 <b>ETH Trend Analyzer v2.0 Started</b>

✅ WebSocket connection established
📊 Historical data loaded (1000 candles)
🔄 Real-time analysis active

<b>Features:</b>
🕯️ <b>Real-time Fibonacci:</b> Every minute
📊 <b>Swing Analysis:</b> Every 5 minutes
🎯 <b>Analysis Window:</b> 20 candles
📈 <b>Tracking:</b> ETH/USDT 1-minute candles

<i>System online and monitoring...</i>

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

<i>Ready for real-time Fibonacci + swing analysis...</i>
        """
        return await self.send_message(test_message.strip())
