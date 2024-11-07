import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import redis
from .models import Message
from members.models import myUser
from asgiref.sync import sync_to_async

import re
from channels.layers import InvalidChannelLayerError
from members import consumers

# import settings
from django.conf import settings

# Connectez-vous à Redis
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

from bs4 import BeautifulSoup

def contient_balises_html(chaine):
    # Parser le contenu avec BeautifulSoup
    soup = BeautifulSoup(chaine, "html.parser")
    
    # Vérifier s'il y a des balises HTML
    return bool(soup.find())

invitations = {}
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.joinedChannels = []
        if not self.user.is_authenticated:
            await self.close()
            return
        self.waitingNotifications = await sync_to_async(list)(self.user.waitingNotifications.all())
        self.waitingNotifications = [notif.id for notif in self.waitingNotifications]
        
        database_sync_to_async(self.user.waitingNotifications.clear)()
        await self.channel_layer.group_add(
            f'user_{self.user.id}_chat',
            self.channel_name
        )
        await self.accept()
        consumers.sessionIDTable[self.user.id] = self.channel_name
        await self.join_channel('PUBLIC_global')

    async def disconnect(self, close_code):
        # leaving all channels
        if self.user.is_authenticated:
            for room in self.joinedChannels:
                await self.remove_user_from_group(room, self.user.username)
                await self.channel_layer.group_discard(
                    room,
                    self.channel_name
                )
                await self.send_to_channel(room, f'{self.user.username} has left the channel', saveMessage=False)
            await self.channel_layer.group_discard(
                f'user_{self.user.id}_chat',
                self.channel_name
            )
            # saving notifications of user
            for notif in self.waitingNotifications:
                await database_sync_to_async(self.user.waitingNotifications.add)(notif)
            # removing the user from the sessionIDTable
            if self in consumers.sessionIDTable:
                consumers.sessionIDTable.pop(self)
            await self.delete_all_invitations_from_id(self.user.id)
        # closing the connection
        self.joinedChannels = []
        await self.close()
    
    async def receive(self, text_data):
        try:
            # getting the action, channel and message from the received message
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            channel = text_data_json.get('channel')
            message = text_data_json.get('message', '')  # message peut être vide par défaut
            # update the user informations
            self.user = await database_sync_to_async(myUser.objects.get)(id=self.user.id)
            # verify if the action is present
            if not action:
                raise ValueError("Missing 'action' in received message")
            
            # redirect to the corresponding function
            if action == 'join':
                await self.join_channel(channel)
            elif action == 'leave':
                await self.leave_channel(channel)
            elif action == 'send':
                await self.send_to_channel(channel, message)
            elif action == 'getHistory':
                await self.giveHistory(channel)
            elif action == 'getUsers':
                await self.getUsers(channel)
            elif action == 'getUsersOnline':
                await self.getUsersOnline()
            elif action == 'mute':
                await self.mute_user(channel)
            elif action == 'unmute':
                await self.unmute_user(channel)
            elif action == 'recoverInformations':
                await self.recover()
            elif action == 'clearNotification':
                await self.clearNotification(channel)
            elif action == 'inviteToPlay':
                await self.inviteToPlay(channel)
            elif action == 'acceptInvitation':
                await self.acceptInvitation(channel)
            elif action == 'cancelInvitation':
                await self.cancelInvitation(channel)
            elif action == 'declineInvitation':
                await self.delete_all_invitations_from_id(self.user.id)
            else:
                raise ValueError(f"Unknown action '{action}'")
        # if an error occurs, send the error message to the user
        except Exception as e:
            await self.chat_message({
                'message': str(e),
                'success': False,
                'action': 'receive',
                'channel': channel
            })

    async def send_to_channel(self, channel, message, saveMessage=True):
        # create the correct message format
        if contient_balises_html(message):
            self.chat_message({
                'message': 'HTML tags are not allowed',
                'success': False,
                'action': 'send',
                'channel': channel
            })
            return
        message = f'<a class="spa_redirect" href="#members/profile/{self.user.id}" data-section="members/profile/{self.user.id}">{self.user.username}</a> : {message}'
        # saving the message in the database
        if saveMessage:
            await self.save_message(self.user, channel, message)
        # check if the channel is a private channel and send a notification to the other user
        if channel.startswith('PRIVATE_'):
            channelCopy = channel
            channelCopy = channelCopy.removeprefix('PRIVATE_')
            userIDs = channelCopy.split('-')
            if int(userIDs[0]) == self.user.id:
                id = userIDs[1]
            else:
                id = userIDs[0]
            if id:
                await self.channel_layer.group_send(
                    f'user_{id}_chat',
                    {
                        'type': 'chat_message',
                        'message': 'You have a new message',
                        'channel': channel,
                        'author': self.user.id,
                        'notification': True,
                    }
                )
        # send the message to the channel
        await self.channel_layer.group_send(
            channel,
            {
                'type': 'chat_message',
                'message': message,
                'channel': channel,
                'author': self.user.id,
                'action': 'send'
            }
        )

    async def join_channel(self, channel):
        try:
            # check if the channel is a private channel to verify if the private channel is already created
            if channel.startswith('PRIVATE_'):
                user = await database_sync_to_async(myUser.objects.get)(id=channel.split('_')[1])
                if not user:
                    await self.chat_message({
                        'message': 'User does not exist',
                        'success': False,
                        'action': 'join',
                        'channel': channel
                    })
                    return
                # check if the private channel is already created
                channel = f'PRIVATE_{self.user.id}-{user.id}'
                channelRedis = redis_instance.exists(channel)
                if not channelRedis:
                    channel = f'PRIVATE_{user.id}-{self.user.id}'
            # check if the user is already in the channel
            if channel in self.joinedChannels:
                await self.chat_message({
                    'message': 'You are already in the channel',
                    'success': False,
                    'action': 'join',
                    'channel': channel
                })
                return

            # add the user to the channel
            await self.channel_layer.group_add(
                channel,
                self.channel_name
            )
            self.joinedChannels.append(channel)
            await self.add_user_to_group(channel, self.user.username)

            # send a message to the user that he has joined the channel
            context = {
                'message': 'You have joined the channel',
                'success': True,
                'action': 'join',
                'channel': channel
            }
            # adding the user to the context if the channel is private
            if channel.startswith('PRIVATE_'):
                context['private'] = True
                context['user'] = user.username
            else:
                context['private'] = False
                context['user'] = None
            # inform the user that he has joined the channel
            await self.chat_message(context)
            # send a message to the channel that the user has joined
            await self.send_to_channel(channel, f'{self.user.username} has joined the channel', saveMessage=False)
        # if an error occurs, send the error message to the user
        except Exception as e:
            await self.chat_message({
                'message': str(e),
                'success': False,
                'action': 'join',
                'channel': channel
            })
    
    async def leave_channel(self, channel):
        # if the size of joined channels is 1, the user cannot leave the channel
        if len(self.joinedChannels) == 1:
            await self.chat_message({
                'message': 'You cannot leave the last channel',
                'success': False,
                'action': 'leave',
                'channel': channel
            })
            return
        await self.channel_layer.group_discard(
            channel,
            self.channel_name
        )
        self.joinedChannels.remove(channel)

        # Supprimer l'utilisateur du groupe dans Redis
        await self.remove_user_from_group(channel, self.user.username)

        await self.chat_message({
            'message': 'You have left the channel',
            'success': True,
            'action': 'leave',
            'channel': channel
        })
    
    async def chat_message(self, event):
        if 'notification' in event:
            if event['notification']:
                event['action'] = 'notification'
                del event['notification']
        
        if 'channel' in event:
            channel = event['channel']
            if channel.startswith('PRIVATE_'):
                if 'author' in event:
                    author = event['author']
                    if author != self.user.id:
                        if author not in self.waitingNotifications:
                            self.waitingNotifications.append(author)

        # Envoie le message formaté au client
        await self.send(text_data=json.dumps(event))

    
    # function to send all messages in a channel (history) to the user
    async def giveHistory(self, channel):
        messages = await self.get_history(channel)
        for message in messages:
            await self.chat_message({
                'action': 'send',
                'message': message['message'],
                'channel': channel,
                'author': message['user_id'],
            })
    
    # function to get all messages in a channel
    @database_sync_to_async
    def get_history(self, channel):
        messages = Message.objects.filter(room_name=channel).order_by("timestamp")
        return [
            {
                "username": message.user.username,
                "user_id": message.user.id,
                "message": message.content,
                "timestamp": message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for message in messages
        ]
    
    # function to save a message in the database
    @database_sync_to_async
    def save_message(self, user, channel, message):
        return Message.objects.create(user=user, room_name=channel, content=message)

    # get all users in a group and send them to the user
    async def getUsers(self, channel):
        users = await self.get_users(channel)
        await self.chat_message({
            'action': 'getUsers',
            'users': [user.decode('utf-8') for user in users]  # Décoder chaque utilisateur de bytes à str
        })
    
    # functions to add and remove users from a group
    async def add_user_to_group(self, group_name, username):
        redis_instance.sadd(group_name, username)
    
    async def remove_user_from_group(self, group_name, username):
        redis_instance.srem(group_name, username)
    
    # function to get all users in a group (dont call this function directly, use getUsers instead)
    async def get_users(self, group_name):
        return redis_instance.smembers(group_name)
    
    # get all users existing in the database and send them to the user with details (is_online, is_playing, id, muted, is_friend)
    async def getUsersOnline(self):
        users = await sync_to_async(list)(myUser.objects.all())
        users = [user for user in users if user != self.user]
        friends = await sync_to_async(list)(self.user.friends.all())
        muted_users = await sync_to_async(list)(self.user.mutedUsers.all())
        waiting_notifications = self.waitingNotifications

        await self.chat_message({
            'action': 'getUsersOnline',
            'users': [
                {
                    'username': user.username,
                    'is_online': user.is_online,
                    'is_playing': user.is_playing,
                    'id': user.id,
                    'muted': user in muted_users,
                    'is_friend': user in friends,
                    'waiting_notification': user.id in waiting_notifications,
                    'invitedYou': True if user.id in invitations and invitations[user.id] == self.user.id else False,
                    'youInvited': True if self.user.id in invitations and invitations[self.user.id] == user.id else False
                }
                for user in users
            ]
        })

                

    # functions to mute and unmute users
    async def mute_user(self, userId):
        user = await database_sync_to_async(myUser.objects.get)(id=userId)
        mutedUsers = await sync_to_async(list)(self.user.mutedUsers.all())
        if user not in mutedUsers:
            await database_sync_to_async(self.user.mutedUsers.add)(user)
            await self.chat_message({
                'message': 'You have muted the user',
                'success': True,
                'action': 'mute',
                'channel': userId
            })
        else:
            await self.chat_message({
                'message': 'User is already muted',
                'success': False,
                'action': 'mute',
                'channel': userId
            })
    
    async def unmute_user(self, userId):
        user = await database_sync_to_async(myUser.objects.get)(id=userId)
        mutedUsers = await sync_to_async(list)(self.user.mutedUsers.all())
        if user in mutedUsers:
            await database_sync_to_async(self.user.mutedUsers.remove)(user)
            await self.chat_message({
                'message': 'You have unmuted the user',
                'success': True,
                'action': 'unmute',
                'channel': userId
            })
        else:
            await self.chat_message({
                'message': 'User is already unmuted',
                'success': False,
                'action': 'unmute',
                'channel': userId
            })

    async def recover(self):
        user = None
        for channel in self.joinedChannels:
            if channel.startswith('PRIVATE_'):
                id = channel.lstrip('PRIVATE_').split('-')
                if int(id[0]) == self.user.id:
                    id = id[1]
                else:
                    id = id[0]
                user = await database_sync_to_async(myUser.objects.get)(id=id)
            await self.chat_message({
                'action': 'join',
                'channel': channel,
                'success': True,
                'user': user.username if user else None
            })

    async def clearNotification(self, channel):
        if channel.startswith('PRIVATE_'):
            channel = channel.lstrip('PRIVATE_').split('-')
            if int(channel[0]) == self.user.id:
                channel = channel[1]
            else:
                channel = channel[0]
            channelINT = int(channel)
            if channelINT in self.waitingNotifications:
                self.waitingNotifications.remove(channelINT)
                await self.chat_message({
                    'action': 'clearNotification',
                    'channel': channel,
                    'success': True
                })
    
    async def inviteToPlay(self, userId):
        if self.user.is_playing:
            await self.chat_message({
                'message': 'You are already playing',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId),
                'sub_action': 'Error'
            })
            return
        if self.user.id in invitations:
            await self.chat_message({
                'message': 'You have already invited a user to play',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId),
                'sub_action': 'Error'
            })
            return
        userToInvite = await sync_to_async(myUser.objects.get)(id=userId)
        if not userToInvite:
            await self.chat_message({
                'message': 'User does not exist',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId),
                'sub_action': 'Error'
            })
        if userToInvite.is_playing:
            await self.chat_message({
                'message': 'User is already playing',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId),
                'sub_action': 'Error'
            })
            return
        invitations[self.user.id] = userToInvite.id
        await self.chat_message({
            'message': 'You have invited the user to play',
            'success': True,
            'action': 'gameButtons',
            'channel': str(userId),
            'sub_action': 'Success'
        })
        await self.channel_layer.group_send(
            f'user_{userId}_chat',
            {
                'type': 'chat_message',
                'message': f'{self.user.username} has invited you to play',
                'author': self.user.id,
                'sub_action': 'ReceivedInvitation',
                'action': 'gameButtons',
            }
        )
    
    async def acceptInvitation(self, userId):
        errorInviteDoesntExist = False
        if userId not in invitations:
            errorInviteDoesntExist = True
        if self.user.id is not invitations[userId]:
            errorInviteDoesntExist = True
        if errorInviteDoesntExist == True:
            await self.chat_message({
                'message': 'this user dont invited you',
                'sub_action': 'Error',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId)
            })
            return
        invitations.pop(userId)
        player1 = self.user
        player2 = await sync_to_async(myUser.objects.get)(id=userId)
        if player1.is_playing or player2.is_playing:
            await self.chat_message({
                'message': 'One of the players is already playing',
                'sub_action': 'Error',
                'success': False,
                'action': 'gameButtons',
                'channel': str(userId)
            })
            return
            await self.channel_layer.group_send(
                f'user_{userId}_chat',
                {
                    'type': 'chat_message',
                    'message': 'One of the players is already playing',
                    'sub_action': 'Error',
                    'success': False,
                    'action': 'gameButtons',
                    'channel': str(userId)
                }
            )
            return
        await self.delete_all_invitations_from_id(userId)
        await self.delete_all_invitations_from_id(self.user.id)
        await self.chat_message({
            'message': 'You have accepted the invitation',
            'sub_action': 'InvitationAccepted',
            'success': True,
            'action': 'gameButtons',
            'channel': str(userId),
            'author': userId,
            'gameRoom': f'game/remote/?room=REMOTE_{player1.id}VS{player2.id}'
        })
        await self.channel_layer.group_send(
            f'user_{userId}_chat',
            {
                'type': 'chat_message',
                'message': f'{self.user.username} has accepted the invitation',
                'sub_action': 'InvitationAccepted',
                'action': 'gameButtons',
                'channel': str(userId),
                'author': self.user.id,
                'gameRoom': f'game/remote/?room=REMOTE_{player1.id}VS{player2.id}'
            }
        )
    
    async def cancelInvitation(self, userId, fromId=None):
        if fromId is None:
            fromId = self.user.id
        if fromId in invitations and invitations[fromId] == userId:
            invitations.pop(fromId)
            await self.channel_layer.group_send(
                f'user_{userId}_chat',
                {
                    'type': 'chat_message',
                    'message': f'{fromId} has canceled the invitation',
                    'sub_action': 'InvitationCanceled',
                    'action': 'gameButtons',
                    'channel': str(userId),
                    'author': fromId
                }
            )
        else:
            await self.channel_layer.group_send(
                f'user_{fromId}_chat',
                {
                    'type': 'chat_message',
                    'message': 'You have not invited a/this user user to play',
                    'sub_action': 'Error',
                    'success': False,
                    'action': 'gameButtons',
                    'channel': str(userId)
                }
            )
    
    async def declineInvitation(self, userId, fromId=None):
        if fromId is None:
            fromId = self.user.id
        if userId in invitations and invitations[userId] == fromId:
            invitations.pop(userId)
            await self.channel_layer.group_send(
                f'user_{userId}_chat',
                {
                    'type': 'chat_message',
                    'message': f'{fromId} has declined the invitation',
                    'sub_action': 'InvitationDeclined',
                    'action': 'gameButtons',
                    'channel': str(userId),
                    'author': self.user.id
                }
            )
    
    async def delete_all_invitations_from_id(self, userId):
        for key, value in (list)(invitations.items()):
            if value == userId:
                await self.declineInvitation(key, userId)
            elif key == userId:
                await self.cancelInvitation(value, userId)
        