"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        if self.login in self.server.logins:
            self.server.history.append(f"<{self.login}> {decoded} ")
            print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                if decoded.replace("login:", "").replace("\r\n", "") not in self.server.logins:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.server.logins.append(self.login)
                    self.transport.write(f"Привет, {self.login}!".encode())
                    self.send_history()
                else:
                    self.transport.write(f"Такой логин уже занят. Отключение...".encode())
                    self.transport.close()
            else:
                self.transport.write(f"Зарегистрируйтесь для начала общения!\n"
                                     f">>> Для регистрации введите команду \"login\" и желаемый логин в формате:\n"
                                     f">>> login:желаемый логин".encode())
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено.")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано.")

    def send_history(self):
        self.transport.write(
            '\n'.join(self.server.history[-10:]).encode()
        )


class Server:
    clients: list
    logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную.")
