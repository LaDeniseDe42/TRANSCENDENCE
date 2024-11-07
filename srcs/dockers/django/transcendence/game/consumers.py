import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from asgiref.sync import sync_to_async
import random
from channels.exceptions import StopConsumer
from members.models import myUser
from history.models import History
from members import consumers
from django.core import serializers
from channels.layers import get_channel_layer
import logging
import datetime

logger = logging.getLogger(__name__)


GAME_WIDTH = 600
GAME_HEIGHT = 400
PADDLE_WIDTH = 5
PADDLE_HEIGHT = 70
BALL_SPEED = 1.5
ORIGINAL_BALL_SPEED = 1.5
NB_POINTS_TO_WIN = 5
HOW_MANY = 0
BALL_SIZE = 10
PADDLE_SPEED = 7
ORIGINAL_PADDLE_SPEED = 5
TIME_COUNTDOWN = 30
    

class MatchmakingConsumer(AsyncWebsocketConsumer):
    waiting_players = []

    async def connect(self):
        self.user = self.scope['user']
        self.user.is_playing = True
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=True)
        await self.accept()
        consumers.sessionIDTable[self] = self.scope['cookies']['sessionid']
        MatchmakingConsumer.waiting_players.append(self)

        if len(MatchmakingConsumer.waiting_players) >= 2:
            player1 = MatchmakingConsumer.waiting_players.pop(0)
            player2 = MatchmakingConsumer.waiting_players.pop(0)

            room_id = f"room_{random.randint(1000, 9999)}"
            await player1.send(text_data=json.dumps({
                'type': 'match_found',
                'player1': player1.scope['user'].id,
                'player2': player2.scope['user'].id,
                'room_id': room_id
            }))
            await player2.send(text_data=json.dumps({
                'type': 'match_found',
                'player1': player1.scope['user'].id,
                'player2': player2.scope['user'].id,
                'room_id': room_id
            }))

    async def disconnect(self, close_code):
        if self in MatchmakingConsumer.waiting_players:
            MatchmakingConsumer.waiting_players.remove(self)
            self.user.is_playing = False
            await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
            if self in consumers.sessionIDTable:
                consumers.sessionIDTable.pop(self)
            self.close()


    async def receive(self, text_data):
        if text_data == 'leave_queue':
            MatchmakingConsumer.waiting_players.remove(self)
            self.user.is_playing = False
            await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
            self.close()


class localStatusIsPlayingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        await self.accept()
        self.user.is_playing = True
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=True)
        consumers.sessionIDTable[self] = self.scope['cookies']['sessionid']

    async def disconnect(self, close_code):
        self.user.is_playing = False
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
        if self in consumers.sessionIDTable:
            consumers.sessionIDTable.pop(self)
        self.close()

    async def receive(self, text_data):
        text_data = json.loads(text_data)
        type = text_data.get('type', '')
        if type == 'end_single_game':
            winner = text_data.get('winner', None)
            looser = text_data.get('looser', None)
            scoreW = text_data.get('scoreW', None)
            scoreL = text_data.get('scoreL', None)
            game = text_data.get('game', None)
            mode = text_data.get('mode', None)
            if winner == self.user.username or winner == "Player1":
                if mode == 'bot':
                    await sync_to_async(History.objects.create)(winner=self.user, name="Bernard Le Bot", scoreW=scoreW, scoreL=scoreL, game=game, mode=mode)
                else:
                    await sync_to_async(History.objects.create)(winner=self.user, name=looser, scoreW=scoreW, scoreL=scoreL, game=game, mode=mode)
            else:
                if mode == 'bot':
                    await sync_to_async(History.objects.create)(name="Bot MoiL'Cul", looser=self.user, scoreW=scoreW, scoreL=scoreL, game=game, mode=mode)
                else:
                    await sync_to_async(History.objects.create)(name=winner, looser=self.user, scoreW=scoreW, scoreL=scoreL, game=game, mode=mode)


