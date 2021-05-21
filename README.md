# 小真步代刀提醒插件 BY：光的速度（2）  
## 请注意！这是一个测试版！
## 说明  
这个插件是基于其他大佬的插件照葫芦画瓢写的代刀便利通知系统，主要是针对Hoshinobot+Yobot的用户   
如果有研究过我的贵族决斗版本，会发现他们的代码非常相似（）   
## 已知问题  
和yobot的查树重复响应，有能力的话可以把yobot关于查树的指令改掉  
和挂树计时冲突  
该插件的所有功能使用前，必须保证已经创建公会，且至少有一刀数据，否则会报错   
如果有发现其他问题，请立刻联系我或提issues！
### 新的版本已经完全重构了，改动如下  
- 1.使用数据库存储代刀数据，重启不再丢失数据  
- 2.记录代刀现在会记录发起代刀的周目和BOSS号  
- 3.追加正在代刀的人和补偿刀  
- 4.可以轻松的清除记录了  
- 5.代刀，查询代刀，取消代刀可以一次性@多个人了  
- 6.私聊失败时，不再会导致插件异常而是会在群里提醒了  
主要功能有：
1.代刀自动私聊    
2.代挂树私聊 
3.代SL私聊   
4.记录暂停伤害   
5.记录锁助战情况   
来自开学以后代刀量猛增，上期还出现重复代刀结果被顶号的头秃会长被迫写的插件。  
可随意取用，修改，欢迎给我提建议！  
随意写的……BUG肯定会有的。  
使用方法是：  

| 关键词     | 作用     |
| :-------------: | :-------------:|
|代刀中@成员  | 发起代刀         
|取消代刀(@成员) |取消对某成员的代刀 
|SL@成员|告知成员使用了SL
|挂树@成员|代报挂树，并私聊告知
|代刀列表|查看目前正在被代刀的人的列表
|补偿刀列表 |查看目前已被登记的补偿刀
|查询代刀(@成员)| 可以查询自己或其他成员是否在被代刀  
|查树|查看当前在树上的人
|暂停:伤害（可以是文本）(@成员)|记录暂停伤害（可以代报）
|详细状态|查看目前锁助战，代刀，暂停，挂树的情况
|清空补偿数据|清空当前群的补偿记录
|清空代刀数据|清空当前群的代刀记录
|记录补偿刀：文本|记录当前群补偿刀
|代刀表|简易代刀表生成
|合刀 伤害1 伤害2 （血量）|计算合刀，自动获取服务器，可以手动输入血量，也可以自动获取血量

每天五点（日服四点）会清空所有数据！
复制该插件到hoshino\modules，然后在_bot_.py中开启即可  

### 目前正在测试，还没有经过公会战的洗礼，很有可能有无法预知的BUG！  
#### V0.2版本修正   
- 1.追加了挂树列表功能  
- 2.移除了部分错误的代码  
- 3.加入了”详细状态“指令，该指令一键查询目前存在的补偿刀，挂树情况  
- 4.追加了记录暂停伤害的功能  
#### V0.3版本修正
- 1.不兼容性更新，需要删库，更新了代刀伤害表，使现在可以报文本了，比如暂停：5s 400w
- 2.修正部分BUG
- 3.挂树模块更新
#### V0.4版本修正
- 1.不兼容性更新，需要删库，更新了补偿刀表，现在以文本方式记录
- 2.尝试加入了一个检查更新的东西，每天五点检查，当插件有新版本时，会通知超级管理员（如果有多个超级管理员，只会私聊通知第一个）
- 3.自行报挂树，暂停时，不再显示刀手了
- 4.挂树加了挂树计时
- 5.锁助战加了个冒号，避免误触
#### V0.5版本修正
- 1.加入了一个单独的暂停列表
- 2.现在没人暂停或者挂树时，尾刀将不再发送空消息
- 3.修正一个文本问题（取消挂树提示）
#### V0.6版本修正
- 1.适配了V0.94FIX4的group_id参数，您可选择性开启，开启后，当机器人为管理员时，可以主动发起私聊而不需要对方向机器人发起过私聊
已知问题：由于V1.0之后的GOCQ版本发送私聊消息会返回Code=100，插件的提示可能会出现异常，但功能正常使用
#### V0.7版本修正  
- 1.移除了锁助战模块（因为目前日台国均无锁助战）  
- 2.现在尾刀会自动记录一个补偿刀，您也可手动使用记录补偿刀：内容（@成员）来更新它  
- 3.随手写了一个简易的代刀表，但是很乱，希望有人PR个图片版本（）  
- 4.加入了合刀功能，该功能会自动获取yobot的血量，自动判断服务器，血量也可以手动输入。（计算式是我六七个月前写的，非常烂，能用就行）  
- 5.优化触发器，减少误触发[@mahosho](https://github.com/mahosho)  
- 6.优化日志处理方式[@A-kirami](https://github.com/A-kirami)  

感谢以下几位大佬
明见佬[@A-kirami](https://github.com/A-kirami) 优化日志处理方式  
魔法书佬[@mahosho](https://github.com/mahosho) 优化触发器  
[@mhy9989](github.com/mhy9989) BUG上报，内容测试  
感谢各位群友，感谢各位使用者！
yysy我一直以为这插件没人用的（），不过在别的群看到自己插件还是挺惊喜的  


