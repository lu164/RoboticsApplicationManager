import threading
import json

from websocket_server import WebsocketServer

from src.manager.ram_logging.log_manager import LogManager


class Server(threading.Thread):
    def __init__(
        self,
        port,
        callback,
    ):
        super().__init__()
        self.update_callback = callback
        self.server = WebsocketServer(port=port, host="127.0.0.1")
        self.server.set_fn_new_client(self.on_open)
        self.server.set_fn_client_left(self.on_close)
        self.server.set_fn_message_received(self.on_message)
        self.current_client = None
        self.client_lock = threading.Lock() # Used to avoid concurrency problems
        self._stop = threading.Event()
        LogManager.logger.info("Server Launched")

    def run(self) -> None:
        try:
            while not self._stop.is_set():
                self.server.run_forever()
        except Exception as ex:
            LogManager.logger.exception(ex)

    def stop(self) -> None:
        self._stop.set()
        self.server.shutdown_gracefully()

    def send(self, data):
        with self.client_lock:
            if self.current_client is not None:
                self.server.send_message(self.current_client, data)

    def on_message(self, client, server, message):
        payload = json.loads(message)
        self.update_callback(payload)
        LogManager.logger.debug(f"Message received from template: {message[:30]}")
        

    def on_close(self, client, server):
        LogManager.logger.info("Connection with client closed")
        with self.client_lock:
            if client == self.current_client:
                self.current_client = None

    def on_open(self, client, server):
        LogManager.logger.info(f"New client connected {client}")
        with self.client_lock:
            self.current_client = client
