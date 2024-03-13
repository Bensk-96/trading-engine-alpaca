import asyncio
import logging 
import math
import numpy as np
from numpy.typing import NDArray
import pickle
from typing import Optional
import time

from core import DataClient, OrderManager
from core import ORDER_CYLE_END_EVENT, ORDER_TYPE_IOC
logging.basicConfig(level=logging.INFO , format='%(asctime)s - %(levelname)s - %(message)s')

class RegimeTrader:
    """
    The RegimeTrader class is an example strategy to test the trading engine. It collects minute bar data from the DataClient and calcualte features (log return and fractions of the bars). 
    Hidden Markov Model is used to determine regime of the stock, it goes on long (short) in bull (bear) regime by submitting a limit price order around the mid-price, until the maximum allowed positions
    Shortability and Sleeping time can be set
    """
    def __init__(self, dataclient: DataClient, ordermanager: OrderManager, model_path: str, sleep_sec: float = 1.0, symbol: Optional[str] = None, max_position: int = 10, shortable: bool = True):
        self._last_close_price : Optional[float] = None 
        self._last_bar_hist_size : Optional[dict] = None
        self._bull_regime : Optional[bool] = None
        self._bear_regime : Optional[bool] = None
        self._feature_array: NDArray[np.float_] = np.array([]).reshape(0, 4) 
        self._side : Optional[str] = None
        self._last_order_id: Optional[str] = None 
        self._dataclient : DataClient = dataclient
        self._ordermanager : OrderManager = ordermanager
        self._sleep_sec :float = sleep_sec
        self._symbol  : Optional[str] = symbol
        self._model_path : str = model_path
        self._model = self.load_model()
        self._max_position  = max_position
        self._shortable = shortable
    
    def load_model(self) -> object:
        with open(self._model_path, "rb") as f:
            return pickle.load(f)

    def order_volume(self) -> float:
        pos_qty = self._dataclient.get_position_by_symbol(self._symbol)   
        #logging.info(f"pos qty of {self._symbol} is  {pos_qty}")     
        if self._bull_regime:
            if pos_qty >= 0:
                volume = self._max_position - pos_qty
            elif pos_qty < 0:
                volume = abs(pos_qty)
        elif self._bear_regime:
            if self._shortable:
                if pos_qty > 0:
                    volume = abs(pos_qty)
                elif pos_qty <= 0:
                    volume = self._max_position - abs(pos_qty)
            elif not self._shortable:
                volume = abs(pos_qty)
        return volume
    
    def calculate_features(self, bar) -> NDArray[np.float_]:
        open_price = bar.open
        high_price = bar.high
        low_price = bar.low
        close_price = bar.close

        h_over_o = high_price / open_price
        l_over_o = low_price / open_price
        c_over_o = close_price / open_price
        log_ret = math.log(close_price / self._last_close_price)

        return np.array([log_ret, h_over_o, l_over_o, c_over_o])
    
    def last_order_is_close(self) -> bool:
        if self._last_order_id is None:
            logging.info(f"No submitted order for {self._symbol}.")
            return True
        
        trade_update = self._dataclient.get_trade_update(self._symbol, self._last_order_id)
        if trade_update is None:
            logging.info("No Trade update.")
            return True
        
        order_status = trade_update.event
        return order_status in ORDER_CYLE_END_EVENT

    async def main(self) -> None:
        while True:
            #t_tick = time.time() ## TODO Remove after development phase 
            #t_trade = None 
            bar_hist = self._dataclient.get_bar_hist(self._symbol)
            if bar_hist is None:
                #logging.info(f"Mising bar history of {self._symbol}, not making regime predition.")
                pass
            else:
                bar_hist_size = len(bar_hist)
                bar = self._dataclient.get_last_bar(self._symbol)
                if bar_hist_size == 1:
                    self._last_close_price = bar.close
                    self._last_bar_hist_size = bar_hist_size
                    logging.info(f"First bar for {self._symbol}, not making regime prediction")
                elif bar_hist_size >= 1:
                    if bar_hist_size == self._last_bar_hist_size:
                        logging.info("No new bar, not making regime prediction")
                    elif bar_hist_size > self._last_bar_hist_size:
                        bar = self._dataclient.get_last_bar(self._symbol)
                        feature = self.calculate_features(bar)
                        self._feature_array = np.vstack((self._feature_array, feature))
                        regime_pred = self._model.predict(self._feature_array)[-1]

                        if regime_pred == 1: 
                            self._bear_regime = True
                            self._bull_regime = False
                            self._side = "sell"
                            price_modifier = -0.1 ## TODO try 0.1 (old value is 0.02)
                            #logging.info("Bear Regime")
                        elif regime_pred == 0:
                            self._bear_regime = False
                            self._bull_regime = True
                            self._side = "buy"
                            price_modifier = 0.1
                            #logging.info("Bull Regime")

                        self._last_bar_hist_size = len(bar_hist)
                        self._last_close_price = bar.close
                        
                    volume = self.order_volume()
                    mid_price = self._dataclient.get_last_mid_price(self._symbol)
                    price = round(mid_price  + price_modifier, 2)
                    last_order_close = self.last_order_is_close()

                    #if self._bear_regime is not None and self._bull_regime is not None: ## TODO Remove after development phase 
                    #    if self._bear_regime is True:
                    #        logging.info(f"{self._symbol} is in bear regime")
                    #    elif self._bull_regime is True:
                    #        logging.info(f"{self._symbol} is in bull regime")
                    # t_trade = time.time()
                    if volume != 0 and last_order_close is True:
                        t_trade = time.time()
                        logging.info(f"Inserting a {self._side} order for {volume} lots at {price}")
                        order = await self._ordermanager.insert_order(symbol=self._symbol, price = price, quantity= volume, side = self._side,order_type=ORDER_TYPE_IOC)
                        self._last_order_id = order.order_id
                            
                    elif volume == 0:
                        #logging.info("Reach max position, not making trade")
                        pass

                    elif last_order_close is False:
                        logging.info("Last order still opens, not making trade")

            #if t_trade is not None: ## TODO Remove after development phase 
                #t_tick_to_trade = (t_trade - t_tick) * 1000 
                #logging.info(f"Tick-to-trade latency is {t_tick_to_trade} ms")

            #logging.info(f'Sleeping for {self._sleep_sec} secs.')
            await asyncio.sleep(self._sleep_sec)


