import asyncio
import base64
import os
import aiohttp
import random
import sqlite3
import math
from datetime import datetime, timedelta
import pytz
from io import BytesIO
from PIL import Image
import hoshino
from hoshino import Service, priv
from hoshino.modules.priconne import _pcr_data_duel
from hoshino.modules.priconne import chara_duel as chara
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
import copy
import json
import nonebot
from nonebot import on_command, on_request
from hoshino import sucmd
from nonebot import get_bot
from hoshino.typing import NoticeSession

sv = Service('daidao', bundle='daidao', help_='''
'''.strip())

DAIDAO_DB_PATH = os.path.expanduser('~/.hoshino/daidao.db')
def get_db_path():
    if not (os.path.isfile(os.path.abspath(os.path.join(os.path.dirname(__file__), "../"
                                                        "yobot/yobot/src/client/yobot_data/yobotdata.db"))) or os.access(os.path.abspath(os.path.join(os.path.dirname(__file__), "../"
                                                                                                                                                      "yobot/yobot/src/client/yobot_data/yobotdata.db")), os.R_OK)):
        return None
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"
                                           "yobot/yobot/src/client/yobot_data/yobotdata.db"))
    return db_path


def get_web_address():
    if not os.path.isfile(os.path.abspath(os.path.join(os.path.dirname(__file__), "../"
                                                       "yobot/yobot/src/client/yobot_data/yobot_config.json"))):
        return None
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"
                                               "yobot/yobot/src/client/yobot_data/yobot_config.json"))
    with open(f'{config_path}', 'r', encoding='utf8')as fp:
        yobot_config = json.load(fp)
    website_suffix = str(yobot_config["public_basepath"])
    port = str(hoshino.config.PORT)
    web_address = "http://127.0.0.1" + ":" + port + website_suffix
    return web_address

yobot_url = get_web_address()
if not yobot_url:
    yobot_url = '' 
    # 获取主页地址：在群内向bot发送指令“手册”，复制bot发送的链接地址，删除末尾的manual/后即为主页地址
    # 例:https://域名/目录/或http://IP地址:端口号/目录/,注意不要漏掉最后的斜杠！

DB_PATH = get_db_path()
if not DB_PATH:
    DB_PATH = ''
    # 例：C:/Hoshino/hoshino/modules/yobot/yobot/src/client/yobot_data/yobotdata.db
    # 注意斜杠方向！！！
    #  
async def get_user_card(bot, group_id, user_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    for m in mlist:
        if m['user_id'] == user_id:
            return m['card'] if m['card']!='' else m['nickname']
    return str(user_id)

def get_apikey(gid:str) -> str:
    # 获取apikey
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f'select apikey from clan_group where group_id={gid}')
    apikey = cur.fetchall()[0][0]
    cur.close()
    conn.close()
    return apikey

class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute("INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?", (date, key,), )
        return
db = RecordDAO(DAIDAO_DB_PATH)

async def get_boss_Zhou(gid:str) -> str:

    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
        Zhou = data["challenges"][-1]["cycle"]  # 获取Boss周目
        return Zhou

async def get_boss_Hao(gid:str) -> str:

    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
        Hao = data["challenges"][-1]["boss_num"]  # 获取Boss号
        return Hao

async def get_boss_HP(gid:str) -> str:

    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
        boss_hp = data["challenges"][-1]["health_ramain"]  # 获取最后一刀的boss血量
        return boss_hp

class DAICounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DAIDAO_DB_PATH), exist_ok=True)
        self._create_Beidai()
        self._create_BCD()

    def _connect(self):
        return sqlite3.connect(DAIDAO_DB_PATH)

