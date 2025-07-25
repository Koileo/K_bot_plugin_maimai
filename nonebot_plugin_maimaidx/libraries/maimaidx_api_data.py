from typing import Any, Dict

import httpx

from ..config import maiconfig
from .maimaidx_error import *
from .maimaidx_model import *


class MaimaiAPI:
    MaiProxyAPI = 'https://proxy.yuzuchan.xyz'

    MaiProberAPI = 'https://www.diving-fish.com/api/maimaidxprober'
    MaiCover = 'https://www.diving-fish.com/covers'
    MaiAliasAPI = 'https://www.yuzuchan.moe/api/maimaidx'
    QQAPI = 'http://q1.qlogo.cn/g'

    def __init__(self) -> None:
        """封装Api"""
        self.headers = None
        self.token = None
        self.MaiProberProxyAPI = None
        self.MaiAliasProxyAPI = None

    def load_token_proxy(self) -> None:
        self.MaiProberProxyAPI = self.MaiProberAPI if not maiconfig.maimaidxproberproxy else self.MaiProxyAPI + '/maimaidxprober'
        self.MaiAliasProxyAPI = self.MaiAliasAPI if not maiconfig.maimaidxaliasproxy else self.MaiProxyAPI + '/maimaidxaliases'
        self.token = maiconfig.maimaidxtoken
        if self.token:
            self.headers = {'developer-token': self.token}

    async def _requestalias(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        别名库通用请求

        Params:
            `method`: 请求方式
            `endpoint`: 请求接口
            `kwargs`: 其它参数
        Returns:
            `Dict[str, Any]` 返回结果
        """
        async with httpx.AsyncClient(timeout=30) as session:
            res = await session.request(method, self.MaiAliasProxyAPI + endpoint, **kwargs)
            if res.status_code == 200:
                data = res.json()['content']
                if data == {} or data == []:
                    raise AliasesNotFoundError
                if isinstance(data, str):
                    raise
            elif res.status_code == 201:
                data = res.json()
            elif res.status_code == 400:
                raise EnterError
            elif res.status_code == 500:
                raise ServerError
            else:
                raise UnknownError
        return data

    async def _requestmai(self, method: str, endpoint: str, **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        查分器通用请求

        Params:
            `method`: 请求方式
            `endpoint`: 请求接口
            `kwargs`: 其它参数
        Returns:
            `Dict[str, Any]` 返回结果
        """
        async with httpx.AsyncClient(timeout=30) as session:
            res = await session.request(method, self.MaiProberProxyAPI + endpoint, headers=self.headers, **kwargs)
            if res.status_code == 200:
                data = res.json()
            elif res.status_code == 400:
                error: Dict = res.json()
                if 'message' in error:
                    if error['message'] == 'no such user':
                        raise UserNotFoundError
                    elif error['message'] == 'user not exists':
                        raise UserNotExistsError
                    else:
                        raise UserNotFoundError
                elif 'msg' in error:
                    if error['msg'] == '开发者token有误':
                        raise TokenError
                    elif error['msg'] == '开发者token被禁用':
                        raise TokenDisableError
                    else:
                        raise TokenNotFoundError
                else:
                    raise UserNotFoundError
            elif res.status_code == 403:
                raise UserDisabledQueryError
            else:
                raise UnknownError
        return data

    async def music_data(self):
        """获取曲目数据"""
        return await self._requestmai('GET', '/music_data')

    async def chart_stats(self):
        """获取单曲数据"""
        return await self._requestmai('GET', '/chart_stats')

    async def query_user_b50(self, *, qqid: Optional[int] = None, username: Optional[str] = None) -> UserInfo:
        """
        获取玩家B50

        Params:
            `qqid`: QQ号
            `username`: 用户名
        Returns:
            `UserInfo` b50数据模型
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username
        json['b50'] = True

        return UserInfo.model_validate(await self._requestmai('POST', '/query/player', json=json))

    async def query_user_b40(self, *, qqid: Optional[int] = None, username: Optional[str] = None) -> UserInfo:
        """
        获取玩家B50

        Params:
            `qqid`: QQ号
            `username`: 用户名
        Returns:
            `UserInfo` b40数据模型
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username

        return UserInfo.model_validate(await self._requestmai('POST', '/query/player', json=json))


    async def query_user_plate(
            self,
            *,
            qqid: Optional[int] = None,
            username: Optional[str] = None,
            version: Optional[List[str]] = None
    ) -> List[PlayInfoDefault]:
        """
        请求用户数据

        Params:
            `qqid`: 用户QQ
            `username`: 查分器用户名
            `version`: 版本
        Returns:
            `List[PlayInfoDefault]` 数据列表
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username
        if version:
            json['version'] = version
        result = await self._requestmai('POST', '/query/plate', json=json)
        if not result['verlist']:
            raise MusicNotPlayError

        return [PlayInfoDefault.model_validate(d) for d in result['verlist']]

    async def query_user_dev(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username
        return await self._requestmai('GET', '/dev/player/records', params=params)


    async def query_user_get_dev(self, *, qqid: Optional[int] = None, username: Optional[str] = None) -> UserInfoDev:
        """
        使用开发者接口获取用户数据，请确保拥有和输入了开发者 `token`

        Params:
            qqid: 用户QQ
            username: 查分器用户名
        Returns:
            `UserInfoDev` 开发者用户信息
        """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

        result = await self._requestmai('GET', '/dev/player/records', params=params)
        return UserInfoDev.model_validate(result)

    async def query_user_post_dev(
            self,
            *,
            qqid: Optional[int] = None,
            username: Optional[str] = None,
            music_id: Union[str, int, List[Union[str, int]]]
    ) -> List[PlayInfoDev]:
        """
        使用开发者接口获取用户指定曲目数据，请确保拥有和输入了开发者 `token`

        Params:
            `qqid`: 用户QQ
            `username`: 查分器用户名
            `music_id`: 曲目id，可以为单个ID或者列表
        Returns:
            `List[PlayInfoDev]` 开发者成绩列表
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username
        json['music_id'] = music_id

        result = await self._requestmai('POST', '/dev/player/record', json=json)
        if result == {}:
            raise MusicNotPlayError

        if isinstance(music_id, list):
            return [PlayInfoDev.model_validate(d) for k, v in result.items() for d in v]
        return [PlayInfoDev.model_validate(d) for d in result[str(music_id)]]

    async def rating_ranking(self) -> List[UserRanking]:
        """
        获取查分器排行榜

        Returns:
            `List[UserRanking]` 按`ra`从高到低排序后的查分器排行模型列表
        """
        result = await self._requestmai('GET', '/rating_ranking')
        return sorted([UserRanking.model_validate(u) for u in result], key=lambda x: x.ra, reverse=True)

    async def get_plate_json(self) -> Dict[str, List[int]]:
        """获取所有版本牌子完成需求"""
        return await self._requestalias('GET', '/maimaidxplate')

    async def get_alias(self) -> Dict[str, Union[str, int, List[str]]]:
        """获取所有别名"""
        return await self._requestalias('GET', '/maimaidxalias')

    async def get_songs(self, name: str) -> Union[List[AliasStatus], List[Alias]]:
        """
        使用别名查询曲目。
        状态码为 `201` 时返回值为 `List[AliasStatus]`。
        状态码为 `200` 时返回值为 `List[Alias]`。

        Params:
            `name`: 别名
        Returns:
            `Union[List[AliasStatus], List[Alias]]`
        """
        result = await self._requestalias('GET', '/getsongs', params={'name': name})
        if 'status_code' in result:
            r = [AliasStatus.model_validate(s) for s in result['content']]
        else:
            r = [Alias.model_validate(s) for s in result]
        return r

    async def get_songs_alias(self, song_id: int) -> Alias:
        """
        使用曲目 `id` 查询别名

        Params:
            `song_id`: 曲目 `ID`
        Returns:
            `Alias`
        """
        result = await self._requestalias('GET', '/getsongsalias', params={'song_id': song_id})
        return Alias.model_validate(result)

    async def get_alias_status(self) -> List[AliasStatus]:
        """获取当前正在进行的别名投票"""
        result = await self._requestalias('GET', '/getaliasstatus')
        return [AliasStatus.model_validate(s) for s in result]

    async def post_alias(self, song_id: int, aliasname: str, user_id: int) -> AliasStatus:
        """
        提交别名申请

        Params:
            `id`: 曲目 `id`
            `aliasname`: 别名
            `user_id`: 提交的用户
        Returns:
            `AliasStatus`
        """
        json = {
            'SongID': song_id,
            'ApplyAlias': aliasname,
            'ApplyUID': user_id
        }
        return AliasStatus.model_validate(await self._requestalias('POST', '/applyalias', json=json))

    async def post_agree_user(self, tag: str, user_id: int) -> str:
        """
        提交同意投票

        Params:
            `tag`: 标签
            `user_id`: 同意投票的用户
        Returns:
            `str`
        """
        json = {
            'Tag': tag,
            'AgreeUser': user_id
        }
        return await self._requestalias('POST', '/agreeuser', json=json)

    async def transfer_music(self):
        """中转查分器曲目数据"""
        return await self._requestalias('GET', '/maimaidxmusic')

    async def transfer_chart(self):
        """中转查分器单曲数据"""
        return await self._requestalias('GET', '/maimaidxchartstats')

    async def qqlogo(self, qqid: int = None, icon: str = None) -> Optional[bytes]:
        """获取QQ头像"""
        session = httpx.AsyncClient(timeout=30)
        if qqid:
            params = {
                'b': 'qq',
                'nk': qqid,
                's': 100
            }
            res = await session.request('GET', self.QQAPI, params=params)
        elif icon:
            res = await session.request('GET', icon)
        else:
            return None
        return res.content


maiApi = MaimaiAPI()