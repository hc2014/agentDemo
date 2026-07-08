# Ai Agent学习记录03 \-FastApi

### 搭建一个建议的API服务

安装fastapi服务包

```Python
pip install fastapi uvicorn
```



创建一个main\.py的文件

```Python
from fastapi import FastAPI
from pydantic import BaseModel

# 1. 初始化 FastAPI 项目
app = FastAPI(title="标准API服务", version="1.0")

# 2. 定义统一返回数据模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: dict = None

# 3. 编写接口（RESTful GET 示例）
@app.get("/api/v1/hello", response_model=ResponseModel, summary="测试接口")
def hello():
    """简易测试接口"""
    return ResponseModel(code=200, msg="请求成功", data={"content": "Hello FastAPI"})
```

在终端执行命令：

```Python
uvicorn main:app --reload --app-dir pythonDemo
```

如果文件名称不是main\.py，那么命令中对应修改main:app为xxx:app，另外 \-dir pythonDemo是当前执行环境的目录，我项目的绝对路径是：E:\\Demo\\agentDemo\\pythonDemo\\main\.py ，但是项目所在的目录是E:\\Demo\\agentDemo，所以需要制定 —dir参数，不然会提示找不到main模块



### 调试代码

#### 第一步：创建调试配置文件

1. 在 VS Code 中，按快捷键 `Ctrl+Shift+P` 打开命令面板。

2. 输入 `Debug: Add Configuration`（调试: 添加配置）并选择。

3. 在弹出的下拉菜单中选择 `Python Debugger`，然后选择 `FastAPI`。

4. 这会在你的项目根目录下自动创建一个 `.vscode/launch.json` 文件。

#### 第二步：修改 `launch.json` 配置

由于你的 `main.py` 在 `pythonDemo` 子目录下，你需要对自动生成的配置进行微调。请将 `configurations` 数组中的内容替换为以下配置：

```JSON
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "main:app",
                "--reload",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--app-dir", "pythonDemo"
            ],
            "jinja": true,
            "justMyCode": false
        }
    ]
}
```

核心配置解析（非常重要）：

- `"module": "uvicorn"`：这是调试 FastAPI 的绝对前提。千万不要写成 `"program": "main.py"`，否则异步上下文会丢失，断点将无法触发。

- `"args": [..., "--app-dir", "pythonDemo"]`：这里把你刚才成功运行的命令参数加了进来，告诉调试器去 `pythonDemo` 目录下找入口文件。

- `"justMyCode": false`：强烈建议设为 `false`。默认的 `true` 会让调试器跳过所有第三方库代码，设为 `false` 后你才能顺利调试 FastAPI 内部的依赖注入（`Depends`）和中间件逻辑。

#### 第三步：设置断点并启动调试

1. 打开 `E:\Demo\agentDemo\pythonDemo\main.py`。

2. 在你想要暂停执行的代码行（例如 `return ResponseModel(...)` 这一行）的左侧行号旁边点击，打上一个红色的圆点（断点）。

3. 按快捷键 `F5`（或点击左侧“运行和调试”面板的绿色播放按钮），选择刚才配置的 `FastAPI Debug` 启动调试。



### fastAPI接口升级

添加3个接口，查询新闻、天气、航班信息

```Python
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
```



执行命令提示服务运行成功：

```YAML
PS E:\Demo\agentDemo> uvicorn main:app --reload --app-dir pythonDemo
INFO:     Will watch for changes in these directories: ['E:\\Demo\\agentDemo']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12816] using StatReload
INFO:     Started server process [24788]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:60490 - "GET /docs/ HTTP/1.1" 307 Temporary Redirect
INFO:     127.0.0.1:60490 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:60490 - "GET /openapi.json HTTP/1.1" 200 OK
INFO:     127.0.0.1:60491 - "GET /api/v1/weather?location=%E6%9D%AD%E5%B7%9E HTTP/1.1" 200 OK

```

浏览器中访问：http://127\.0\.0\.1:8000/docs  可以看到各个接口



