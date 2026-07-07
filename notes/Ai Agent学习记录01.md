# Ai Agent学习记录

### 第一个Demo

下载vscode安装相关插件

访问https://langchain\-doc\.cn/v1/python/langchain/quickstart\.html，测试第一个demo

```Python
from langchain.agents import create_agent


def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手",
)

# 运行代理
agent.invoke(
    {"messages": [{"role": "user", "content": "旧金山的天气怎么样"}]}
)
```



报错信息：

```JavaScript
**发生异常: ModuleNotFoundError**

No module named 'langchain'
  File "E:\Demo\pythonDemo\firstDemo.py", line 1, in <module>
    from langchain.agents import create_agent
ModuleNotFoundError: No module named 'langchain'
```



通过命令 安装插件：

```Plain Text
python -m pip install langchain
```

但是依旧报错，错误原因是，我本地有多个版本的 python ，默认安装的是3\.10版本的

通过 py \-3\.13 \-m pip install langchain来指定版本安装，这里也有个坑，需要把环境变量里面原本3\.10的地址全部删掉，缓存 3\.13版本的地址，

在终端查看python 版本 已经变成了3\.13版本

```Plain Text

PS E:\Demo\pythonDemo> python --version
Python 3.13.2
PS E:\Demo\pythonDemo> 

```



继续执行还是报错，分析以后得知

太棒了！环境终于彻底对齐了！🎉

从报错信息可以看出，你的 Python 3\.13 已经成功加载了 `langchain`，并且识别到了你要使用 Anthropic 的模型。

报错信息已经非常贴心地给出了提示：
`ImportError: Initializing ChatAnthropic requires the langchain-anthropic package.`

```Plain Text
python -m pip install langchain-anthropic
```

继续执行代码提示需要anthropic的api，目前我是没有的，就切换成了用千问的模型

安装插件

```Plain Text
python -m pip install langchain_openai
```

```Python
from langchain_openai import ChatOpenAI

# 使用通义千问模型
model = ChatOpenAI(
    model="qwen-turbo",  # 通义千问的模型名
    api_key="你的通义千问-API-Key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里百炼兼容地址
)

response = model.invoke("你好，请介绍一下自己")
print(response.content)
```

这里有个坑，一直提示403，查了很多资料都没有解决，后来发现是我的阿里云账户里面金额是\-0\.05元，部分功能不可用，充值了10元，代码执行是正常的





### 查询天气案例



```Python
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

#从环境变量中读取api-key
API_KEY=os.getenv("QWEN_PLUS")

print("API Key 读取结果:", API_KEY) 

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
```



执行代码会报错，提示缺少langchain库

使用的 Python 版本是 3\.13，请确保安装的 LangChain 也是最新的兼容版本。在终端中运行以下命令进行升级

```Plain Text
pip install --upgrade langchain langchain-core langchain-openai
```



LangChain 的模块化拆分意味着 `AgentExecutor` 等核心组件可能依赖特定的子包。如果升级后仍然报错，请尝试显式安装 `langchain-community`

```Plain Text
pip install langchain-community
```

执行以后提示成功了





### 问题：代码里面 让ai 去调用get\_current\_weather工具，入参是怎么传递的，它是怎么知道要查询“黄冈”的天气预报的

### 核心机制：入参是如何传递的？

入参的传递过程分为三个步骤：

#### 第一步：定义工具接口（你写的代码）

你在代码中定义了工具函数 `get_current_weather`，并明确指定了参数：

```Python
@tool
def get_current_weather(location: str) -> str:
```

这里的 `location: str` 告诉 LangChain：“这个工具需要一个叫 `location` 的字符串参数”。

#### 第二步：大模型的“思考”与提取（自动发生）

当用户输入“今天黄冈天气如何？”时，LangChain 会把这段话和你的工具描述一起发送给大模型（Qwen\-Plus）。
模型会根据你的 `system_prompt` 和工具的 Docstring（文档字符串）进行推理：

- System Prompt 告诉它：“如果用户询问天气，请务必使用 `get_current_weather` 工具。”

- 工具 Docstring 告诉它：“这个工具是用来查询实时天气的，参数是地点。”

- 模型的推理：用户问的是“黄冈”的天气 \-\> 我需要调用 `get_current_weather` \-\> 这个函数需要一个 `location` 参数 \-\> 用户提到的城市是“黄冈” \-\> 所以我应该把 `location` 设置为 “黄冈”。

#### 第三步：自动调用与传值

LangChain 接收到模型返回的“思考结果”（通常是一个 JSON 格式的 Action），解析出参数，然后自动执行：

```Python
get_current_weather.invoke({"location": "黄冈"})
```

这就是入参传递的全过程：用户输入 \-\> 模型理解并提取实体 \-\> LangChain 框架自动填充参数 \-\> 执行函数。

### 关键点：它是怎么知道要查“黄冈”的？

这主要依赖于 参数命名的语义化 和 工具描述的清晰度。

