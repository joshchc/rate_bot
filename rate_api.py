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
    return {"item_id": currency, "query": rate.rate_time, "data":rate.data}

