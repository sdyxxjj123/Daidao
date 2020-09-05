from nonebot import on_command, MessageSegment
from hoshino.typing import CQEvent
from hoshino.modules.priconne import chara
from hoshino.util import DaiDaoLimiter, concat_pic, pic2b64, silence
import re
import datetime, random, os, csv
from PIL import Image, ImageDraw, ImageFont
from time import sleep
import random
from datetime import timedelta
import nonebot
from nonebot import Message, MessageSegment, message_preprocessor, on_command
from nonebot.message import _check_calling_me_nickname
import hoshino
from hoshino.service import sucmd
from hoshino.typing import CommandSession, CQHttpError
from hoshino import R, Service, util, priv

sv = Service('daidao', bundle='daidao', help_='''
'''.strip())


class CommandConfirmer:    
    def __init__(self, max_valid_time):
        self.last_command_time = datetime.datetime(2020, 4, 17, 0, 0, 0, 0)
        self.max_valid_time = max_valid_time

    def check(self):
        now_time = datetime.datetime.now()
        delta_time = now_time - self.last_command_time
        return delta_time.seconds <= self.max_valid_time
    
    def record_command(self, command_name):
        self.last_command_name = command_name
        self.last_command_time = datetime.datetime.now()
        
    def has_command_wait_to_confirm(self):
        return self.last_command_time != datetime.datetime(2020, 4, 17, 0, 0, 0, 0)
        
    def reset(self):
        self.last_command_time = datetime.datetime(2020, 4, 17, 0, 0, 0, 0)
        
#async def check_tenjo_num(bot, ev: CQEvent):
    #uid = int(m.data['qq'])



MAX_VALID_TIME = 30
BOT_NICKNAME = ''
SEND_INTERVAL = 0.5
COMMAND_NAMES = ['boxcolle', 'boxcolle_replenish']
command_confirmer = CommandConfirmer(MAX_VALID_TIME)
broadcast_list= []
broadcast_msg = ''
daidao_limit = DaiDaoLimiter(1)
TENJO_EXCEED_NOTICE = f'该用户正在被代刀,无法重复代刀！请小心顶号！如果确认该账号未在代刀中，请为其取消代刀'

VALID_STAR = ['0', '1', '2', '3', '4', '5', '6']

@sv.on_prefix(('代刀中','正在代刀','代刀'))
async def kakin(bot, ev: CQEvent):
    arg = str(ev.raw_message)
    rex = re.compile(BOT_NICKNAME)
    mm = rex.search(arg)
    count = 0
    if mm:
        for m in ev.message:
          if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            if not daidao_limit.check(uid):
               await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)
            daidao_limit.increase(uid)
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手({ev.user_id})正在为您代刀，请勿登录！')
            count += 1
    if count:
        await bot.send(ev, f"{ev.user_id}开始代刀！已通知{count}位用户！")
        
@sv.on_prefix(('报刀','尾刀'))
async def baodao(bot, ev: CQEvent):
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手({ev.user_id})已经为您代刀完毕!可以登录！')
            daidao_limit.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"{ev.user_id}代刀结束！已通知{count}位用户！")
        
@sv.on_rex(r'^(?:SL|sl) *([\?？])?')
async def SLL(bot, ev: CQEvent):
    match = ev['match']
    is_jp = match.group(1) == '？'
    is_tw = match.group(1) == '?'
    if is_jp:
        return
    elif is_tw:
        return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手({ev.user_id})使用了您的SL!请关注群消息！')
            count += 1
    if count:
        await bot.send(ev, f"{ev.user_id}在代刀中使用了SL！已通知{count}位用户！")
        
@sv.on_prefix('挂树')
async def guashu(bot, ev: CQEvent):
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手({ev.user_id})在您的账号上代刀时挂树!请暂时不要登陆并关注群消息！')
            count += 1
    if count:
        await bot.send(ev, f"{ev.user_id}在代刀中挂树！已通知{count}位用户！")
        
@sv.on_prefix(('取消代刀','结束代刀'))
async def guashu(bot, ev: CQEvent):
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            await bot.send_private_msg(user_id=int(uid), message=f'您好~您的账号不符合代刀条件代刀手({ev.user_id})已取消代刀!请关注群消息！')
            daidao_limit.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"{ev.user_id}取消了代刀！已通知{count}位用户！")