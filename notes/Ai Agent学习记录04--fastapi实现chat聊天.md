# Ai Agent 学习记录04\-\-fastapi实现chat聊天

结合前面的案例，我想实现一个 通过添加一个api入口，用来获取用户数传入的数据，然后接口根据用户的数据，去调用对应的tools，并且把结果返回

需要注意的是第12行代码：from multipleTools import agent  ，原本的agent代码是写在了名为“multipleTools\.py”中，所以这里需要从该模块中引用agent对象

```Python
# -*- coding: utf-8 -*-
"""
agent_server.py
基于 LangChain Agent 的 FastAPI 服务入口
"""

import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from multipleTools import agent  

# 1. 定义请求和响应的数据模型
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    code: int
    msg: str
    data: str = None

# 2. 创建 FastAPI 应用
app = FastAPI(title="LangChain Agent API", version="1.0.0")

# 3. 定义 API 接口
@app.post("/chat", response_model=ChatResponse, summary="与智能体对话")
async def chat_endpoint(request: ChatRequest):
    """
    接收用户输入，调用 Agent 处理，并返回结果。
    """
    try:
        # 调用 Agent
        # 注意：agent.invoke 的输入结构需要符合你定义的 Agent 的要求
        response = agent.invoke({
            "messages": [HumanMessage(content=request.message)]
        })
        
        # 提取 Agent 返回的最终内容
        # 假设 response 是一个包含 messages 的字典，取最后一条消息的内容
        final_message = response.get("messages", [])[-1].content
        
        return ChatResponse(code=200, msg="请求成功", data=final_message)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

# 4. 根路径提示
@app.get("/")
async def root():
    return {"message": "Agent 服务运行正常，请访问 /docs 查看文档", "docs": "/docs"}

# --- 启动命令 ---
# 如果直接运行此文件，请取消下面的注释
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
```

启动服务以后，通过http://127\.0\.0\.1:8000/docs可以看到接口地址调用接口查看天气：

```YAML
curl -X 'POST' \
  'http://127.0.0.1:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "查一下杭州今天的天气"
}'
```

返回值：

```YAML
{
  "code": 200,
  "msg": "请求成功",
  "data": "杭州今天天气为多云，气温为32.8°C，风速约为9.9 km/h。外出请注意防晒和适当补水哦！"
}
```



继续查看关于ai的新闻：

```YAML
curl -X 'POST' \
  'http://127.0.0.1:8000/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "最近有什么关于人工智能的新闻？"
}'
```

返回内容：

```YAML

Response body
Download
{
  "code": 200,
  "msg": "请求成功",
  "data": "目前暂时没有找到关于“人工智能”的最新新闻。可能是因为近期相关报道较少，或者关键词匹配未覆盖到最新内容。如果您有更具体的关注方向（比如某家公司、技术突破、政策动态等），欢迎告诉我，我可以帮您进一步查找！"
}
```

