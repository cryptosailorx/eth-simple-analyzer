"""
main.py
ETH Trend Analyzer v2.0 - Ana Çalıştırma Dosyası
Tüm bileşenleri birleştirip çalıştırır
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime

from simple_analyzer_logfazla import SimpleFibAnalyzer
from websocket_handler import SimpleWebSocketHandler
from telegram_bot import SimpleTelegramBot

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eth_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ETHAnalyzerApp:
    def __init__(self):
        self.analyzer = None
        self.websocket_handler = None
        self.telegram_bot = None
        self.running = False
        
        # Configuration
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """Konfigürasyonu yükle (environment variables veya config file)"""
        config = {
            # Telegram Bot Settings
            "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
            
            # Analysis Settings
            "analysis_window": int(os.getenv("ANALYSIS_WINDOW", "20")),
            "update_interval": int(os.getenv("UPDATE_INTERVAL", "5")),
            "historical_limit": int(os.getenv("HISTORICAL_LIMIT", "1000")),
            
            # System Settings
            "enable_telegram": os.getenv("ENABLE_TELEGRAM", "true").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
        
        return config
    
    def validate_config(self) -> bool:
        """Konfigürasyonu doğrula"""
        if self.config["enable_telegram"]:
            if not self.config["telegram_bot_token"]:
                logger.error("❌ TELEGRAM_BOT_TOKEN is required when telegram is enabled")
                return False
            if not self.config["telegram_chat_id"]:
                logger.error("❌ TELEGRAM_CHAT_ID is required when telegram is enabled")
                return False
        
        logger.info("✅ Configuration validated successfully")
        return True
    
    async def initialize_components(self):
        """Tüm bileşenleri başlat"""
        logger.info("🚀 Initializing ETH Trend Analyzer v2.0...")
        
        # 1. Analyzer
        self.analyzer = SimpleFibAnalyzer()
        logger.info("✅ Analyzer initialized")
        
        # 2. Telegram Bot (opsiyonel)
        if self.config["enable_telegram"]:
            self.telegram_bot = SimpleTelegramBot(
                self.config["telegram_bot_token"],
                self.config["telegram_chat_id"]
            )
            
            # Test connection
            if await self.telegram_bot.test_connection():
                logger.info("✅ Telegram bot initialized and tested")
                await self.telegram_bot.send_startup_message()
            else:
                logger.error("❌ Telegram bot test failed")
                return False
        else:
            logger.info("⚠️ Telegram integration disabled")
        
        # 3. WebSocket Handler
        self.websocket_handler = SimpleWebSocketHandler(
            self.analyzer, 
            self.telegram_bot
        )
        logger.info("✅ WebSocket handler initialized")
        
        return True
    
    async def start(self):
        """Ana uygulamayı başlat"""
        logger.info("=" * 60)
        logger.info("🎯 ETH TREND ANALYZER v2.0 - STARTING")
        logger.info("=" * 60)
        
        # Konfigürasyonu doğrula
        if not self.validate_config():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Bileşenleri başlat
        if not await self.initialize_components():
            logger.error("❌ Component initialization failed")
            return False
        
        # Ana loop başlat
        self.running = True
        logger.info("🚀 Starting main application loop...")
        
        try:
            # WebSocket handler'ı başlat (blocking call)
            await self.websocket_handler.start()
        except KeyboardInterrupt:
            logger.info("⚠️ Interrupted by user")
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
            if self.telegram_bot:
                await self.telegram_bot.send_error_message(str(e))
        finally:
            await self.shutdown()
        
        return True
    
    async def shutdown(self):
        """Uygulamayı güvenli şekilde kapat"""
        logger.info("🛑 Shutting down ETH Trend Analyzer...")
        
        self.running = False
        
        # WebSocket handler'ı durdur
        if self.websocket_handler:
            self.websocket_handler.stop()
        
        # Telegram session'ı kapat
        if self.telegram_bot:
            # Shutdown message
            try:
                shutdown_msg = f"""
🛑 <b>ETH Analyzer Shutdown</b>

✅ System stopped gracefully
⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

<i>Thank you for using ETH Trend Analyzer v2.0</i>
                """.strip()
                await self.telegram_bot.send_message(shutdown_msg)
            except:
                pass  # Ignore errors during shutdown
            
            await self.telegram_bot.close_session()
        
        logger.info("✅ Shutdown completed")
    
    def print_startup_info(self):
        """Başlangıç bilgilerini göster"""
        print("\n" + "=" * 60)
        print("🎯 ETH TREND ANALYZER v2.0")
        print("=" * 60)
        print(f"📊 Analysis Window: {self.config['analysis_window']} candles")
        print(f"🔄 Update Interval: {self.config['update_interval']} minutes")
        print(f"📈 Historical Data: {self.config['historical_limit']} candles")
        print(f"📱 Telegram: {'Enabled' if self.config['enable_telegram'] else 'Disabled'}")
        print("=" * 60)
        print("🚀 Starting in 3 seconds...")
        print("💡 Press Ctrl+C to stop")
        print("=" * 60 + "\n")

def setup_signal_handlers(app):
    """Signal handler'ları ayarla"""
    def signal_handler(signum, frame):
        logger.info(f"⚠️ Received signal {signum}")
        asyncio.create_task(app.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Ana fonksiyon"""
    app = ETHAnalyzerApp()
    
    # Signal handler'ları ayarla
    setup_signal_handlers(app)
    
    # Başlangıç bilgilerini göster
    app.print_startup_info()
    
    # Kısa bekleme
    await asyncio.sleep(3)
    
    # Uygulamayı başlat
    success = await app.start()
    
    if success:
        logger.info("✅ Application finished successfully")
    else:
        logger.error("❌ Application finished with errors")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)