from astrbot.api.all import *
from astrbot.api.message_components import Image as BotImage
import requests
import logging
from typing import Optional
from astrbot.api.message_components import *
from astrbot.core.message.components import Image, Plain



# 配置日志
logger = logging.getLogger(__name__)

@register("animedb api的动漫识别插件", "rikka", "anime_trace", "1.0.0")
class AnimeTracePlugin(Star):
    
    API_URL = "https://api.animetrace.com/v1/search"
    
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.model = self.config.get("model", "pre_stable")
        self.num = self.config.get("num", 3)
        self.ai = self.config.get("ai", 1)
        self.img = {}
        
        
        
    @command_group("anime")
    async def anime(self, event: AstrMessageEvent):
        '''动漫角色识别插件'''
        pass
        
    @anime.command("帮助")
    async def set_help(self, event: AstrMessageEvent):
        """显示动漫角色识别插件的完整帮助信息"""
        help_text = """
        📘 动漫角色识别插件帮助

        🔍 主要功能:
        /anime 识图+[图片]  -- 识别图片中的动漫角色

        ⚙️ 设置选项:
        1. 设置默认识别模型:
        /anime 模型 <模型名称>
        可用模型: 
        [1] pre_stable (默认)
        [2] anime_model_lovelive
        [3] anime
        [4] full_game_model_kira

        2. 设置AI模式:
        /anime ai [1/2]
        1: 开启 (默认) | 2: 关闭

        3. 设置显示匹配角色数量:
        /anime num [1-10]
        默认显示前3个匹配结果
        
        📊模型介绍:
        [1] pre_stable: 适用于(同人,原画)等
        [2] anime_model_lovelive: 适用于各种场景
        [3] anime: 适用于动漫原画
        [4] full_game_model_kira: 适用于galgame
        """
        yield event.plain_result(help_text.strip())


    @anime.command("num")
    async def set_num(self, event: AstrMessageEvent, num: int):
        '''设置显示匹配角色数量'''
        if num < 1 or num > 10:
            yield event.plain_result("❌ 无效数量，范围：1-10")
            logger.error(f"无效数量：{num}")
            return
        self.config["num"] = num
        yield event.plain_result(f"✅ 已设置显示匹配角色数量为: {num}")
        
    @anime.command("ai")
    async def set_ai(self, event: AstrMessageEvent, ai: int):
        '''设置ai'''
        aion = {1: "开启", 2: "关闭"}
        if ai not in [1, 2]:
            yield event.plain_result("❌ 无效ai，可选：1, 2")
            logger.error(f"无效ai：{ai}")
            return
        self.config["ai"] = ai
        yield event.plain_result(f"✅ 已切换ai为: {aion[ai]},")
        
    

    @anime.command("识图")
    async def recognize_anime(self, event: AstrMessageEvent):
        '''识别图片中的动漫角色'''

        # 获取图片数据
        image_data = await self.extract_image_data(event)
        self.img = image_data
        
        if not image_data:
            yield event.plain_result("❌ 未检测到有效图片")
            return

        # 调用API
        try:
            result = await self.call_animetrace_api(image_data)
            if result["code"] not in [0, 17731]:
                # 修改这行，传入event参数
                yield self.handle_api_error(result, event)
                return
                
            yield self.format_results(result["data"], event)
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            yield event.plain_result("🔧 服务暂时不可用，请稍后再试")

    @anime.command("模型")
    async def set_model(self, event: AstrMessageEvent, model_name: str):
        '''设置默认识别模型'''
        available_models = ["pre_stable", "anime_model_lovelive", "anime","full_game_model_kira"]
        if model_name not in available_models:
            labeled_models = [f'[{i+1}] {model}' for i, model in enumerate(available_models)] # 添加了数字标签
            available_models_str = '\n'.join(labeled_models) # 用带有标签的模型字符串列表生成最终字符串
            yield event.plain_result(f"❌ 无效模型，可选：\n{available_models_str}")
            return
        
        if model_name == self.config["model"]:
            yield event.plain_result(f"❌ 默认模型已经是：{model_name}")
            return
        self.config["model"] = model_name
        yield event.plain_result(f"✅ 已切换默认模型为：{model_name}")
        print(self.config)

    async def extract_image_data(self, event: AstrMessageEvent) -> Optional[dict]:
        '''从消息中提取图片数据'''
        # 优先处理直接上传的图片
        for component in event.message_obj.message:
            logger.info(f"{component}")
            if isinstance(component, Image):
                if component.url.startswith("http"):
                    return {"url": component.url}
                else:
                    return {"file": component.file}
        
        # 处理文字中的URL或base64
        
        text = event.message_str.strip()
        if text.startswith("http"):
            return {"url": text}
        elif len(text) > 100:  # 简单判断base64
            return {"base64": text}
        
        return None

    async def call_animetrace_api(self, image_data: dict) -> dict:
        '''调用识别API'''
        ai = self.config["ai"]
        payload = {
            "is_multi": 1,
            "model": self.config["model"],
            "ai_detect": ai
        }
        
        # 处理不同输入类型
        if "file" in image_data:
            files = {"file": open(image_data["file"], "rb")}
            response = requests.post(self.API_URL, data=payload, files=files)
        else:
            payload.update(image_data)
            response = requests.post(self.API_URL, json=payload)
        
        return response.json()

    def format_results(self, results: list, event: AstrMessageEvent):
        '''格式化识别结果'''
        if not results:
            logger.info(f"{results}")
            return event.plain_result("🔍 未识别到匹配角色")
        
        # 获取第一个检测框的所有角色匹配结果
        characters = results[0].get('character', [])
        num = self.config["num"]
        if not characters:
            logger.info(f"{results}")
            return event.plain_result("🔍 未识别到匹配角色")
        
        
        # 只显示前3个匹配结果
        top_characters = characters[:num]
        
        # 构建消息链
        chains = [
            Image.fromURL(self.img['url']),
            Plain("🎯 角色识别结果：\n") 
        ]
        
        # 添加每个匹配的角色信息
        for idx, char in enumerate(top_characters, 1):
            chains.append(Plain(
                f"{idx}. {char['character']} 「{char['work']}」\n"
            ))
        
        # 如果结果超过3个，添加提示信息
        if len(characters) > 3:
            chains.append(Plain(f"\n（共{len(characters)}个匹配结果，已显示前3项）"))
            
        
        return event.chain_result(chains)


    def handle_api_error(self, result: dict, event: AstrMessageEvent):
        '''处理API错误'''
        
        msg = result['zh_message']
        logger.error(f"API错误：{msg}（code：{result}")
        return event.plain_result(f"❌ 错误：{msg}（code：{result['code']}）")
    
    


    @llm_tool(name="search_anime")
    async def search_anime_tool(self, event: AstrMessageEvent):
        '''根据用户希望识别图片角色时调用此工具
        '''
        
        image_data = await self.extract_image_data(event)
        self.img = image_data
        
        if not image_data:
            
            return

        # 调用API
        try:
            result = await self.call_animetrace_api(image_data)
            if result["code"] not in [0, 17731]:
                # 修改这行，传入event参数
                yield self.handle_api_error(result, event)
                return
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            
        
      