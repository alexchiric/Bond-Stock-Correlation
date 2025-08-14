import websocket
import time
import json
import os
from datetime import datetime
from string import ascii_uppercase
import pandas as pd
import random as random

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
                df["Symbol"] = symbol
                all_data.append(df)
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")

        if all_data:
            return pd.concat(all_data).sort_index()
        else:
            return pd.DataFrame()
        
    def get_symbol(self, symbol):
        command = {
            "cmd": "Symbol",
            "prm": {
                "symbol": symbol
            }
        }

        response_str = self.send_and_receive_message(json.dumps(command))
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError:
            raise ValueError("Failed to decode response JSON")

        if "data" in response and isinstance(response["data"], list):
            df = pd.DataFrame(response["data"])
        else:
            df = pd.DataFrame([response])

        return df
    
    def search_symbol(self, search_param):
        command = {
            "cmd":"SearchSymbol",
            "prm": {
                "search":"electric"
            }
        }

        response_str = self.send_and_receive_message(json.dumps(command))

        try:
            response = json.loads(response_str)
        except json.JSONDecodeError:
            raise ValueError("Failed to decode response JSON")

        if "data" in response and isinstance(responsep["data"], list):
            df = pd.DataFrame(response["data"])
        else:
            df = pd.DataFrame([response])

        return df


    
    def find_available_symbols(self, start_year=2000, end_year=2025, delay=0.1):
        """
        Scans symbols matching R[YY][MM][A-Z] pattern and returns a list of valid ones.
        """
        valid_symbols = []

        for year in range(start_year, end_year + 1):
            yy = f"{year % 100:02d}"
            for month in range(1, 13):
                mm = f"{month:02d}"
                for edition in ascii_uppercase:
                    symbol = f"R{yy}{mm}{edition}"
                    try:
                        df = self.get_symbol(symbol)
                        if not df.empty:
                            print(f"✅ Found valid symbol: {symbol}")
                            valid_symbols.append(symbol)
                    except Exception:
                        pass
                    time.sleep(delay)

        return valid_symbols


if __name__ == "__main__":
    gd = GetData([], "2000-01-01", "2025-12-31")

    print("\n🔍 Scanning for available symbols in the API...\n")
    valid_symbols = gd.find_available_symbols(start_year=2000, end_year=2025, delay= random.randint(1, 5))

    print(f"\n🎯 Final list of {len(valid_symbols)} valid symbols:")
    print(valid_symbols)

    gd.close()


#Idea : Reconstruct bond prices from 10-year bond yields