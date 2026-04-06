# VOIDEX CSU — Discord Bot
# Run on Railway | Python 3.11+
# pip install discord.py aiohttp

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
import asyncio
from datetime import datetime

TOKEN      = os.environ.get('DISCORD_BOT_TOKEN')
API_URL    = os.environ.get('VOIDEX_API_URL', 'https://your-render-app.onrender.com')
OWNER_PW   = os.environ.get('OWNER_PASSWORD', '')
GUILD_ID   = int(os.environ.get('DISCORD_GUILD_ID', 0)) if os.environ.get('DISCORD_GUILD_ID') else None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

# ── Helpers ──────────────────────────────
async def api_get(path):
    async with aiohttp.ClientSession() as s:
        async with s.get(f'{API_URL}{path}', timeout=aiohttp.ClientTimeout(total=10)) as r:
            return await r.json()

async def api_post(path, data, headers=None):
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f'{API_URL}{path}', json=data,
            headers=headers or {},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as r:
            return await r.json()

async def api_put(path, data, headers=None):
    async with aiohttp.ClientSession() as s:
        async with s.put(
            f'{API_URL}{path}', json=data,
            headers=headers or {},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as r:
            return await r.json()

def owner_headers():
    return {'x-owner-password': OWNER_PW}

def red_embed(title, desc=''):
    e = discord.Embed(title=title, description=desc, color=0xdc2626)
    e.set_footer(text='Voidex CSU Bot')
    return e

def green_embed(title, desc=''):
    e = discord.Embed(title=title, description=desc, color=0x4ade80)
    e.set_footer(text='Voidex CSU Bot')
    return e

# ── Bot Ready ─────────────────────────────
@bot.event
async def on_ready():
    print(f'[BOT] Logged in as {bot.user} ({bot.user.id})')
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f'[BOT] Synced to guild {GUILD_ID}')
        else:
            await tree.sync()
            print('[BOT] Synced globally')
    except Exception as e:
        print(f'[BOT] Sync error: {e}')
    keepalive.start()

# ── Keepalive ─────────────────────────────
@tasks.loop(minutes=10)
async def keepalive():
    try:
        await api_get('/api/status')
        print('[BOT] Keepalive ping sent')
    except:
        pass

# ══════════════════════════════════════════
#  /ping
# ══════════════════════════════════════════
@tree.command(name='ping', description='Check bot and server status')
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    start = datetime.utcnow()
    try:
        data = await api_get('/api/status')
        ms   = int((datetime.utcnow() - start).total_seconds() * 1000)
        e = discord.Embed(title='🏓 Pong!', color=0x4ade80)
        e.add_field(name='Bot Latency',    value=f'`{round(bot.latency*1000)}ms`', inline=True)
        e.add_field(name='API Latency',    value=f'`{ms}ms`',                      inline=True)
        e.add_field(name='Server Status',  value='`🟢 ONLINE`',                    inline=True)
        e.add_field(name='Version',        value=f'`v{data.get("version","?")}`',  inline=True)
        e.add_field(name='Total Loggers',  value=f'`{data.get("clans",0)}`',       inline=True)
        e.add_field(name='Secrets Logged', value=f'`{data.get("hatches",0)}`',     inline=True)
        e.add_field(name='Uptime',         value=f'`{data.get("uptime",0)}s`',     inline=True)
        e.set_footer(text='Voidex CSU Bot')
        await interaction.followup.send(embed=e)
    except Exception as ex:
        e = red_embed('❌ API Unreachable', str(ex))
        await interaction.followup.send(embed=e)

# ══════════════════════════════════════════
#  /leaderboard
# ══════════════════════════════════════════
@tree.command(name='leaderboard', description='View the Secret hatch leaderboard')
@app_commands.describe(type='clans or players')
@app_commands.choices(type=[
    app_commands.Choice(name='Clans',   value='clans'),
    app_commands.Choice(name='Players', value='players'),
])
async def leaderboard(interaction: discord.Interaction, type: str = 'clans'):
    await interaction.response.defer()
    try:
        if type == 'clans':
            data = await api_get('/api/leaderboard')
            e = discord.Embed(
                title='🏆 Clan Leaderboard',
                description='Top clans by Secret hatches',
                color=0xdc2626
            )
            medals = ['🥇','🥈','🥉']
            lines  = []
            for i, clan in enumerate(data[:10]):
                medal = medals[i] if i < 3 else f'`#{i+1}`'
                lines.append(
                    f'{medal} **{clan["clanName"]}** — '
                    f'`{clan["hatches"]} secrets`'
                )
            e.description = '\n'.join(lines) if lines else 'No clans yet!'
            e.set_footer(text='Voidex CSU • Clan Leaderboard')

        else:
            data = await api_get('/api/leaderboard/players')
            e = discord.Embed(
                title='👤 Player Leaderboard',
                description='Top players by Secret hatches',
                color=0xdc2626
            )
            medals = ['🥇','🥈','🥉']
            lines  = []
            for i, p in enumerate(data[:10]):
                medal = medals[i] if i < 3 else f'`#{i+1}`'
                lines.append(
                    f'{medal} **{p["player"]}** — '
                    f'`{p["hatches"]} secrets` • Fav: {p["favPet"]}'
                )
            e.description = '\n'.join(lines) if lines else 'No players yet!'
            e.set_footer(text='Voidex CSU • Player Leaderboard')

        await interaction.followup.send(embed=e)
    except Exception as ex:
        await interaction.followup.send(embed=red_embed('❌ Error', str(ex)))

