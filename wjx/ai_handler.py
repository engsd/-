"""
AI 答案生成器模块
使用 OpenAI 兼容的 API 为填空题生成候选答案
"""
import json
import logging
from typing import List

import requests

from wjx.config import AI_API_KEY, AI_BASE_URL

# Mock 开关 - 调试时使用模拟数据，避免消耗 Token
USE_MOCK = False

# Mock 数据 - 5个固定测试答案
MOCK_ANSWERS = [
    "挺好的，继续保持",
    "还需要改进一下",
    "非常满意，感谢",
    "有些地方不太方便",
    "整体体验不错"
]


def generate_answers_for_question(question_title: str) -> List[str]:
    """
    为单个题目生成5个候选答案

    Args:
        question_title: 题目文本，如"您对食堂的建议是？"

    Returns:
        包含5个字符串的列表，如 ['回答1', '回答2', ...]
        失败时返回空列表
    """
    # ========== Mock 模式 ==========
    if USE_MOCK:
        logging.info("[AI Mock] 正在使用模拟 AI 数据")
        logging.debug(f"[AI Mock] 题目: {question_title[:30]}...")
        logging.info(f"[AI Mock] 返回5个模拟答案")
        return MOCK_ANSWERS.copy()

    # ========== 真实 API 模式 ==========
    if not AI_API_KEY:
        logging.warning("[AI] AI_API_KEY 未配置，跳过 AI 生成")
        return []

    try:
        # 构造 Prompt
        prompt = f"请为问卷题目'{question_title}'生成 5 个简短、真实、口语化的回答。请直接返回 JSON 数组格式，不要包含 Markdown 标记。"

        logging.info(f"[AI] 正在为题目生成答案: {question_title[:50]}...")
        logging.debug(f"[AI] Prompt 内容: {prompt[:50]}...")

        # 构造 API 请求（OpenAI ChatCompletion 格式）
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 200
        }

        api_url = f"{AI_BASE_URL.rstrip('/')}/chat/completions"
        logging.debug(f"[AI] 发送请求到: {api_url}")

        # 发送请求
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        # 记录响应状态
        logging.info(f"[AI] API 响应状态码: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"[AI] API 请求失败: {response.status_code} - {response.text[:200]}")
            return []

        # 解析响应
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        logging.debug(f"[AI] 原始响应内容: {content[:100]}...")

        # 提取 JSON 数组
        answers = _parse_ai_response(content)

        if answers:
            logging.info(f"[AI] 成功生成 {len(answers)} 个答案: {answers}")
            return answers
        else:
            logging.warning(f"[AI] 未能从响应中解析出有效答案")
            return []

    except requests.exceptions.Timeout:
        logging.error("[AI] API 请求超时（30秒）")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"[AI] API 请求异常: {e}")
        return []
    except (KeyError, IndexError) as e:
        logging.error(f"[AI] 响应格式解析失败: {e}")
        return []
    except Exception as e:
        logging.error(f"[AI] 未知错误: {e}", exc_info=True)
        return []


def _parse_ai_response(content: str) -> List[str]:
    """
    从 AI 响应中解析 JSON 数组

    Args:
        content: AI 返回的文本内容

    Returns:
        解析出的字符串列表
    """
    try:
        # 尝试直接解析 JSON
        answers = json.loads(content)
        if isinstance(answers, list):
            return [str(a) for a in answers[:5]]
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 代码块
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end > start:
            try:
                answers = json.loads(content[start:end].strip())
                if isinstance(answers, list):
                    return [str(a) for a in answers[:5]]
            except json.JSONDecodeError:
                pass

    # 尝试提取普通数组
    if "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end > start:
            try:
                answers = json.loads(content[start:end].strip())
                if isinstance(answers, list):
                    return [str(a) for a in answers[:5]]
            except json.JSONDecodeError:
                pass

    logging.debug(f"[AI] JSON 解析失败，原始内容: {content[:200]}")
    return []