- 参数名即提示（Prompting）：
你将参数命名为 `location`（地点），这是一个非常通用的标准英文单词。大模型在训练时见过海量代码，它非常清楚 `location` 代表什么。如果你把参数名写成 `abc`，模型可能就无法准确将“黄冈”对应到 `abc` 上。

- 工具描述（Docstring）：
你写的这行注释非常重要：
`"""当用户询问某个城市或地点的实时天气..."""`。
这句话直接告诉模型：“用户提到的城市/地点，就是这个工具需要的输入”。

- 当前时间的利用：
虽然代码中没有显式传递时间，但你的工具调用的是“实时天气”接口。模型知道“今天”代表查询当前时间的天气，所以它会直接调用接口获取当前数据，而不需要把“今天”这个字眼作为参数传给你的函数。

### 代码中的一个小修正

我注意到你的代码中存在一个小的不一致，建议修正以确保逻辑完全正确：

在 `if name == "main":` 块中，你打印的是：

```Python
print("正在查询黄冈天气...")
```

但实际发送给 Agent 的消息是：

```Python
{"role": "user", "content": "今天黄石天气如何？"}
```

AI 并不是“知道”要查黄冈，而是通过 自然语言理解（NLU） 从用户输入中提取了“黄冈”这个实体，并根据你的 函数定义 知道这个实体应该填入 `location` 这个参数中。这就是 LangChain Agent 的核心魅力：你不需要写正则表达式去提取城市名，大模型会帮你自动完成。



### 问题：代码中我定义了get\_current\_weather 这个工具，那如果我定义了多个工具，那么在response = agent\.invoke\(\{
        "messages": \[
            \{"role": "user", "content": "今天黄冈天气如何？"\}
        \]
    \}\) 中，它是怎么知道要调用的是哪个工具呢？

这是一个非常棒的问题！当定义了多个工具时，大模型（LLM）之所以能准确“挑”出正确的工具，核心在于 LangChain 框架在后台自动完成了一项关键工作：将工具列表转换为大模型能听懂的“系统提示词（System Prompt）”的一部分。

我们可以把这个过程拆解为以下几个步骤来理解：

### 工具的“自我推销”（Schema 序列化）

当你使用 `@tool` 装饰器定义一个函数时，LangChain 会自动提取该函数的三个关键信息：

- 函数名：`get_current_weather`

- 参数结构：`{"location": {"type": "string"}}`

- Docstring（文档字符串）：`当用户询问某个城市或地点的实时天气...`

LangChain 会将这些信息打包成一个标准的 JSON Schema（类似于 OpenAI 的 Function Calling 规范）。

### 将工具“塞进”大模型的视野

当你执行 `agent.invoke(...)` 时，LangChain 会把你定义的所有工具（比如 `tools=[get_current_weather, search_web, calculate]`）的 JSON Schema 作为附加上下文，连同你的 `system_prompt` 和用户的提问一起发送给大模型。

此时，大模型接收到的完整指令大概是这样的：

> 系统设定：你是一个智能助手。
> 你可以使用的工具：
> 
> 1. `get_current_weather(location: str)` \- 当用户询问某个城市或地点的实时天气、温度、降水等信息时，必须调用此工具。
> 
> 2. `search_web(query: str)` \- 当用户询问最新的新闻、百科知识或未知概念时，必须调用此工具。
> 
> 用户提问：今天黄冈天气如何？
> 
> 

### 大模型的“语义匹配”与决策

大模型本质上是一个极其强大的“文本接龙”和“逻辑推理”机器。当它看到上述完整的上下文时，它会进行语义匹配：

- 用户提到了“黄冈”和“天气”。

- 模型扫视“可用工具列表”，发现 `get_current_weather` 的描述中包含了“城市”、“实时天气”等关键词。

- 模型判定：用户的意图与 `get_current_weather` 的描述高度吻合。

### 结构化输出（而不是直接调用）

非常重要的一点是：大模型本身并不能直接“执行”你的 Python 代码。

当模型决定使用 `get_current_weather` 时，它返回的不是执行结果，而是一段结构化的 JSON 指令（通常被称为 Tool Call / Function Call），例如：

```Python
{
  "tool_name": "get_current_weather",
  "arguments": {"location": "黄冈"}
}
```

### LangChain 的“调度器”执行

LangChain 接收到这段 JSON 后，它的 Agent 调度器（Router）就会去你的 `tools` 列表中查找名为 `get_current_weather` 的函数，并把 `{"location": "黄冈"}` 作为参数传进去执行，最后把执行结果再喂回给大模型，让它生成最终的回复。

---

### 💡 总结与最佳实践

大模型之所以能选对工具，完全依赖于你写的工具描述（Docstring）的质量。

如果你把代码改成这样：

```Python
@tool
def get_current_weather(location: str) -> str:
    """获取数据。"""  # 描述太模糊！
```

因此，写好工具的 Docstring（告诉模型这个工具是干什么的、什么时候该用、什么时候不该用），是让 Agent 准确路由的最核心秘诀。



