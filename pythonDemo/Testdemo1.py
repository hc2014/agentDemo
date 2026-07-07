import os
from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

# 1. 定义系统提示（将用户ID直接写入提示词中，避免接口传参报错）
SYSTEM_PROMPT = """你是一位擅长用双关语表达的专家天气预报员。
你可以使用两个工具：
- get_weather_for_location：用于获取特定地点的天气
- get_user_location：用于获取用户的位置

当前系统上下文信息：
- 用户ID (user_id): 1

如果用户询问天气，请确保你知道具体位置。如果从问题中可以判断他们指的是自己所在的位置，请使用 get_user_location 工具来查找他们的位置。"""

# 2. 定义上下文模式
@dataclass
class Context:
    """自定义运行时上下文模式。"""
    user_id: str

# 3. 定义工具
@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取用户信息。"""
    # 从运行时上下文中获取 user_id
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"

# 4. 配置通义千问模型
model = ChatOpenAI(
    model="qwen-plus",
    api_key="sk-ws-H.EMDHMEY.0NFG.MEUCIQC3uP4JRgIItbQnwDB-DX3h8KPr1xiQ4u9qFChPomDbCgIgfsPtwIjk3hm2pgSeIV-OvKcQA5237ptO358yss_2ecY", # 你的百炼 API Key
    base_url="https://llm-e7m788c1nugxtk2f.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)

# 5. 定义响应格式（结构化输出）
@dataclass
class ResponseFormat:
    """代理的响应模式。"""
    # 带双关语的回应（始终必需）
    punny_response: str
    # 天气的任何有趣信息（如果有）
    weather_conditions: Optional[str] = None

# 6. 设置记忆
checkpointer = InMemorySaver()

# 7. 创建代理
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# 8. 运行代理
# `thread_id` 是给定对话的唯一标识符，用于记忆管理
config = {"configurable": {"thread_id": "1"}}

print("正在发起第一轮对话...")
response = agent.invoke(
    {"messages": [{"role": "user", "content": "外面的天气怎么样？"}]},
    config=config,
    # 将上下文对象传入，供 ToolRuntime 使用
    context=Context(user_id="1") 
)

print("\n第一轮结构化回复:")
print(response['structured_response'])

# 9. 测试多轮对话（使用相同的 thread_id）
print("\n正在发起第二轮对话...")
response = agent.invoke(
    {"messages": [{"role": "user", "content": "谢谢！"}]},
    config=config,
    context=Context(user_id="1")
)

print("\n第二轮结构化回复:")
print(response['structured_response'])