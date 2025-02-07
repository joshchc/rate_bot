from fastapi import FastAPI
from get_rate import Rate
from datetime import timedelta

app = FastAPI()
rate = Rate()


# 測試 API
@app.get("/")
def read_root():
    return {"message": "Hello"}

# 取得參數
@app.get("/rate/{currency}")
def read_item(currency: str):
    rate.main(curr=currency)
    return {
        "Time": rate.rate_time + timedelta(hours = 8),
        "Currency": currency,
        f"USD to {currency}":rate.data,
        f"{currency} to USD":1.0/rate.data
    }

@app.get("/22")
def read_item():
    return {
        "EUR":rate.main("EUR"),
        "GBP":rate.main("GBP"),
        "AUD":rate.main("AUD"),
        "SGD":rate.main("SGD")
    }

