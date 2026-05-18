import enum


class TradeSide(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class AccountType(str, enum.Enum):
    LIVE = "LIVE"
    DEMO = "DEMO"
    PROP = "PROP"


class ConnectionStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    PENDING = "PENDING"
    ERROR = "ERROR"


class MarketType(str, enum.Enum):
    STOCK = "STOCK"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"
    CRYPTO = "CRYPTO"


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExpenseCategory(str, enum.Enum):
    FOOD = "FOOD"
    HOUSING = "HOUSING"
    TRANSPORT = "TRANSPORT"
    UTILITIES = "UTILITIES"
    ENTERTAINMENT = "ENTERTAINMENT"
    SHOPPING = "SHOPPING"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    SUBSCRIPTIONS = "SUBSCRIPTIONS"
    TRAVEL = "TRAVEL"
    OTHER = "OTHER"


class InvestmentType(str, enum.Enum):
    STOCK_IN = "STOCK_IN"
    STOCK_US = "STOCK_US"
    ETF_IN = "ETF_IN"
    ETF_US = "ETF_US"
    MUTUAL_FUND = "MUTUAL_FUND"
    GOLD_ETF = "GOLD_ETF"
    GOLD_SGB = "GOLD_SGB"
    GOLD_DIGITAL = "GOLD_DIGITAL"
    GOLD_PHYSICAL = "GOLD_PHYSICAL"
    BOND = "BOND"
