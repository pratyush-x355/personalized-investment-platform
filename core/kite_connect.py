from kiteconnect import KiteConnect
import logging
from typing import Dict, List, Optional, Union, Any
import pandas as pd

class Kite_Api:
    """
    A comprehensive wrapper class for KiteConnect API to simplify trading operations.
    Provides easy-to-use methods for placing orders, managing positions, and retrieving market data.
    """
    
    def __init__(self, api_key: str, access_token: str) -> None:
        """
        Initialize the Kite API wrapper.
        
        Args:
            api_key (str): Your Kite Connect API key
            access_token (str): Access token obtained after login
        """
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.api_key = api_key
        self.access_token = access_token
        self.map_variables()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def map_variables(self):
        """Initialize all the mapping dictionaries for easy parameter passing."""
        
        # Transaction types
        self.t_type_dict = {
            "BUY": self.kite.TRANSACTION_TYPE_BUY,
            "SELL": self.kite.TRANSACTION_TYPE_SELL,
        }
        
        # Exchange segments
        self.ex_seg_dict = {
            "NSE": self.kite.EXCHANGE_NSE,
            "BSE": self.kite.EXCHANGE_BSE,
            "NFO": self.kite.EXCHANGE_NFO,  # NSE F&O
            "BFO": self.kite.EXCHANGE_BFO,  # BSE F&O
            "CDS": self.kite.EXCHANGE_CDS,  # Currency Derivatives
            "MCX": self.kite.EXCHANGE_MCX,  # Commodities
        }
        
        # Order validity
        self.validity_dict = {
            "DAY": self.kite.VALIDITY_DAY,
            "IOC": self.kite.VALIDITY_IOC,
            "TTL": self.kite.VALIDITY_TTL,
        }
        
        # Product types - Only supported ones
        self.p_type_dict = {
            "CNC": self.kite.PRODUCT_CNC,      # Cash and Carry (Delivery)
            "MIS": self.kite.PRODUCT_MIS,      # Margin Intraday Squareoff
            "NRML": self.kite.PRODUCT_NRML,    # Normal (overnight positions for F&O)
        }
        
        # Order types
        self.o_type_dict = {
            "MARKET": self.kite.ORDER_TYPE_MARKET,
            "LIMIT": self.kite.ORDER_TYPE_LIMIT,
            "SL": self.kite.ORDER_TYPE_SL,          # Stop Loss Limit
            "SLM": self.kite.ORDER_TYPE_SLM,        # Stop Loss Market
        }
        
        # Order varieties - Only supported ones
        self.variety_dict = {
            "REGULAR": self.kite.VARIETY_REGULAR,
            "AMO": self.kite.VARIETY_AMO,           # After Market Order
        }
    
    # ==================== ORDER PLACEMENT METHODS ====================
    
    def place_market_order(self, tradingsymbol: str, exchange: str, t_type: str, 
                          quantity: int, p_type: str, price: float = 0, 
                          validity: str = "DAY", variety: str = "REGULAR", 
                          tag: Optional[str] = None) -> Dict:
        """
        Place a market order.
        
        Args:
            tradingsymbol (str): Trading symbol (e.g., "RELIANCE", "NIFTY23FEB17000CE")
            exchange (str): Exchange segment ("NSE", "BSE", "NFO", etc.)
            t_type (str): Transaction type ("BUY" or "SELL")
            quantity (int): Number of shares/lots
            p_type (str): Product type ("CNC", "MIS", "NRML")
            price (float): Price (usually 0 for market orders)
            validity (str): Order validity ("DAY", "IOC", "TTL")
            variety (str): Order variety ("REGULAR", "AMO")
            tag (str): Optional tag for the order
            
        Returns:
            Dict: Order response from Kite API
        """
        try:
            response = self.kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=self.ex_seg_dict[exchange],
                transaction_type=self.t_type_dict[t_type],
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.p_type_dict[p_type],
                price=price,
                validity=self.validity_dict[validity],
                variety=self.variety_dict[variety],
                tag=tag
            )
            self.logger.info(f"Market order placed: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return {"status": "error", "message": str(e)}
    
    def place_limit_order(self, tradingsymbol: str, exchange: str, t_type: str, 
                         quantity: int, p_type: str, price: float, 
                         validity: str = "DAY", variety: str = "REGULAR", 
                         tag: Optional[str] = None) -> Dict:
        """
        Place a limit order.
        
        Args:
            tradingsymbol (str): Trading symbol
            exchange (str): Exchange segment
            t_type (str): Transaction type ("BUY" or "SELL")
            quantity (int): Number of shares/lots
            p_type (str): Product type ("CNC", "MIS", "NRML")
            price (float): Limit price
            validity (str): Order validity
            variety (str): Order variety
            tag (str): Optional tag for the order
            
        Returns:
            Dict: Order response from Kite API
        """
        try:
            response = self.kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=self.ex_seg_dict[exchange],
                transaction_type=self.t_type_dict[t_type],
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                product=self.p_type_dict[p_type],
                price=price,
                validity=self.validity_dict[validity],
                variety=self.variety_dict[variety],
                tag=tag
            )
            self.logger.info(f"Limit order placed: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return {"status": "error", "message": str(e)}
    
    def place_stoploss_limit_order(self, tradingsymbol: str, exchange: str, t_type: str, 
                                  quantity: int, p_type: str, price: float, 
                                  trigger_price: float, validity: str = "DAY", 
                                  variety: str = "REGULAR", tag: Optional[str] = None) -> Dict:
        """
        Place a stop-loss limit order.
        
        Args:
            tradingsymbol (str): Trading symbol
            exchange (str): Exchange segment
            t_type (str): Transaction type ("BUY" or "SELL")
            quantity (int): Number of shares/lots
            p_type (str): Product type ("CNC", "MIS", "NRML")
            price (float): Limit price
            trigger_price (float): Stop-loss trigger price
            validity (str): Order validity
            variety (str): Order variety
            tag (str): Optional tag for the order
            
        Returns:
            Dict: Order response from Kite API
        """
        try:
            response = self.kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=self.ex_seg_dict[exchange],
                transaction_type=self.t_type_dict[t_type],
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_SL,
                product=self.p_type_dict[p_type],
                price=price,
                trigger_price=trigger_price,
                validity=self.validity_dict[validity],
                variety=self.variety_dict[variety],
                tag=tag
            )
            self.logger.info(f"Stop-loss limit order placed: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error placing stop-loss limit order: {e}")
            return {"status": "error", "message": str(e)}
    
    def place_stoploss_market_order(self, tradingsymbol: str, exchange: str, t_type: str, 
                                   quantity: int, p_type: str, trigger_price: float, 
                                   validity: str = "DAY", variety: str = "REGULAR", 
                                   tag: Optional[str] = None) -> Dict:
        """
        Place a stop-loss market order.
        
        Args:
            tradingsymbol (str): Trading symbol
            exchange (str): Exchange segment
            t_type (str): Transaction type ("BUY" or "SELL")
            quantity (int): Number of shares/lots
            p_type (str): Product type ("CNC", "MIS", "NRML")
            trigger_price (float): Stop-loss trigger price
            validity (str): Order validity
            variety (str): Order variety
            tag (str): Optional tag for the order
            
        Returns:
            Dict: Order response from Kite API
        """
        try:
            response = self.kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=self.ex_seg_dict[exchange],
                transaction_type=self.t_type_dict[t_type],
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_SLM,
                product=self.p_type_dict[p_type],
                trigger_price=trigger_price,
                validity=self.validity_dict[validity],
                variety=self.variety_dict[variety],
                tag=tag
            )
            self.logger.info(f"Stop-loss market order placed: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error placing stop-loss market order: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== ORDER MANAGEMENT METHODS ====================
    
    def modify_order(self, order_id: str, quantity: Optional[int] = None, price: Optional[float] = None, 
                    order_type: Optional[str] = None, trigger_price: Optional[float] = None, 
                    validity: Optional[str] = None, parent_order_id: Optional[str] = None) -> Dict:
        """
        Modify an existing order.
        
        Args:
            order_id (str): Order ID to modify
            quantity (int): New quantity
            price (float): New price
            order_type (str): New order type
            trigger_price (float): New trigger price
            validity (str): New validity
            parent_order_id (str): Parent order ID (for special orders)
            
        Returns:
            Dict: Modification response from Kite API
        """
        try:
            params: dict[str, Any] = {"order_id": order_id}
            if quantity is not None:
                params["quantity"] = quantity
            if price is not None:
                params["price"] = price
            if order_type is not None:
                params["order_type"] = self.o_type_dict[order_type]
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            if validity is not None:
                params["validity"] = self.validity_dict[validity]
            if parent_order_id is not None:
                params["parent_order_id"] = parent_order_id
            
            response = self.kite.modify_order(**params)
            self.logger.info(f"Order modified: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error modifying order: {e}")
            return {"status": "error", "message": str(e)}
    
    def cancel_order(self, order_id: str, variety: str = "REGULAR", 
                    parent_order_id: str = None) -> Dict:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): Order ID to cancel
            variety (str): Order variety
            parent_order_id (str): Parent order ID (for special orders)
            
        Returns:
            Dict: Cancellation response from Kite API
        """
        try:
            response = self.kite.cancel_order(
                variety=self.variety_dict[variety],
                order_id=order_id,
                parent_order_id=parent_order_id
            )
            self.logger.info(f"Order cancelled: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== DATA RETRIEVAL METHODS ====================
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders for the day."""
        try:
            orders = self.kite.orders()
            return orders # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_order_history(self, order_id: str) -> List[Dict]:
        """Get order history for a specific order."""
        try:
            history = self.kite.order_history(order_id)
            return history # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching order history: {e}")
            return []
    
    def get_positions(self) -> Dict:
        """Get current positions."""
        try:
            positions = self.kite.positions()
            return positions # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching positions: {e}")
            return {"net": [], "day": []}
    
    def get_holdings(self) -> List[Dict]:
        """Get current holdings."""
        try:
            holdings = self.kite.holdings()
            return holdings # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching holdings: {e}")
            return []
    
    def get_margins(self, segment: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """
        Get margin details.
        
        Args:
            segment (str): Specific segment ("equity" or "commodity")
            
        Returns:
            Dict or List[Dict]: Margin information
        """
        try:
            if segment:
                margins = self.kite.margins(segment)
            else:
                margins = self.kite.margins()
            return margins # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching margins: {e}")
            return {} if segment else []
    
    def get_profile(self) -> Dict:
        """Get user profile."""
        try:
            profile = self.kite.profile()
            return profile # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching profile: {e}")
            return {}
    
    # ==================== MARKET DATA METHODS ====================
    
    def get_quote(self, instruments: Union[str, List[str]]) -> Dict:
        """
        Get market quotes for instruments.
        
        Args:
            instruments: Single instrument or list of instruments (e.g., "NSE:RELIANCE")
            
        Returns:
            Dict: Quote data
        """
        try:
            if isinstance(instruments, str):
                instruments = [instruments]
            quotes = self.kite.quote(instruments)
            return quotes
        except Exception as e:
            self.logger.error(f"Error fetching quotes: {e}")
            return {}
    
    def get_ltp(self, instruments: Union[str, List[str]]) -> Dict:
        """
        Get Last Traded Price for instruments.
        
        Args:
            instruments: Single instrument or list of instruments
            
        Returns:
            Dict: LTP data
        """
        try:
            if isinstance(instruments, str):
                instruments = [instruments]
            ltp = self.kite.ltp(instruments)
            return ltp # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching LTP: {e}")
            return {}
    
    def get_ohlc(self, instruments: Union[str, List[str]]) -> Dict:
        """
        Get OHLC data for instruments.
        
        Args:
            instruments: Single instrument or list of instruments
            
        Returns:
            Dict: OHLC data
        """
        try:
            if isinstance(instruments, str):
                instruments = [instruments]
            ohlc = self.kite.ohlc(instruments)
            return ohlc # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching OHLC: {e}")
            return {}
    
    def get_historical_data(self, instrument_token: str, from_date: str, to_date: str, 
                           interval: str, continuous: bool = False, oi: bool = False) -> List[Dict]:
        """
        Get historical data for an instrument.
        
        Args:
            instrument_token (str): Instrument token
            from_date (str): Start date (YYYY-MM-DD)
            to_date (str): End date (YYYY-MM-DD)
            interval (str): Candle interval (minute, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute, day)
            continuous (bool): Continuous contract data for futures
            oi (bool): Include Open Interest data
            
        Returns:
            List[Dict]: Historical data
        """
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi
            )
            return data
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return []
    
    def get_instruments(self, exchange: Optional[str] = None) -> List[Dict]:
        """
        Get instrument list.
        
        Args:
            exchange (str): Exchange segment (optional)
            
        Returns:
            List[Dict]: Instrument data
        """
        try:
            if exchange:
                instruments = self.kite.instruments(exchange)
            else:
                instruments = self.kite.instruments()
            return instruments
        except Exception as e:
            self.logger.error(f"Error fetching instruments: {e}")
            return []
    
    # ==================== UTILITY METHODS ====================
    
    def convert_position(self, exchange: str, tradingsymbol: str, t_type: str, 
                        quantity: int, old_p_type: str, new_p_type: str) -> Dict:
        """
        Convert position from one product type to another.
        
        Args:
            exchange (str): Exchange segment
            tradingsymbol (str): Trading symbol
            t_type (str): Transaction type
            quantity (int): Quantity to convert
            old_p_type (str): Current product type ("CNC", "MIS", "NRML")
            new_p_type (str): Target product type ("CNC", "MIS", "NRML")
            
        Returns:
            Dict: Conversion response
        """
        try:
            response = self.kite.convert_position(
                exchange=self.ex_seg_dict[exchange],
                tradingsymbol=tradingsymbol,
                transaction_type=self.t_type_dict[t_type],
                position_type=self.kite.POSITION_TYPE_DAY,
                quantity=quantity,
                old_product=self.p_type_dict[old_p_type],
                new_product=self.p_type_dict[new_p_type]
            )
            self.logger.info(f"Position converted: {response}")
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error converting position: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_order_margins(self, orders: List[Dict]) -> Dict:
        """
        Get margin requirements for orders.
        
        Args:
            orders (List[Dict]): List of order parameters
            
        Returns:
            Dict: Margin requirements
        """
        try:
            margins = self.kite.order_margins(orders)
            return margins # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching order margins: {e}")
            return {}
    
    def get_basket_margins(self, orders: List[Dict], consider_positions: bool = True) -> Dict:
        """
        Get basket margin for multiple orders.
        
        Args:
            orders (List[Dict]): List of order parameters
            consider_positions (bool): Consider existing positions
            
        Returns:
            Dict: Basket margin requirements
        """
        try:
            margins = self.kite.basket_order_margins(orders, consider_positions)
            return margins # type: ignore
        except Exception as e:
            self.logger.error(f"Error fetching basket margins: {e}")
            return {}
    
    # ==================== HELPER METHODS ====================
    
    def get_pnl_summary(self) -> Dict:
        """Get a summary of P&L from positions."""
        try:
            positions = self.get_positions()
            net_positions = positions.get('net', [])
            
            total_pnl = 0
            realized_pnl = 0
            unrealized_pnl = 0
            
            for pos in net_positions:
                if pos.get('pnl'):
                    total_pnl += pos['pnl']
                if pos.get('realised'):
                    realized_pnl += pos['realised']
                if pos.get('unrealised'):
                    unrealized_pnl += pos['unrealised']
            
            return {
                'total_pnl': total_pnl,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'position_count': len(net_positions)
            }
        except Exception as e:
            self.logger.error(f"Error calculating P&L summary: {e}")
            return {}
    
    def search_instruments(self, search_term: str, exchange: Optional[str] = None) -> List[Dict]:
        """
        Search for instruments by trading symbol or name.
        
        Args:
            search_term (str): Search term
            exchange (str): Exchange to search in (optional)
            
        Returns:
            List[Dict]: Matching instruments
        """
        try:
            instruments = self.get_instruments(exchange)
            search_term = search_term.upper()
            
            matching = []
            for instrument in instruments:
                if (search_term in instrument.get('tradingsymbol', '').upper() or 
                    search_term in instrument.get('name', '').upper()):
                    matching.append(instrument)
            
            return matching
        except Exception as e:
            self.logger.error(f"Error searching instruments: {e}")
            return []
    
    # ==================== ADDITIONAL UTILITY METHODS ====================
    
    def get_supported_product_types(self) -> List[str]:
        """Get list of supported product types."""
        return list(self.p_type_dict.keys())
    
    def get_supported_order_types(self) -> List[str]:
        """Get list of supported order types."""
        return list(self.o_type_dict.keys())
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges."""
        return list(self.ex_seg_dict.keys())
    
    def validate_order_params(self, exchange: str, p_type: str, order_type: str) -> Dict:
        """
        Validate order parameters before placing order.
        
        Args:
            exchange (str): Exchange segment
            p_type (str): Product type
            order_type (str): Order type
            
        Returns:
            Dict: Validation result
        """
        errors = []
        
        if exchange not in self.ex_seg_dict:
            errors.append(f"Unsupported exchange: {exchange}. Supported: {list(self.ex_seg_dict.keys())}")
            
        if p_type not in self.p_type_dict:
            errors.append(f"Unsupported product type: {p_type}. Supported: {list(self.p_type_dict.keys())}")
            
        if order_type not in self.o_type_dict:
            errors.append(f"Unsupported order type: {order_type}. Supported: {list(self.o_type_dict.keys())}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }