import time

import httpx

from crypto_trade.models import Kline


class BinanceClient:
    """HTTP client for the Binance Futures USD-M klines endpoint."""

    def __init__(
        self,
        base_url: str = "https://fapi.binance.com",
        limit: int = 1500,
        rate_limit_pause: float = 0.25,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.limit = limit
        self.rate_limit_pause = rate_limit_pause
        self._transport = transport

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[Kline]:
        """Fetch klines with automatic pagination.

        Loops until the API returns fewer than `limit` results,
        advancing startTime after each batch.
        """
        all_klines: list[Kline] = []
        current_start = start_time

        client_kwargs: dict = {"base_url": self.base_url}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport
        with httpx.Client(**client_kwargs) as http:
            while True:
                params: dict[str, str | int] = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": self.limit,
                }
                if current_start is not None:
                    params["startTime"] = current_start
                if end_time is not None:
                    params["endTime"] = end_time

                resp = http.get("/fapi/v1/klines", params=params)
                resp.raise_for_status()
                raw_klines = resp.json()

                if not raw_klines:
                    break

                batch = [Kline.from_api(row) for row in raw_klines]
                all_klines.extend(batch)

                if len(batch) < self.limit:
                    break

                # Advance past the last kline's open_time
                current_start = batch[-1].open_time + 1
                time.sleep(self.rate_limit_pause)

        return all_klines