# ══════════════════════════════════════════
#  /stats
# ══════════════════════════════════════════
@tree.command(name='stats', description='View stats for a specific clan')
@app_commands.describe(clan='Clan name to look up')
async def stats(interaction: discord.Interaction, clan: str):
    await interaction.response.defer()
    try:
        data = await api_get('/api/leaderboard')
        found = next(
            (c for c in data if c['clanName'].lower() == clan.lower()),
            None
        )
        if not found:
            await interaction.followup.send(
                embed=red_embed('❌ Not Found', f'No clan named `{clan}` on the leaderboard.')
            )
            return
        e = discord.Embed(
            title=f'📊 {found["clanName"]}',
            color=0xdc2626
        )
        e.add_field(name='⭐ Secrets', value=f'`{found["hatches"]}`', inline=True)
        e.add_field(name='📅 Created', value=f'`{found.get("created","?")[:10]}`', inline=True)
        e.set_footer(text='Voidex CSU Bot')
        await interaction.followup.send(embed=e)
    except Exception as ex:
        await interaction.followup.send(embed=red_embed('❌ Error', str(ex)))

# ══════════════════════════════════════════
#  /announce  (owner only)
# ══════════════════════════════════════════
@tree.command(name='announce', description='[OWNER] Broadcast a message to all clan webhooks')
@app_commands.describe(
    message='Message to broadcast',
    title='Optional title',
)
async def announce(
    interaction: discord.Interaction,
    message: str,
    title: str = 'Announcement'
):
    await interaction.response.defer(ephemeral=True)
    if not OWNER_PW:
        await interaction.followup.send('❌ OWNER_PASSWORD not set on bot.', ephemeral=True)
        return
    try:
        res = await api_post(
            '/api/owner/broadcast',
            {'message': message, 'title': title},
            headers=owner_headers()
        )
        if res.get('success'):
            await interaction.followup.send(
                f'✅ Broadcast sent to **{res.get("count",0)}** clan(s).',
                ephemeral=True
            )
        else:
            await interaction.followup.send(f'❌ {res.get("error","Failed")}', ephemeral=True)
    except Exception as ex:
        await interaction.followup.send(f'❌ {ex}', ephemeral=True)

