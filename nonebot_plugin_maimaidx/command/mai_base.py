from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER

from ..libraries.maimaidx_music_info import *
from ..libraries.maimaidx_player_score import *
from ..libraries.maimaidx_update_plate import *
from ..libraries.tool import qqhash

allhelp    = on_command('帮助', aliases={'help',"bothelp"})
update_data = on_command('更新maimai数据', permission=SUPERUSER)
maimaidxhelp = on_command('帮助maimaiDX', aliases={'帮助maimaidx'})
maimaidxrepo = on_command('项目地址maimaiDX', aliases={'项目地址maimaidx'})
mai_today = on_command('今日mai', aliases={'今日舞萌', '今日运势'})
mai_nearcade = on_command('附近机厅', aliases={'机厅查询'})
mai_what = on_regex(r'.*mai.*什么(.+)?')
random_song = on_regex(r'^[随来给]个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?).*')



@update_data.handle()
async def _(event: PrivateMessageEvent):
    await mai.get_music()
    await mai.get_music_alias()
    await update_data.finish('maimai数据更新完成')

@maimaidxhelp.handle()
async def _():
    await maimaidxhelp.send(MessageSegment.image(image_to_base64(Image.open(Root / 'maimaidxhelp.png'))),reply_message=True)
    await maimaidxhelp.finish("""
🎵 舞萌DX Bot 命令帮助

🔍 玩家数据查询（所有都可以用qq号视奸别人）
- b40 - 查询您的 Best 40 成绩单
- ap50/ap+50 - 查询AP(All Perfect)成绩单/理论值成绩单
- fc50/fc50+ - 查询Full Combo成绩单
- 我有多菜 - 查看水鱼榜排名

🎮 特色成绩单
- 拟合50 - 拟合算法生成的B50
- pcb50 - 通过游玩次数生成的B50
- 三星b50/四星b50/五星b50 - 按星级筛选的B50
- ab50/b100 - 全部歌曲B50/扩展版B100
- 绿50/黄50/红50 - 按难度(Basic/Advanced/Expert)筛选
- 紫50/白50 - 高难度(Master/Remaster)筛选
- 绿分数列表/黄分数列表/红分数列表 - 按难度(Basic/Advanced/Expert)筛选
- 紫分数列表/白分数列表 - 高难度(Master/Remaster)筛选

🌟 主题成绩单
- 术力口50 - VOCALOID曲目专题
- 东方50 - 东方Project曲目专题
- 动漫50 - 动漫流行曲专题
- 越级50 - 越级挑战曲目
- 寸止50 - 高难度收尾曲目
- 锁血50 - 低血量通关曲目

🔗 账号功能
- bind - 绑定舞萌DX账号
- seeme - 查看绑定信息
- 舞萌足迹 - 查看游玩历程
- maicard - 生成舞萌卡片
- 绑定帮助 - 查看绑定教程
- gb/同步/syup/导/上传/导入 - 手动同步数据

💡 使用提示
1. 所有命令均支持大小写混合
2. 成绩单命令大多有别名(如b50/B50/maib50)
3. 首次使用请先使用bind绑定账号
4. 查询结果可能需要3-5秒生成
""")

@mai_nearcade.handle()
async def _():
    await maimaidxrepo.finish(
        'https://nearcade.phi.zone/',
        reply_message=True
    )


@maimaidxrepo.handle()
async def _():
    await maimaidxrepo.finish(
        '项目地址：https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx\n求star，求宣传~',
        reply_message=True
    )


@mai_today.handle()
async def _(event: MessageEvent):
    wm_list = [
        '拼机',
        '推分',
        '越级',
        '下埋',
        '夜勤',
        '练底力',
        '练手法',
        '打旧框',
        '干饭',
        '抓绝赞',
        '收歌'
    ]
    h = qqhash(event.user_id)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f'\n今日人品值：{rp}\n'
    for i in range(11):
        if wm_value[i] == 3:
            msg += f'宜 {wm_list[i]}\n'
        elif wm_value[i] == 0:
            msg += f'忌 {wm_list[i]}\n'
    music = mai.total_list[h % len(mai.total_list)]
    ds = '/'.join([str(_) for _ in music.ds])
    msg += f'{maiconfig.botName} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲：'
    msg += f'ID.{music.id} - {music.title}'
    msg += MessageSegment.image(music_picture(music.id))
    msg += ds
    await mai_today.finish(msg, reply_message=True)


@mai_what.handle()
async def _(event: MessageEvent, match=RegexMatched()):
    music = mai.total_list.random()
    user = None
    if (point := match.group(1)) and ('推分' in point or '上分' in point or '加分' in point):
        try:
            user = await maiApi.query_user_b50(qqid=event.user_id)
            r = random.randint(0, 1)
            _ra = 0
            ignore = []
            if r == 0:
                if sd := user.charts.sd:
                    ignore = [m.song_id for m in sd if m.achievements < 100.5]
                    _ra = sd[-1].ra
            else:
                if dx := user.charts.dx:
                    ignore = [m.song_id for m in dx if m.achievements < 100.5]
                    _ra = dx[-1].ra
            if _ra != 0:
                ds = round(_ra / 22.4, 1)
                musiclist = mai.total_list.filter(ds=(ds, ds + 1))
                for _m in musiclist:
                    if int(_m.id) in ignore:
                        musiclist.remove(_m)
                music = musiclist.random()
        except (UserNotFoundError, UserDisabledQueryError):
            pass
    await mai_what.finish(await draw_music_info(music, event.user_id, user))


@random_song.handle()
async def _(match=RegexMatched()):
    try:
        diff = match.group(1)
        if diff == 'dx':
            tp = ['DX']
        elif diff == 'sd' or diff == '标准':
            tp = ['SD']
        else:
            tp = ['SD', 'DX']
        level = match.group(3)
        if match.group(2) == '':
            music_data = mai.total_list.filter(level=level, type=tp)
        else:
            music_data = mai.total_list.filter(
                level=level,
                diff=['绿黄红紫白'.index(match.group(2))],
                type=tp
            )
        if len(music_data) == 0:
            msg = '没有这样的乐曲哦。'
        else:
            msg = await draw_music_info(music_data.random())
    except:
        msg = '随机命令错误，请检查语法'
    await random_song.finish(msg, reply_message=True)




async def data_update_daily():
    await mai.get_music()
    mai.guess()
    log.info('maimaiDX数据更新完毕')