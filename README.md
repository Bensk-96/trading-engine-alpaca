# Trading Engine on Alpaca Broker

## Introduction
This project presents a trading engine tailored for medium-frequency trading environments on Alpaca Broker(Why Alpaca? It is comission free). Built with Python, it leverages asynchronous programming and object-oriented principles for efficient market data processing and trade order management. The engine is versatile, supporting sophisticated trading strategies like one demonstrated here, which uses a Hidden Markov Model for market regime identification.

## Key Components
- DataClient: Fetches and processes real-time market data, including 1-minute bars, trades, and quotes, alongside order updates via WebSocket.
- PositionManager: Manages and updates position information for different instruments within the trading engine.
- OrderManager: Handles the execution and management of diverse trade orders.
- RegimeTrader (Strategy File): An example strategy that utilizes DataClient to gather minute bar data, calculate features (log returns, fractions of the bars), and determine market regime with a Hidden Markov Model, guiding long or short positions based on identified regimes.

For more details, please refer to the core and strategy files in the repository.

![image](https://github.com/Bensk-96/trading-engine-alpaca/assets/91371262/9f81be98-e262-4421-8c56-8757737a1f0a)

## Thoughts on Latency 
- Broker Response Time: Approximately 200ms for equity orders with Alpaca Broker.
- Network Latency: Due to data and account server locations, there's an inherent network latency (estimated at around 20ms).
https://forum.alpaca.markets/t/alpaca-data-center-locations/5640
- Deployment Suggestion: Using AWS in North Virginia or Google Cloud in us-east4 can potentially reduce application-server latency to around 10ms.
- Internal Latency: Depends on strategy complexity (e.g., < 20ms for the HMM Strategy).
- Round Trip Time: Minimum expected is around 250ms from market data receipt to order response.

## Improvement in the Future
- Modify Credentials class for more secure key management(e.g. load credentials from .env)
- Implement limits on stored order IDs in OrderManager.
- Add order amendment and cancellation functionalities.
- Develop RiskManager and SystemMonitoring classes for risk oversight and latency monitoring.
- Transition to an event-driven architecture with a Strategy Abstract Base Class (ABC).
- Introduce a user interface.
- Expand capabilities to include options and cryptocurrency trading.
