import os
import json
import base64
import logging
import aiohttp
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_service")

class BaiduVoiceService:
    """百度语音服务"""
    
    # API配置
    API_KEY = os.environ.get("BAIDU_API_KEY", "")
    SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "")
    
    # 访问令牌
    access_token = None
    
    @classmethod
    async def get_access_token(cls):
        """获取百度API访问令牌"""
        if cls.access_token:
            return cls.access_token
            
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={cls.API_KEY}&client_secret={cls.SECRET_KEY}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                result = await response.json()
                if "access_token" in result:
                    cls.access_token = result["access_token"]
                    return cls.access_token
                else:
                    raise Exception(f"获取百度访问令牌失败: {result}")
    
    @classmethod
    async def speech_to_text(cls, audio_data: bytes, format: str = "wav", rate: int = 16000) -> str:
        """语音识别：将语音转换为文本
        
        Args:
            audio_data: 音频二进制数据
            format: 音频格式，如wav、pcm、amr
            rate: 采样率
            
        Returns:
            识别结果文本
        """
        token = await cls.get_access_token()
        url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=python&token={token}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "format": format,
            "rate": rate,
            "channel": 1,
            "token": token,
            "cuid": "python",
            "len": len(audio_data),
            "speech": base64.b64encode(audio_data).decode(),
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=json.dumps(data)) as response:
                result = await response.json()
                if "result" in result:
                    return result["result"][0]
                else:
                    logger.error(f"语音识别失败: {result}")
                    return ""
    
    @classmethod
    async def text_to_speech(cls, text: str, voice_type: int = 0) -> bytes:
        """语音合成：将文本转换为语音
        
        Args:
            text: 要合成的文本
            voice_type: 发音人选择，0为女声，1为男声，3为情感合成-度逍遥，4为情感合成-度丫丫
            
        Returns:
            音频二进制数据
        """
        token = await cls.get_access_token()
        url = f"https://tsn.baidu.com/text2audio"
        
        params = {
            "tok": token,
            "tex": text,
            "per": voice_type,
            "spd": 5,  # 语速，5为中等
            "pit": 5,  # 音调，5为中等
            "vol": 5,  # 音量，5为中等
            "aue": 6,  # 格式，3为mp3，6为wav
            "cuid": "python",
            "lan": "zh",  # 语言，zh为中文
            "ctp": 1,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                # 检查是否返回音频
                if response.headers.get("Content-Type").startswith("audio/"):
                    return await response.read()
                else:
                    result = await response.json()
                    logger.error(f"语音合成失败: {result}")
                    raise Exception(f"语音合成失败: {result}")
