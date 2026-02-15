from crypto_trade.config import load_settings


def main() -> None:
    settings = load_settings()
    print(f"crypto-trade started (API key configured: {bool(settings.binance_api_key)})")


if __name__ == "__main__":
    main()