channel_layer = get_channel_layer()
class tournamentConsumers(AsyncWebsocketConsumer):
    waiting_players = []
    tournaments = {}
    numberOfTournaments = 0

    tournamentLaunched = 0
    async def connect(self):
        self.user = self.scope['user']
        self.user.is_playing = True
        self.joinedTournament = None
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=True)
        await self.accept()
        consumers.sessionIDTable[self] = self.scope['cookies']['sessionid']
        # result = await self.joinLeavedTournament()
        # if result == True:
        #     return
        tournamentConsumers.waiting_players.append(self)
        waiting_player_two = (list)(tournamentConsumers.waiting_players)
        if len(waiting_player_two) == 4:
            players = []
            actualTournament = tournamentConsumers.numberOfTournaments
            tournamentConsumers.numberOfTournaments += 1
            for i in range(4):
                playerWebsocket = waiting_player_two.pop(0)
                playerWebsocket.joinedTournament = actualTournament
                tournamentConsumers.waiting_players.remove(playerWebsocket)
                if playerWebsocket:
                    players.append(playerWebsocket.user)
                    await playerWebsocket.channel_layer.group_add(
                        f"TOURNAMENT_{actualTournament}",
                        playerWebsocket.channel_name
                    )
                    await playerWebsocket.channel_layer.group_add(
                        f"TOURNAMENT_PLAYER_{playerWebsocket.user.id}",
                        playerWebsocket.channel_name
                    )
            tournamentConsumers.tournamentLaunched += 1
            tournamentConsumers.tournaments[actualTournament] = {}
            tournamentConsumers.tournaments[actualTournament] = {'players': {}, 'games':{'game1':[],'game2':[],'final1':[],'final2':[],}, 'demiFinalsLaunched': False, 'finalsLauched': False, 'finalsEnded': False, 'tournamentEnded': False, 'endOfRound': None, 'adapting': False}
            tc = tournamentConsumers.tournaments[actualTournament]
            for player in players:
                tc['players'][player] = {}
                tc['players'][player]['matchJoined'] = False
                tc['players'][player]['match1Finished'] = False
                tc['players'][player]['match2Finished'] = False
                tc['players'][player]['winner'] = False
                tc['players'][player]['disconnect'] = False
            tc['games']['game1'].extend(players[0:2])
            tc['games']['game2'].extend(players[2:4])
            data1 = [
                {'username': player.username, 'tournamentName': player.tournamentName}
                for player in players[0:2]
            ]
            data2 = [
                {'username': player.username, 'tournamentName': player.tournamentName}
                for player in players[2:4]
            ]
            await channel_layer.group_send(
                f"TOURNAMENT_{actualTournament}",
                {
                    'type': 'sendMessage',
                    'action': 'joinTournament',
                    'game2': data2,
                    'game1': data1
                }
            )
            for player in tc['games']['game1']:
                await channel_layer.group_send(
                    f"TOURNAMENT_PLAYER_{player.id}",
                    {
                        'type': 'sendMessage',
                        'action': 'joinMatch',
                        'game': 'game1',
                        'nbT': actualTournament
                    }
                )
            for player in tc['games']['game2']:
                await channel_layer.group_send(
                    f"TOURNAMENT_PLAYER_{player.id}",
                    {
                        'type': 'sendMessage',
                        'action': 'joinMatch',
                        'game': 'game2',
                        'nbT': actualTournament
                    }
                )
            current_time = datetime.datetime.now()

            tournamentConsumers.tournaments[actualTournament]['endOfRound'] = current_time + datetime.timedelta(seconds=TIME_COUNTDOWN)
            await channel_layer.group_send(
                f"TOURNAMENT_{actualTournament}",
                {
                    'type': 'start_countdown',
                    'nbT': actualTournament,
                }
            )

    async def sendMessage(self, event):
        try:
            await asyncio.wait_for(self.send(text_data=json.dumps(event)), timeout=5)
            await self.sendInfoToChat(event)
        except asyncio.TimeoutError:
            self.disconnect(1000)

    async def sendInfoToChat(self, event):
        actualTime = datetime.datetime.now()
        if event.get('action', None) == 'countdown':
            if event['seconds'] % 5 == 0:
                await channel_layer.group_send(
                    f"user_{self.user.id}_chat",
                    {
                        'type': 'chat_message',
                        'channel': 'TOURNAMENT',
                        'action': 'send',
                        'message': f"Your next game will start in {event['seconds']} seconds.",
                        'current_time': str(actualTime)
                    }
                )
        elif event.get('action', None) == 'tournamentEnded':
            await channel_layer.group_send(
                f"user_{self.user.id}_chat",
                {
                    'type': 'chat_message',
                    'channel': 'TOURNAMENT',
                    'action': 'send',
                    'message': f"The tournament has ended, the winner is {event['first']}.",
                    'current_time': str(actualTime)
                }
            )
        elif event.get('action', None) == 'finalsAborted':
            await channel_layer.group_send(
                f"user_{self.user.id}_chat",
                {
                    'type': 'chat_message',
                    'channel': 'TOURNAMENT',
                    'action': 'send',
                    'message': f"The finals have been aborted, the tournament is over.",
                    'current_time': str(actualTime)
                }
            )
        elif event.get('action', None) == 'cancelTournament':
            await channel_layer.group_send(
                f"user_{self.user.id}_chat",
                {
                    'type': 'chat_message',
                    'channel': 'TOURNAMENT',
                    'action': 'send',
                    'message': f"The tournament has been canceled.",
                    'current_time': str(actualTime)
                }
            )
        elif event.get('action', None) == 'joinMatch':
            await channel_layer.group_send(
                f"user_{self.user.id}_chat",
                {
                    'type': 'chat_message',
                    'channel': 'TOURNAMENT',
                    'action': 'send',
                    'message': f"You can join your next match.",
                    'current_time': str(actualTime)
                }
            )
        elif event.get('action', None) == 'joinedTournament':
            await channel_layer.group_send(
                f"user_{self.user.id}_chat",
                {
                    'type': 'chat_message',
                    'channel': 'TOURNAMENT',
                    'action': 'send',
                    'message': f"Tournament found!",
                    'current_time': str(actualTime)
                }
            )

    async def receive(self, text_data=None):
        data = json.loads(text_data)
        action = data.get('action', None)
        if action == None:
            await self.sendMessage({'error': 'invalid action'})
        elif action == "joinGame":
            await self.joinGame(data)

    async def joinLeavedTournament(self):
        duplicate = (list)(tournamentConsumers.tournaments.items())
        for tournament_id, tournament in duplicate:
            if tournament['tournamentEnded'] == True:
                continue
            if self.user in tournament['players']:
                await self.channel_layer.group_add(
                    f"TOURNAMENT_{tournament_id}",
                    self.channel_name,
                )
                await self.channel_layer.group_add(
                    f"TOURNAMENT_PLAYER_{self.user.id}",
                    self.channel_name,
                )
                data1 = [
                    {'username': player.username, 'tournamentName': player.tournamentName}
                    for player in tournament['games']['game1']
                ]
                data2 = [
                    {'username': player.username, 'tournamentName': player.tournamentName}
                    for player in tournament['games']['game2']
                ]
                await channel_layer.group_send(
                    f"TOURNAMENT_PLAYER_{self.user.id}",
                    {
                        'type': 'sendMessage',
                        'action': 'joinTournament',
                        'game2': data2,
                        'game1': data1
                    }
                )
                if tournament['finalsEnded'] == False:
                    if tournament['finalsLauched'] == True:
                        type = 'final'
                        tcGames = tournament['games']
                        final1Data = [
                            {'username': player.username, 'tournamentName': player.tournamentName}
                            for player in tcGames['final1']
                        ]
                        final2Data = [
                            {'username': player.username, 'tournamentName': player.tournamentName}
                            for player in tcGames['final2']
                        ]
                        await channel_layer.group_send(
                            f"TOURNAMENT_PLAYER_{self.user.id}",
                            {
                                'type': 'sendMessage',
                                'action': 'tournamentUpdate',
                                'final1': final1Data,
                                'final2': final2Data
                            }
                        )
                    else:
                        type = 'game'
                    if self.user in tournament['games'][type + '1']:
                        gameToPlay = type + '1'
                    elif self.user in tournament['games'][type + '2']:
                        gameToPlay = type + '2'
                    if tournament['demiFinalsLaunched'] == False:
                        await channel_layer.group_send(
                            f"TOURNAMENT_PLAYER_{self.user.id}",
                            {
                                'type': 'sendMessage',
                                'action': 'joinMatch',
                                'game': gameToPlay,
                                'nbT': tournament_id
                            }
                        )
                    elif tournament['finalsLauched'] == True and tournament['finalsEnded'] == False:
                        await channel_layer.group_send(
                            f"TOURNAMENT_PLAYER_{self.user.id}",
                            {
                                'type': 'sendMessage',
                                'action': 'joinMatch',
                                'game': gameToPlay,
                                'nbT': tournament_id
                            }
                        )
                    tournament['players'][self.user]['disconnect'] = False
                    self.joinedTournament = tournament_id
                    await channel_layer.group_send(
                        f"TOURNAMENT_PLAYER_{self.user.id}",
                        {
                            'type': 'start_countdown',
                            'nbT': tournament_id,
                        }
                    )
                return True
        return False

    async def disconnect(self, close_code):
        if self in tournamentConsumers.waiting_players:
            tournamentConsumers.waiting_players.remove(self)
        self.user.is_playing = False
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
        await self.handle_disconnection()
        if self in consumers.sessionIDTable:
            consumers.sessionIDTable.pop(self)
        if self.joinedTournament is not None:
            await self.channel_layer.group_discard(
                f"TOURNAMENT_{self.joinedTournament}",
                self.channel_name,
            )
            await self.channel_layer.group_discard(
                f"TOURNAMENT_PLAYER_{self.user.id}",
                self.channel_name,
            )
        oldTournamentName = self.user.tournamentName
        oldTournamentName = oldTournamentName.split('_')
        oldTournamentName = oldTournamentName[0]
        await sync_to_async(myUser.objects.filter(username=self.user.username).update)(tournamentName=oldTournamentName)
        await self.close()

    async def handle_disconnection(self):
        duplicate = (list)(tournamentConsumers.tournaments.items())
        for tournament_id, tournament in duplicate:
            if tournament['tournamentEnded']:
                continue
            if self.user in tournament['players']:
                tournament['players'][self.user]['disconnect'] = True
                tournament['players'][self.user]['matchJoined'] = False
                tournament['players'][self.user]['match1Finished'] = True
                tournament['players'][self.user]['match2Finished'] = True
                # tournament['players'][self.user]['disconnect'] = True
                # tournament['players'][self.user]['matchJoined'] = False
                # if tournament['demiFinalsLaunched'] == True:
                #     tournament['players'][self.user]['match1Finished'] = True
                # elif tournament['finalsLauched'] == True:
                #     tournament['players'][self.user]['match2Finished'] = True
                # stopTournament = True
                # for player, playerInner in tournament['players'].items():
                #     if playerInner['disconnect'] == False:
                #         stopTournament = False
                #         break
                # if stopTournament:
                #     tournament['tournamentEnded'] = True

    # Logique pour adapter la suite du tournoi en cas de déconnexion
    async def adapt_tournament(self, tournament_id, abortFinalCall=False):
        tournament = tournamentConsumers.tournaments[tournament_id]
        tournament['adapting'] = True
        if tournament['finalsLauched']:
            type = 'final'
        else:
            type = 'game'
        clear1 = False
        clear2 = False
        nbNotJoin = 0
        tcGames = tournament['games']
        for player, playerInner in tournament['players'].items():
            if playerInner['matchJoined'] == False:
                nbNotJoin += 1
                if player in tcGames[type + '1']:
                    clear1 = True
                elif player in tcGames[type + '2']:
                    clear2 = True
        if nbNotJoin > 2:
            tournament['tournamentEnded'] = True
            if tournament['finalsLauched']:
                await channel_layer.group_send(
                    f"TOURNAMENT_{tournament_id}",
                    {
                        'type': 'sendMessage',
                        'action': 'finalsAborted',
                    }
                )
            else:
                await channel_layer.group_send(
                    f"TOURNAMENT_{tournament_id}",
                    {
                        'type': 'sendMessage',
                        'action': 'cancelTournament',
                    }
                )
                return
        if clear1:
            for player in tcGames[type + '1']:
                if type == 'game':
                    tournament['players'][player]['match1Finished'] = True
                elif type == 'final':
                    tournament['players'][player]['match2Finished'] = True
            if tournament['players'][tcGames[type + '1'][0]]['disconnect'] == True and tournament['players'][tcGames[type + '1'][1]]['disconnect'] == True:
                winner = random.choice(tcGames[type + '1'])
                tournament['players'][winner]['winner'] = True
            elif tournament['players'][tcGames[type + '1'][0]]['disconnect'] == True:
                tournament['players'][tcGames[type + '1'][1]]['winner'] = True
            elif tournament['players'][tcGames[type + '1'][1]]['disconnect'] == True:
                tournament['players'][tcGames[type + '1'][0]]['winner'] = True
            elif tournament['players'][tcGames[type + '1'][0]]['matchJoined'] == True:
                tournament['players'][tcGames[type + '1'][0]]['winner'] = True
            elif tournament['players'][tcGames[type + '1'][1]]['matchJoined'] == True:
                tournament['players'][tcGames[type + '1'][1]]['winner'] = True
            elif tournament['players'][tcGames[type + '1'][0]]['disconnect'] == False and tournament['players'][tcGames[type + '1'][1]]['disconnect'] == False:
                winner = random.choice(tcGames[type + '1'])
                tournament['players'][winner]['winner'] = True
            else:
                winner = random.choice(tcGames[type + '1'])
                tournament['players'][winner]['winner'] = True
            for player in tcGames[type + '1']:
                tournament['players'][player]['joinedMatch'] = False   
        if clear2:
            for player in tcGames[type + '2']:
                if type == 'game':
                    tournament['players'][player]['match1Finished'] = True
                elif type == 'final':
                    tournament['players'][player]['match2Finished'] = True
            if tournament['players'][tcGames[type + '2'][0]]['disconnect'] == True and tournament['players'][tcGames[type + '2'][1]]['disconnect'] == True:
                winner = random.choice(tcGames[type + '2'])
                tournament['players'][winner]['winner'] = True
            elif tournament['players'][tcGames[type + '2'][0]]['disconnect'] == True:
                tournament['players'][tcGames[type + '2'][1]]['winner'] = True
            elif tournament['players'][tcGames[type + '2'][1]]['disconnect'] == True:
                tournament['players'][tcGames[type + '2'][0]]['winner'] = True
            elif tournament['players'][tcGames[type + '2'][0]]['matchJoined'] == True:
                tournament['players'][tcGames[type + '2'][0]]['winner'] = True
            elif tournament['players'][tcGames[type + '2'][1]]['matchJoined'] == True:
                tournament['players'][tcGames[type + '2'][1]]['winner'] = True
            elif tournament['players'][tcGames[type + '2'][0]]['disconnect'] == False and tournament['players'][tcGames[type + '2'][1]]['disconnect'] == False:
                winner = random.choice(tcGames[type + '2'])
                tournament['players'][winner]['winner'] = True
            else:
                winner = random.choice(tcGames[type + '2'])
                tournament['players'][winner]['winner'] = True
            for player in tcGames[type + '2']:
                tournament['players'][player]['joinedMatch'] = False
        if abortFinalCall == False:
            if type == 'final':
                await self.endTournament({'nbT': tournament_id})
            elif type == 'game':
                await self.check_and_start_finals({'nbT': tournament_id})
        
    async def joinGame(self, data):
        nbT = data.get('nbT', None)
        if nbT is not None:
            if nbT in tournamentConsumers.tournaments:
                tc = tournamentConsumers.tournaments[nbT]
                if self.user in tc['players']:
                    tc['players'][self.user]['matchJoined'] = True

    
    async def start_countdown(self, event):
        asyncio.create_task(self.send_countdown(event))

    async def send_countdown(self, event):
        actualTime = datetime.datetime.now()
        nbT = event.get('nbT', None)
        seconds = int((tournamentConsumers.tournaments[nbT]['endOfRound'] - actualTime).total_seconds())
        allAccepted = False
        allAccepted2 = False
        if seconds <= 0:
            await self.sendMessage({'action': 'countdown', 'seconds': 0, 'details': 'you are too late for join a game'})
            return
        for i in range(seconds, 0, -1):
            try:
                if self.scope["client"]:
                    detailsValue = ""
                    if i == 1:
                        detailsValue = "Your opponent left or dont join, wait for the next or for the results"
                        if nbT in tournamentConsumers.tournaments:
                            if self.user in tournamentConsumers.tournaments[nbT]['players']:
                                if tournamentConsumers.tournaments[nbT]['players'][self.user]['matchJoined'] == False:
                                    detailsValue = "Too late to rejoin this game, but you can wait for the next or for the results"
                    await asyncio.wait_for(self.sendMessage({
                        'action': 'countdown',
                        'seconds': i - 1,
                        'details': detailsValue
                    }), timeout=3)  # Timeout de 3 secondes
                    if nbT is not None:
                        if nbT in tournamentConsumers.tournaments:
                            tc = tournamentConsumers.tournaments[nbT]
                            if self.user in tc['players']:
                                if tc['players'][self.user]['disconnect']:
                                    break
                            if tc.get('finalsLauched', False):
                                gameToPlay1 = 'final1'
                                gameToPlay2 = 'final2'
                            else:
                                gameToPlay1 = 'game1'
                                gameToPlay2 = 'game2'
                            if self.user in tc['players']:
                                if self.user in tc['games'][gameToPlay1]:
                                    if tc['players'][tc['games'][gameToPlay1][0]]['matchJoined'] and tc['players'][tc['games'][gameToPlay1][1]]['matchJoined']:
                                        allAccepted = True
                                        break
                                elif self.user in tc['games'][gameToPlay2]:
                                    if tc['players'][tc['games'][gameToPlay2][0]]['matchJoined'] and tc['players'][tc['games'][gameToPlay2][1]]['matchJoined']:
                                        allAccepted2 = True
                                        break
                    await asyncio.sleep(1)
                else:
                    break
            except asyncio.TimeoutError:
                await self.close(1000)
                break
            except Exception as e:
                await self.close(1000)
                break
        if tc['players'][self.user]['disconnect']:
            return
        if nbT in tournamentConsumers.tournaments:
            tc = tournamentConsumers.tournaments[nbT]
        if tc.get('finalsLauched', False):
            gameToPlay1 = 'final1'
            gameToPlay2 = 'final2'
        else:
            gameToPlay1 = 'game1'
            gameToPlay2 = 'game2'
            tc['demiFinalsLaunched'] = True
        if allAccepted:
            roomName = f"TOURNAMENT_{nbT}_{tc['games'][gameToPlay1][0].id}VS{tc['games'][gameToPlay1][1].id}"
            if self.user == tc['games'][gameToPlay1][0]:
                for player in tournamentConsumers.tournaments[nbT]['games'][gameToPlay1]:
                    await channel_layer.group_send(
                        f"TOURNAMENT_PLAYER_{player.id}",
                        {
                            'type': 'sendMessage',
                            'action': 'startGame',
                            'room': roomName
                        },
                    )
        elif allAccepted2:
            roomName = f"TOURNAMENT_{nbT}_{tc['games'][gameToPlay2][0].id}VS{tc['games'][gameToPlay2][1].id}"
            if self.user == tc['games'][gameToPlay2][0]:
                for player in tournamentConsumers.tournaments[nbT]['games'][gameToPlay2]:
                    await channel_layer.group_send(
                        f"TOURNAMENT_PLAYER_{player.id}",
                        {
                            'type': 'sendMessage',
                            'action': 'startGame',
                            'room': roomName
                        },
                    )
        else:
            for player, playerInner in tc['players'].items():
                if playerInner['matchJoined'] == False:
                    if tc['adapting'] == False:
                        await self.adapt_tournament(nbT)
                    else:
                        if tc['finalsLauched'] == False:
                            await self.sendMessage({'action': 'waitingNextMatch'})
                    break
    

    async def check_and_start_finals(self, event):
        nbT = event['nbT']
        tc = tournamentConsumers.tournaments[nbT]
        await self.sendMessage({'action': 'waitingNextMatch'})
        if tc.get('finalsLauched', False):
            return
        if tc['adapting'] == False:
            for player, playerInner in tc['players'].items():
                if playerInner['disconnect'] == True:
                    await self.adapt_tournament(nbT, True)
        if tc['players'][tc['games']['game1'][0]]['match1Finished'] and tc['players'][tc['games']['game1'][1]]['match1Finished'] and tc['players'][tc['games']['game2'][0]]['match1Finished'] and tc['players'][tc['games']['game2'][1]]['match1Finished']:
            tc['finalsLauched'] = True
            actualTime = datetime.datetime.now()
            futureTime = actualTime + datetime.timedelta(seconds=TIME_COUNTDOWN)
            tc['endOfRound'] = futureTime
            await self.start_finals(nbT)

    async def start_finals(self, nbT):

        for player, playerInner in tournamentConsumers.tournaments[nbT]['players'].items():
            playerInner['matchJoined'] = False
        tournamentConsumers.tournaments[nbT]['adapting'] = False
        tcGames = tournamentConsumers.tournaments[nbT]["games"]
        for player in tournamentConsumers.tournaments[nbT]['players']:
            if tournamentConsumers.tournaments[nbT]['players'][player]['winner'] == True:
                tcGames["final1"].append(player)
            else:
                tcGames["final2"].append(player)
            tournamentConsumers.tournaments[nbT]['players'][player]["winner"] = False

        final1Data = [
            {'username': player.username, 'tournamentName': player.tournamentName}
            for player in tcGames['final1']
        ]
        final2Data = [
            {'username': player.username, 'tournamentName': player.tournamentName}
            for player in tcGames['final2']
        ]
        await channel_layer.group_send(
            f"TOURNAMENT_{nbT}",
            {
                'type': 'sendMessage',
                'action': 'tournamentUpdate',
                'final1': final1Data,
                'final2': final2Data
            }
        )
        for player in tournamentConsumers.tournaments[nbT]['games']['final1']:
                await channel_layer.group_send(
                    f"TOURNAMENT_PLAYER_{player.id}",
                    {
                        'type': 'sendMessage',
                        'action': 'joinMatch',
                        'game': 'final1',
                        'nbT': nbT
                    }
                )
        for player in tournamentConsumers.tournaments[nbT]['games']['final2']:
                await channel_layer.group_send(
                    f"TOURNAMENT_PLAYER_{player.id}",
                    {
                        'type': 'sendMessage',
                        'action': 'joinMatch',
                        'game': 'final2',
                        'nbT': nbT,
                    }
                )
        await channel_layer.group_send(
                f"TOURNAMENT_{nbT}",
                {
                    'type': 'start_countdown',
                    'nbT': nbT,
                }
            )

    async def endTournament(self, event):
        nbT = event['nbT']
        tc = tournamentConsumers.tournaments[nbT]
        await self.sendMessage({'action': 'waitingForTheResult'})
        if tc.get('finalsEnded', False):
            return
        if tc['adapting'] == False:
            for player, playerInner in tc['players'].items():
                if playerInner['disconnect'] == True:
                    await self.adapt_tournament(nbT, True)
        if tc['players'][tc['games']['final1'][0]]['match2Finished'] and tc['players'][tc['games']['final1'][1]]['match2Finished'] and tc['players'][tc['games']['final2'][0]]['match2Finished'] and tc['players'][tc['games']['final2'][1]]['match2Finished']:
            tc['finalsEnded'] = True
            tournamentConsumers.tournamentLaunched -= 1
            first = tc['games']['final1'][0] if tc['players'][tc['games']['final1'][0]]['winner'] else tc['games']['final1'][1]
            second = tc['games']['final1'][0] if not tc['players'][tc['games']['final1'][0]]['winner'] else tc['games']['final1'][1]
            third = tc['games']['final2'][0] if tc['players'][tc['games']['final2'][0]]['winner'] else tc['games']['final2'][1]
            fourth = tc['games']['final2'][0] if not tc['players'][tc['games']['final2'][0]]['winner'] else tc['games']['final2'][1]
            tc['tournamentEnded'] = True
            await channel_layer.group_send(
                f"TOURNAMENT_{nbT}",
                {
                    'type': 'sendMessage',
                    'action': 'tournamentEnded',
                    'first': first.tournamentName,
                    'second': second.tournamentName,
                    'third': third.tournamentName,
                    'fourth': fourth.tournamentName,
                }
            )


