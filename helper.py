import discord
from discord.ext import commands
import random
import asyncio
from math import floor
import time


async def maxweapon(ctx, typeweapon, cost, stat1, stat2, stat3):
    yellow = 0xffd700
    red = 0x8b0000
    gray = 0x808080
    blue = 0x0000ff
    purple = 0x800080
    cyan = 0x00ffff
    orange = 0xff8c00
    if typeweapon:
        if typeweapon.lower() == 'bow':
            if cost and (220 >= cost >= 120):
                statcost = ((220 - cost) / (220 - 120)) * 100
                if stat1 and (110.0 <= stat1 <= 160.0):
                    statstat1 = ((stat1 - 110) / (160 - 110)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521367695364.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'sword':
            if cost and (250 >= cost >= 150):
                statcost = ((250 - cost) / (250 - 150)) * 100
                if stat1 and (55.0 >= stat1 >= 35.0):
                    statstat1 = ((stat1 - 35) / (55 - 35)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521271095299.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'shield' or typeweapon.lower() == 'aegis':
            if cost and (250 >= cost >= 150):
                statcost = ((250 - cost) / (250 - 150)) * 100
                if stat1 and (50.0 >= stat1 >= 30.0):
                    statstat1 = ((stat1 - 30) / (50 - 30)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521648713767.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'estaff':
            if cost and (200 >= cost >= 100):
                statcost = ((200 - cost) / (200 - 100)) * 100
                if stat1 and (65.0 >= stat1 >= 35.0):
                    statstat1 = ((stat1 - 35) / (65 - 35)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521736663051.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'vstaff':
            if cost and (200 >= cost >= 100):
                statcost = ((200 - cost) / (200 - 100)) * 100
                if stat1 and (45.0 >= stat1 >= 25.0):
                    statstat1 = ((stat1 - 25) / (45 - 25)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521371627561.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'hstaff':
            if cost and (200 >= cost >= 125):
                statcost = ((200 - cost) / (200 - 125)) * 100
                if stat1 and (150.0 >= stat1 >= 100.0):
                    statstat1 = ((stat1 - 100) / (150 - 100)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/594613521950441481.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'axe':
            if cost and (220 >= cost >= 120):
                statcost = ((220 - cost) / (220 - 120)) * 100
                if stat1 and (80.0 >= stat1 >= 50.0):
                    statstat1 = ((stat1 - 50) / (80 - 50)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/622681663289294850.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'rstaff':
            if cost and (400 >= cost >= 300):
                statcost = ((400 - cost) / (400 - 300)) * 100
                if stat1 and (80.0 >= stat1 >= 50.0):
                    statstat1 = ((stat1 - 50) / (80 - 50)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/622681759880052757.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'scepter':
            if cost and (200 >= cost >= 125):
                statcost = ((200 - cost) / (200 - 125)) * 100
                if stat1 and (70.0 >= stat1 >= 40.0):
                    statstat1 = ((stat1 - 40) / (70 - 40)) * 100
                    maxstat = (statcost + statstat1 + 100) / 3
                    if maxstat == 100:
                        quality = 'Fabled'
                        color = cyan
                        emojis = '<a:Fabled:760029464292884503>'
                    elif maxstat >= 95:
                        quality = 'Legendary'
                        color = yellow
                        emojis = '<a:Legendary:760029450913316874>'
                    elif maxstat >= 81:
                        quality = 'Mythic'
                        color = purple
                        emojis = '<:mythic:760029618732007424>'
                    elif maxstat >= 61:
                        quality = 'Epic'
                        color = blue
                        emojis = '<:epic:760029607755513886>'
                    elif maxstat >= 41:
                        quality = 'Rare'
                        color = orange
                        emojis = '<:rare:760029595365539850>'
                    elif maxstat >= 21:
                        quality = 'Uncommon'
                        color = gray
                        emojis = '<:uncommon:760029577635692545> '
                    else:
                        quality = 'Common'
                        color = red
                        emojis = '<:common:760029564649865267>'
                    link = 'https://cdn.discordapp.com/emojis/622681759330598913.png?v=1'
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'dagger':
            if cost and (200 >= cost >= 100):
                statcost = ((200 - cost) / (200 - 100)) * 100
                if stat1 and (100.0 >= stat1 >= 70.0):
                    statstat1 = ((stat1 - 70) / (100 - 70)) * 100
                    if stat2 and (65.0 >= stat2 >= 40.0):
                        statstat2 = ((stat2 - 40) / (65 - 40)) * 100
                        maxstat = (statcost + statstat1 + statstat2 + 100) / 4
                        if maxstat == 100:
                            quality = 'Fabled'
                            color = cyan
                            emojis = '<a:Fabled:760029464292884503>'
                        elif maxstat >= 95:
                            quality = 'Legendary'
                            color = yellow
                            emojis = '<a:Legendary:760029450913316874>'
                        elif maxstat >= 81:
                            quality = 'Mythic'
                            color = purple
                            emojis = '<:mythic:760029618732007424>'
                        elif maxstat >= 61:
                            quality = 'Epic'
                            color = blue
                            emojis = '<:epic:760029607755513886>'
                        elif maxstat >= 41:
                            quality = 'Rare'
                            color = orange
                            emojis = '<:rare:760029595365539850>'
                        elif maxstat >= 21:
                            quality = 'Uncommon'
                            color = gray
                            emojis = '<:uncommon:760029577635692545> '
                        else:
                            quality = 'Common'
                            color = red
                            emojis = '<:common:760029564649865267>'
                        link = 'https://cdn.discordapp.com/emojis/594613521543856128.png?v=1'
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'scythe':
            if cost and (200 >= cost >= 100):
                statcost = ((200 - cost) / (200 - 100)) * 100
                if stat1 and (100.0 >= stat1 >= 70.0):
                    statstat1 = ((stat1 - 70) / (100 - 70)) * 100
                    if stat2 and (60.0 >= stat2 >= 30.0):
                        statstat2 = ((stat2 - 30) / (60 - 30)) * 100
                        maxstat = (statcost + statstat1 + statstat2 + 100) / 4
                        if maxstat == 100:
                            quality = 'Fabled'
                            color = cyan
                            emojis = '<a:Fabled:760029464292884503>'
                        elif maxstat >= 95:
                            quality = 'Legendary'
                            color = yellow
                            emojis = '<a:Legendary:760029450913316874>'
                        elif maxstat >= 81:
                            quality = 'Mythic'
                            color = purple
                            emojis = '<:mythic:760029618732007424>'
                        elif maxstat >= 61:
                            quality = 'Epic'
                            color = blue
                            emojis = '<:epic:760029607755513886>'
                        elif maxstat >= 41:
                            quality = 'Rare'
                            color = orange
                            emojis = '<:rare:760029595365539850>'
                        elif maxstat >= 21:
                            quality = 'Uncommon'
                            color = gray
                            emojis = '<:uncommon:760029577635692545> '
                        else:
                            quality = 'Common'
                            color = red
                            emojis = '<:common:760029564649865267>'
                        link = 'https://cdn.discordapp.com/emojis/622681759401639936.png?v=1'
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'sstaff':
            if cost and (225 >= cost >= 125):
                statcost = ((225 - cost) / (225 - 125)) * 100
                if stat1 and (50.0 >= stat1 >= 30.0):
                    statstat1 = ((stat1 - 30) / (50 - 30)) * 100
                    if stat2 and (30.0 >= stat2 >= 20.0):
                        statstat2 = ((stat2 - 20) / (30 - 20)) * 100
                        maxstat = (statcost + statstat1 + statstat2 + 100) / 4
                        if maxstat == 100:
                            quality = 'Fabled'
                            color = cyan
                            emojis = '<a:Fabled:760029464292884503>'
                        elif maxstat >= 95:
                            quality = 'Legendary'
                            color = yellow
                            emojis = '<a:Legendary:760029450913316874>'
                        elif maxstat >= 81:
                            quality = 'Mythic'
                            color = purple
                            emojis = '<:mythic:760029618732007424>'
                        elif maxstat >= 61:
                            quality = 'Epic'
                            color = blue
                            emojis = '<:epic:760029607755513886>'
                        elif maxstat >= 41:
                            quality = 'Rare'
                            color = orange
                            emojis = '<:rare:760029595365539850>'
                        elif maxstat >= 21:
                            quality = 'Uncommon'
                            color = gray
                            emojis = '<:uncommon:760029577635692545> '
                        else:
                            quality = 'Common'
                            color = red
                            emojis = '<:common:760029564649865267>'
                        link = 'https://cdn.discordapp.com/emojis/594613521581473851.png?v=1'
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'wand':
            if cost and (250 >= cost >= 150):
                statcost = ((250 - cost) / (250 - 150)) * 100
                if stat1 and (100.0 >= stat1 >= 80.0):
                    statstat1 = ((stat1 - 80) / (100 - 80)) * 100
                    if stat2 and (40.0 >= stat2 >= 20.0):
                        statstat2 = ((stat2 - 20) / (40 - 20)) * 100
                        maxstat = (statcost + statstat1 + statstat2 + 100) / 4
                        if maxstat == 100:
                            quality = 'Fabled'
                            color = cyan
                            emojis = '<a:Fabled:760029464292884503>'
                        elif maxstat >= 95:
                            quality = 'Legendary'
                            color = yellow
                            emojis = '<a:Legendary:760029450913316874>'
                        elif maxstat >= 81:
                            quality = 'Mythic'
                            color = purple
                            emojis = '<:mythic:760029618732007424>'
                        elif maxstat >= 61:
                            quality = 'Epic'
                            color = blue
                            emojis = '<:epic:760029607755513886>'
                        elif maxstat >= 41:
                            quality = 'Rare'
                            color = orange
                            emojis = '<:rare:760029595365539850>'
                        elif maxstat >= 21:
                            quality = 'Uncommon'
                            color = gray
                            emojis = '<:uncommon:760029577635692545> '
                        else:
                            quality = 'Common'
                            color = red
                            emojis = '<:common:760029564649865267>'
                        link = 'https://cdn.discordapp.com/emojis/594613521703108631.png?v=1'
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'banner':
            if cost and (300 >= cost >= 250):
                statcost = ((300 - cost) / (300 - 250)) * 100
                if stat1 and (20.0 >= stat1 >= 10.0):
                    statstat1 = ((stat1 - 10) / (20 - 10)) * 100
                    if stat2 and (30.0 >= stat2 >= 20.0):
                        statstat2 = ((stat2 - 20) / (30 - 20)) * 100
                        if stat3 and (40.0 >= stat3 >= 30.0):
                            statstat3 = ((stat3 - 30) / (40 - 30)) * 100
                            maxstat = (statcost + statstat1 + statstat2 + statstat3 + 100) / 5
                            if maxstat == 100:
                                quality = 'Fabled'
                                color = cyan
                                emojis = '<a:Fabled:760029464292884503>'
                            elif maxstat >= 95:
                                quality = 'Legendary'
                                color = yellow
                                emojis = '<a:Legendary:760029450913316874>'
                            elif maxstat >= 81:
                                quality = 'Mythic'
                                color = purple
                                emojis = '<:mythic:760029618732007424>'
                            elif maxstat >= 61:
                                quality = 'Epic'
                                color = blue
                                emojis = '<:epic:760029607755513886>'
                            elif maxstat >= 41:
                                quality = 'Rare'
                                color = orange
                                emojis = '<:rare:760029595365539850>'
                            elif maxstat >= 21:
                                quality = 'Uncommon'
                                color = gray
                                emojis = '<:uncommon:760029577635692545> '
                            else:
                                quality = 'Common'
                                color = red
                                emojis = '<:common:760029564649865267>'
                            link = 'https://cdn.discordapp.com/emojis/622681759565479956.png?v=1'
                        else:
                            await ctx.send('Please provide stat 3 in command')
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        elif typeweapon.lower() == 'fstaff':
            if cost and (200 >= cost >= 100):
                statcost = ((200 - cost) / (200 - 100)) * 100
                if stat1 and (80.0 >= stat1 >= 60.0):
                    statstat1 = ((stat1 - 60) / (80 - 60)) * 100
                    if stat2 and (40.0 >= stat2 >= 20.0):
                        statstat2 = ((stat2 - 20) / (40 - 20)) * 100
                        if stat3 and (60.0 >= stat3 >= 40.0):
                            statstat3 = ((stat3 - 40) / (60 - 40)) * 100
                            maxstat = (statcost + statstat1 + statstat2 + statstat3 + 100) / 5
                            if maxstat == 100:
                                quality = 'Fabled'
                                color = cyan
                                emojis = '<a:Fabled:760029464292884503>'
                            elif maxstat >= 95:
                                quality = 'Legendary'
                                color = yellow
                                emojis = '<a:Legendary:760029450913316874>'
                            elif maxstat >= 81:
                                quality = 'Mythic'
                                color = purple
                                emojis = '<:mythic:760029618732007424>'
                            elif maxstat >= 61:
                                quality = 'Epic'
                                color = blue
                                emojis = '<:epic:760029607755513886>'
                            elif maxstat >= 41:
                                quality = 'Rare'
                                color = orange
                                emojis = '<:rare:760029595365539850>'
                            elif maxstat >= 21:
                                quality = 'Uncommon'
                                color = gray
                                emojis = '<:uncommon:760029577635692545> '
                            else:
                                quality = 'Common'
                                color = red
                                emojis = '<:common:760029564649865267>'
                            link = 'https://cdn.discordapp.com/emojis/594613521573216266.png?v=1'
                        else:
                            await ctx.send('Please provide stat 3 in command')
                    else:
                        await ctx.send('Please provide stat 2 in command')
                else:
                    await ctx.send('Please provide stat in command')
                    return
            else:
                await ctx.send('Please provide weapon cost in command')
                return

        else:
            await ctx.send('Please provide correct weapon type in command')
            return
    else:
        await ctx.send('Please Provide weapon type in command\n'
                       'List weapon name:\n'
                       '```Bow\n'
                       'sword\n'
                       'shield / aegis\n'
                       'axe\n'
                       'estaff\n'
                       'vstaff\n'
                       'hstaff\n'
                       'rstaff\n'
                       'scepter\n'
                       'dagger\n'
                       'sstaff\n'
                       'wand\n'
                       'banner\n'
                       'fstaff```'
                       'Ex: s!maxwstat bow 120 160')
        return
    custom_embed = discord.Embed(title='Stat', description=f'Type: **{typeweapon}**', color=color)
    custom_embed.add_field(name="Cost Quality", value=f'**{statcost}%**', inline=False)
    custom_embed.add_field(name="Stat Quality", value=f'**{statstat1}%**', inline=False)
    if stat1:
        maxignore = round((statcost + statstat1) / 2, 2)
        minstat = round((statcost + statstat1) / 3, 2)
        maxcrit = round((statcost + statstat1 + 200) / 4, 2)
        mincrit = round((statcost + statstat1) / 4, 2)
    if stat2:
        custom_embed.add_field(name="Stat 2 Quality", value=f'**{statstat2}%**', inline=False)
        maxignore = round((statcost + statstat1 + statstat2) / 3, 2)
        minstat = round((statcost + statstat1 + statstat2) / 4, 2)
        maxcrit = round((statcost + statstat1 + statstat2 + 200) / 5, 2)
        mincrit = round((statcost + statstat1 + statstat2) / 5, 2)
    if stat3:
        custom_embed.add_field(name="Stat 3 Quality", value=f'**{statstat3}%**', inline=False)
        maxignore = round((statcost + statstat1 + statstat2 + statstat3) / 4, 2)
        minstat = round((statcost + statstat1 + statstat2 + statstat3) / 5, 2)
        maxcrit = round((statcost + statstat1 + statstat2 + statstat3 + 200) / 6, 2)
        mincrit = round((statcost + statstat1 + statstat2 + statstat3) / 6, 2)

    maxstat = round(maxstat, 2)
    custom_embed.add_field(name='Max Stat', value=f'**{maxstat}%**', inline=False)
    custom_embed.add_field(name='Rarity', value=f'**{quality}** {emojis}', inline=False)
    custom_embed.add_field(name='Additional info',
                     value=f'Minimum stat: **{minstat}%**\nMax stat ignoring passive: **{maxignore}%**\nMin stat with crit: **{mincrit}%**\nMax stat with crit: **{maxcrit}%**')
    custom_embed.set_thumbnail(url=link)
    await ctx.send(embed=custom_embed)


async def visualstat(ctx, level, hp, strength, pr, wp, mag, mr):
    blue = 0x00ffff
    ehp, eatt, epr, ewp, emag, emr = '<:hp:759752326973227029>', '<:att:759752341678194708>', '<:pr:759752354467414056>', '<:wp:759752292713889833>', '<:mag:759752304080715786>', '<:mr:759752315904196618>'
    if hp == '.':
        hpstat = 500 + level * 2
    elif hp.isdigit():
        hp = int(hp)
        hpstat = 500 + hp * level * 2
    else:
        await ctx.send('Please input correct hp, use \'.\' as 1 stat ')
        return

    if strength == '.':
        strstat = 100 + level
    elif strength.isdigit():
        strength = int(strength)
        strstat = 100 + strength * level
    else:
        await ctx.send('Please input correct str, use \'.\' as 1 stat ')
        return

    if pr == '.':
        prstat = round((25 + (2 * level)) / (125 + (2 * level)) * .8 * 100)
    elif pr.isdigit():
        pr = int(pr)
        prstat = round((25 + (2 * pr * level)) / (125 + (2 * pr * level)) * .8 * 100)
    else:
        await ctx.send('Please input correct pr, use \'.\' as 1 stat ')
        return

    if wp == '.':
        wpstat = 500 + level * 2
    elif wp.isdigit():
        wp = int(wp)
        wpstat = 500 + wp * level * 2
    else:
        await ctx.send('Please input correct wp, use \'.\' as 1 stat ')
        return

    if mag == '.':
        magstat = 100 + level
    elif mag.isdigit():
        mag = int(mag)
        magstat = 100 + mag * level
    else:
        await ctx.send('Please input correct mag, use \'.\' as 1 stat ')
        return

    if mr == '.':
        mrstat = round((25 + (2 * level)) / (125 + (2 * level)) * .8 * 100)
    elif mr.isdigit():
        mr = int(mr)
        mrstat = round((25 + (2 * mr * level)) / (125 + (2 * mr * level)) * .8 * 100)
    else:
        await ctx.send('Please input correct mr, use \'.\' as 1 stat ')
        return

    if hp >= 8:
        category1 = 'Tank'
        if 3 <= wp <= 5:
            category = 'Energize'
        elif wp >= 6:
            category = 'Regen'
        else:
            category = 'Bad'
    elif strength >= 9:
        category = 'Str'
        if wp >= 3:
            category1 = 'Support'
        elif strength >= 11:
            category1 = 'Attacker'
        else:
            category1 = 'Bad'
    elif mag >= 7:
        category = 'Mag'
        if mag <= 10 and wp >= 3:
            category1 = 'Healer'
        elif mag >= 11:
            category1 = 'Attacker'
        else:
            category1 = 'Bad'
    else:
        category, category1 = '-', '-'
    custom_embed = discord.Embed(title=' Pet Stats',
                                 description=f'{ehp} `{hpstat}`  {eatt} `{strstat}`  {epr} `{prstat}%`\n'
                                             f'{ewp} `{wpstat}`  {emag} `{magstat}`  {emr} `{mrstat}%`',
                                 color=blue)
    custom_embed.add_field(name='Category', value=f'{category} {category1}', inline=False)
    await ctx.send(embed=custom_embed)


class HelperCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='maxwstat', help='Show max stat on your weapon', aliases=['wstat', 'statw', 'wcheck'])
    async def countmax(self, ctx, typeweapon: str = None, cost: int = None, stat1: float = None, stat2: float = None,
                       stat3: float = None):
        if typeweapon:
            await maxweapon(ctx, typeweapon, cost, stat1, stat2, stat3)
        else:
            async for x in ctx.message.channel.history(limit=3):
                if x.author.id == 408785106942164992:
                    embeded = x.embeds
                    for y in embeded:
                        y = y.to_dict()
                    new = y['description'].split('\n')
                    typeweapon = new[0].split('**')[2].lower()
                    cost = int(new[5].split('**')[2].split(' ')[1])
                    if not (('banner' in typeweapon) ^ ('aegis' in typeweapon)):
                        stat1 = float(new[6].split('**')[3].replace('%', ''))
                    if 'great' in typeweapon.lower():
                        typeweapon = 'sword'
                    elif 'healing' in typeweapon:
                        typeweapon = 'hstaff'
                    elif 'defender' in typeweapon:
                        typeweapon = 'aegis'
                        stat1 = float(new[8].split('**')[-2])
                    elif 'vampiric' in typeweapon:
                        typeweapon = 'vstaff'
                    elif 'energy' in typeweapon:
                        typeweapon = 'estaff'
                    elif 'poison' in typeweapon:
                        typeweapon = 'dagger'
                        stat2 = float(new[8].split('**')[3].replace('%', ''))
                    elif 'wand' in typeweapon:
                        typeweapon = 'wand'
                        stat2 = float(new[6].split('**')[-2].replace('%', ''))
                    elif 'flame' in typeweapon:
                        typeweapon = 'fstaff'
                        stat2 = float(new[8].split('**')[3].replace('%', ''))
                        stat3 = float(new[8].split('**')[-2].replace('%', ''))
                    elif 'spirit' in typeweapon:
                        typeweapon = 'sstaff'
                        stat2 = float(new[8].split('**')[-2].replace('%', ''))
                    elif 'scepter' in typeweapon:
                        typeweapon = 'scepter'
                    elif 'resurrection' in typeweapon:
                        typeweapon = 'rstaff'
                    elif 'glacial' in typeweapon:
                        typeweapon = 'axe'
                    elif 'banner' in typeweapon:
                        typeweapon = 'banner'
                        stat1 = float(new[8].split('**')[-2].replace('%', ''))
                        stat2 = float(new[9].split('**')[-2].replace('%', ''))
                        stat3 = float(new[10].split('**')[-2].replace('%', ''))
                    elif 'scythe' in typeweapon:
                        typeweapon = 'scythe'
                        stat2 = float(new[8].split('**')[-2].replace('%', ''))
                    elif 'bow' in typeweapon:
                        typeweapon = 'bow'
                    await maxweapon(ctx, typeweapon, cost, stat1, stat2, stat3)
                    return
            await ctx.reply('Please provide weapon type. '
                            'You also can do owo weapon and calling this command (detect 3 message before you)',
                            delete_after=6, author_reply=False)

    @commands.command(name='petstat', help='Visualize pet stat in certain level',
                 aliases=['statpet', 'petlevel', 'levelpet'])
    async def petstats(self, ctx, level=None, hp=None, strength=None, pr=None, wp=None, mag=None, mr=None):
        if level.isdigit():
            level = int(level)
            if hp and strength and pr and wp and mag and mr:
                await visualstat(ctx, level, hp, strength, pr, wp, mag, mr)
            elif not (hp or strength or pr or wp or mag or mr):
                async for x in ctx.message.channel.history(limit=3):
                    if x.author.id == 408785106942164992:
                        embeded = x.embeds
                        y = {}
                        for y in embeded:
                            y = y.to_dict()
                        new = y['description'].split('`')
                        if len(new) != 13:
                            return
                        hp, strength, pr, wp, mag, mr = [new[z] for z in range(1, 12, 2)]
                        await visualstat(ctx, level, hp, strength, pr, wp, mag, mr)
                        return
                    elif x.author.id == 750534176666550384:
                        embeded = x.embeds
                        y = {}
                        for y in embeded:
                            y = y.to_dict()
                        new = y['fields'][1]['value'].split('`')
                        hp, strength, pr, wp, mag, mr = [new[z] for z in range(1, 12, 2)]
                        await visualstat(ctx, level, hp, strength, pr, wp, mag, mr)
                        return
                await ctx.reply('Please input complete stat', author_reply=False)

            else:
                await ctx.reply(
                    'Please input complete stat `<level> <hp> <str> <pr> <wp> <mag> <mr>` , use \'.\' as 1 stat',
                    author_reply=False)
        else:
            await ctx.reply('Invalid argument :c', mention_author=False)

    @commands.command(name='ultralog', aliases=['ulog'])
    async def log_calculator(self, ctx):
        # if ctx.author.id in restricted:
        #     return
        async for x in ctx.message.channel.history(limit=3):
            if x.author.id != 555955826880413696:
                continue
            y = None
            embedded = x.embeds
            for y in embedded:
                y = y.to_dict()
            if 'inventory' in y['author']['name']:
                inventory_dict = y['fields'][0]['value'].split('**')
                log_data = {}
                for z in range(len(inventory_dict)):
                    if ' log' in inventory_dict[z]:
                        log_data.update({inventory_dict[z].lower(): int(
                            inventory_dict[z + 1].replace(': ', '').split('\n')[0])})
                # calculating
                solution = ''
                solution_crafter = ''
                hyper_log, mega_log, super_log, epic_log, wooden_log = [0 for value in range(5)]

                if 'hyper log' in log_data:
                    if log_data['hyper log'] >= 10:
                        solution = 'rpg craft ultra log'
                        solution_crafter = solution
                    else:
                        hyper_log = log_data['hyper log']
                if 'mega log' in log_data:
                    mega_log = log_data['mega log']
                    if not solution:
                        required_log = 10 - hyper_log
                        if mega_log >= required_log * 10:
                            solution = f'rpg craft hyper log {required_log}\n' \
                                       f'rpg craft ultra log'
                            solution_crafter = solution
                if 'super log' in log_data:
                    super_log = log_data['super log']
                    if not solution:
                        required_log = (10 - hyper_log) * 10 - mega_log
                        if super_log >= required_log * 10:
                            solution = f'rpg craft mega log {required_log}\n' \
                                       f'rpg craft hyper log all\n' \
                                       f'rpg craft ultra log'
                if 'epic log' in log_data:
                    epic_log = log_data['epic log']
                    if not solution:
                        required_log = (10 - hyper_log) * 100 - mega_log * 10 - super_log
                        if epic_log >= required_log * 10:
                            solution = f'rpg craft super log {required_log}\n' \
                                       f'rpg craft mega log all\n' \
                                       f'rpg craft hyper log all\n' \
                                       f'rpg craft ultra log'
                if 'wooden log' in log_data:
                    wooden_log = log_data['wooden log']
                    if not solution:
                        required_log = (10 - hyper_log) * 1000 - mega_log * 100 - super_log * 10 - epic_log
                        if wooden_log >= required_log * 25:
                            solution = f'rpg craft epic log {required_log}\n' \
                                       f'rpg craft super log all\n' \
                                       f'rpg craft mega log all\n' \
                                       f'rpg craft hyper log all\n' \
                                       f'rpg craft ultra log'
                        else:
                            await ctx.send(
                                f'You need at least {required_log * 25 - wooden_log} wooden log to do this')
                            break
                elif not solution:
                    await ctx.send("No solution found")
                    break
                calculator = discord.Embed(title='Efficiency Calculation',
                                           description='**Crafter Solution still on test so it maybe wrong** '
                                                       'Feel free to suggest efficient way for crafter',
                                           color=7864132)
                calculator.add_field(name='Non crafter', value=solution)
                await ctx.send(embed=calculator)

                if not solution_crafter:
                    def verify(m):
                        if (m.author == ctx.author and m.content.lower() in ["y", "n", "yes", "no"]
                                and m.channel.id == ctx.channel.id):
                            if m.content.lower() in ["no", "n"]:
                                raise asyncio.TimeoutError
                            return True
                        return False

                    await ctx.send("Would you like to calculate for crafter solution? (y/n)\n"
                                   "Aborting in 10 seconds")
                    try:
                        await self.bot.wait_for("message", check=verify, timeout=10)
                    except asyncio.TimeoutError:
                        await ctx.send("Aborting")
                        break

                    def verify2(m):
                        if m.author == ctx.author and m.channel.id == ctx.channel.id:
                            try:
                                float(m.content)
                                return True
                            except OverflowError:
                                pass
                            except ValueError:
                                pass
                        return False

                    await ctx.send("Gib your current percentage of returned item. Aborting in 15 seconds")
                    try:
                        returned_item = await self.bot.wait_for("message", check=verify2, timeout=15)
                    except asyncio.TimeoutError:
                        await ctx.send("Aborting")
                        break
                    returned_item = float(returned_item.content) / 100
                    original = await ctx.send("Calculating <a:discordloading:792012369168957450>")
                    await ctx.trigger_typing()
                    solved = False
                    tier = ["hyper log", "mega log", "super log", "epic log"]
                    dump = 0
                    amount = 0
                    t1 = time.time()
                    while not solved:
                        if hyper_log >= 10:
                            if dump != 0 and amount != 0:
                                solution_crafter += f"\nrpg craft {tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            solution_crafter += "\nrpg craft ultra log"
                            solved = True

                        elif mega_log >= 10:
                            if dump != 1 and amount != 0:
                                solution_crafter += f"\nrpg craft {tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if mega_log >= (10 - hyper_log) * 10:
                                dump = 1
                                amount += 10 - hyper_log
                                # actually useless but whatever
                                mega_log -= (10 - hyper_log) * 10 - floor((100 - 10 * hyper_log) * returned_item)
                                hyper_log = 10
                            else:
                                solution_crafter += f"\nrpg craft hyper log all"
                                hyper_log += floor(mega_log / 10)
                                mega_log = (mega_log % 10) + floor(floor(mega_log / 10) * 10 * returned_item)

                        elif super_log >= 10:
                            if dump != 2 and amount != 0:
                                solution_crafter += f"\nrpg craft {tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if super_log >= (100 - 10 * hyper_log - mega_log) * 10:
                                dump = 2
                                amount += 100 - 10 * hyper_log - mega_log
                                super_log -= (100 - 10 * hyper_log - mega_log) * 10 - \
                                             floor((100 - 10 * hyper_log - mega_log) * 10 * returned_item)
                                mega_log = 100 - 10 * hyper_log

                            else:
                                solution_crafter += f"\nrpg craft mega log all"
                                mega_log += floor(super_log / 10)
                                super_log = (super_log % 10) + floor(floor(super_log / 10) * 10 * returned_item)
                        elif epic_log >= 10:
                            if dump != 3 and amount != 0:
                                solution_crafter += f"\nrpg craft {tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            if epic_log >= (100 - 10 * mega_log - super_log) * 10:
                                dump = 3
                                amount += 100 - 10 * mega_log - super_log
                                epic_log -= (100 - 10 * mega_log - super_log) * 10 - \
                                            floor((100 - 10 * mega_log - super_log) * 10 * returned_item)
                                super_log = 100 - 10 * mega_log
                            else:
                                solution_crafter += f"\nrpg craft super log all"
                                super_log += floor(epic_log / 10)
                                epic_log = (epic_log % 10) + floor(floor(epic_log / 10) * 10 * returned_item)
                        else:
                            if dump != 4 and amount != 0:
                                solution_crafter += f"\nrpg craft {tier[dump - 1]} {amount}"
                                dump, amount = 0, 0
                            dump = 4
                            if wooden_log >= (100 - 10 * super_log - epic_log) * 25:
                                wooden_log -= (100 - 10 * super_log - epic_log) * 25 - \
                                              floor((100 - 10 * super_log - epic_log) * 25 * returned_item)
                                amount += 100 - 10 * super_log - epic_log
                                epic_log = 100 - 10 * super_log
                            elif wooden_log >= 25:
                                solution_crafter += f"\nrpg craft epic log log all"
                                epic_log += floor(wooden_log / 25)
                                wooden_log = (wooden_log % 25) + floor(floor(wooden_log / 25) * 25 * returned_item)
                            else:
                                await ctx.send("OwO what is this? solution not found. Aborting..")
                                break
                    try:
                        if len(solution_crafter) > 2000:
                            async def divide_conquer(string):
                                if len(string) > 2000:
                                    s1 = len(string) // 2
                                    s2 = s1
                                    while string[s1] != '\n':
                                        s1 += 1
                                        s2 += 1
                                    await divide_conquer(string[:s1])
                                    await divide_conquer(string[s2:])
                                else:
                                    await ctx.send(string)

                            await divide_conquer(solution_crafter)
                            await ctx.send(f"Elapsed time: {time.time() - t1}")
                        else:
                            await original.edit(content=solution_crafter)
                    except discord.HTTPException:
                        await original.edit(content="Character limit reached")

    @commands.command(name='countstreak', help='Count bonus xp depends on streak',
                 aliases=['streakcount', 'bonusxp', 'countxp'])
    async def countstreaks(self, ctx, streak: int = None):
        yellow = 0xfff00
        if streak:
            if streak % 1000 == 0:
                bonus = 25 * (pow(streak / 100, 1 / 2) * 100 + 500)
            elif streak % 500 == 0:
                bonus = 10 * (pow(streak / 100, 1 / 2) * 100 + 500)
            elif streak % 100 == 0:
                bonus = 5 * (pow(streak / 100, 1 / 2) * 100 + 500)
            elif streak % 50 == 0:
                bonus = 3 * (pow(streak / 100, 1 / 2) * 100 + 500)
            elif streak % 10 == 0:
                bonus = pow(streak / 100, 1 / 2) * 100 + 500
            else:
                bonus = 0
            bonus = round(bonus)
            if bonus > 100000:
                bonus = 100000
            decoration = random.randint(1, 20)
            name = ctx.author.name
            custom_embed = discord.Embed(title=f'{name} goes into battle!', description=f'You won in {decoration} '
                                                                                        f'turns! your team gained **200 + {bonus}** xp! '
                                                                                        f'streak: {streak}',
                                         color=yellow)
            await ctx.send(embed=custom_embed)


def setup(bot):
    bot.add_cog(HelperCommand(bot))