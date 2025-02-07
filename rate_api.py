from fastapi import FastAPI
from get_rate import Rate


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
        "Time": rate.rate_time,
        "Currency": currency,
        f"USD to {currency}":rate.data,
        f"{currency} to USD":1.0/rate.data
    }