async def _regimetrader():
    i = DataClient(symbols={"TSLA","AAPL","NVDA"})
    o = OrderManager()
    TSLA_Trader = RegimeTrader(dataclient=i, ordermanager=o, sleep_sec=1, symbol="TSLA",model_path="TSLA_BW_2yr_bt_1.pkl",max_position=10,shortable= True)
    AAPL_Trader = RegimeTrader(dataclient=i, ordermanager=o, sleep_sec=1, symbol="AAPL",model_path="AAPL_GMMHMM_n_mix_2_1_min_Episode_457.pkl",max_position=10,shortable= True) ## TODO Check labels of the regimes
    NVDA_Trader = RegimeTrader(dataclient=i, ordermanager=o, sleep_sec=1, symbol="NVDA",model_path="NVDA_GMMHMM_n_mix_2_1_min_Episode_283.pkl",max_position=10,shortable= True) ## TODO Check labels of the regimes
    asyncio.create_task(i.start())
    await o.start()   
    await asyncio.sleep(5)   
    #await TSLA_Trader.main()
    await asyncio.gather(TSLA_Trader.main(), AAPL_Trader.main(),NVDA_Trader.main())

def regimetrader():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_regimetrader())
    except KeyboardInterrupt:
        logging.info('Stopped (KeyboardInterrupt)')


regimetrader()      