#被代刀部分
    def _create_Beidai(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS BEIDAI
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           ID           INT    NOT NULL,
                           ZHOU           INT    NOT NULL,
                           HAO         INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建被代刀表发生错误')

    def _get_Daidao_owner(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ID FROM BEIDAI WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')
    
    def _get_Daidao_ZHOU(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ZHOU FROM BEIDAI WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')
    
    def _get_Daidao_HAO(self, gid, uid):
        try:
            r = self._connect().execute("SELECT HAO FROM BEIDAI WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')

    def _set_DAIDAO_owner(self, gid, id, uid,zhou, hao):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO BEIDAI (GID, ID, UID, ZHOU, HAO) VALUES (?, ?, ?, ?, ?)",
                (gid, id, uid, zhou, hao),
            )

    def _delete_DAIDAO_owner(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM BEIDAI  WHERE GID=? AND UID=?",
                (gid, uid),
            )
#补偿刀部分
    def _create_BCD(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS BCD
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           ZHOU           INT    NOT NULL,
                           HAO         INT    NOT NULL,
                           NUM         INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建被代刀表发生错误')

    def _get_Weidao_owner(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM BCD WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')
    
    def _get_Weidao_ZHOU(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ZHOU FROM BCD WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')
    
    def _get_Weidao_HAO(self, gid, uid):
        try:
            r = self._connect().execute("SELECT HAO FROM BCD WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')

    def _set_Weidao_owner(self, gid, uid, zhou, hao, num):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO BCD (GID, UID, ZHOU, HAO ,NUM) VALUES (?, ?, ?, ?, ?)",
                (gid, uid, zhou, hao ,num),
            )

    def _delete_Weidao_owner(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM BCD  WHERE GID=? AND UID=?",
                (gid, uid),
            )

    def _get_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM BEIDAI WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')
    def _get_BC_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM BCD WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')


@sv.on_prefix(('代刀中','正在代刀','代刀'))
async def kakin(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    count = 0
    fail = 0
    user_card = await get_user_card(bot, ev.group_id, ev.user_id)
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            owner = dai._get_Daidao_owner(gid,uid)
            if owner ==0:
                Zhou = await get_boss_Zhou(gid)
                Hao = await get_boss_Hao(gid)
                HP = await get_boss_HP(gid)
                if HP == 0:
                    Hao += 1
                    if Hao == 6:
                        Hao = 1
                        Zhou +=1
                dai._set_DAIDAO_owner(gid,ev.user_id,uid,Zhou,Hao)
                try:
                    await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})正在为您代刀，请勿登录！本次代刀发起是在{Zhou}周目{Hao}号BOSS！')
                    count += 1
                except:
                    await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录）')
                    fail += 1
            else:
                zhou = dai._get_Daidao_ZHOU(gid,uid)
                hao = dai._get_Daidao_HAO(gid,uid)
                user_card = await get_user_card(bot, ev.group_id, owner)
                user_card2 = await get_user_card(bot, ev.group_id, uid)
                await bot.send(ev, f'{user_card2}在{zhou}周目{hao}号BOSS由{user_card}发起了代刀，无法重复代刀')
    if count:
        if fail:
            await bot.send(ev, f"{user_card}开始代刀！已私聊通知{count}位用户！{fail}位用户通知失败！")
        else:
            await bot.send(ev, f"{user_card}开始代刀！已私聊通知{count}位用户！")

@sv.on_prefix('报刀')
async def baodao(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    num = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            dai._delete_DAIDAO_owner(gid,uid)
            dai._delete_Weidao_owner(gid,uid)
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            num += 1
            try:
                await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!')
                await bot.send(ev, f"{user_card}代刀结束！已私聊通知该用户！")
            except:
                await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录）')
    if num == 0:
        dai._delete_DAIDAO_owner(gid,ev.user_id)
        
@sv.on_prefix('查询代刀')
async def kakin(bot, ev: CQEvent):
        dai = DAICounter()
        gid = ev.group_id
        num = 0
        for m in ev.message:
          if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            owner = dai._get_Daidao_owner(gid,uid)
            if owner == 0:
                user_card = await get_user_card(bot, ev.group_id, uid)
                await bot.send(ev, f"{user_card}的账号未在代刀状态！您可确认后登录！")
            else:
                zhou = dai._get_Daidao_ZHOU(gid,uid)
                hao = dai._get_Daidao_HAO(gid,uid)
                user_card = await get_user_card(bot, ev.group_id, owner)
                user_card2 = await get_user_card(bot, ev.group_id, uid)
                await bot.send(ev, f'{user_card2}在{zhou}周目{hao}号BOSS由{user_card}发起了代刀，请小心顶号！')
            num += 1
        if num == 0:
          uid = ev.user_id
          user_card = await get_user_card(bot, ev.group_id, uid)
          owner = dai._get_Daidao_owner(gid,uid)
          if owner == 0:
            user_card = await get_user_card(bot, ev.group_id, uid)
            await bot.finish(ev, f"您的账号未在代刀状态！您可确认后登录！")
          else:
            zhou = dai._get_Daidao_ZHOU(gid,uid)
            hao = dai._get_Daidao_HAO(gid,uid)
            user_card = await get_user_card(bot, ev.group_id, owner)
            user_card2 = await get_user_card(bot, ev.group_id, uid)
            await bot.send(ev, f'您的账号在{zhou}周目{hao}号BOSS由{user_card}发起了代刀，请小心顶号！')
        
@sv.on_prefix('尾刀')
async def weidao(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    num = 0
    kill = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            dai._delete_DAIDAO_owner(gid,uid)
            print 
            if dai._get_Weidao_owner(gid,uid) != 0:
                dai._delete_Weidao_owner(gid,uid)
                kill = 1
            else:
                Zhou = await get_boss_Zhou(gid)
                Hao = await get_boss_Hao(gid)
                dai._set_Weidao_owner(gid,uid,Zhou,Hao,1)#这一段用来判断尾余刀
            num += 1
            try:
                if kill == 1:
                    await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!(您是尾余刀，请关注群消息)')
                    await bot.send(ev, f"{user_card}代刀结束！已私聊通知该用户！（尾余刀不记录)！")
                else:
                    await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!(您是尾刀，请关注群消息)')
                    await bot.send(ev, f"{user_card}代刀结束！已私聊通知该用户！且已记录补偿刀！")
            except:
                await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录）')
    if num == 0:
        uid = ev.user_id
        dai._delete_DAIDAO_owner(gid,uid)
        if dai._get_Weidao_owner(gid,uid) != 0:
            dai._delete_Weidao_owner(gid,uid)
        else:
            Zhou = await get_boss_Zhou(gid)
            Hao = await get_boss_Hao(gid)
            dai._set_Weidao_owner(gid,uid,Zhou,Hao,1)#这一段用来判断尾余刀
      
@sv.on_rex(r'^(?:SL|sl) *([\?？])?')
async def SLL(bot, ev: CQEvent):
    match = ev['match']
    a = match.group(1) == '？'
    b = match.group(1) == '?'
    if a:
        return
    elif b:
        return
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})使用了您的SL!请关注群消息！')
            count += 1
    if count:
        await bot.send(ev, f"{user_card}在代刀中使用了SL！已通知{count}位用户！")
        
@sv.on_prefix('挂树')
async def guashu(bot, ev: CQEvent):
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})在您的账号上代刀时挂树!请暂时不要登陆并关注群消息！')
            count += 1
    if count:
        await bot.send(ev, f"{user_card}在代刀中挂树！已通知{count}位用户！")
        
@sv.on_prefix(('取消代刀','结束代刀'))
async def quxiao(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    user_card = await get_user_card(bot, ev.group_id, ev.user_id)
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            owner = dai._get_Daidao_owner(gid,uid)
            if owner !=0:
                dai._delete_DAIDAO_owner(gid,uid)
                user_card2 = await get_user_card(bot, ev.group_id, uid)
                try:
                    await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})取消了代刀！')
                    await bot.send(ev, f"{user_card}取消了为{user_card2}的代刀！已私聊通知该用户！")
                except:
                    await bot.finish(ev, f'发送私聊取消代刀消息时发生错误，{user_card2}可能没有私聊过机器人（但取消代刀正常记录）')
            else:
                await bot.finish(ev, f'{user_card2}未在代刀状态！')

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d        

async def get_gid_dict(bot, group_id):
    glist = await bot.get_group_list()
    d = {}
    for m in mlist:
        d[m['group_id']] = m['group_id']
    return d   

@sv.on_fullmatch('代刀列表')
async def Race_ranking(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_dict2 = {}
        dai = DAICounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_Daidao_owner(gid,uid)
                if owner !=0:
                    Zhou = dai._get_Daidao_ZHOU(gid,uid)
                    Hao = dai._get_Daidao_HAO(gid,uid)
                    user = await get_user_card(bot, ev.group_id, owner)
                    score_dict[user_card_dict[uid]] = [Zhou,Hao,user]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg = '当前正在被代刀的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                msg += f'{i+1}. {group_ranking[i][0]} 在{group_ranking[i][1][0]}周目{group_ranking[i][1][1]}号BOSS被{group_ranking[i][1][2]}发起代刀\n'
        if msg == '当前正在被代刀的有:\n':
            msg = '当前没有人正在被代刀'
        await bot.send(ev, msg.strip())

@sv.on_fullmatch('补偿刀列表')
async def Race_ranking(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        score_dict2 = {}
        dai = DAICounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_Weidao_owner(gid,uid)
                if owner !=0:
                    Zhou = dai._get_Weidao_ZHOU(gid,uid)
                    Hao = dai._get_Weidao_HAO(gid,uid)
                    score_dict[user_card_dict[uid]] = [Zhou,Hao]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg = '当前记录的补偿刀有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                msg += f'{i+1}. {group_ranking[i][0]} 在{group_ranking[i][1][0]}周目{group_ranking[i][1][1]}号BOSS收尾\n'
        if msg == '当前记录的补偿刀有:\n':
            msg = '当前没有补偿刀'
        await bot.send(ev, msg.strip())

@sv.on_fullmatch('清空代刀数据')
async def Reset(bot, ev: CQEvent):   
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '无权进行该操作！', at_sender=True)
    gid = ev.group_id
    dai = DAICounter()
    umlist = dai._get_uid_list(gid)
    for s in range(len(umlist)):
        uid = int(umlist[s])   
        dai._delete_DAIDAO_owner(gid,uid)
    await bot.finish(ev, '已清空正在代刀的数据！')

@sv.on_fullmatch('清空补偿数据')
async def Reset(bot, ev: CQEvent):   
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '无权进行该操作！', at_sender=True)
    gid = ev.group_id
    dai = DAICounter()
    umlist = dai._get_BC_list(gid)
    for s in range(len(umlist)):
        uid = int(umlist[s])   
        dai._delete_Weidao_owner(gid,uid)
    await bot.finish(ev, '已清空目前记录的补偿刀数据！')