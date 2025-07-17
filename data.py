import websocket
import time
import json
import os
import pandas as pd

from websocket import create_connection

class MyWebSocket:
    def __init__(self):
        websocket.enableTrace(False)

        if os.path.isfile(".env"):
            self.user = os.getenv("API_USER")
            self.password = os.getenv("API_PASSWORD")
        else:
            raise ValueError("Environmental Variables are not defined")

        self.ws = create_connection("wss://api.tradeville.ro:443", subprotocols=["apitv"])
        self.login()

    def login(self):
        login_payload = {
            "cmd": "login",
            "prm": {
                "coduser": self.user,
                "parola": self.password,
                "demo": False
            }
        }
        self.ws.send(json.dumps(login_payload))
        result = self.ws.recv()
        print(f"Login result: {result}")

    def send_and_receive_message(self, message_str):
        self.ws.send(message_str)
        print(f"Sent message: {message_str}")
        result = self.ws.recv()
        print(f"Received: {result}\n")
        return result

    def wait_for_messages(self, number_of_messages):
        for _ in range(number_of_messages):
            time.sleep(1)
            result = self.ws.recv()
            print(f"Received message: {result}\n")

    def close(self):
        print("Closing connection.")
        self.ws.close()

class GetData(MyWebSocket):

    def __init__(self, symbols):
        super().__init__()

        self.symbols = symbols


    def get_time_series(self, symbol, start_date, end_date, adj=1):

        command = {
            "cmd": "DailyValues",
            "prm": {
                "symbol": symbol,
                "dstart": start_date,
                "dend": end_date,
                "adj": adj
            }
        }

        response_str = self.send_and_receive_message(json.dumps(command))
        response = json.loads(response_str)

        if "data" not in response:
            raise ValueError("Response missing 'data' field")

        df = pd.DataFrame(response["data"])
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)

        return df
    
    def get_portfolio_data(self):
        return None


if __name__ == "__main__":
    gd = GetData(["BRD"])
    df = gd.get_time_series("BRD", "1nov05", "20nov24")
    print(df.head())
    gd.close()
