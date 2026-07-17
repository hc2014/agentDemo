# Function Calling讲解

 

如果将 RAG 比作给大模型配了一本“参考书”，那么 **Function Calling（函数调用）** 就是给大模型装上了“手脚”，让它从“只会纸上谈兵的顾问”升级为“能动手解决实际问题的办事员”。

### 一、 什么是 Function Calling？

大语言模型（LLM）本质上是一个文本生成器，它无法直接查询数据库、发送邮件或获取实时天气。Function Calling 充当了**模型思考与外部行动之间的关键桥梁**。

它允许开发者预先告诉模型“你拥有哪些工具”，当用户提出需求时，模型会自主判断是否需要使用工具。如果需要，模型不会自己瞎编数据，而是输出一个结构化的请求（通常是 JSON），由开发者系统去执行真实的代码，最后将结果反馈给模型，由模型生成最终的自然语言回复。

### 二、 Function Calling 的核心执行流程

一个标准的 Function Calling 交互通常分为五个关键步骤：

1. **函数注册（开发者）**：预先向大模型声明可用的函数列表，包含函数名称、功能描述以及参数结构（通常使用 JSON Schema 规范）。
2. **用户提问**：用户发送自然语言请求（例如：“帮我订一张明天去上海的机票”）。
3. **大模型决策与参数提取**：模型理解意图后，判断需要调用 `book_flight` 函数，并自动提取参数，生成一个标准的 JSON 格式调用请求（如 `{"destination": "上海", "date": "明天"}`）。
4. **安全校验与执行（开发者）**：开发者系统解析 JSON，进行严格的参数校验和安全性检查（如防 SQL 注入），然后调用真实的 API 或本地代码，获取执行结果。
5. **结果整合与回复（大模型）**：开发者将执行结果（如“航班已满”或“订单已生成”）反馈给大模型，模型结合上下文，将其转化为用户友好的自然语言回复。

### 三、 核心技术架构与实现难点

在实际的工程落地中，Function Calling 并非简单的“一问一答”，而是需要一套严密的系统架构来支撑：

1. **函数注册与发现机制**：  
   构建一个函数注册中心（Function Registry）是第一步。通过装饰器模式等编程技巧，可以实现函数元数据（如参数类型、返回值）的自动收集与动态注册，支持热插拔和版本控制。
2. **参数解析与类型转换引擎**：  
   大模型生成的参数可能存在格式偏差。系统需要实现动态调用引擎，包含参数验证、缺失必填项时的自动追问、以及数据类型的自动转换（如将字符串 "123" 转换为整数）。
3. **上下文感知与决策权重**：  
   模型如何判断“什么时候该调用，什么时候不该调用”？这依赖于模型的注意力机制。系统会综合评估信息缺失度、风险敏感度和计算成本，动态调整调用阈值，避免过度调用导致的性能浪费。

### 四、 为什么企业级应用离不开 Function Calling？

1. **突破能力边界**：让 AI 从单纯的知识库升级为可以联动各类工具的“实用操作系统”，轻松对接 CRM、ERP、支付系统等。
2. **极高的可靠性**：将数学计算、数据库查询等敏感操作交给专业的代码执行，彻底避免了模型“幻觉”带来的致命错误。
3. **安全性与可控性**：大模型本身不直接操作敏感系统，实际的代码执行在受控的开发者后端环境中进行，且经过了严格的参数校验。
   
   

### 五、 Function Calling 实战：给大模型装上“手脚”

在理解了 RAG 解决了“知识”问题后，我们需要解决“行动”问题。Function Calling（函数调用）并不是让模型直接去执行代码，而是让模型**学会“看菜谱”并“下达指令”**。

Function Calling 的本质是一个**结构化输出**的过程。

#### 注册工具：将函数“翻译”给模型

这是 Function Calling 的第一步。大模型本身并不认识你的 Python 函数，所以我们需要把函数的**名称、参数、用途**等信息，以一种模型能理解的结构化格式（通常是 JSON Schema）告诉它。

在代码中，`@tool` 装饰器就是完成这个“翻译”工作的关键。

```python
# 1. 定义天气查询工具
@tool
def get_current_weather(location: str) -> str:
    """当用户询问某个城市或地点的实时天气、温度、降水等信息时，必须调用此工具。"""
    # ... 函数体 ...
```

