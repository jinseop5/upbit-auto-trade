import time
import requests
import json
from pyupbit import Upbit

# ✅ 업비트 API 키 입력
ACCESS_KEY = "WiGpRlLMnut4VeC4NqfeFTQ2FjdLc1gxYRiT6DOH"
SECRET_KEY = "jsVpBXDdACwU6SYj2Y6eITjUfLRrEHfwycI6vuv8"

# ✅ 텔레그램 설정
TELEGRAM_TOKEN = "8025718450:AAHPdi-tgOhY-OqWTV8RvmN_T9betoCwpto"
TELEGRAM_CHAT_ID = "7752168245"

# 📌 업비트 객체 생성
upbit = Upbit(ACCESS_KEY, SECRET_KEY)

# 📌 텔레그램 메시지 전송 함수
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 전송 오류: {e}")

# 📌 현재 보유 자산 조회
def get_total_balance():
    balances = upbit.get_balances()
    if isinstance(balances, dict) and "error" in balances:
        raise Exception(f"API 오류: {balances['error']}") 
    
    total_balance = 0
    for b in balances:
        if isinstance(b, dict) and "currency" in b and "balance" in b:
            if b["currency"] != "KRW":  
                price = upbit.get_current_price(f"KRW-{b['currency']}")  
                if price:
                    total_balance += float(b["balance"]) * price  
    return total_balance

# 📌 시장가 매도 함수 (손절)
def market_sell(ticker, volume):
    try:
        order = upbit.sell_market_order(ticker, volume)  
        return order
    except Exception as e:
        print(f"{ticker} 매도 오류: {e}")
        return None

# 📌 손절 실행 함수
def auto_cut_loss(loss_threshold=1.0):
    send_telegram_message("📢 프로그램을 시작합니다.")  # 💡 프로그램 시작 메시지 추가
    initial_balance = get_total_balance()  
    print(f"📢 초기 총 잔고: {initial_balance:,.0f} KRW")
    
    last_report_time = time.time()  

    while True:
        time.sleep(10)  

        current_balance = get_total_balance()  
        loss_amount = initial_balance - current_balance  
        loss_rate = (loss_amount / initial_balance) * 100  

        print(f"현재 잔고: {current_balance:,.0f} KRW | 손실: {loss_amount:,.0f} KRW ({loss_rate:.2f}%)")

        # 1시간마다 상태 보고
        if time.time() - last_report_time >= 3600:
            report_message = f"📊 [상태 보고] \n현재 잔고: {current_balance:,.0f} KRW\n손실: {loss_amount:,.0f} KRW ({loss_rate:.2f}%)"
            send_telegram_message(report_message)
            last_report_time = time.time()  

        # 전체 손실률이 기준 이상이면 손절 실행
        if loss_rate >= loss_threshold:
            balances = upbit.get_balances()
            for b in balances:
                if "currency" in b and "balance" in b and b["currency"] != "KRW":
                    ticker = f"KRW-{b['currency']}"
                    volume = float(b["balance"])
                    if volume > 0:
                        market_sell(ticker, volume)  
                        message = f"🚨 [손절] {ticker} \n손실금액: {loss_amount:,.0f} KRW ({loss_rate:.2f}%)"
                        send_telegram_message(message)  
                        print(message)

            print("✅ 모든 자산 손절 완료. 프로그램 종료.")
            break

# ✅ 프로그램 실행
if __name__ == "__main__":
    auto_cut_loss(loss_threshold=1.0)  
