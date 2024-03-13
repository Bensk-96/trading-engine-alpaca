# Trading Engine on Alpaca Broker

## Introduction
- This project houses an trading engine designed for medium frequency trading environments.
- Utilizing Python's asynchronous capabilities and OOP, the engine efficiently processes market data, manages trade orders, and implements a sophisticated trading strategies
- Example strategy is based on market regime identification through Hidden Markov Model

## Key Components
- DataClient class fetches and processing real-time market data(1-minute bar, trade and quote) and order updates via websocket. 
- PositionManager class is responsible for managing and updating postiion information for different instrucments in the trading engine.
- OrderManager handles execution and management of different trade orders. 
- For more detail of the trading engine, check out the core file
- The Strategy file consists of a the RegimeTrader class which is the example strategy to test the functionaility of the trading engine.
- RegimeTrader collects minute bar data from the DataClient and calcualte features (log return and fractions of the bars).
Hidden Markov Model is used to determine regime of the stock, it goes on long (short) in bull (bear) regime by submitting a limit price order around the mid-price, until the maximum allowed positions.

![image](https://github.com/Bensk-96/trading-engine-alpaca/assets/91371262/9f81be98-e262-4421-8c56-8757737a1f0a)

## Latency Analysis
- The order reponse time of Alpaca Broker is around 200ms for equity.
- Alpaca's data server is in New York while their account server is in North Virginia, this results in a network latency around 20ms(included in Alpaca Sever's response time?). 
https://forum.alpaca.markets/t/alpaca-data-center-locations/5640
- Deploying the trading algorithm in AWS in North Virginia(us-east-1) or Google Cloud(us-east4), the latency the trading application and Alpaca can be reduced to 10ms(?).
- The internel latency of the trading engine depends on the complexity of the trading logic(say 20ms for the HMM Strategy)
- The round trip time (time form receive market data -> strategy -> submit order -> receive response from Alpaca) will not be less than 250ms

## Improvement in the Future
- Modify the Credentials class - load KEY_ID and SECRET_KEY from .env by Python Decouple, this will replace the usage of key.txt
- Set max number of order id to be saved in the OrderManager class
- Add replace_order, cancel_order and cancel_all_orders methos in OrderMaanger class
- Create AmendOrderResponse and CancelOrderReponse classes
- Create RiskManger class
- Create SystemMonitoring class to monitor latency 
- create an event driven architecture and Strategty Abstract Base Class(ABC). 
- Create UI
- Inlcude option and cryptocurrency trading functions
