"""
Kite Ticker WebSocket Wrapper
A Python wrapper for Kite Connect Ticker API with WebSocket support
"""

import json
import logging
import threading
import time
import struct
from typing import Dict, List, Callable, Optional, Any
from collections import defaultdict
from datetime import datetime
import websocket
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    from kiteconnect import KiteTicker
except ImportError:
    print("Please install pykiteconnect: pip install kiteconnect")
    raise


class KiteTickerWrapper:
    """
    Enhanced wrapper class for KiteTicker with additional features:
    - Automatic reconnection handling
    - Data storage and retrieval
    - Event logging
    - Easy subscription management
    - Custom callbacks
    - Connection status monitoring
    """
    
    def __init__(self, api_key: str, access_token: str, 
                 debug: bool = False, 
                 auto_reconnect: bool = True,
                 log_level: str = "INFO"):
        """
        Initialize the KiteTickerWrapper
        
        Args:
            api_key: Kite Connect API key
            access_token: Access token from login flow
            debug: Enable debug mode
            auto_reconnect: Enable automatic reconnection
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.api_key = api_key
        self.access_token = access_token
        self.debug = debug
        self.auto_reconnect = auto_reconnect
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        self.logger = logging.getLogger(__name__)
        
        # Initialize KiteTicker
        self.kws = KiteTicker(
            api_key=api_key, 
            access_token=access_token, 
            debug=debug,
            reconnect=auto_reconnect
        )
        
        # Data storage
        self.tick_data = defaultdict(list)  # Store tick history
        self.latest_ticks = {}  # Store latest tick for each instrument
        self.subscribed_instruments = {}  # Track subscribed instruments and their modes
        self.order_updates = []  # Store order updates
        
        # Connection status
        self.connection_status = "DISCONNECTED"
        self.connection_count = 0
        self.last_tick_time = None
        
        # Custom callbacks
        self.custom_tick_callbacks = []
        self.custom_connect_callbacks = []
        self.custom_disconnect_callbacks = []
        self.custom_error_callbacks = []
        self.custom_order_callbacks = []
        
        # Setup KiteTicker callbacks
        self._setup_callbacks()
        
        # Threading
        self.connection_thread = None
        self.is_running = False
        
    def _setup_callbacks(self):
        """Setup internal callbacks for KiteTicker"""
        self.kws.on_ticks = self._on_ticks
        self.kws.on_connect = self._on_connect
        self.kws.on_close = self._on_close
        self.kws.on_error = self._on_error
        self.kws.on_order_update = self._on_order_update
        self.kws.on_reconnect = self._on_reconnect
        self.kws.on_noreconnect = self._on_noreconnect
    
    def _on_ticks(self, ws, ticks):
        """Internal tick handler"""
        self.last_tick_time = datetime.now()
        
        for tick in ticks:
            instrument_token = tick['instrument_token']
            
            # Store in history (limit to last 1000 ticks per instrument)
            self.tick_data[instrument_token].append({
                'timestamp': datetime.now(),
                'data': tick
            })
            if len(self.tick_data[instrument_token]) > 1000:
                self.tick_data[instrument_token] = self.tick_data[instrument_token][-1000:]
            
            # Update latest tick
            self.latest_ticks[instrument_token] = tick
        
        # Call custom callbacks
        for callback in self.custom_tick_callbacks:
            try:
                callback(ticks)
            except Exception as e:
                self.logger.error(f"Error in custom tick callback: {e}")
        
        self.logger.debug(f"Received {len(ticks)} ticks")
    
    def _on_connect(self, ws, response):
        """Internal connect handler"""
        self.connection_status = "CONNECTED"
        self.connection_count += 1
        self.logger.info(f"Connected to Kite Ticker (attempt #{self.connection_count})")
        
        # Resubscribe to instruments if reconnecting
        if self.subscribed_instruments and self.connection_count > 1:
            self.logger.info("Resubscribing to instruments after reconnection...")
            self._resubscribe_all()
        
        # Call custom callbacks
        for callback in self.custom_connect_callbacks:
            try:
                callback(response)
            except Exception as e:
                self.logger.error(f"Error in custom connect callback: {e}")
    
    def _on_close(self, ws, code, reason):
        """Internal close handler"""
        self.connection_status = "DISCONNECTED"
        self.logger.warning(f"Connection closed: {code} - {reason}")
        
        # Call custom callbacks
        for callback in self.custom_disconnect_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                self.logger.error(f"Error in custom disconnect callback: {e}")
    
    def _on_error(self, ws, code, reason):
        """Internal error handler"""
        self.logger.error(f"Connection error: {code} - {reason}")
        
        # Call custom callbacks
        for callback in self.custom_error_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                self.logger.error(f"Error in custom error callback: {e}")
    
    def _on_order_update(self, ws, data):
        """Internal order update handler"""
        self.order_updates.append({
            'timestamp': datetime.now(),
            'data': data
        })
        
        # Call custom callbacks
        for callback in self.custom_order_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in custom order callback: {e}")
        
        self.logger.info(f"Order update received: {data.get('order_id')}")
    
    def _on_reconnect(self, ws, attempts_count):
        """Internal reconnect handler"""
        self.logger.info(f"Reconnection attempt #{attempts_count}")
    
    def _on_noreconnect(self, ws):
        """Internal no-reconnect handler"""
        self.logger.error("Max reconnection attempts reached. Connection failed.")
        self.connection_status = "FAILED"
    
    def _resubscribe_all(self):
        """Resubscribe to all previously subscribed instruments"""
        if not self.subscribed_instruments:
            return
        
        # Group instruments by mode
        mode_groups = defaultdict(list)
        for token, mode in self.subscribed_instruments.items():
            mode_groups[mode].append(token)
        
        # Subscribe and set modes
        for mode, tokens in mode_groups.items():
            try:
                self.subscribe(tokens, mode, resubscribe=True)
            except Exception as e:
                self.logger.error(f"Error resubscribing instruments {tokens}: {e}")
    
    def connect(self, threaded: bool = True, **kwargs):
        """
        Connect to Kite Ticker
        
        Args:
            threaded: Run in threaded mode (recommended)
            **kwargs: Additional arguments for KiteTicker.connect()
        """
        try:
            self.is_running = True
            
            if threaded:
                self.connection_thread = threading.Thread(
                    target=self._connect_worker, 
                    kwargs=kwargs
                )
                self.connection_thread.daemon = True
                self.connection_thread.start()
                self.logger.info("Started KiteTicker in threaded mode")
            else:
                self._connect_worker(**kwargs)
                
        except Exception as e:
            self.logger.error(f"Error connecting: {e}")
            raise
    
    def _connect_worker(self, **kwargs):
        """Worker method for connection"""
        try:
            self.kws.connect(threaded=True, **kwargs)
        except Exception as e:
            self.logger.error(f"Connection worker error: {e}")
            self.connection_status = "FAILED"
    
    def disconnect(self):
        """Disconnect from Kite Ticker"""
        try:
            self.is_running = False
            if self.kws:
                self.kws.close()
            self.logger.info("Disconnected from Kite Ticker")
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    def subscribe(self, instruments: List[int], mode: str = None, resubscribe: bool = False):
        """
        Subscribe to instruments
        
        Args:
            instruments: List of instrument tokens
            mode: Streaming mode ('ltp', 'quote', 'full'). Default is 'quote'
            resubscribe: Internal flag for resubscription
        """
        if not isinstance(instruments, list):
            instruments = [instruments]
        
        mode = mode or self.kws.MODE_QUOTE
        
        # Validate mode
        valid_modes = [self.kws.MODE_LTP, self.kws.MODE_QUOTE, self.kws.MODE_FULL]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        try:
            # Subscribe to instruments
            self.kws.subscribe(instruments)
            
            # Set mode if specified
            if mode != self.kws.MODE_QUOTE:  # Default mode
                self.kws.set_mode(mode, instruments)
            
            # Track subscribed instruments
            for token in instruments:
                self.subscribed_instruments[token] = mode
            
            action = "Resubscribed to" if resubscribe else "Subscribed to"
            self.logger.info(f"{action} {len(instruments)} instruments in {mode} mode")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to instruments: {e}")
            raise
    
    def unsubscribe(self, instruments: List[int]):
        """
        Unsubscribe from instruments
        
        Args:
            instruments: List of instrument tokens to unsubscribe
        """
        if not isinstance(instruments, list):
            instruments = [instruments]
        
        try:
            self.kws.unsubscribe(instruments)
            
            # Remove from tracking
            for token in instruments:
                self.subscribed_instruments.pop(token, None)
                self.latest_ticks.pop(token, None)
            
            self.logger.info(f"Unsubscribed from {len(instruments)} instruments")
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from instruments: {e}")
            raise
    
    def set_mode(self, mode: str, instruments: List[int]):
        """
        Set streaming mode for instruments
        
        Args:
            mode: Streaming mode ('ltp', 'quote', 'full')
            instruments: List of instrument tokens
        """
        if not isinstance(instruments, list):
            instruments = [instruments]
        
        try:
            self.kws.set_mode(mode, instruments)
            
            # Update tracking
            for token in instruments:
                if token in self.subscribed_instruments:
                    self.subscribed_instruments[token] = mode
            
            self.logger.info(f"Set mode {mode} for {len(instruments)} instruments")
            
        except Exception as e:
            self.logger.error(f"Error setting mode: {e}")
            raise
    
    def add_tick_callback(self, callback: Callable):
        """Add custom tick callback function"""
        self.custom_tick_callbacks.append(callback)
    
    def add_connect_callback(self, callback: Callable):
        """Add custom connect callback function"""
        self.custom_connect_callbacks.append(callback)
    
    def add_disconnect_callback(self, callback: Callable):
        """Add custom disconnect callback function"""
        self.custom_disconnect_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add custom error callback function"""
        self.custom_error_callbacks.append(callback)
    
    def add_order_callback(self, callback: Callable):
        """Add custom order update callback function"""
        self.custom_order_callbacks.append(callback)
    
    def get_latest_tick(self, instrument_token: int) -> Optional[Dict]:
        """Get latest tick for an instrument"""
        return self.latest_ticks.get(instrument_token)
    
    def get_tick_history(self, instrument_token: int, count: int = None) -> List[Dict]:
        """
        Get tick history for an instrument
        
        Args:
            instrument_token: Instrument token
            count: Number of latest ticks to return (default: all)
        """
        history = self.tick_data.get(instrument_token, [])
        if count:
            return history[-count:]
        return history
    
    def get_connection_status(self) -> Dict:
        """Get connection status information"""
        return {
            'status': self.connection_status,
            'connection_count': self.connection_count,
            'last_tick_time': self.last_tick_time,
            'subscribed_count': len(self.subscribed_instruments),
            'is_connected': self.kws.is_connected() if self.kws else False
        }
    
    def get_subscribed_instruments(self) -> Dict:
        """Get currently subscribed instruments and their modes"""
        return self.subscribed_instruments.copy()
    
    def get_order_updates(self, count: int = None) -> List[Dict]:
        """
        Get order updates
        
        Args:
            count: Number of latest updates to return (default: all)
        """
        if count:
            return self.order_updates[-count:]
        return self.order_updates
    
    def clear_data(self):
        """Clear stored tick data and order updates"""
        self.tick_data.clear()
        self.latest_ticks.clear()
        self.order_updates.clear()
        self.logger.info("Cleared all stored data")
    
    def export_data(self, filename: str, instrument_tokens: List[int] = None):
        """
        Export tick data to JSON file
        
        Args:
            filename: Output filename
            instrument_tokens: Specific instruments to export (default: all)
        """
        try:
            export_data = {}
            
            if instrument_tokens:
                for token in instrument_tokens:
                    if token in self.tick_data:
                        export_data[token] = self.tick_data[token]
            else:
                export_data = dict(self.tick_data)
            
            # Convert datetime objects to strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, default=convert_datetime, indent=2)
            
            self.logger.info(f"Exported data to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Example usage class for Flask integration
class FlaskKiteTickerIntegration:
    """
    Example class showing how to integrate with Flask using SocketIO
    """
    
    def __init__(self, app, socketio, api_key: str, access_token: str):
        self.app = app
        self.socketio = socketio
        self.ticker = KiteTickerWrapper(api_key, access_token)
        self.setup_callbacks()
        
    def setup_callbacks(self):
        """Setup ticker callbacks"""
        self.ticker._on_connect(self._on_connect)
        self.ticker.on_disconnect(self._on_disconnect)
        self.ticker.on_error(self._on_error)
        self.ticker.on_message(self._on_tick)
        
    def _on_connect(self, ticker):
        """Handle ticker connection"""
        print("Kite Ticker connected")
        self.socketio.emit('ticker_status', {'status': 'connected'})
        
    def _on_disconnect(self, ticker):
        """Handle ticker disconnection"""
        print("Kite Ticker disconnected")
        self.socketio.emit('ticker_status', {'status': 'disconnected'})
        
    def _on_error(self, error):
        """Handle ticker errors"""
        print(f"Kite Ticker error: {error}")
        self.socketio.emit('ticker_error', {'error': str(error)})
        
    def _on_tick(self, ticker, ticks):
        """Handle incoming tick data"""
        # Emit tick data to all connected clients
        self.socketio.emit('tick_data', {'ticks': ticks})
        
    def start(self):
        """Start the ticker connection"""
        return self.ticker.connect()
        
    def stop(self):
        """Stop the ticker connection"""
        self.ticker.disconnect()
        
    def subscribe_instruments(self, tokens: List[int], mode: str = "ltp"):
        """Subscribe to instruments"""
        self.ticker.subscribe(tokens, mode)
        
    def unsubscribe_instruments(self, tokens: List[int]):
        """Unsubscribe from instruments"""
        self.ticker.unsubscribe(tokens)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    API_KEY = "your_api_key"
    ACCESS_TOKEN = "your_access_token"
    
    def my_tick_handler(ticks):
        """Custom tick handler"""
        for tick in ticks:
            print(f"Tick: {tick['instrument_token']} - LTP: {tick['last_price']}")
    
    def my_connect_handler(response):
        """Custom connect handler"""
        print("Connected successfully!")
    
    def my_error_handler(code, reason):
        """Custom error handler"""
        print(f"Error occurred: {code} - {reason}")
    
    # Using context manager
    try:
        with KiteTickerWrapper(API_KEY, ACCESS_TOKEN, debug=True) as ticker:
            # Add custom callbacks
            ticker.add_tick_callback(my_tick_handler)
            ticker.add_connect_callback(my_connect_handler)
            ticker.add_error_callback(my_error_handler)
            
            # Connect
            ticker.connect()
            
            # Wait for connection
            time.sleep(2)
            
            # Subscribe to instruments (example tokens)
            instruments = [738561, 5633]  # RELIANCE, ACC
            ticker.subscribe(instruments, mode=ticker.kws.MODE_FULL)
            
            # Let it run for some time
            time.sleep(10)
            
            # Get status
            status = ticker.get_connection_status()
            print(f"Connection Status: {status}")
            
            # Get latest ticks
            for token in instruments:
                latest = ticker.get_latest_tick(token)
                if latest:
                    print(f"Latest tick for {token}: {latest['last_price']}")
            
            # Export data
            ticker.export_data("tick_data.json", instruments)
            
    except Exception as e:
        print(f"Error: {e}")