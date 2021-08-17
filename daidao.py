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
from hoshino.typing import CQEvent
import copy
import json
import nonebot
from nonebot import on_command, on_request
from hoshino import sucmd,config,get_bot
from hoshino.typing import NoticeSession
from multiprocessing import Pool
import requests


sv = Service('daidao', bundle='daidao', help_='''
'''.strip())

boss_HP = {
}
bossData = {
    'cn':{    
    'hp1': [6000000, 8000000, 10000000, 12000000, 15000000],
    'hp2': [6000000, 8000000, 10000000, 12000000, 15000000],
    'hp3': [6000000, 8000000, 10000000, 12000000, 15000000],
    'hp4': [6000000, 8000000, 10000000, 12000000, 15000000],
    },
    'tw':{    
    'hp1': [6000000, 8000000, 10000000, 12000000, 15000000],
    'hp2': [6000000, 8000000, 10000000, 12000000, 15000000],
    'hp3': [7000000, 9000000, 13000000, 15000000, 20000000],
    'hp4': [17000000, 18000000, 20000000, 21000000, 23000000],
    'hp5': [85000000, 90000000, 95000000, 100000000, 110000000],}
}
DAIDAO_DB_PATH = os.path.expanduser('~/.hoshino/daidao.db')
SUPERUSERS = config.SUPERUSERS
GroupID_ON = True #当GO版本为0.94fix4以上时，允许从群内发起私聊（即使用管理员身份强制私聊，不需要对方主动私聊过），如果低于该版本请不要开启
NOprivate = False #全局开关，启用后，不再尝试私聊，也不会在群内发送“私聊失败”等消息，仅做记录使用，降低机器人冻结风险。
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
Version = '0.8.1'  
# 检查客户端版本
def check_update_run():
    try:
        url = 'http://update.ftcloud.top:5050/version'
        resp = requests.get(url)
        resp.encoding = 'UTF-8'
        if resp.status_code != 200:
            sv.logger.error('【代刀插件】服务器连接失败')
            return True
        if resp.text == Version:
            sv.logger.info('【代刀插件】插件已是最新版本')
            return True
        version_new = resp.text
        url_log = 'http://update.ftcloud.top:5050/new/log'
        resp = requests.get(url_log)
        resp.encoding = 'UTF-8'
        sv.logger.info(f"代刀插件有更新\n您本地的版本为{Version}，目前最新的版本为{version_new},更新内容为{resp.text}\n建议您立刻前往https://github.com/sdyxxjj123/Daidao/更新")
        return True
    except Exception as e:
        sv.logger.error('【代刀插件】网络错误')
        return True
#定时检查并私聊给管理员
def check_update():
    try:
        url = 'http://update.ftcloud.top:5050/version'
        resp = requests.get(url)
        resp.encoding = 'UTF-8'
        if resp.status_code != 200:
            sv.logger.error('【代刀插件】服务器连接失败')
            return True
        if resp.text == Version:
            sv.logger.info('【代刀插件】插件已是最新版本')
            return True
        version_new = resp.text
        url_log = 'http://update.ftcloud.top:5050/new/log'
        resp = requests.get(url_log)
        resp.encoding = 'UTF-8'
        msg = f"代刀插件有更新：\n您本地的版本为{Version}，目前最新的版本为{version_new},更新内容为{resp.text}\n建议您立刻前往https://github.com/sdyxxjj123/Daidao/更新"
        return msg
    except Exception as e:
        sv.logger.error('【代刀插件】网络错误')
        return True


