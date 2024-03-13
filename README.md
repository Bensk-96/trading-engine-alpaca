# Trading Engine on Alpaca Broker

## Introduction
- This project houses an trading engine designed for higher frequency trading environments.
- Utilizing Python's asynchronous capabilities and OOP, the engine efficiently processes market data, manages trade orders, and implements a sophisticated trading strategies
- Example strategy is based on market regime identification through Hidden Markov Model

## Key Components
- DataClient class fetches and processing real-time market data(1-minute bar, trade and quote) and order updates via websocket. 
- PositionManager class is responsible for managing and updating postiion information for different instrucments in the trading engine.
- OrderManager handles execution and management of different trade orders. 
- For more detail of the trading engine, check out the core file
- The Strategy file consists of a the RegimeTrader class which is the example strategy to test the functionaility of the trading engine.
- RegimeTrader collects minute bar data from the DataClient and calcualte features (log return and fractions of the bars).
Hidden Markov Model is used to determine regime of the stock, it goes on long (short) in bull (bear) regime by submitting a limit price order around the mid-price, until the maximum allowed positions
    Shortability and Sleeping time can be set
