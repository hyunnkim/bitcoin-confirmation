import requests
import time
import sys
import os

class BTCConfirmationMonitor:
    def __init__(self, txid, discord_webhook=None, telegram_bot_token=None, telegram_chat_id=None):
        self.txid = txid
        self.api_url = f"https://blockchain.info/rawtx/{txid}"
        self.notified = False
        self.discord_webhook = discord_webhook
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        
    def get_confirmations(self):
        """Fetch the number of confirmations for the transaction"""
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()

            block_height = data.get('block_height')
            
            if block_height is not None:
                current_block_response = requests.get("https://blockchain.info/latestblock")
                current_block_response.raise_for_status()
                current_block = current_block_response.json()
                current_height = current_block['height']
                confirmations = current_height - block_height + 1
                return confirmations
            else:
                return 0
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch transaction data: {e}")
            return None
    
    def send_discord_notification(self, confirmations):
        """Send notification to Discord via webhook"""
        if not self.discord_webhook:
            return False
            
        try:
            data = {
                "content": f"**Bitcoin Transaction Confirmed**\n\nTransaction: `{self.txid}`\nConfirmations: **{confirmations}**\n\nBlockchain Explorer: https://blockchain.info/tx/{self.txid}"
            }
            response = requests.post(self.discord_webhook, json=data)
            response.raise_for_status()
            print("[SUCCESS] Discord notification sent")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send Discord notification: {e}")
            return False
    
    def send_telegram_notification(self, confirmations):
        """Send notification to Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": f"🔔 Bitcoin Transaction Confirmed\n\nTransaction: {self.txid}\nConfirmations: {confirmations}\n\nView: https://blockchain.info/tx/{self.txid}",
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=data)
            response.raise_for_status()
            print("[SUCCESS] Telegram notification sent")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send Telegram notification: {e}")
            return False
    
    def send_notifications(self, confirmations):
        """Send all configured notifications"""
        discord_sent = self.send_discord_notification(confirmations)
        telegram_sent = self.send_telegram_notification(confirmations)
        
        if not discord_sent and not telegram_sent:
            print("[WARNING] No notifications were sent. Please check your configuration.")
        
        print(f"\n[SUCCESS] Transaction has {confirmations} confirmation(s)")
    
    def monitor(self, check_interval=60):
        """Monitor the transaction until it gets 1 confirmation"""
        print(f"[INFO] Monitoring transaction: {self.txid}")
        print(f"[INFO] Checking every {check_interval} seconds")
        
        if self.discord_webhook:
            print("[INFO] Discord notifications: ENABLED")
        else:
            print("[INFO] Discord notifications: DISABLED")
            
        if self.telegram_bot_token and self.telegram_chat_id:
            print("[INFO] Telegram notifications: ENABLED")
        else:
            print("[INFO] Telegram notifications: DISABLED")
            
        print("\n[INFO] Press Ctrl+C to stop\n")
        
        try:
            while not self.notified:
                confirmations = self.get_confirmations()
                
                if confirmations is not None:
                    if confirmations == 0:
                        print(f"The transaction is still unconfirmed")
                    elif confirmations >= 1 and not self.notified:
                        self.send_notifications(confirmations)
                        self.notified = True
                        break
                    else:
                        print(f"Transaction has {confirmations} confirmations")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n[INFO] Monitoring stopped by user")
            sys.exit(0)

def main():
    if len(sys.argv) > 1:
        txid = sys.argv[1]
    else:
        txid = input("\nEnter Bitcoin transaction ID (txid): ").strip()
    
    if not txid:
        print("[ERROR] Transaction ID is required!")
        sys.exit(1)
    
    discord_webhook = os.environ.get('DISCORD_WEBHOOK')
    if not discord_webhook:
        discord_input = input("\nEnter Discord webhook URL (or press Enter to skip): ").strip()
        discord_webhook = discord_input if discord_input else None
    
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not telegram_bot_token:
        telegram_input = input("Enter Telegram bot token (or press Enter to skip): ").strip()
        telegram_bot_token = telegram_input if telegram_input else None
    
    if telegram_bot_token and not telegram_chat_id:
        chat_id_input = input("Enter Telegram chat ID: ").strip()
        telegram_chat_id = chat_id_input if chat_id_input else None
    
    if not discord_webhook and not telegram_bot_token:
        print("\n[WARNING] No notification methods configured!")
        print("[WARNING] The script will run but you won't receive notifications.")
        proceed = input("\nContinue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("[INFO] Exiting...")
            sys.exit(0)
    
    # change number of seconds
    check_interval = 15
    if len(sys.argv) > 2:
        try:
            check_interval = int(sys.argv[2])
        except ValueError:
            print("[WARNING] Invalid interval, using default 60 seconds")
    
    monitor = BTCConfirmationMonitor(
        txid, 
        discord_webhook=discord_webhook,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id
    )
    monitor.monitor(check_interval)
    
    print("\n[COMPLETE] Monitoring finished successfully")

if __name__ == "__main__":
    main()
