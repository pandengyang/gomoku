from langchain_openai import ChatOpenAI

# 教学版按需求使用硬编码配置
API_KEY = "your_api_key"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
TEMPERATURE = 0.2
TIMEOUT_SECONDS = 20

_MODEL: ChatOpenAI | None = None


def create_chat_model() -> ChatOpenAI:
    """
    创建或返回单例 ChatOpenAI 客户端（DeepSeek API）。

    参数：
    无

    返回：
    已配置 model、base_url、temperature 的 ChatOpenAI 实例
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if not API_KEY or API_KEY == "your_api_key":
        raise ValueError("请先在 agent/client.py 中填写有效的 API_KEY。")

    _MODEL = ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=TEMPERATURE,
        timeout=TIMEOUT_SECONDS,
        extra_body={
            "thinking": {"type": "disabled"} # 关闭思考模式
        },
    )
    return _MODEL
