

import websocket
import time
import json
from websocket import create_connection

class MyWebSocket:
    def __init__(self):
        websocket.enableTrace(False)
        self.ws = create_connection("wss://api.tradeville.ro:443", subprotocols=["apitv"])
        self.login()

    def login(self):
        login_payload = {
            "cmd": "login",
            "prm": {
                "coduser": "AlexChiric",
                "parola": "Enter3108",
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
    
if __name__ == "__main__":
    my_web_socket = MyWebSocket()
    print("\n")
    
    result = my_web_socket.send_and_receive_message('{ "cmd": "Portfolio", "prm": { "data": "null" } }')

    my_web_socket.wait_for_messages(5)


    my_web_socket.close()
                