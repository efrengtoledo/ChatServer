import aioconsole
import asyncio
import click
from server.chat_server import ChatServer
from client.chat_client import (
    ChatClient,
    #NotConnectedError,
    #LoginConflictError,
    #LoginError
)

async def display_msgs(chat_client):
    while True:
        msg = await chat_client.get_user_msg()
        print('\n\n\t\tRECEIVED MESSAGE: {}'.format(msg))


async def handle_user_input(chat_client, loop):
    while True:

        print('\n\n')
        print('< 1 > closes connection and quits')
        print('< 2 > list logged-in users')
        print('< 3 > login')
        print('< 4 > list rooms')
        print('< 5 > Post public message')
        print('< 6 > Create private room')
        print('< 7 > Join Private Room')
        print('< 8 > Leave private room')
        print('< 9 > DM a user')
        print('< 10 > Post message to a room')

        print('\tchoice: ', end='', flush=True)

        command = await aioconsole.ainput()
        if command == '1':
            # disconnect
            try:
                chat_client.disconnect()
                print('disconnected')
                loop.stop()
            except NotConnectedError:
                print('client is not connected ...')
            except Exception as e:
                print('error disconnecting {}'.format(e))
                
        elif command == '2':  # list registered users
            users = await chat_client.lru()
            print('logged-in users: {}'.format(', '.join(users)))
            
        elif command == '3':
            login_name = await aioconsole.ainput('enter login-name: ')
            try:
                await chat_client.login(login_name)

            except Exception as e:
                print('error getting rooms from server {}'.format(e))
            #return login_name

        elif command == '4':# command to list rooms
            try:
                rooms = await chat_client.lrooms()
                for room in rooms:
                    print('\n\t\troom name ({}), owner ({}): {}'.format(room['name'], room['owner'], room['description']))

            except Exception as e:
                print('error getting rooms from server {}'.format(e))
            

        elif command == '5': #post a public message
            try:

                user_message = await aioconsole.ainput('enter your message: ')
                await chat_client.post(user_message, 'public')

            except Exception as e:
                print('error posting message {}'.format(e))

        elif command == '6':
            try:
                room_name = await aioconsole.ainput('enter room name: ')
                await chat_client.crooms(room_name)
                #print('loop test')

            except Exception as e:
                print('error creating room {}'.format(e))

        elif command == '7': #command to join a private room
            rName = await aioconsole.ainput("Enter the name of the room you would like to join: ")
            await chat_client.jroom(rName)
            
        
        elif command == '8':# to leave private room
            
            rName = await aioconsole.ainput("Enter name of the room you are leaving: ")
            await chat_client.leaveRoom(rName)
    

        
        elif command == '9':#send dm to user
            if not login_name:
                print()
            else:
                users = await chat_client.lru()
                if users == False:
                    print('There are no users online at the moment')
                else:
                    print('Select a user to DM')
                    usernumber = 0
                    for i in users:
                        usernumber += 1
                        print(str(usernumber) + ') ' + str(i))
                    dm_choice = await aioconsole.ainput('Choice: ')
                    recipient = users[int(dm_choice) - 1]
                    if recipient == login_name:
                        print('Error: User cannot DM himself')
                    else:
                        print('Recipient: {}'.format(recipient))
                        dm_message = await aioconsole.ainput("Enter DM: ")
                        print('pre-test')
                        await chat_client.dm(recipient, dm_message)
                        print('test')
                        #print('Message from {}'.format(login_name))
                        #print(result)
            

        elif command == '10': #post message to a room

            try:
                rName = await aioconsole.ainput('enter room name:')
                uMessage = await aioconsole.ainput('enter message: ')
                await chat_client.post(uMessage, rName)

            except Exception as e:
                print('error posting your message :-(')
        


@click.group()
def cli():
    pass
@cli.command(help="run chat client")
@click.argument("host")
@click.argument("port", type=int)
def connect(host, port):
    chat_client = ChatClient(ip=host, port=port)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(chat_client._connect())

    # display menu, wait for command from user, invoke method on client
    asyncio.ensure_future(handle_user_input(chat_client=chat_client, loop=loop))
    asyncio.ensure_future(display_msgs(chat_client=chat_client))

    loop.run_forever()

@cli.command(help='run chat server')
@click.argument('port', type=int)
def listen(port):
    click.echo('starting chat server at {}'.format(port))
    chat_server = ChatServer(port=port)
    chat_server.start()
if __name__ == '__main__':
    cli()