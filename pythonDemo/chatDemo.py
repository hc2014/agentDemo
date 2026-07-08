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