check_update_run()
async def get_user_card(bot, group_id, user_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    for m in mlist:
        if m['user_id'] == user_id:
            return m['card'] if m['card']!='' else m['nickname']
    return str(user_id)

async def get_group_sv(gid:str) -> str:
    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
        server = data["groupinfo"][-1]["game_server"]  # 获取服务器
        return server

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
        if boss_hp == 0:
            server = data["groupinfo"][-1]["game_server"]  # 获取服务器
            Zhou = data["challenges"][-1]["cycle"]
            Hao = data["challenges"][-1]["boss_num"]
            Hao += 1
            if Hao > 5:
                Zhou += 1
                Hao = 1
            if Zhou <= 3:
                boss_hp = bossData[server]['hp1'][Hao-1]
            if Zhou <= 10:
                boss_hp = bossData[server]['hp2'][Hao-1]
            if Zhou <= 34:
                boss_hp = bossData[server]['hp3'][Hao-1]
            if Zhou >= 35:
                boss_hp = bossData[server]['hp4'][Hao-1]
        return boss_hp

class DAICounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DAIDAO_DB_PATH), exist_ok=True)
        self._create_Beidai()
        self._create_BCD()
        self._create_ZZ()
        self._create_GS()
        self._create_SHB()

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
                           DATA           NTEXT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建补偿刀表发生错误')

    def _get_Weidao_owner(self, gid, uid):
        try:
            r = self._connect().execute("SELECT NUM FROM BCD WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找代刀归属发生错误')
    
    def _set_BC_owner(self, gid, uid, data):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO BCD (GID, UID, DATA) VALUES (?, ?, ?)",
                (gid, uid, data),
            )
    def _get_BC(self, gid, uid):
        try:
            r = self._connect().execute("SELECT DATA FROM BCD WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找助战归属发生错误')
    #移除补偿刀
    def _delete_BC(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM BCD WHERE GID=? AND UID=?",
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
    


#助战部分
    def _create_ZZ(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS ZZ
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           ZZ            NTEXT   NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建锁助战表发生错误')

    def _get_ZZ_Suo(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ZZ FROM ZZ WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找助战归属发生错误')
            
    def _get_ZZ_Suo_list(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ZZ FROM ZZ WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找助战归属发生错误')
            
    def _set_ZZ_owner(self, gid, uid, ZZ, num=1):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ZZ (GID, UID, ZZ, NUM) VALUES (?, ?, ?,?)",
                (gid, uid, ZZ, num),
            )

    def _delete_ZZ_Suo(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM ZZ  WHERE GID=? AND UID=?",
                (gid, uid),
            )
#挂树部分
    def _create_GS(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GS
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           HOUR            NTEXT   NOT NULL,
                           MIN           INT    NOT NULL,
                           ID           INT    NOT NULL,
                           LY        NTEXT   NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建挂树表发生错误')

    def _get_GS_Hour(self, gid, uid):
        try:
            r = self._connect().execute("SELECT HOUR FROM GS WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树时间发生错误')
    
    def _get_GS_MIN(self, gid, uid):
        try:
            r = self._connect().execute("SELECT MIN FROM GS WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树时间发生错误')

    def _get_GS_id(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ID FROM GS WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树归属发生错误')
    def _get_GS_ly(self, gid, uid):
        try:
            r = self._connect().execute("SELECT LY FROM GS WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树归属发生错误')
            
    def _set_GS_owner(self, gid, uid, Hour, Min, id ,ly):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GS (GID, UID, HOUR, MIN ,ID,LY) VALUES (?, ?, ?, ?, ?, ?)",
                (gid, uid, Hour, Min, id,ly),
            )

    def _delete_GS(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM GS  WHERE GID=? AND UID=?",
                (gid, uid),
            )
#暂停伤害部分
    def _create_SHB(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SHB
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           ID           INT    NOT NULL,
                           SH           NTEXT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建挂树表发生错误')

    def _get_SHB_SH(self, gid, uid):
        try:
            r = self._connect().execute("SELECT SH FROM SHB WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树时间发生错误')
    
    def _get_SHB_ID(self, gid, uid):
        try:
            r = self._connect().execute("SELECT ID FROM SHB WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找挂树时间发生错误')

    def _set_SH_owner(self, gid, uid, id, sh):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO SHB (GID, UID, ID, SH) VALUES (?, ?, ?, ?)",
                (gid, uid, id, sh),
            )

    def _delete_SH(self, gid, uid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM SHB  WHERE GID=? AND UID=?",
                (gid, uid),
            )    
#获取列表部分    
    def _get_SH_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM SHB WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')

    def _get_GS_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM GS WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')

    def _get_DD_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM BEIDAI WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')

    def _get_ZZ_uid_list(self, gid):
        try:
            r = self._connect().execute("SELECT DISTINCT(UID) FROM ZZ WHERE GID=? ", (gid,)).fetchall()
            return [u[0] for u in r] if r else {}
        except:
            raise Exception('查找uid表发生错误')


@sv.on_rex(r'^(代刀中?|开始代刀) ?$')
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
                if not NOprivate:
                    try:
                        if GroupID_ON == True:
                            await bot.send_private_msg(user_id=int(uid),group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})正在为您代刀，请勿登录！本次代刀发起是在{Zhou}周目{Hao}号BOSS！')
                        else:
                            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})正在为您代刀，请勿登录！本次代刀发起是在{Zhou}周目{Hao}号BOSS！')
                        count += 1
                    except:
                        await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录，若机器人是管理员，则消息已正常发出）')
                        fail += 1
                else:
                    sv.logger.info('已记录代刀')
            else:
                zhou = dai._get_Daidao_ZHOU(gid,uid)
                hao = dai._get_Daidao_HAO(gid,uid)
                user_card = await get_user_card(bot, ev.group_id, owner)
                user_card2 = await get_user_card(bot, ev.group_id, uid)
                await bot.send(ev, f'{user_card2}在{zhou}周目{hao}号BOSS由{user_card}发起了代刀，无法重复代刀')
    if count and not NOprivate:
        if fail:
            await bot.send(ev, f"{user_card}开始代刀！已私聊通知{count}位用户！{fail}位用户通知失败！")
        else:
            await bot.send(ev, f"{user_card}开始代刀！已私聊通知{count}位用户！")
    if NOprivate:
        await bot.send(ev, f"{user_card}开始代刀！")
    
    
@sv.on_rex(r'^报刀 ?\d+ ?$')
async def baodao(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    num = 0
    Zhou = await get_boss_Zhou(gid)
    Hao = await get_boss_Hao(gid)
    HP = await get_boss_HP(gid)
    if HP == 0:
        Hao += 1
        if Hao == 6:
            Hao = 1
            Zhou +=1 
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            dai._delete_DAIDAO_owner(gid,uid)
            dai._delete_ZZ_Suo(gid,uid)
            dai._delete_GS(gid,uid)
            dai._delete_SH(gid,uid)
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            num += 1
            if not NOprivate:
                try:
                    if GroupID_ON == True:
                        await bot.send_private_msg(user_id=int(uid),group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!')
                    else:
                        await bot.send_private_msg(user_id=int(uid),message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!')
                    await bot.send(ev, f"{user_card}代刀结束！已私聊通知该用户！")
                except:
                    await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录，若机器人是管理员，则消息已正常发出）')
            else:
                await bot.send(ev, f"{user_card}代刀结束！")
    await bot.send(ev, f"状态反馈：当前{Zhou}周目{Hao}号怪，血量{HP}.")
    if num == 0:
        uid = ev.user_id
        dai._delete_DAIDAO_owner(gid,uid)
        dai._delete_GS(gid,uid)
        dai._delete_SH(gid,uid)
        dai._delete_ZZ_Suo(gid,uid)
        
@sv.on_rex(r'^查询代刀 ?$')
async def search_kakin(bot, ev: CQEvent):
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
        
@sv.on_rex(r'^尾刀$')
async def weidao(bot, ev: CQEvent):
    dai = DAICounter()
    gid = ev.group_id
    num = 0
    #kill = 0
    umlist = dai._get_SH_uid_list(gid)
    if umlist !=0:
        msgSH = "暂停的下来吧:\n"
        for s in range(len(umlist)):
            uid = int(umlist[s])
            dai._delete_SH(gid,uid)
            msgSH += f"[CQ:at,qq={uid}]"
        if msgSH != "暂停的下来吧:\n":
            await bot.send(ev, msgSH)
    umlist = dai._get_GS_uid_list(gid)
    if umlist !=0:
        msgGS = "挂树的下来吧:\n"
        for s in range(len(umlist)):
            uid = int(umlist[s])
            dai._delete_GS(gid,uid)
            msgGS += f"[CQ:at,qq={uid}]"
        if msgGS != "挂树的下来吧:\n":
            await bot.send(ev, msgGS)
    Zhou = await get_boss_Zhou(gid)
    Hao = await get_boss_Hao(gid)
    HP = await get_boss_HP(gid)
    Hao += 1
    if Hao == 6:
        Hao = 1
        Zhou +=1 
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            dai._delete_DAIDAO_owner(gid,uid)
            dai._delete_ZZ_Suo(gid,uid)
            uid = int(m.data['qq'])
            data = str(f'在{Zhou}周目{Hao}号BOSS收尾，代刀手为{user_card}')
            dai._set_BC_owner(gid,uid,data)
            num += 1
            if not NOprivate:
                try:
                    if GroupID_ON == True:
                        await bot.send_private_msg(user_id=int(uid), group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!(您是尾刀，请关注群消息)')
                    else:
                        await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})已经为您代刀完毕!(您是尾刀，请关注群消息)')
                    await bot.send(ev, f"{user_card}代刀结束！已私聊通知该用户！补偿刀信息已录入，请及时更新！")
                except:
                    await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录，若机器人是管理员，则消息已正常发出）')
            else:
                await bot.send(ev, f"{user_card}代刀结束！补偿刀信息已录入，请及时更新！")
    await bot.send(ev, f"状态反馈：当前{Zhou}周目{Hao}号怪，血量{HP}.")
    if num == 0:
        uid = ev.user_id
        dai._delete_DAIDAO_owner(gid,uid)
        Zhou = await get_boss_Zhou(gid)
        Hao = await get_boss_Hao(gid)
        HP = await get_boss_HP(gid)
        if HP == 0:
            Hao += 1
            if Hao == 6:
                Hao = 1
                Zhou +=1
        data = str(f'在{Zhou}周目{Hao}号BOSS收尾')
        dai._set_BC_owner(gid,uid,data)
      
@sv.on_rex(r'^(?:SL|sl) *([\?？])?')
async def SLL(bot, ev: CQEvent):
    match = ev['match']
    gid = ev.group_id
    if bool(match.group(1)):
        return
    count = 0
    dai = DAICounter()
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            if dai._get_GS_id(gid,uid) !=0:
                dai._delete_GS(gid,uid)
            if not NOprivate:
                try:
                    if GroupID_ON == True:
                        await bot.send_private_msg(user_id=int(uid),group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})使用了您的SL!请关注群消息！')
                    else:
                        await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})使用了您的SL!请关注群消息！')
                except:
                    await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录，若机器人是管理员，则消息已正常发出）')
                count += 1
    if count:
        await bot.send(ev, f"{user_card}在代刀中使用了SL！已通知{count}位用户！")
    if NOprivate:
        await bot.send(ev, f"{user_card}在代刀中使用了SL！")
        
@sv.on_rex(r'^挂树 ?$|^挂树[：:](.*)') #这个地方match.group(1)提取留言
async def guashu(bot, ev: CQEvent):
    count = 0
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    Hour = now.hour
    Min = now.minute
    dai = DAICounter()
    gid = ev.group_id
    id = ev.user_id
    match = ev['match']
    ly = match.group(1)
    if ly == None:
        ly = '无'
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            dai._set_GS_owner(gid,uid,Hour,Min,id,ly)
            if not NOprivate:
                try:
                    if GroupID_ON == True:
                        await bot.send_private_msg(user_id=int(uid),group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})在您的账号上代刀时挂树!请暂时不要登陆并关注群消息！')
                    else:
                        await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})在您的账号上代刀时挂树!请暂时不要登陆并关注群消息！')
                except:
                    await bot.send(ev, '发送私聊代刀消息时发生错误，该用户可能没有私聊过机器人（但代刀正常记录，若机器人是管理员，则消息已正常发出）')
            count += 1
    if count:
        if not NOprivate:
            await bot.send(ev, f"{user_card}在代刀中挂树！已通知{count}位用户！")
        else:
            await bot.send(ev, f"{user_card}在代刀中挂树！")
    else:
        uid = ev.user_id
        dai._set_GS_owner(gid,uid,Hour,Min,id,ly)
        await bot.send(ev, '已记录挂树')

@sv.on_rex(r'^取消挂树 ?$')
async def guashu_del(bot, ev: CQEvent):
    count = 0
    #id = ev.user_id
    dai = DAICounter()
    gid = ev.group_id
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            user_card = await get_user_card(bot, ev.group_id, ev.user_id)
            user_card2 = await get_user_card(bot, ev.group_id, uid)
            if dai._get_GS_id(gid,uid) !=0:
                dai._delete_GS(gid,uid)
                await bot.send(ev, f'{user_card}已取消{user_card2}的挂树状态！')
            else:
                await bot.send(ev, f'{user_card}没有挂树！')
            count += 1   
    if count:
        return
    else:
        uid = ev.user_id
        if dai._get_GS_id(gid,uid) !=0:
            dai._delete_GS(gid,uid)
            await bot.send(ev, f'已取消挂树状态！')
        else:
            await bot.send(ev, f'您没有挂树！')

@sv.on_rex(r'^(:?取消|结束)代刀 ?$')
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
                if not NOprivate:
                    try:
                        if GroupID_ON == True:
                            await bot.send_private_msg(user_id=int(uid),group_id=int(gid),message=f'您好~代刀手{user_card}({ev.user_id})取消了代刀！')
                        else:
                            await bot.send_private_msg(user_id=int(uid), message=f'您好~代刀手{user_card}({ev.user_id})取消了代刀！')
                        await bot.send(ev, f"{user_card}取消了为{user_card2}的代刀！已私聊通知该用户！")
                    except:
                        await bot.finish(ev, f'发送私聊取消代刀消息时发生错误，{user_card2}可能没有私聊过机器人（但取消代刀正常记录）')
                else:
                    await bot.send(ev, f"{user_card}取消了为{user_card2}的代刀！")
            else:
                await bot.finish(ev, f'{user_card2}未在代刀状态！')

@sv.on_rex(f'^暂停(:|：)(.*)$')
async def zt(bot, ev: CQEvent):
    gid = ev.group_id
    id = ev.user_id
    dai = DAICounter()
    match = ev['match']
    try:
        uid = int(ev.message[1].data['qq'])
    except:
        uid = ev.user_id
    user_card = await get_user_card(bot, ev.group_id, uid)
    num = str(match.group(2))
    if dai._get_SHB_SH(gid,uid) != 0:
        dai._set_SH_owner(gid,uid,id,num)
        await bot.finish(ev, f'您的暂停伤害已更新为{num}！')
    else:
        dai._set_SH_owner(gid,uid,id,num)
        await bot.finish(ev, f'已记录{user_card}的伤害为{num}！')

@sv.on_rex(f'^记录补偿刀(:|：)(.*)$')
async def jl(bot, ev: CQEvent):
    gid = ev.group_id
    #id = ev.user_id
    dai = DAICounter()
    match = ev['match']
    try:
        uid = int(ev.message[1].data['qq'])
    except:
        uid = ev.user_id
    user_card = await get_user_card(bot, ev.group_id, uid)
    num = str(match.group(2))
    dai._set_BC_owner(gid,uid,num)
    await bot.finish(ev, f'已记录{user_card}补偿刀{num}！')
                
async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card']!='' else m['nickname']
    return d        

async def get_gid_dict(bot, group_id):
    mlist = await bot.get_group_list()
    d = {}
    for m in mlist:
        d[m['group_id']] = m['group_id']
    return d   

@sv.on_fullmatch('详细状态')
async def XXZT(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        dai = DAICounter()
        gid = ev.group_id
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
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
        msg1 = '当前正在被代刀的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                msg1 += f'{i+1}. {group_ranking[i][0]} 在{group_ranking[i][1][0]}周目{group_ranking[i][1][1]}号BOSS被{group_ranking[i][1][2]}发起代刀\n'
        if msg1 == '当前正在被代刀的有:\n':
            msg1 = '当前没有人正在被代刀\n'

        score_dict = {}
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_SHB_SH(gid,uid)
                if owner !=0:
                    SH = dai._get_SHB_SH(gid,uid)
                    id = dai._get_SHB_ID(gid,uid)
                    user = await get_user_card(bot, ev.group_id, id)
                    score_dict[user_card_dict[uid]] = [SH,user]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg3 = '当前暂停的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                if group_ranking[i][0] != group_ranking[i][1][1]:
                    msg3 += f'{i+1}. {group_ranking[i][0]} 伤害：{group_ranking[i][1][0]} 刀手：{group_ranking[i][1][1]}\n'
                else:
                    msg3 += f'{i+1}. {group_ranking[i][0]} 伤害：{group_ranking[i][1][0]}\n'
        if msg3 == '当前暂停的有:\n':
            msg3 = '当前没有人成刀暂停\n'

        score_dict = {}
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_GS_id(gid,uid)
                if owner !=0:
                    Hour = dai._get_GS_Hour(gid,uid)
                    Min = dai._get_GS_MIN(gid,uid)
                    id = dai._get_GS_id(gid,uid)
                    ly = dai._get_GS_ly(gid,uid)
                    user = await get_user_card(bot, ev.group_id, id)
                    score_dict[user_card_dict[uid]] =  [Hour,Min,user,ly]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)

        msg4 = '当前挂树的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                if group_ranking[i][1][2] != group_ranking[i][0]:
                    msg4 += f'{i+1}. {group_ranking[i][0]} 挂树开始时间：{group_ranking[i][1][0]} 时{group_ranking[i][1][1]} 分 刀手：{group_ranking[i][1][2]},留言：{group_ranking[i][1][3]},已挂树{60*(now.hour-int(group_ranking[i][1][0]))+now.minute-int(group_ranking[i][1][1])}分钟\n'
                else:
                    msg4 += f'{i+1}. {group_ranking[i][0]} 挂树开始时间：{group_ranking[i][1][0]} 时{group_ranking[i][1][1]} 分,留言：{group_ranking[i][1][3]},已挂树{60*(now.hour-int(group_ranking[i][1][0]))+now.minute-int(group_ranking[i][1][1])}分钟\n'
        if msg4 == '当前挂树的有:\n':
            msg4 = '当前没有人挂树\n'
        msg = msg1+msg3+msg4
        await bot.send(ev, msg.strip())

@sv.on_fullmatch('查树')
async def CHASHU(bot, ev: CQEvent):
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        dai = DAICounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_GS_id(gid,uid)
                if owner !=0:
                    Hour = dai._get_GS_Hour(gid,uid)
                    Min = dai._get_GS_MIN(gid,uid)
                    id = dai._get_GS_id(gid,uid)
                    ly = dai._get_GS_ly(gid,uid)
                    user = await get_user_card(bot, ev.group_id, id)
                    score_dict[user_card_dict[uid]] =  [Hour,Min,user,ly]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg = '当前挂树的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                if group_ranking[i][1][2] != group_ranking[i][0]:
                    msg += f'{i+1}. {group_ranking[i][0]} 挂树开始时间：{group_ranking[i][1][0]} 时{group_ranking[i][1][1]} 分 刀手：{group_ranking[i][1][2]},留言：{group_ranking[i][1][3]},已挂树{60*(now.hour-int(group_ranking[i][1][0]))+now.minute-int(group_ranking[i][1][1])}分钟\n'
                else:
                    msg += f'{i+1}. {group_ranking[i][0]} 挂树开始时间：{group_ranking[i][1][0]} 时{group_ranking[i][1][1]} 分,留言：{group_ranking[i][1][3]},已挂树{60*(now.hour-int(group_ranking[i][1][0]))+now.minute-int(group_ranking[i][1][1])}分钟\n'
        if msg == '当前挂树的有:\n':
            msg = '当前没有人挂树\n'
        await bot.send(ev, msg.strip())

@sv.on_fullmatch('代刀列表')
async def DDB(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
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

@sv.on_fullmatch('暂停列表')
async def ZZB(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        dai = DAICounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_SHB_SH(gid,uid)
                if owner !=0:
                    SH = dai._get_SHB_SH(gid,uid)
                    id = dai._get_SHB_ID(gid,uid)
                    user = await get_user_card(bot, ev.group_id, id)
                    score_dict[user_card_dict[uid]] = [SH,user]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg = '当前暂停的有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                if group_ranking[i][0] != group_ranking[i][1][1]:
                    msg += f'{i+1}. {group_ranking[i][0]} 伤害：{group_ranking[i][1][0]} 刀手：{group_ranking[i][1][1]}\n'
                else:
                    msg += f'{i+1}. {group_ranking[i][0]} 伤害：{group_ranking[i][1][0]}\n'
        if msg == '当前暂停的有:\n':
            msg = '当前没有人成刀暂停\n'
        await bot.send(ev, msg.strip())
    
@sv.on_fullmatch('补偿刀列表')
async def BCB(bot, ev: CQEvent):
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        score_dict = {}
        dai = DAICounter()
        gid = ev.group_id
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                owner = dai._get_BC(gid,uid)
                if owner !=0:
                    score_dict[user_card_dict[uid]] = [1,owner]
                else:
                    continue
        group_ranking = sorted(score_dict.items(),key = lambda x:x[1],reverse = True)
        msg = '当前记录的补偿刀有:\n'
        for i in range(len(group_ranking)):
            if group_ranking[i][1] != 0:
                msg += f'{i+1}. {group_ranking[i][0]} 记录了：{group_ranking[i][1][1]}\n'
        if msg == '当前记录的补偿刀有:\n':
            msg = '当前没有记录的补偿刀'
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
async def reset(bot, ev: CQEvent):   
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '无权进行该操作！', at_sender=True)
    gid = ev.group_id
    dai = DAICounter()
    umlist = dai._get_BC_list(gid)
    for s in range(len(umlist)):
        uid = int(umlist[s])   
        dai._delete_BC(gid,uid)
    await bot.finish(ev, '已清空目前记录的补偿刀数据！')

@sv.scheduled_job('cron', hour ='*',)
async def clock():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if now.hour !=5 and now.hour !=4:
        return
    dai = DAICounter()
    bot = nonebot.get_bot()
    mlist = await bot.get_group_list()
    d = {}
    for m in mlist:
        d[m['group_id']] = m['group_id']
    value_list = list(d.values())
    for e in range(len(value_list)):
        gid = int(value_list[e])
        server = 0
        try:
            server = str(await get_group_sv(gid))
        except:
            server = "cn" #获取失败时，转而认定为国服
        if server == "cn" or "tw":
            if not now.hour == 5: #每天5点结算
                return
        if server == "jp":
            if not now.hour == 4: #日服每天4点结算
                return   
        umlist = dai._get_SH_uid_list(gid)  
        if umlist !=0:
            for s in range(len(umlist)):
                uid = int(umlist[s])
                dai._delete_SH(gid,uid)
        umlist = dai._get_GS_uid_list(gid)
        if umlist !=0:
            for s in range(len(umlist)):
                uid = int(umlist[s])
                dai._delete_GS(gid,uid)
        umlist = dai._get_DD_uid_list(gid)
        if umlist !=0:
            for s in range(len(umlist)):
                uid = int(umlist[s])
                dai._delete_DAIDAO_owner(gid,uid)
        umlist = dai._get_ZZ_uid_list(gid)
        if umlist !=0:
            for s in range(len(umlist)):
                uid = int(umlist[s])
                dai._delete_ZZ_Suo(gid,uid)
        umlist = dai._get_BC_list(gid)
        if umlist !=0:
            for s in range(len(umlist)):
                uid = int(umlist[s])   
                dai._delete_BC(gid,uid)

@sv.scheduled_job('cron', hour ='*',)
async def checkupdate():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if now.hour !=5:
        return
    bot = nonebot.get_bot()
    log = check_update()
    if log != True:
        await bot.send_private_msg(user_id=int(SUPERUSERS[0]), message=log)

async def get_dao(gid:str) -> str:
    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
    with open(os.path.join(os.path.dirname(__file__),f"data.json"), "w", encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4,ensure_ascii=False))
    challenges = data['challenges']
    dao = {}
    members = data['members']
    print(challenges)
    for member in members:
        dao[member['qqid']] = 0
    for challenge in challenges:
        if challenge['is_continue'] == False:
            num = 1
        else:
            num = 0
        if challenge['damage'] == 0:
            continue
        if challenge['behalf'] == None or challenge['behalf'] == challenge['qqid']:
            dao[challenge['qqid']] += num
        if challenge['behalf'] != None:
            continue
    return dao

async def get_dai(gid:str) -> str:
    apikey = get_apikey(gid)
    url = f'{yobot_url}clan/{gid}/statistics/api/?apikey={apikey}'
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        data = await resp.json()
    with open(os.path.join(os.path.dirname(__file__),f"data.json"), "w", encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4,ensure_ascii=False))
    challenges = data['challenges']
    dai = {}
    members = data['members']
    for member in members:
        dai[member['qqid']] = 0
    for challenge in challenges:
        if challenge['is_continue'] == False:
            num = 1
        else:
            num = 0
        if challenge['damage'] == 0:
            continue
        if challenge['behalf'] == None:
            continue
        if challenge['behalf'] != None and challenge['behalf'] != challenge['qqid']:
            dai[challenge['behalf']] += num
    return dai

@sv.on_fullmatch('代刀表')
async def cddqk(bot,ev):
    gid = ev.group_id
    dao = await get_dao(gid)
    dai = await get_dai(gid)
    newdao = ''
    for qq in dao:
        try:
            name = (await bot.get_group_member_info(group_id=ev.group_id,user_id=qq))['nickname']
        except:
            name = "不在群成员"
        if dao[qq]+dai[qq] != 0:
            newdao += name + ':' + '出刀'+str(dao[qq]) + '刀 ' + '  代刀' + str(dai[qq]) + '刀' + '   总出刀' + str(dao[qq]+dai[qq]) + '刀\n'
    await bot.send(ev,str(newdao))

@sv.on_prefix(["合刀"])
async def hedao(bot, ev):
    args = ev.message.extract_plain_text().split()
    if not args:
        return
    if len(args) < 2:
        return
    gid = str(ev['group_id'])
    if len(args) == 2:
        boss_HP[gid] = float(await get_boss_HP(gid))
    if len(args) == 3:
        boss_HP[gid] = args[2]
    server = str(await get_group_sv(gid))
    if server == 'cn':
        bz = 10
        mode = '国服'
    else:
        bz = 20
        mode = '日/台服'
    a = float(args[0])
    b = float(args[1])
    if a < 10000:
        a = 10000 * a
    if b < 10000:
        b = 10000 * b
    c = float(boss_HP[gid])
    if c < 10000:
        c = 10000 * c
    d = int(c)
    if a>c :
        time = ((1-(c)/a)*90+bz)
        if time > 90 :
            time = (90)
        time = math.ceil(time)
        msg = f"存在可以直接收尾的刀，请确认！刀1直出可补偿{time}秒"
        await bot.send(ev, msg)
    if b>c :
        time2 = ((1-(c)/b)*90+bz)
        if time2 > 90 :
            time2 = (90)
        time2 = math.ceil(time2)
        msg = f"存在可以直接收尾的刀，请确认！刀2直出可补偿{time2}秒"
        await bot.send(ev, msg)
    if (a+b>c):
        time = ((1-(c-a)/b)*90+bz)
        if time > 90 :
            time = (90)
        time2 = ((1-(c-b)/a)*90+bz)
        if time2 > 90 :
            time2 = (90)
        time = math.ceil(time)
        time2 = math.ceil(time2)
        msg = f"当前BOSS血量为{d}\n若1先2后，则补偿{time}秒，若2先1后，则补偿{time2}秒\n当前群为{mode}！"
        await bot.send(ev, msg)
    if (a+b<c):
        msg = f"当前BOSS血量为{d}\n这两刀打不死！"
        await bot.send(ev, msg)