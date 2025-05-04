"""
AI服务配置模块 - 用于与OpenAI API集成
"""
import os
import json
import logging
import aiohttp
import base64
from typing import Dict, Any, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

# AI服务配置
class AIServiceConfig:
    """AI服务配置"""
    
    # OpenAI API配置
    API_KEY = os.environ.get("OPENAI_API_KEY", "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")
    API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # 图像识别模型
    VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4-vision-preview")
    # 对话模型
    CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")

class AIService:
    """OpenAI服务接口"""
    
    @staticmethod
    async def analyze_image(image_path: str, prompt: str, products_info: List[Dict]) -> Dict[str, Any]:
        """分析图像内容
        
        Args:
            image_path: 图像文件路径
            prompt: 提示词
            products_info: 产品信息列表，用于匹配
            
        Returns:
            分析结果
        """
        logger.info(f"分析图像: {image_path}")
        
        try:
            # 读取图像并转为base64
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # 构建产品列表文本
            products_text = "可用的产品列表:\n"
            for p in products_info:
                products_text += f"- ID: {p['id']}, 名称: {p['name']}, 价格: {p['price']}, 单位: {p['unit_type']}\n"
            
            # 构建完整提示
            full_prompt = f"""
            {prompt}
            
            {products_text}
            
            请识别这张图片中的订单信息，返回JSON格式的结果。
            请将识别到的产品名称与提供的产品列表进行匹配。
            """
            
            # 构建请求体
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AIServiceConfig.API_KEY}"
            }
            
            payload = {
                "model": AIServiceConfig.VISION_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的订单识别助手，负责从图片中识别订单内容。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": full_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 1500
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{AIServiceConfig.API_BASE}/chat/completions", 
                    headers=headers, 
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if "error" in result:
                        logger.error(f"OpenAI API错误: {result['error']}")
                        raise Exception(f"OpenAI API错误: {result['error']}")
                    
                    # 提取回复内容
                    response_text = result["choices"][0]["message"]["content"]
                    logger.info(f"OpenAI响应: {response_text[:200]}...")
                    
                    # 尝试从回复中提取JSON
                    try:
                        # 查找JSON部分
                        import re
                        json_matches = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                        
                        if json_matches:
                            json_str = json_matches[0]
                            recognition_result = json.loads(json_str)
                        else:
                            # 尝试直接解析整个响应
                            recognition_result = json.loads(response_text)
                        
                        # 处理识别结果
                        processed_items = []
                        
                        # 如果回复有标准格式
                        if "items" in recognition_result:
                            for item in recognition_result["items"]:
                                # 查找匹配的产品
                                product_name = item.get("name", "")
                                quantity = item.get("quantity", 1)
                                
                                matched_product = None
                                for p in products_info:
                                    if product_name.lower() in p["name"].lower() or p["name"].lower() in product_name.lower():
                                        matched_product = p
                                        break
                                
                                if matched_product:
                                    processed_items.append({
                                        "product_id": matched_product["id"],
                                        "product_name": matched_product["name"],
                                        "quantity": quantity,
                                        "unit_price": float(matched_product["price"]),
                                        "unit_type": matched_product["unit_type"],
                                        "confidence": 0.9  # 默认置信度
                                    })
                        
                        return {
                            "items": processed_items,
                            "original_text": recognition_result.get("original_text", response_text)
                        }
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析错误: {str(e)}, 尝试解析文本")
                        # 尝试从文本中提取产品信息
                        processed_items = []
                        
                        # 简单的文本处理
                        lines = response_text.strip().split('\n')
                        for line in lines:
                            for p in products_info:
                                if p["name"] in line:
                                    # 尝试提取数量
                                    import re
                                    quantity_matches = re.findall(r'\d+', line)
                                    quantity = int(quantity_matches[0]) if quantity_matches else 1
                                    
                                    processed_items.append({
                                        "product_id": p["id"],
                                        "product_name": p["name"],
                                        "quantity": quantity,
                                        "unit_price": float(p["price"]),
                                        "unit_type": p["unit_type"],
                                        "confidence": 0.8  # 降低置信度
                                    })
                                    break
                        
                        return {
                            "items": processed_items,
                            "original_text": response_text
                        }
        
        except Exception as e:
            logger.error(f"分析图像失败: {str(e)}")
            raise
    
    @staticmethod
    async def process_chat_adjustment(
        message: str, 
        current_items: List[Dict], 
        chat_history: List[Dict],
        all_products: List[Dict]
    ) -> Dict[str, Any]:
        """处理订单调整对话
        
        Args:
            message: 用户消息
            current_items: 当前订单项
            chat_history: 对话历史
            all_products: 所有可用产品
            
        Returns:
            处理结果
        """
        logger.info(f"处理调整请求: {message}")
        
        try:
            # 构建产品列表文本
            products_text = "可用的产品列表:\n"
            for p in all_products:
                products_text += f"- ID: {p['id']}, 名称: {p['name']}, 价格: {p['price']}, 单位: {p['unit_type']}\n"
            
            # 构建当前订单文本
            current_order_text = "当前订单项:\n"
            for item in current_items:
                current_order_text += f"- {item['product_name']}: {item['quantity']} {item['unit_type']}, 单价: {item['unit_price']}\n"
            
            # 构建系统提示
            system_prompt = f"""
            你是一个智能订单助手，负责帮助用户调整订单内容。
            
            {current_order_text}
            
            {products_text}
            
            请根据用户的消息调整订单内容。你可以：
            1. 替换产品（如"将A替换为B"）
            2. 添加产品（如"添加A，3份"）
            3. 删除产品（如"删除A"）
            4. 修改数量（如"A改为3份"）
            
            你的回复必须包含以下JSON格式，用于系统处理：
            
            ```json
            {{
              "items": [
                {{
                  "product_id": 产品ID,
                  "product_name": "产品名称",
                  "quantity": 数量,
                  "unit_price": 单价,
                  "unit_type": "单位类型"
                }}
              ],
              "response": "给用户的回复消息"
            }}
            ```
            """
            
            # 构建消息历史
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 添加对话历史
            for chat in chat_history:
                messages.append({
                    "role": chat["role"],
                    "content": chat["content"]
                })
            
            # 添加用户消息
            messages.append({"role": "user", "content": message})
            
            # 构建请求体
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {AIServiceConfig.API_KEY}"
            }
            
            payload = {
                "model": AIServiceConfig.CHAT_MODEL,
                "messages": messages,
                "max_tokens": 1500
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{AIServiceConfig.API_BASE}/chat/completions", 
                    headers=headers, 
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if "error" in result:
                        logger.error(f"OpenAI API错误: {result['error']}")
                        raise Exception(f"OpenAI API错误: {result['error']}")
                    
                    # 提取回复内容
                    response_text = result["choices"][0]["message"]["content"]
                    logger.info(f"OpenAI响应: {response_text[:200]}...")
                    
                    # 尝试从回复中提取JSON
                    try:
                        # 查找JSON部分
                        import re
                        json_matches = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                        
                        if json_matches:
                            json_str = json_matches[0]
                            adjustment_result = json.loads(json_str)
                            
                            return adjustment_result
                        else:
                            # 如果没有找到JSON，返回原始消息和未更改的订单项
                            logger.warning("未找到JSON格式的响应")
                            return {
                                "items": current_items,
                                "response": "很抱歉，我无法理解您的请求。请尝试使用更明确的指令，如'添加产品'、'删除产品'或'修改数量'。"
                            }
                    
                    except Exception as e:
                        logger.error(f"处理调整响应失败: {str(e)}")
                        return {
                            "items": current_items,
                            "response": "处理请求时出现错误。请尝试使用更明确的指令，如'添加产品'、'删除产品'或'修改数量'。"
                        }
        
        except Exception as e:
            logger.error(f"调整订单失败: {str(e)}")
            return {
                "items": current_items,
                "response": f"处理请求时出现错误: {str(e)}"
            }
