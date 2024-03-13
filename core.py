## Latest Update : 13.03.2024
import asyncio
import aiohttp
import logging 
import json
from collections import defaultdict, deque
from typing import Optional, Set

from alpaca_trade_api.common import URL
from alpaca_trade_api.stream import Stream
logging.basicConfig(level=logging.INFO , format='%(asctime)s - %(levelname)s - %(message)s')

FILL = "fill"
PARTIAL_FILL = "partial_fill"
FILL_EVENT = [FILL, PARTIAL_FILL]

CANCELED = "canceled"
ORDER_CYLE_END_EVENT = [FILL, CANCELED]


SIDE_BUY = 'buy'
SIDE_SELL = 'sell'
ALL_SIDES= [SIDE_BUY, SIDE_SELL]

ORDER_TYPE_LIMIT = 'limit'
ORDER_TYPE_IOC = 'ioc'
ALL_ORDER_TYPES = [ORDER_TYPE_LIMIT, ORDER_TYPE_IOC]

class Credentials:
    """
    The Credentials class is responsible for managing API credentials used in the asynchronous trading engine. 
    It stores the key ID, secret key, headers, and maintains a flag to track whether the credentials have been loaded. 
    The class provides methods to load credentials from a specified file and access the key ID, secret key, and headers. 
    It utilizes a static method to load credentials from a file only once, ensuring efficient usage of resources.
    
    Attributes:
        key_id (str): The API key ID for authentication.
        secret_key (str): The API secret key for secure communication.
        headers (dict): Headers used in API requests, including authentication information.
        _credentials_loaded (bool): A flag indicating whether the credentials have been loaded.
    
    Methods:
        load_credentials: Reads credentials from a file and initializes class attributes.
        KEY_ID: Returns the API key ID, loading credentials if necessary.
        SECRET_KEY: Returns the API secret key, loading credentials if necessary.
        HEADERS: Returns the API request headers, loading credentials if necessary.
    """
    key_id = None
    secret_key = None
    headers = None
    _credentials_loaded = False

    @staticmethod
    def load_credentials(credentials_file='key.txt'):
        if not Credentials._credentials_loaded:  # Only load if not already loaded
            try:
                with open(credentials_file, 'r') as file:
                    Credentials.headers = json.loads(file.read())
                    Credentials.key_id = Credentials.headers.get('APCA-API-KEY-ID')
                    Credentials.secret_key = Credentials.headers.get('APCA-API-SECRET-KEY')
                    Credentials._credentials_loaded = True  # Set flag to True after loading
            except Exception as e:
                print(f"Error loading credentials: {e}")

    @classmethod
    def KEY_ID(cls):
        cls.load_credentials()  # Will load only if not already loaded
        return cls.key_id

    @classmethod
    def SECRET_KEY(cls):
        cls.load_credentials()  # Will load only if not already loaded
        return cls.secret_key

    @classmethod
    def HEADERS(cls):
        cls.load_credentials()  # Will load only if not already loaded
        return cls.headers


class Client:
    """
    The Client class represents the asynchronous client used in the trading engine for making API requests.
    It manages a client session for sending requests with the necessary headers, specifically tailored for asynchronous operation.
    
    This class uses the aiohttp library to create and manage an asynchronous HTTP client session, 
    leveraging the credentials managed by the Credentials class. It ensures efficient management of network resources 
    by creating and closing the client session as needed.

    Attributes:
        session (aiohttp.ClientSession): An asynchronous HTTP session for API requests.

    Methods:
        start_session: Asynchronously creates a client session if one does not already exist.
        close_session: Asynchronously closes the existing client session and sets it to None.
    """
    session = None

    @classmethod
    async def start_session(cls):
        if not cls.session:
            cls.session = aiohttp.ClientSession(headers=Credentials.HEADERS())

    @classmethod
    async def close_session(cls):
        if cls.session:
            await cls.session.close()
            cls.session = None


