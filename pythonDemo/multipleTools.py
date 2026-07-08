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

# 2. 定义新闻查询工具
@tool
def get_latest_news(keyword: str) -> str:
    """
    当用户想要了解最新的新闻、时事、科技、体育等信息时，调用此工具。
    参数 keyword 是用户搜索的关键词。
    """
    # 这里使用一个免费的聚合新闻API作为示例
    # 注意：在实际生产环境中，你可能需要申请自己的API密钥
    url = f"https://newsdata.io/api/1/news?apikey=pub_586779630ed113f2e28e1e91c436d14146118&q={keyword}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "success" and data.get("results"):
            # 取前3条新闻标题和摘要
            news_items = data["results"][:3]
            result = f"为您找到关于 '{keyword}' 的最新新闻：\n\n"
            for i, item in enumerate(news_items, 1):
                title = item.get("title", "无标题")
                description = item.get("description", "暂无摘要")[:100] + "..."
                link = item.get("link", "#")
                result += f"{i}. **{title}**\n   {description}\n   [阅读原文]({link})\n\n"
            return result
        else:
            return f"抱歉，暂时没有找到关于 '{keyword}' 的相关新闻。"
    except Exception as e:
        return f"获取新闻时发生错误: {str(e)}"

# 3. 定义航班查询工具
@tool
def get_flight_status(flight_number: str) -> str:
    """
    当用户询问特定航班的状态、起飞时间、到达时间、延误情况时，调用此工具。
    参数 flight_number 是航班号，例如 "CA1833" 或 "CZ3101"。
    """
    # 这里使用一个模拟或测试用的航班API端点
    # 实际使用中请替换为付费或官方提供的航班查询API
    url = f"https://mock-flight-api.example.com/status/{flight_number}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("success"):
            flight = data["data"]
            status = flight.get("status", "未知") # 如：准点、延误、已起飞
            dep_time = flight.get("departure", {}).get("scheduled", "N/A")
            arr_time = flight.get("arrival", {}).get("scheduled", "N/A")
            airline = flight.get("airline", {}).get("name", "未知航司")
            
            return json.dumps({
                "flight_number": flight_number,
                "airline": airline,
                "status": status,
                "scheduled_departure": dep_man,
                "scheduled_arrival": arr_time
            }, ensure_ascii=False)
        else:
            return f"抱歉，未查询到航班 {flight_number} 的信息。"
    except Exception as e:
        return f"查询航班信息时发生错误: {str(e)}"

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
    tools=[get_current_weather, get_latest_news, get_flight_status], # 在这里添加新工具
    system_prompt="""
    你是一个功能强大的智能助手。请根据用户的需求，选择合适的工具来完成任务：
    1. 如果用户询问天气，请使用 get_current_weather 工具。
    2. 如果用户询问新闻、时事、热点，请使用 get_latest_news 工具。
    3. 如果用户询问航班号、航班状态、飞机起飞时间，请使用 get_flight_status 工具。
    
    请根据工具返回的结果，整理成自然、友好的语言回复给用户。
    """,
)

# 4. 运行测试
if __name__ == "__main__":
    print("正在测试智能体功能...")
    
    # 测试天气
    print("\n--- 测试天气查询 ---")
    response = agent.invoke({
        "messages": [{"role": "user", "content": "今天黄冈天气如何？"}]
    })
    print(response["messages"][-1].content)

    # 测试新闻
    print("\n--- 测试新闻查询 ---")
    response = agent.invoke({
        "messages": [{"role": "user", "content": "最近有什么关于人工智能的新闻？"}]
    })
    print(response["messages"][-1].content)

    # 测试航班
    print("\n--- 测试航班查询 ---")
    response = agent.invoke({
        "messages": [{"role": "user", "content": "帮我查一下航班号 CA183 的状态。"}]
    })
    print(response["messages"][-1].content)