import time
import requests
import json

# ✅ 업비트 API 키 입력
ACCESS_KEY = "WiGpRlLMnut4VeC4NqfeFTQ2FjdLc1gxYRiT6DOH"
SECRET_KEY = "jsVpBXDdACwU6SYj2Y6eITjUfLRrEHfwycI6vuv8"

# ✅ 텔레그램 설정
TELEGRAM_TOKEN = "8025718450:AAHPdi-tgOhY-OqWTV8RvmN_T9betoCwpto"
TELEGRAM_CHAT_ID = "7752168245"

# ✅ 업비트 API 기본 URL
UPBIT_URL = "https://api.upbit.com/v1"

# ✅ 텔레그램 메시지 보내는 함수
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# ✅ 내 계좌 잔고 조회
def get_balances():
    headers = {"Authorization": f"Bearer {ACCESS_KEY}"}
    res = requests.get(UPBIT_URL + "/accounts", headers=headers)
    return res.json()

# ✅ 현재 가격 조회 함수
def get_current_price(market):
    url = f"{UPBIT_URL}/ticker?markets={market}"
    res = requests.get(url)
    return res.json()[0]["trade_price"]

# ✅ 시장가 매도 함수
def sell_market_order(market, volume):
    headers = {
        "Authorization": f"Bearer {ACCESS_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "market": market,
        "side": "ask",
        "volume": str(volume),
        "ord_type": "market"
    }
    res = requests.post(UPBIT_URL + "/orders", headers=headers, data=json.dumps(data))
    return res.json()

# ✅ 매수 시 평균 매수가 기록
buy_prices = {}

# ✅ 초기 잔고 기록 (기준이 될 총자산)
initial_balances = get_balances()
initial_total_balance = sum(float(b["balance"]) * get_current_price(b["currency"]) for b in initial_balances if b["currency"] != "KRW")

# ✅ 5초마다 손절 확인
while True:
    balances = get_balances()
    total_balance = 0  # 현재 총자산

    for b in balances:
        if b["currency"] == "KRW":
            continue

        market = "KRW-" + b["currency"]
        volume = float(b["balance"])
        if volume == 0:
            continue

        current_price = get_current_price(market)
        avg_buy_price = float(b["avg_buy_price"])  # 평균 매수가
        total_balance += volume * current_price

        # 🔥 손실율 계산
        loss_percentage = ((current_price - avg_buy_price) / avg_buy_price) * 100
        loss_amount = (avg_buy_price - current_price) * volume  # 손실 금액

        if loss_percentage <= -1:  # 🔥 -1% 손절
            sell_market_order(market, volume)
            msg = f"🔴 {market} 손절!\n"
            msg += f"💰 손절 금액: {loss_amount:,.0f} KRW\n"
            msg += f"📉 손실율: {loss_percentage:.2f}%"
            send_telegram_message(msg)

    # 🔥 전체 잔고 대비 손실율 출력
    total_loss_percentage = ((total_balance - initial_total_balance) / initial_total_balance) * 100
    print(f"총 잔고 변동율: {total_loss_percentage:.2f}%")

    time.sleep(5)  # 5초마다 체크
