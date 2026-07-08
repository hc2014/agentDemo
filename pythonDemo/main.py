import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import requests
from starlette.middleware.cors import CORSMiddleware

# 1. 初始化 FastAPI 项目
app = FastAPI(
    title="智能助手 API 服务", 
    version="1.0.0",
    description="提供天气、新闻、航班查询等功能的 RESTful API"
)

# 2. 添加 CORS 跨域中间件（方便前端或 Dify 等 AI 平台调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 定义统一返回数据模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: dict = None

# ==================== 业务接口实现 ====================
@app.get("/api/v1/weather", response_model=ResponseModel, summary="查询实时天气")
def get_weather(location: str = Query(..., description="城市名称，如：北京")):
    """
    根据城市名称查询实时天气信息。
    使用 Open-Meteo 免费 API。
    """
    try:
        # 1. 获取经纬度
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=zh"
        geo_response = requests.get(geo_url, timeout=5).json()
        
        if "results" not in geo_response:
            raise HTTPException(status_code=404, detail=f"找不到 '{location}' 的地理坐标")
            
        lat = geo_response["results"][0]["latitude"]
        lon = geo_response["results"][0]["longitude"]
        city_name = geo_response["results"][0]["name"]

        # 2. 获取实时天气
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Shanghai"
        weather_response = requests.get(weather_url, timeout=5).json()
        
        current = weather_response["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]
        weathercode = current["weathercode"]

        # 简单的天气代码转换
        weather_desc = "晴天" if weathercode == 0 else "多云" if weathercode < 4 else "雨天" if weathercode < 7 else "雪天"

        return ResponseModel(
            code=200, 
            msg="请求成功", 
            data={
                "city": city_name,
                "temperature": f"{temp}°C",
                "weather": weather_desc,
                "windspeed": f"{windspeed} km/h"
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取天气信息时发生错误: {str(e)}")


@app.get("/api/v1/news", response_model=ResponseModel, summary="查询最新新闻")
def get_news(keyword: str = Query(..., description="搜索关键词，如：人工智能")):
    """
    根据关键词搜索最新的新闻标题和摘要。
    使用 NewsData.io 免费 API。
    """
    try:
        # 注意：实际使用时，请替换为你在 newsdata.io 申请的真实 API Key
        api_key = "pub_586779630ed113f2e28e1e91c436d14146118" 
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={keyword}"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get("status") == "success" and data.get("results"):
            news_items = data["results"][:3] # 默认只返回前3条
            formatted_news = []
            for item in news_items:
                formatted_news.append({
                    "title": item.get("title", "无标题"),
                    "description": (item.get("description", "暂无摘要") or "")[:100] + "...",
                    "link": item.get("link", "#")
                })
            return ResponseModel(code=200, msg="请求成功", data={"keyword": keyword, "news_list": formatted_news})
        else:
            raise HTTPException(status_code=404, detail=f"暂时没有找到关于 '{keyword}' 的相关新闻")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻时发生错误: {str(e)}")


@app.get("/api/v1/flight", response_model=ResponseModel, summary="查询航班状态")
def get_flight(flight_number: str = Query(..., description="航班号，如：CA1833")):
    """
    根据航班号查询航班的实时状态、起降时间等信息。
    (注：此处为模拟数据返回，实际生产需对接真实航班数据源)
    """
    try:
        # 模拟返回数据（真实场景下这里会调用如 Flightera 等第三方航班 API）
        mock_data = {
            "flight_number": flight_number,
            "airline": "中国国际航空",
            "status": "准点",
            "scheduled_departure": "2026-07-08 16:00",
            "scheduled_arrival": "2026-07-08 18:30"
        }
        return ResponseModel(code=200, msg="请求成功", data=mock_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询航班信息时发生错误: {str(e)}")


# 5. 根路由测试
@app.get("/", summary="服务健康检查")
def root():
    return {"message": "智能助手 API 服务运行正常", "docs": "/docs"}