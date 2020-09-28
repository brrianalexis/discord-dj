import math
import re
from discord.ext import commands
import lavalink
from discord import utils
from discord import Embed

time_rx = re.compile('[0-9]+')


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.music = lavalink.Client(self.bot.user.id)
        self.bot.music.add_node(
            'localhost', 8000, 'estonoesporno', 'br', 'music-node')
        self.bot.add_listener(
            self.bot.music.voice_update_handler, 'on_socket_response')
        self.bot.music.add_event_hook(self.track_hook)

    # *     works
    @commands.command(name='join')
    async def join(self, ctx):
        member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
        if member is not None and member.voice is not None:
            vc = member.voice.channel
            player = self.bot.music.player_manager.create(
                ctx.guild.id, endpoint=str(ctx.guild.region))
            if not player.is_connected:
                player.store('channel', ctx.channel.id)
                await self.connect_to(ctx.guild.id, str(vc.id))

    # *     works
    @commands.command(name='nv')
    async def disconnect(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            return await ctx.send('No estoy conectado, mostro')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('No me podés desconectar si no estás en mi canal, gil')

        player.queue.clear()

        await player.stop()

        await self.connect_to(ctx.guild.id, None)
        await ctx.send('Nv 👋🏻')

    # *     works
    @commands.command(name='play')
    async def play(self, ctx, *, query):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            # ? acá se puede jugar con en qué plataforma buscar. ver application.yml para las otras plataformas que soporta Lavalink
            query = f'ytsearch:{query}'
            results = await player.node.get_tracks(query)
            tracks = results['tracks'][0:10]
            i = 0
            query_result = ''
            for track in tracks:
                i = i + 1
                query_result = query_result + \
                    f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
            embed = Embed()
            embed.description = query_result

            await ctx.channel.send(embed=embed)

            def check(m):
                return m.author.id == ctx.author.id

            response = await self.bot.wait_for('message', check=check)
            track = tracks[int(response.content) - 1]

            player.add(requester=ctx.author.id, track=track)
            if not player.is_playing:
                await player.play()

        except Exception as error:
            print(error)

    # *     works
    @commands.command(name='vol')
    async def volume(self, ctx, volume: int = None):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not volume:
            return await ctx.send(f'🔊 | {player.volume}%')

        await player.set_volume(volume)
        await ctx.send(f'🔊 | Cambié el volumen a {player.volume}%')

    # *     works
    @commands.command(name='stop')
    async def stop(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Parado')

    # *     works
    @commands.command(name='pause')
    async def pause(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        if player.paused:
            await player.set_pause(False)
            await ctx.send('⏯ | Resumido')
        else:
            await player.set_pause(True)
            await ctx.send('⏸ | Pausado')

    # *     works
    @commands.command(name='skip')
    async def skip(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        await ctx.send('⏭ | Salteado')
        await player.skip()

    # *     works
    @commands.command(name='queue')
    async def queue(self, ctx, page: int = 1):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('No hay nada en la queue 😟')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''

        for i, track in enumerate(player.queue[start:end], start=start):
            queue_list += f'`{i+1})` [**{track.title}**]({track.uri})\n'

        embed = Embed(colour=ctx.guild.me.top_role.colour,
                      description=f'**{len(player.queue)} tracks**\n\n{queue_list}')
        embed.set_footer(text=f'Página {page}/{pages}')
        await ctx.send(embed=embed)

    # *     works
    @commands.command(name='now')
    async def now(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)
        song = 'Nothing'

        print(dir(lavalink))

        if player.current:
            position = lavalink.format_time(player.position)
            if player.current.stream:
                duration = 'LIVE'
            else:
                duration = lavalink.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({position}/{duration})'

        embed = Embed(colour=ctx.guild.me.top_role.colour,
                      title='Reproduciendo', description=song)
        await ctx.send(embed=embed)

    # !     debug
    @commands.command(name='seek')
    async def seek(self, ctx, time):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        position = '+'
        if time.startsWith('-'):
            position = '-'

        seconds = time_rx.search(time)

        if not seconds:
            return await ctx.send('Tenés que especificar la cantidad de segundos a saltear 🤡')

        seconds = int(seconds.group()) * 1000

        if position == '-':
            seconds = seconds * -1

        track_time = player.position + seconds

        await player.seek(track_time)

        await ctx.send(f'Moví el track a **{lavalink.format_time(track_time)}**')

    # *     works
    @commands.command(name='remove')
    async def remove(self, ctx, index: int):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('No hay nada en la queue 😟')

        if index > len(player.queue) or index < 1:
            return await ctx.send('El índice tiene que ser >= a 1 y <= al largo de la queue!')

        index = index - 1
        removed = player.queue.pop(index)

        await ctx.send('Quité **' + removed.title + '** de la queue')

    # *     works
    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        player.shuffle = not player.shuffle

        await ctx.send('🔀 | Shuffle ' + ('activado' if player.shuffle else 'desactivado'))

    # *     works
    @commands.command(name='repeat')
    async def repeat(self, ctx):
        player = self.bot.music.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('No estoy reproduciendo nada 😶')

        player.repeat = not player.repeat

        await ctx.send('🔁 | Repeat ' + ('activado' if player.repeat else 'desactivado'))

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)


def setup(bot):
    bot.add_cog(MusicCog(bot))
