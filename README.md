</div>

<div align="center">

![:name](https://count.getloli.com/@anime_trace?name=anime_trace&theme=booru-jaypee&padding=7&offset=-5&align=top&scale=1&pixelated=1&darkmode=auto&num=0)

</div>

# 目前只支持aiohttp

# 使用animedb api进行动漫角色识别
- api文档<https://ai.animedb.cn/docs/#/introduction>

# 使用帮助
- `/anime 帮助` ---查看帮助
- `/anime 识图 [图片]` ----> 进行角色识别
- `/anime num <1-10>` ----> 获取识别角色判断的数量,`1-10`
- `/anime ai <1/2>` ----> 是否开启ai识别,`1`开启,`2`关闭
- `/anime 模型 <模型名>` ----> 进行模型切换
- 模型可选: `pre_stable`, `anime_model_lovelive`, `anime`
- 模型`anime_model_lovelive`高级动画识别模型①---->**适用于(同人,原画)等**
- 模型`pre_stable`高级动画识别模型②---->**适用于各种场景**
- 模型`anime`普通动画识别模型---->**适用于动漫原画**
- 模型`full_game_model_kira`---->**适用于galgame**

# LLM函数调用

  支持通过自然语言，比如: `这角色是谁 [图片]` 或者 `帮我识别一下这角色是谁 [图片]`

  需要模型支持函数调用，推荐 `gpt-4o-mini`

  关闭这个功能 `/tool off search_anime`

# 更新日志
- 新增`llm`函数调用
- 重构指令



# 支持
[帮助文档](https://astrbot.soulter.top/center/docs/%E5%BC%80%E5%8F%91/%E6%8F%92%E4%BB%B6%E5%BC%80%E5%8F%91/
)
