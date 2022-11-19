import asyncio

class LoginConflictError(Exception):
    pass

class InvalidStateError(Exception):
    pass

class ChatClientProtocol(asyncio.Protocol):
    def __init__(self):
        self._pieces = []
        self._login_name = None
        self._responses_q = asyncio.Queue()
        self._user_messages_q = asyncio.Queue()

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport

    def data_received(self,data):
        self._pieces.append(data.decode('utf-8'))

        if ''.join(self._pieces).endswith('$'):
            protocol_msg = ''.join(self._pieces).rstrip('$')

            if protocol_msg.startswith('/MSG '):
                user_msg = protocol_msg.lstrip('/MSG')
                asyncio.ensure_future(self._user_messages_q.put(user_msg))
            else:
                asyncio.ensure_future(self._responses_q.put(''.join(self._pieces).rstrip('$')))

            self._pieces = []

    def connection_lost(self, exc):
        self._transport.close()

class ChatClient:
    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._connected = False
    def disconnect(self):
        if not self._connected:
            raise NotConnectedError()
        self._transport.close()
        
    async def _connect(self):
        try:
            loop = asyncio.get_event_loop()
            self._transport, self._protocol = await loop.create_connection(
                lambda: ChatClientProtocol(),
                self._ip,
                self._port)
            self._connected = True
            print('connected to chat server')
        except ConnectionRefusedError:
            print('error connecting to chat server - connection refused')
        except TimeoutError:
            print('error connecting to chat server - connection timeout')
        except Exception as e:
            print('error connecting to chat server - fatal error')
            
    def connect(self):
        loop = asyncio.get_event_loop()
        try:
            asyncio.ensure_future(self._connect())
            loop.run_forever()
        except Exception as e:
            print(e)
        finally:
            print('{} - closing main event loop'.format(threading.current_thread().getName()))
            loop.close()
            
    async def lru(self):
        self._transport.write('/lru $'.encode('utf-8'))
        # await for response message from server
        lru_response = await self._protocol._responses_q.get()
        
        users = lru_response.lstrip('/lru ').split(', ')
        # filter out any Nones or empty strings
        users = [u for u in users if u and u != '']
        return users
    
    async def login(self, login_name):
        self._transport.write('/login {}$'.format(login_name).encode('utf-8'))
        login_response = await self._protocol._responses_q.get()
        success = login_response.lstrip('/login ')
        if success == 'already exists':
            raise LoginConflictError()
        elif success != 'success':
            raise LoginError()
        self._login_name = login_name
        
    async def lrooms(self):
        
        # expected response format:
        # /lroom public&system&public room\nroom1, omari, room to discuss chat service impl
        self._transport.write('/lrooms $'.encode('utf-8'))
        lrooms_response = await self._protocol._responses_q.get()
        lines = lrooms_response.lstrip('/lrooms ').split('\n')
        rooms = []
        for line in lines:
            room_attributes = line.split('&')
            rooms.append({'name': room_attributes[0], 'owner': room_attributes[1], 'description': room_attributes[2]})

        return rooms


    async def crooms(self, room_name):#add
        
        self._transport.write('/croom {}$'.format(room_name).encode('utf-8'))
        crooms_response = await self._protocol._responses_q.get()
        result = crooms_response.lstrip('/croom').rstrip('$').strip()
        
        if result == 'success':
            return 'Created {}'.format(room_name)
        else:
            return result


    async def jroom(self, room_name):
        self._transport.write('/jroom {}$'.format(room_name).encode('utf-8'))
        jroom_response = await self._protocol._responses_q.get()
        success = jroom_response.lstrip('/jroom ')


    async def post(self, msg, room):
        # post to a room:
        # /post public&hello everyone
        self._transport.write('/post {}&{}$'.format(room.strip(), msg.strip()).encode('utf-8'))

    async def leaveRoom(self, room_name):  # add
        self._transport.write('/leaveRoom {}$'.format(room_name).encode('utf-8'))
        response = await self._protocol._responses_q.get()
        status = response.lstrip('/leaveRoom ')

        if status == 'Room does not exist':
            pass
        elif status == 'user is not in the room':
            pass
        elif status != 'success':
            pass

    
    async def dm(self, recipient, dm_msg):
        if self._login_name != None:
            self._transport.write('/dm {}&{}&{}$'.format(self._login_name,recipient, dm_msg).encode('utf-8'))
            await self._protocol._responses_q.get()
            result = dm_response.lstrip('/dm').rstrip('$').strip()
            if result == 'success':
                return result
            #else:
                #return result
            else:
                 'Message failed to send'
        
    async def get_user_msg(self):
        return await self._protocol._user_messages_q.get()

if __name__ == '__main__':
    LOCAL_HOST = '127.0.0.1'
    PORT = 8080
    loop = asyncio.get_event_loop()
    chat_client = ChatClient(LOCAL_HOST, PORT)
    asyncio.ensure_future(chat_client._connect())
    chat_client.disconnect()