class DataClient(): 
    """
    The DataClient class is responsible for managing and processing market data in the asynchronous trading engine.
    It subscribes to various data streams (trades, quotes, bars, trade updates) and maintains historical data and current state for each symbol.

    Attributes:
        _max_trade_history (int): Maximum number of trade ticks to store in history.
        _symbols (Set[str]): A set of symbols (tickers) that the client will track.
        _base_url (str): The base URL for API requests.
        _data_feed (str): Identifier for the data feed source.
        _last_trade_price (dict): Stores the last trade price for each symbol.
        _trade_tick_hist (dict): Stores the historical trade ticks for each symbol.
        _last_quote (dict): Stores the last quote for each symbol.
        _last_mid_price (dict): Stores the last calculated mid price for each symbol.
        _last_bar (dict): Stores the last bar data for each symbol.
        _bar_hist (dict): Stores the historical bar data for each symbol.
        _trade_update (dict): Stores the trade updates for each symbol.
        _position_manager (PositionManager): An instance of PositionManager to manage positions.

    Methods:
        start: Initializes and starts the data stream with subscriptions for trades, quotes, bars, and trade updates.
        on_trade: Callback function for handling incoming trade data.
        on_quote: Callback function for handling incoming quote data.
        on_bar: Callback function for handling incoming bar data.
        on_trade_update: Callback function for handling trade update data.
        get_last_trade_price: Returns the last trade price for a given symbol.
        get_last_mid_price: Returns the last calculated mid price for a given symbol.
        get_last_bar: Returns the last bar data for a given symbol.
        get_bar_hist: Returns the bar history for a given symbol.
        get_trade_update: Returns trade updates for a given symbol and optionally a specific trade ID.
        get_position_by_symbol: Retrieves the current position quantity for a given symbol.
        get_all_positions: Retrieves all current positions.
    """
    def __init__(self, max_nr_trade_history: int = 100, symbols : Optional[Set[str]] = None):   
        self._max_trade_history = max_nr_trade_history
        self._symbols = symbols if symbols is not None else set()
        self._base_url = URL('https://paper-api.alpaca.markets')
        self._data_feed = "iex"
        self._last_trade_price = {}
        self._trade_tick_hist = defaultdict(deque)
        self._last_quote = defaultdict(deque)
        self._last_mid_price = {}
        self._last_bar = {}
        self._bar_hist = defaultdict(deque)
        self._trade_update = defaultdict(dict)
        self._position_manager = PositionManager()
                      
    async def start(self):
        self._position_manager = await PositionManager.create()
        stream = Stream(Credentials.KEY_ID(), Credentials.SECRET_KEY(), base_url=self._base_url, data_feed=self._data_feed)
        stream.subscribe_trades(self.on_trade, *self._symbols)
        stream.subscribe_quotes(self.on_quote, *self._symbols)
        stream.subscribe_bars(self.on_bar, *self._symbols)
        stream.subscribe_trade_updates(self.on_trade_update) 
        if asyncio.get_event_loop().is_running():
            await stream._run_forever()
        else:
            await stream.run()
    
    async def on_trade(self,trade_tick ) -> None:    
        symbol = trade_tick.symbol
        self._last_trade_price[symbol] = trade_tick.price
        _trade_hist_to_update = self._trade_tick_hist[symbol]
        _trade_hist_to_update.append(trade_tick)
        while len(_trade_hist_to_update) > self._max_trade_history:
            _trade_hist_to_update.popleft()
        #logging.info(trade_tick)

    def get_last_trade_price(self, symbol : str) ->  Optional[float]:
        return self._last_trade_price.get(symbol, None)
                                                  
    async def on_quote(self, quote) -> None:
        symbol = quote.symbol
        self._last_quote[symbol] = quote
        if quote.ask_price != 0 and quote.bid_price != 0:
            midprice = round((quote.ask_price + quote.bid_price) * 0.5 , 2)
            self._last_mid_price[symbol] = midprice
        else: 
            pass        
        #logging.info(quote)
      
    def get_last_mid_price(self, symbol : str) ->  Optional[float]:
        return self._last_mid_price.get(symbol, None)

    async def on_bar(self, bar) -> None:
        symbol = bar.symbol
        self._last_bar[symbol] = bar
        _bar_hist_to_update = self._bar_hist[symbol]
        _bar_hist_to_update.append(bar)
    
    def get_last_bar(self, symbol):
        return self._last_bar.get(symbol, None)
    
    def get_bar_hist(self, symbol):
        return self._bar_hist.get(symbol, None)

    async def on_trade_update(self, trade_update) -> None:
        symbol = trade_update.order["symbol"]
        id = trade_update.order["id"]      
        #logging.info(f"Symbol: {symbol}, ID: {id}, Type of _trade_update[symbol]: {type(self._trade_update[symbol])}")  
        if trade_update.event in FILL_EVENT:   ## TODO order status update : fill, cancel, rejected 
            #print(f"update position for {symbol}")
            position_qty = float(trade_update.position_qty)
            await self._position_manager.update_position(symbol, position_qty)
        self._trade_update[symbol][id] = trade_update
        #logging.info(trade_update)

    #def get_trade_update(self, symbol : str, id :str):
    #        return self._trade_update.get(symbol, None)
        
    def get_trade_update(self, symbol: str, id: str = None):
        symbol_trades = self._trade_update.get(symbol, {})
        if id is None:
            return symbol_trades  # Return all trade updates for the symbol
        else:
            return symbol_trades.get(id)  # Return a specific trade update for the id

    
    def get_position_by_symbol(self, symbol) -> float:
        position_info = self._position_manager._positions_by_symbol.get(symbol, None)
        if position_info is not None:
            return position_info.get("position", 0.0)
        else:
            return 0.0  # Return 0.0 if the symbol is not found
        
    def get_all_positions(self) -> dict:
        return self._position_manager._positions_by_symbol


