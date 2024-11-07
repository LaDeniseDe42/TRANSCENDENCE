import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
# from asgiref.sync import async_to_sync
# import requests
import logging

from members.models import myUser

logger = logging.getLogger(__name__)

sessionIDTable = {}
class statusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = "all_users"
        self.other_group_name = f"user_{self.user.id}"

        if self.user.is_authenticated:
            try:
                await database_sync_to_async(self.update_user_status)(self.user.pk, True)
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.channel_layer.group_add(
                    self.other_group_name,
                    self.channel_name
                )
                await self.accept()
                sessionIDTable[self] = self.scope['cookies']['sessionid']
                
                await self.send(text_data=json.dumps({"message": "Bienvenue !"}))
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'status_notification',
                        'user': self.user.username,
                        'status': 'online',
                        'is_playing': self.user.is_playing
                    }
                )
                self.pending_friends = await self.get_pending_friends()
                for friend in self.pending_friends:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'friend_request_notification',
                            'user': friend.username
                        }
                    )
            except Exception as e:
                await self.close(code=4000)
        else:
            await self.close()

    @database_sync_to_async
    def get_pending_friends(self):
        return list(self.user.GuysWhoWantToBeMyFriend.all())
    
    async def disconnect(self, close_code):
        try:
            if self.user.is_authenticated:
                await self.send(text_data=json.dumps({"message": "DISCONNECTED"}))
                await database_sync_to_async(self.update_user_status)(self.user.pk, False)
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'status_notification',
                        'user': self.user.username,
                        'status': 'offline',
                        'is_playing': self.user.is_playing
                    }
                )
                await self.channel_layer.group_discard(
                    self.other_group_name,
                    self.channel_name
                )
            if self in sessionIDTable:
                sessionIDTable.pop(self)
            await self.close()
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion WebSocket: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message
                }
            )
        except Exception as e:
            logger.error(f"Erreur lors de la réception de données WebSocket: {e}")

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def status_notification(self, event):
        user = event['user']
        status = event['status']
        in_game = event['is_playing']
        if in_game:
            await self.send(text_data=json.dumps({
                'message': f"{user} is now {status} and playing"
            }))
        else:    
            await self.send(text_data=json.dumps({
                'message': f"{user} is now {status}"
        }))

    @staticmethod
    def update_user_status(user_id, status):
        myUser.objects.filter(pk=user_id).update(is_online=status)

    async def friend_request_notification(self, event):
        user = event['user']
        await self.send(text_data=json.dumps({
            'message': f"Vous avez reçu une demande d'ami de {user}"
        }))
    
    async def friend_request_accepted(self, event):
        user = event['user']
        await self.send(text_data=json.dumps({
            'message': f"{user} a accepté votre demande d'ami"
        }))

    async def friend_request_removed(self, event):
        user = event['user']
        await self.send(text_data=json.dumps({
            'message': f"{user} vous a retiré de sa liste d'amis"
        }))
    
    async def username_change_notification(self, event):
        user = event['user']
        await self.send(text_data=json.dumps({
            'message': f"{user} a changé de nom d'utilisateur"
        }))
    