class gameConsumers(AsyncWebsocketConsumer):
    game_states = {}
    players = {}
    history_recorded = {}
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope['user']
        gameConsumers.history_recorded[self.room_id] = False
        await self.channel_layer.group_add(
            self.room_id,
            self.channel_name
        )
        await self.accept()
        consumers.sessionIDTable[self] = self.scope['cookies']['sessionid']

        if self.room_id not in gameConsumers.game_states:
            gameConsumers.game_states[self.room_id] = {}
            gameConsumers.game_states[self.room_id] = {
                'ball_position': {'x': GAME_WIDTH / 2, 'y': GAME_HEIGHT / 2},
                'ball_velocity': {'x': BALL_SPEED, 'y': BALL_SPEED},
                'paddle_positions': {'player1': (GAME_HEIGHT / 2) - (PADDLE_HEIGHT / 2), 'player2': (GAME_HEIGHT / 2) - (PADDLE_HEIGHT / 2)},
                'scores': {'player1': 0, 'player2': 0},
                'paddle_height': PADDLE_HEIGHT,
                'paddle_width': PADDLE_WIDTH,
                'ball_size': BALL_SIZE,
                'ball_speed': BALL_SPEED,
                'paddle_speed': PADDLE_SPEED,
                'how_many': HOW_MANY,
                'gameStarting': False
            }
        if self.room_id not in gameConsumers.players:
            gameConsumers.players[self.room_id] = {}
        if len(gameConsumers.players[self.room_id]) == 0:
            self.paddle = 'player2'
        else:
            self.paddle = 'player1'

        gameConsumers.players[self.room_id][self.user] = self.paddle

        await self.send(text_data=json.dumps({
            'action': 'assign_paddle',
            'paddle': self.paddle
        }))
        await sync_to_async(myUser.objects.filter(id=self.user.id).update)(is_playing=True)
        if len(gameConsumers.players[self.room_id]) == 2:
            await self.start_game()


    async def start_game(self):
        player1 = None
        player2 = None
        if gameConsumers.game_states[self.room_id]['gameStarting']:
            return
        gameConsumers.game_states[self.room_id]['gameStarting'] = True
        for user, paddle in gameConsumers.players[self.room_id].items():
            if paddle == 'player1':
                player1 = {
                    'username': user.username,
                    'tournamentName': user.tournamentName
                }
            elif paddle == 'player2':
                player2 = {
                    'username': user.username,
                    'tournamentName': user.tournamentName
                }
        await self.channel_layer.group_send(
            self.room_id,
            {
                'type': 'send_countdown'
            }
        )

        await self.channel_layer.group_send(
            self.room_id,
            {
                'type': 'send_game_start',
                'message': 'Game started',
                'game_state': gameConsumers.game_states[self.room_id],
                'player1': player1,
                'player2': player2
            }
        )

    async def send_countdown(self, event):
        seconds = 3
        for i in range(seconds, 0, -1):
            await self.send(text_data=json.dumps({
                    'action': 'countdown',
                    'seconds': i,
                }))
            await asyncio.sleep(1)

    async def send_game_start(self, event):
        if self.room_id.startswith('TOURNAMENT'):
            await self.send(text_data=json.dumps({
                'action': 'game_start',
                'message': event['message'],
                'game_state': event['game_state'],
                'player1': event['player1'],
                'player2': event['player2'],
                'player1tournamentName': event['player1']['tournamentName'],
                'player2tournamentName': event['player2']['tournamentName'],
            }))
        else:
            await self.send(text_data=json.dumps({
                'action': 'game_start',
                'message': event['message'],
                'game_state': event['game_state'],
                'player1': event['player1'],
                'player2': event['player2'],
                'player1tournamentName': event['player1']['username'],
                'player2tournamentName': event['player2']['username'],
            }))
        asyncio.create_task(self.game_loop())
    
    async def game_loop(self):
        while self.room_id in gameConsumers.game_states:
            await self.update_ball_position()
            await asyncio.sleep(1 / 60)
            if self.room_id in gameConsumers.game_states:
                await self.channel_layer.group_send(
                    self.room_id,
                    {
                        'type': 'game_state_update',
                        'game_state': gameConsumers.game_states[self.room_id]
                    }
                )

    async def game_state_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'game_state': event['game_state']
        }))

    async def update_ball_position(self):
        ball_position = gameConsumers.game_states[self.room_id]['ball_position']
        ball_velocity = gameConsumers.game_states[self.room_id]['ball_velocity']
        how_many = gameConsumers.game_states[self.room_id].get('how_many', 0)
        paddle_speed = gameConsumers.game_states[self.room_id].get('paddle_speed', PADDLE_SPEED)
        ball_speed = gameConsumers.game_states[self.room_id].get('ball_speed', BALL_SPEED)
        gameState = gameConsumers.game_states[self.room_id]
        

        ball_position['x'] += ball_velocity['x']
        ball_position['y'] += ball_velocity['y']
        # Vérifiez les collisions avec les paddles
        if ball_position['x'] <= PADDLE_WIDTH + (BALL_SIZE * 2):
            if gameConsumers.game_states[self.room_id]['paddle_positions']['player1'] <= ball_position['y'] <= gameConsumers.game_states[self.room_id]['paddle_positions']['player1'] + PADDLE_HEIGHT:
                ball_velocity['x'] = -ball_velocity['x']
                if how_many == 0:
                    # Rétablir la vitesse normale de la balle
                    ball_velocity['x'] = ball_speed if ball_velocity['x'] > 0 else -ball_speed
                    ball_velocity['y'] = ball_speed if ball_velocity['y'] > 0 else -ball_speed 
                gameState["how_many"] += 1
                if how_many == 6:
                    ball_velocity['x'] = ball_speed * 1.25 if ball_velocity['x'] > 0 else -ball_speed * 1.25
                    ball_velocity['y'] = ball_speed * 1.25 if ball_velocity['y'] > 0 else -ball_speed * 1.25
                if how_many == 7:
                    gameState['ball_speed'] = ball_speed * 1.25
                    gameState["paddle_speed"] = paddle_speed * 1.25
                    gameState["how_many"] = 0     
            else:
                gameConsumers.game_states[self.room_id]['scores']['player2'] += 1
                await self.check_winner('player2')
                await self.reset_ball('player1')
        elif ball_position['x'] >= GAME_WIDTH - PADDLE_WIDTH - (BALL_SIZE * 2):
            if gameConsumers.game_states[self.room_id]['paddle_positions']['player2'] <= ball_position['y'] <= gameConsumers.game_states[self.room_id]['paddle_positions']['player2'] + PADDLE_HEIGHT:
                ball_velocity['x'] = -ball_velocity['x']
                if how_many == 0:
                    # Rétablir la vitesse normale de la balle
                    ball_velocity['x'] = ball_speed if ball_velocity['x'] > 0 else -ball_speed
                    ball_velocity['y'] = ball_speed if ball_velocity['y'] > 0 else -ball_speed
                gameState["how_many"] += 1
                if how_many == 6:
                    ball_velocity['x'] = ball_speed * 1.25 if ball_velocity['x'] > 0 else -ball_speed * 1.25
                    ball_velocity['y'] = ball_speed * 1.25 if ball_velocity['y'] > 0 else -ball_speed * 1.25
                if how_many == 7:
                    gameState['how_many'] = 0
                    gameState['ball_speed'] = ball_speed * 1.25
                    gameState['paddle_speed'] = paddle_speed * 1.25
            else:
                gameConsumers.game_states[self.room_id]['scores']['player1'] += 1
                await self.check_winner('player1')
                await self.reset_ball('player2')
        # Vérifiez les collisions avec le haut et le bas du canvas
        if ball_position['y'] <= 0 or ball_position['y'] >= GAME_HEIGHT:
            ball_velocity['y'] = -ball_velocity['y']


    async def check_winner(self, player):
        global ORIGINAL_BALL_SPEED
        global ORIGINAL_PADDLE_SPEED
        global NB_POINTS_TO_WIN
        game_state = gameConsumers.game_states[self.room_id]

        if game_state['scores'][player] >= NB_POINTS_TO_WIN:
            game_state['ball_speed'] = ORIGINAL_BALL_SPEED
            game_state['paddle_speed'] = ORIGINAL_PADDLE_SPEED
            winner = player
            loser = 'player1' if player == 'player2' else 'player2'
            asyncio.create_task(self.end_game(winner, loser))

    async def reset_ball(self, scored_on_player):
    # Générer une position y aléatoire pour la balle sauf haut/bas de l'ecran
        gameConsumers.game_states[self.room_id]['ball_speed'] = ORIGINAL_BALL_SPEED
        upper_bound = GAME_HEIGHT // 3
        lower_bound = 2 * GAME_HEIGHT // 3
        random_y = random.randint(upper_bound, lower_bound)
        gameConsumers.game_states[self.room_id]['ball_position'] = {'x': GAME_WIDTH // 2, 'y': random_y}
        
        # Générer une vitesse y aléatoire pour la balle à la moitié de BALL_SPEED
        random_y_velocity = random.choice([-BALL_SPEED / 2, BALL_SPEED / 2 - (BALL_SPEED / 4)])
        
        # Si le joueur 1 a encaissé un point, la balle va vers la droite (joueur 2)
        if scored_on_player == 'player1':
            gameConsumers.game_states[self.room_id]['ball_velocity'] = {'x': BALL_SPEED / 2, 'y': random_y_velocity}
            gameConsumers.game_states[self.room_id]['how_many'] = 0
        # Si le joueur 2 a encaissé un point, la balle va vers la gauche (joueur 1)
        else:
            gameConsumers.game_states[self.room_id]['ball_velocity'] = {'x': -BALL_SPEED / 2, 'y': random_y_velocity}
            gameConsumers.game_states[self.room_id]['how_many'] = 0



    async def end_game(self, winner=None, loser=None, why=None):
        room_id = self.room_id
        if room_id is None:
            for key, value in gameConsumers.game_states.items():
                if key.includes(self.id):
                    room_id = key
        if winner is None:
            if self.paddle == 'player1':
                winner = 'player2'
                loser = 'player1'
            else:
                winner = 'player1'
                loser = 'player2'
        for user, paddle in gameConsumers.players[self.room_id].items():
            if paddle == winner:
                WinName  = user
            elif paddle == loser:
                loseName = user
        scoreWinner = gameConsumers.game_states[room_id]['scores'][winner]
        scoreLoser = gameConsumers.game_states[room_id]['scores'][loser]
        if gameConsumers.history_recorded[self.room_id] == False:
            gameConsumers.history_recorded[self.room_id] = True
            if room_id.startswith("TOURNAMENT"):
                await sync_to_async(History.objects.create)(winner=WinName, looser=loseName, scoreW=scoreWinner, scoreL=scoreLoser, game='Pong', mode='Tournament')
            else:
                await sync_to_async(History.objects.create)(winner=WinName, looser=loseName, scoreW=scoreWinner, scoreL=scoreLoser, game='Pong', mode='Remote')
        await self.channel_layer.group_send(
            self.room_id,
            {
                'type': 'game_end',
                'winner': winner,
                'loser': loser,
                'why': why,
                'winId': WinName.id,
                'loseId': loseName.id,
            }
        )
        await self.channel_layer.group_discard(
            self.room_id,
            self.channel_name
        )

    async def game_end(self, event):
        winner = event['winner']
        loser = event['loser']
        winName = await sync_to_async(myUser.objects.get)(id=event['winId'])
        why = event['why']
        await self.send(text_data=json.dumps({
            'type': 'game_end',
            'action': 'game_end',
            'winner': winner,
            'loser': loser,
            'why': why
        }))
        room_id = self.room_id
        await self.close()
        if self in consumers.sessionIDTable:
            consumers.sessionIDTable.pop(self)
        if not room_id.startswith("TOURNAMENT"):
            self.user.is_playing = False
            await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
        if room_id in gameConsumers.players:
            del gameConsumers.players[room_id]
        if room_id in gameConsumers.game_states:
            del gameConsumers.game_states[room_id]
        if room_id.startswith("TOURNAMENT"):
            tournamentInfo = room_id.split("_")
            nbT = int(tournamentInfo[1])
            if nbT in tournamentConsumers.tournaments:
                tc = tournamentConsumers.tournaments[nbT]
                if self.user in tc['players']:
                    if tc['finalsLauched'] == True:
                        if self.user in tc['games']['final1']:
                            if self.user == tc['games']['final1'][0]:
                                secondPlayer = tc['games']['final1'][1]
                            else:
                                secondPlayer = tc['games']['final1'][0]
                        if self.user in tc['games']['final2']:
                            if self.user == tc['games']['final2'][0]:
                                secondPlayer = tc['games']['final2'][1]
                            else:
                                secondPlayer = tc['games']['final2'][0]
                    if tc['players'][self.user]['match1Finished'] == False:
                        tc['players'][self.user]['match1Finished'] = True
                    elif tc['finalsLauched'] == True:
                        tc['players'][self.user]['match2Finished'] = True 
                        tc['players'][secondPlayer]['match2Finished'] = True
                    if winName == self.user:
                        tc['players'][self.user]['winner'] = True
                    else:
                        tc['players'][self.user]['winner'] = False
                    if tc['finalsLauched']:
                        type = 'endTournament'
                    else:
                        type = 'check_and_start_finals'
                    userID = self.user.id
                    if tc['players'][self.user]['disconnect']:
                        if event['loseId'] == self.user.id:
                            userID = event['winId']
                        else:
                            userID = event['loseId']
                    await self.channel_layer.group_send(
                        f"TOURNAMENT_PLAYER_{userID}",
                        {
                            'type': type,
                            'nbT': nbT,
                            'winner': winner,
                            'looser': loser,
                        }
                    )
        raise StopConsumer()


    async def disconnect(self, close_code):
        if not self.room_id.startswith("TOURNAMENT"):
            self.is_playing = False
            await sync_to_async(myUser.objects.filter(username=self.user.username).update)(is_playing=False)
        if self in consumers.sessionIDTable:
            consumers.sessionIDTable.pop(self)
        if self.room_id in gameConsumers.players:
            await self.end_game(why='disconnected')
        raise StopConsumer()
        

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action', None)
        if action == 'paddle_move':
            await self.move_paddle(data)
    
    async def move_paddle(self, data):
        move = data.get('move', None)
        if move is not None:
            if move == 'up':
                gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] -= PADDLE_SPEED
            elif move == 'down':
                gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] += PADDLE_SPEED
            if gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] < 0:
                gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] = 0
            elif gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] > GAME_HEIGHT - PADDLE_HEIGHT:
                gameConsumers.game_states[self.room_id]['paddle_positions'][self.paddle] = GAME_HEIGHT - PADDLE_HEIGHT
            await self.channel_layer.group_send(
                self.room_id,
                {
                    'type': 'game_state_update',
                    'game_state': gameConsumers.game_states[self.room_id]
                }
            )
