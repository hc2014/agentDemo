import json
import os
import requests
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

# 1. 定义天气查询工具
@tool
def get_current_weather(location: str) -> str:
    """当用户询问某个城市或地点的实时天气、温度、降水等信息时，必须调用此工具。"""
    try:
        # 获取经纬度
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=zh"
        geo_response = requests.get(geo_url).json()
        
        if "results" not in geo_response:
            return f"抱歉，我找不到 '{location}' 这个地点的地理坐标。"
            
        lat = geo_response["results"][0]["latitude"]
        lon = geo_response["results"][0]["longitude"]
        city_name = geo_response["results"][0]["name"]

        # 获取实时天气
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Shanghai"
        weather_response = requests.get(weather_url).json()
        
        current = weather_response["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]
        weathercode = current["weathercode"]

        # 简单的天气代码转换
        weather_desc = "晴天" if weathercode == 0 else "多云" if weathercode < 4 else "雨天" if weathercode < 7 else "雪天"

        return json.dumps({
            "city": city_name,
            "temperature": f"{temp}°C",
            "weather": weather_desc,
            "windspeed": f"{windspeed} km/h"
        }, ensure_ascii=False)
    except Exception as e:
        return f"获取天气信息时发生错误: {str(e)}"



API_KEY=os.getenv("QWEN_PLUS")

#print("API Key 读取结果:", API_KEY) 

# 2. 初始化模型
model = ChatOpenAI(
    model="qwen-plus",
    api_key=API_KEY,
    base_url="https://llm-e7m788c1nugxtk2f.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)

# 3. 使用 create_agent 创建智能体 (替代了 AgentExecutor)
agent = create_agent(
    model=model,
    tools=[get_current_weather],
    system_prompt="你是一个功能强大的智能助手。如果用户询问天气，请务必使用 get_current_weather 工具获取实时数据并回答。",
)

# 4. 运行测试
if __name__ == "__main__":
    print("正在查询黄冈天气...")
    # 新版调用方式
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": "今天黄冈天气如何？"}
        ]
    })
    # 提取最后的 AI 回复内容
    print("\n最终回复:", response["messages"][-1].content)