# ══════════════════════════════════════════
#  /clanlist  (owner only)
# ══════════════════════════════════════════
@tree.command(name='clanlist', description='[OWNER] List all registered clans')
async def clanlist(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        data  = await api_get('/api/leaderboard')
        lines = []
        for i, c in enumerate(data):
            status = '🚫' if c.get('banned') else '✅'
            lines.append(f'{status} `#{i+1}` **{c["clanName"]}** — {c["hatches"]} secrets')
        e = discord.Embed(
            title=f'📋 All Clans ({len(data)})',
            description='\n'.join(lines) or 'No clans',
            color=0xdc2626
        )
        e.set_footer(text='Voidex CSU Bot')
        await interaction.followup.send(embed=e, ephemeral=True)
    except Exception as ex:
        await interaction.followup.send(f'❌ {ex}', ephemeral=True)

# ══════════════════════════════════════════
#  /customize
# ══════════════════════════════════════════
@tree.command(name='customize', description='Get a link to customize your clan webhook embed')
async def customize(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    e = discord.Embed(
        title='🎨 Customize Your Webhook',
        description=(
            f'Visit the dashboard to customize your embed:\n\n'
            f'**[{API_URL}/]({API_URL})**\n\n'
            '1. Go to **My Logger**\n'
            '2. Login with your clan name + password\n'
            '3. Click **🎨 Webhook** to open the builder\n'
            '4. Customize colors, text, fields, images\n'
            '5. Hit **💾 Save** when done'
        ),
        color=0xdc2626
    )
    e.set_footer(text='Voidex CSU Bot')
    await interaction.followup.send(embed=e, ephemeral=True)

# ══════════════════════════════════════════
#  /hatch  (manual log — owner only)
# ══════════════════════════════════════════
@tree.command(name='hatch', description='[OWNER] Manually log a secret hatch')
@app_commands.describe(
    player='Roblox username',
    pet='Pet name',
    scope='SERVER or GLOBAL'
)
@app_commands.choices(scope=[
    app_commands.Choice(name='SERVER', value='SERVER'),
    app_commands.Choice(name='GLOBAL', value='GLOBAL'),
])
async def hatch(
    interaction: discord.Interaction,
    player: str,
    pet: str,
    scope: str = 'SERVER'
):
    await interaction.response.defer(ephemeral=True)
    try:
        res = await api_post('/api/hatch', {
            'player':   player,
            'pet':      pet,
            'rarity':   'Secret',
            'scope':    scope,
            'reporter': f'discord_bot:{interaction.user.id}',
        })
        if res.get('success'):
            notified = res.get('notified', [])
            await interaction.followup.send(
                f'✅ Logged **{pet}** for **{player}** '
                f'({scope}) — notified {len(notified)} clan(s).',
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f'❌ {res.get("error","Failed")}',
                ephemeral=True
            )
    except Exception as ex:
        await interaction.followup.send(f'❌ {ex}', ephemeral=True)

# ══════════════════════════════════════════
#  /ban  (owner only)
# ══════════════════════════════════════════
@tree.command(name='ban', description='[OWNER] Toggle ban on a clan')
@app_commands.describe(clan='Clan key (uppercase, underscores)')
async def ban(interaction: discord.Interaction, clan: str):
    await interaction.response.defer(ephemeral=True)
    try:
        res = await api_put(
            f'/api/owner/clan/{clan}/ban',
            {},
            headers=owner_headers()
        )
        if res.get('success'):
            state = '🚫 Banned' if res.get('banned') else '✅ Unbanned'
            await interaction.followup.send(f'{state} clan `{clan}`', ephemeral=True)
        else:
            await interaction.followup.send(f'❌ {res.get("error","Failed")}', ephemeral=True)
    except Exception as ex:
        await interaction.followup.send(f'❌ {ex}', ephemeral=True)

# ══════════════════════════════════════════
#  /setscore  (owner only)
# ══════════════════════════════════════════
@tree.command(name='setscore', description='[OWNER] Set a clan secret count')
@app_commands.describe(clan='Clan key', score='New score')
async def setscore(interaction: discord.Interaction, clan: str, score: int):
    await interaction.response.defer(ephemeral=True)
    try:
        res = await api_put(
            f'/api/owner/clan/{clan}/setscore',
            {'score': score},
            headers=owner_headers()
        )
        if res.get('success'):
            await interaction.followup.send(
                f'✅ Score for `{clan}` set to `{score}`',
                ephemeral=True
            )
        else:
            await interaction.followup.send(f'❌ {res.get("error","Failed")}', ephemeral=True)
    except Exception as ex:
        await interaction.followup.send(f'❌ {ex}', ephemeral=True)

# ══════════════════════════════════════════
#  /help
# ══════════════════════════════════════════
@tree.command(name='help', description='List all bot commands')
async def help_cmd(interaction: discord.Interaction):
    e = discord.Embed(
        title='📖 Voidex CSU Bot Commands',
        color=0xdc2626
    )
    cmds = [
        ('/ping',        'Check bot and server status'),
        ('/leaderboard', 'View clan or player leaderboard'),
        ('/stats',       'View a specific clan\'s stats'),
        ('/customize',   'Get link to webhook embed builder'),
        ('/help',        'Show this message'),
        ('── Owner ──',  ''),
        ('/announce',    'Broadcast to all clan webhooks'),
        ('/clanlist',    'List all registered clans'),
        ('/hatch',       'Manually log a secret hatch'),
        ('/ban',         'Toggle ban on a clan'),
        ('/setscore',    'Set a clan\'s secret count'),
    ]
    desc = ''
    for name, desc_txt in cmds:
        if name.startswith('──'):
            desc += f'\n**{name}**\n'
        else:
            desc += f'`{name}` — {desc_txt}\n'
    e.description = desc
    e.set_footer(text='Voidex CSU Bot • Made by Aousisgood1')
    await interaction.response.send_message(embed=e, ephemeral=True)

# ── Run ───────────────────────────────────
if __name__ == '__main__':
    if not TOKEN:
        print('ERROR: DISCORD_BOT_TOKEN not set')
    else:
        bot.run(TOKEN)
