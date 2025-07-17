import websocket
import time
import json
import os
from datetime import datetime
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

    def __init__(self, symbols, start_date, end_date):
        super().__init__()

        self.symbols = symbols
        self.start_date = self.format_date(start_date)
        self.end_date = self.format_date(end_date)

    @staticmethod
    def format_date(date_input):
        if isinstance(date_input, datetime):
            dt = date_input
        else:
            dt = datetime.strptime(date_input, "%Y-%m-%d")

        day = dt.day
        month = dt.strftime("%b").lower()
        year = dt.strftime("%y")    

        return f"{day}{month}{year}"

    def get_time_series(self, symbol, adj=1):

        command = {
            "cmd": "DailyValues",
            "prm": {
                "symbol": symbol,
                "dstart": self.start_date,
                "dend": self.end_date,
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
        all_data = []

        for symbol in self.symbols:
            try:
                df = self.get_time_series(symbol)
                df["Symbol"] = symbol  # Add symbol column to preserve identity
                all_data.append(df)
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")

        if all_data:
            return pd.concat(all_data).sort_index()
        else:
            return pd.DataFrame()
            


if __name__ == "__main__":
    gd = GetData(["BRD", "SNN"], "2000-11-01", "2020-11-01")
    df = gd.get_portfolio_data()
    print(df)
    gd.close()