class PositionManager():
    """
    The PositionManager class is responsible for managing and updating position information for different symbols in the trading engine.
    It interacts with an external API to fetch and update position data, and maintains a record of current positions for various symbols.

    Attributes:
        _pos_url (str): URL for querying position data from the API.
        _position_objects_by_symbol (dict): Stores detailed position data for each symbol.
        _positions_by_symbol (dict): Stores position quantities for each symbol.

    Methods:
        create: Class method to instantiate the PositionManager and initialize data by fetching current positions.
        get_positions: Fetches current positions from the API and updates internal data structures.
        update_position: Updates the position quantity for a given symbol.
    """
    def __init__(self):
        #self.session = None 
        self._pos_url = "https://paper-api.alpaca.markets/v2/positions"
        self._position_objects_by_symbol = {}
        self._positions_by_symbol = {}

    @classmethod
    async def create(cls):
        instance = cls()
        await Client.start_session()
        await instance.get_positions()
        return instance

    async def get_positions(self, symbol=None):
        url = f"{self._pos_url}/{symbol}" if symbol else self._pos_url
        try:
            async with Client.session.get(url) as result:
                if result.status == 200:
                    response = await result.json()
                    if symbol:
                        response = [response]  # Wrap in a list for uniformity

                    for individual_response in response:
                        symbol = individual_response.get("symbol", "Unknown")
                        qty = float(individual_response.get("qty", 0))
                        self._position_objects_by_symbol[symbol] = individual_response
                        self._positions_by_symbol[symbol] = {"position": qty}
                else:
                    response_text = await result.text()
                    logging.warning(f"Failed to get positions: Status {result.status}, Details: {response_text}")
        except Exception as e:
            logging.warning(f"Error to get positions: {e}")    

    async def update_position(self, symbol, position_qty):
        # Check if the symbol already exists in the dictionary
        if symbol not in self._positions_by_symbol:
            self._positions_by_symbol[symbol] = {"position": 0}
        self._positions_by_symbol[symbol]["position"] = position_qty


