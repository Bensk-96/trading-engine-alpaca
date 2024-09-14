# Trading Engine on Alpaca Broker

## Introduction
This project presents a trading system tailored for medium-frequency trading environments on Alpaca Broker(Why Alpaca? It is comission free). Built with Python, it leverages asynchronous programming and object-oriented principles for efficient market data processing and trade order management. The engine is versatile, supporting sophisticated trading strategies like one demonstrated here, which uses a Hidden Markov Model for market trend identification.

## Key Components
- DataClient: Fetches and processes real-time market data, including 1-minute bars, trades, and quotes, alongside order updates via WebSocket.
- PositionManager: Manages and updates position information for different instruments within the trading engine.
- OrderManager: Handles the execution and management of diverse trade orders(Support only "Immediate Or Cancel" order at the moment).
- RegimeTrader (Strategy File): An example strategy that utilizes DataClient to gather minute bar data, calculate features (log returns, fractions of the bars), and determine market trend with Hidden Markov Model, guiding long or short positions based on identified regimes.

For more details, please refer to the core and strategy files in the repository.

![image](https://github.com/Bensk-96/trading-engine-alpaca/assets/91371262/9f81be98-e262-4421-8c56-8757737a1f0a)

## Improvement in the Future
- Modify Credentials class for more secure key management(e.g. load credentials from .env)
- Implement limits on stored order IDs in OrderManager.
- Add order amendment and cancellation functionalities.
- Develop RiskManager and SystemMonitoring classes for risk oversight and latency monitoring.
- Transition to an event-driven architecture with a Strategy Abstract Base Class (ABC) and EventHandler class.
- Introduce a user interface.
- Expand capabilities to include options and cryptocurrency trading.
- Deploy on AWS EC2 us-east-1 for testing
