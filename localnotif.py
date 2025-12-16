import requests
import time
from plyer import notification
import sys

class BTCConfirmationMonitor:
    def __init__(self, txid):
        self.txid = txid
        self.api_url = f"https://blockchain.info/rawtx/{txid}"
        self.notified = False
        
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
            print(f"Error fetching transaction data: {e}")
            return None
    
    def send_notification(self, confirmations):
        """Send a desktop notification"""
        notification.notify(
            title="Bitcoin Transaction Confirmed",
            message=f"Transaction {self.txid[:16]}... has {confirmations} confirmation(s)",
            app_name="BTC Monitor",
            timeout=10
        )
        print(f"\n[SUCCESS] Notification sent. Transaction has {confirmations} confirmation(s)")
    
    def monitor(self, check_interval=60):
        """Monitor the transaction until it gets 1 confirmation"""
        print(f"Monitoring transaction: {self.txid}")
        print(f"Checking every {check_interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while not self.notified:
                confirmations = self.get_confirmations()
                
                if confirmations is not None:
                    if confirmations == 0:
                        print(f"The transaction is still unconfirmed")
                    elif confirmations >= 1 and not self.notified:
                        self.send_notification(confirmations)
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
        print("Error: Transaction ID is required!")
        sys.exit(1)
    
    # check interval sets the seconds between checks
    check_interval = 30
    if len(sys.argv) > 2:
        try:
            check_interval = int(sys.argv[2])
        except ValueError:
            print("Warning: Invalid interval, using default 60 seconds")
    
    monitor = BTCConfirmationMonitor(txid)
    monitor.monitor(check_interval)
    
    print("\n[COMPLETE] Monitoring finished successfully")

if __name__ == "__main__":
    main()