class OrderManager():
    """
    The OrderManager class is responsible for managing orders in the asynchronous trading engine.
    It provides functionality to insert new orders, close individual positions, and close all positions.
    The class interacts with an external API for order management and keeps track of the submitted orders.

    Attributes:
        _order_url (str): URL for creating new orders.
        _pos_url (str): URL for managing positions.
        session (aiohttp.ClientSession, optional): An asynchronous HTTP session for API requests, initialized in an async context.
        _submitted_order_by_order_id (dict): A record of submitted orders indexed by their order ID.

    Methods:
        start: Ensures that a client session is started before making any API requests.
        insert_order: Asynchronously inserts a new order with specified parameters such as symbol, price, quantity, side, and order type.
        close_all_positions: Asynchronously closes all positions, with an option to cancel all open orders.
        close_position: Asynchronously closes a specific position for a given symbol, with the option to specify the quantity or percentage to close.

    The class makes extensive use of asynchronous programming to handle orders and positions in a non-blocking manner,
    ensuring efficient execution in a real-time trading environment.
    """
    def __init__(self):
        self._order_url = "https://paper-api.alpaca.markets/v2/orders"
        self._pos_url = "https://paper-api.alpaca.markets/v2/positions"
        self.session = None  # We'll initialize this in an async context
        self._submitted_order_by_order_id = defaultdict(dict)
           
    async def start(self):
        if not Client.session:
            await Client.start_session()

    async def insert_order(self, symbol: str, price: float, quantity: int, side: str, order_type: str):
        assert side in ALL_SIDES, f"side must be one of {ALL_SIDES}"
        assert order_type in ALL_ORDER_TYPES, f"order_type must be one of {ALL_ORDER_TYPES}"
        params = {"symbol": symbol,"qty": quantity, "side": side,"type": ORDER_TYPE_LIMIT, "limit_price": price,"time_in_force": ORDER_TYPE_IOC}
        await Client.start_session()
        try:
            async with Client.session.post(self._order_url, json=params) as result:
            #async with self.session.post(self._order_url, json=params) as result:
                response_text = await result.text()
                if result.status == 200:
                    logging.info(f"Succesful Order Insertion - Symbol : {symbol}, Qty : {quantity}, Side : {side}, Price : {price}")
                    order_response = await result.json()
                    #logging.info(f"Successful Order Insertion: {order_response}")
                    symbol = order_response["symbol"]
                    id = order_response["id"]
                    self._submitted_order_by_order_id[symbol][id] = id ## record id instead of order_response
                    return InsertOrderResponse(success=True, order_id=id, error=None)
                else:
                    logging.warning(f"Order Insertion Error (Status {result.status}): {response_text}")
                    return InsertOrderResponse(success=False, order_id=None, error= f"Error (Status {result.status}): {response_text}" )
                    
        except Exception as e:
            logging.warning(f"Error inserting order: {e}")
            return InsertOrderResponse(success=False, order_id=None, error=e)

    ## Todo: add close order response        
    async def close_all_positions(self, cancel_orders: bool = True):
        params = {"cancel_orders": cancel_orders}
        try:
            async with Client.session.delete(self._pos_url, json=params) as result:
                response_text = await result.text()
                if result.status == 207:  # Handle Multi-Status responses
                    logging.info("Close All Positions Request Received Multi-Status Response")
                    response = await result.json()
                    # Process each individual response in the multi-status response
                    for individual_response in response:
                        symbol = individual_response.get("symbol", "Unknown")
                        status = individual_response.get("status")
                        body = individual_response.get("body", {})
                        id = individual_response.get("id")
                        if status == 200:
                            logging.info(f"Closed position for {symbol}: {body}")
                            self._submitted_order_by_order_id[symbol][id] = individual_response
                        else:
                            logging.warning(f"Failed to close position for {symbol}: Status {status}, Details: {body}")
                else:
                    logging.warning(f"Unexpected status {result.status} received: {response_text}")
        except Exception as e:
            logging.warning(f"Error closing all positions: {e}")
   
    async def close_position(self, symbol: str, qty: float = None, percentage: float = None):
        # Ensure that either qty or percentage is provided, but not both.
        assert (qty is not None) != (percentage is not None), "Either qty or percentage must be specified, but not both"

        # Construct the URL for the specific symbol's position.
        pos_url_with_symbol = f"{self._pos_url}/{symbol}"
        
        # Prepare the parameters for the request.
        params = {}
        if qty is not None:
            params["qty"] = qty
        if percentage is not None:
            params["percentage"] = percentage
        try:
            # Send the DELETE request to the API.
            async with Client.session.delete(pos_url_with_symbol, params=params) as result:
                response_text = await result.text()
                
                # Check for a successful response.
                if result.status == 200:
                    logging.info(f"Closed position for {symbol}.")
                    order_response = await result.json()
                    logging.info(f"Order response: {order_response}")
                else:
                    logging.warning(f"Failed to close position for {symbol} (Status {result.status}): {response_text}")
        except Exception as e:
            logging.warning(f"Error closing position for {symbol}: {e}")        

    ## Todo in future if needed
    async def replace_order(self):
        pass

    async def cancel_all_orders(self):
        pass

    async def cancel_order(self):
        pass     

class InsertOrderResponse:

    def __init__(self, success: bool, order_id: Optional[int], error: Optional[str]):
        self.success: bool = success
        self.order_id: Optional[int] = order_id
        self.error_reason: Optional[str] = error

    def __str__(self):
        return f"InsertOrderResponse(success={self.success}, order_id={self.order_id}, error='{self.error}')"

## Todo
class ModifyOrderResponse:
    pass


class CancelOrderResponse:
    pass



class RiskManager():
    pass


class SystemMonitoring():
    pass