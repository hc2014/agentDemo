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