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
    async def show_help(self, event: AstrMessageEvent):
        '''显示插件帮助信息'''
        yield event.plain_result("📖 动漫角色识别帮助：\n/anime 识图 + [图片] ----发送图片进行角色识别\n/anime 模型 <pre_stable, anime_model_lovelive, anime> ----设置默认识别模型\n/anime ai [1/2] ----设置ai\n/anime num [1-10] ----设置显示匹配角色数量")
        
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
        available_models = ["pre_stable", "anime_model_lovelive", "anime"]
        if model_name not in available_models:
            yield event.plain_result(f"❌ 无效模型，可选：{', '.join(available_models)}")
            logger.error(f"无效模型：{model_name}")
            return
            
        self.config["model"] = model_name
        yield event.plain_result(f"✅ 已切换默认模型为：{model_name}")

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
        error_map = {
            17701: "图片大小超过5MB限制",
            17705: "仅支持JPEG/PNG格式",
            17731: "服务器繁忙，请稍后再试"
        }
        
        msg = error_map.get(result["code"], "识别服务暂时不可用")
        logger.error(f"API错误：{msg}（代码：{result}")
        return event.plain_result(f"❌ 错误：{msg}（代码：{result['code']}）")
    
    


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
            
        
      