* **`@tool`**: 这是 LangChain 提供的装饰器。它会自动分析 `get_current_weather` 这个函数。
* **`def get_current_weather(location: str) -> str`**: 函数签名定义了工具的名称是 `get_current_weather`，它需要一个名为 `location` 的字符串参数。
* **`当用户询问某个城市或地点的实时天气、温度、降水等信息时，必须调用此`**: 这段话是函数的文档字符串（Docstring）至关重要！它清晰地描述了工具的用途。模型正是根据这段描述来判断“用户的问题是否需要调用这个工具”。

LangChain 会在后台将上述信息打包成一个 JSON 对象，并在调用模型时通过 `tools` 参数传给它。

```python
agent = create_agent(
    model=model,
    tools=[get_current_weather], # 在这里，LangChain 自动完成了工具的注册
    # ...
)
```



#### 意图识别：模型判断“要不要”调用

当用户提出问题后，模型会结合你提供的 `system_prompt` 和注册的工具描述，来分析用户的意图。

```python
# 4. 运行测试
if __name__ == "__main__":
    # ...
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": "今天黄冈天气如何？"} # 用户输入
        ]
    })
```

* **用户输入**: `"今天黄冈天气如何？"`
* **模型思考**: 模型接收到这个问题后，会回顾你给它的指令（`system_prompt`）和工具描述。它会发现，用户的问题是关于“天气”的，而 `get_current_weather` 工具的描述正好是“当用户询问某个城市或地点的实时天气...时，必须调用此工具”。
* **决策**: 因此，模型判断出需要调用 `get_current_weather` 工具来回答用户，而不是自己凭空生成一个答案。



#### 参数提取：模型生成调用指令

一旦模型决定要调用工具，它的下一个任务就是从用户的自然语言中提取出调用该工具所需的参数，并生成一个标准的 JSON 格式指令。

* **用户输入**: `"今天黄冈天气如何？"`
* **模型提取**: 模型会识别出 `location` 参数的值是 `"黄冈"`。
* **生成指令**: 模型会输出一个类似如下的结构化请求（这个过程对用户是透明的，由 LangChain 在后台处理）：



```python
{
  "name": "get_current_weather",
  "arguments": {
    "location": "黄冈"
  }
}
```

这个 JSON 就是模型下达的“行动指令”，它告诉你的程序：“请执行 `get_current_weather` 函数，并把 `黄冈` 作为 `location` 参数传进去。”



#### 执行与反馈：程序执行并返回结果

这是最后一步，也是真正“动手”的环节。你的程序接收到模型生成的 JSON 指令后，会执行以下操作：

1. **执行函数**: 调用你定义的 `get_current_weather("黄冈")` 函数。
2. **获取数据**: 函数内部会向天气 API 发起真实的网络请求，获取数据。
3. **返回结果**: 函数将获取到的数据（一个 JSON 字符串）返回给 LangChain 框架。
4. **反馈给模型**: LangChain 将这个结果作为新的上下文，再次发送给模型。
5. **生成最终回复**: 模型结合用户原始问题和工具返回的真实数据，组织成一段自然、流畅的语言回复给用户。

```python
@tool
def get_current_weather(location: str) -> str:
    """..."""
    try:
        # ⚙️ 执行：向外部 API 发起真实请求
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=zh"
        geo_response = requests.get(geo_url).json()
        # ... (获取经纬度)

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Shanghai"
        weather_response = requests.get(weather_url).json()

        # ... (处理数据)

        # ⚙️ 反馈：将结果返回给框架，框架会再传给模型
        return json.dumps({
            "city": city_name,
            "temperature": f"{temp}°C",
            "weather": weather_desc,
            "windspeed": f"{windspeed} km/h"
        }, ensure_ascii=False)
    except Exception as e:
        return f"获取天气信息时发生错误: {str(e)}"
```

最终，在控制台看到的 `最终回复` 就是模型根据 `get_current_weather` 函数返回的 JSON 数据生成的自然语言。

 

### 六、 总结：RAG + Function Calling = AI Agent

现在，我们可以把这两块拼图拼在一起了：

* **RAG（检索增强生成）**：解决了模型“不知道”的问题（外挂知识库）。
* **Function Calling（函数调用）**：解决了模型“做不到”的问题（外挂工具箱）。

当一个大模型既能查阅公司内部文档（RAG），又能调用系统接口去执行审批、下单（Function Calling）时，它就进化成了真正的 **AI Agent（智能体）**。这就是目前 AI 应用开发最主流、最实用的技术路径。


