# LLM Customer Service

基于 Python、FastAPI、LangGraph 的电商对话 Agent 项目，包含订单、物流与售后流程，以及 Neo4j 图谱检索示例。

## 代码结构

- `atguigu_ai/`：对话编排、命令理解、策略、Action、Tracker 与接入层。
- `ecs_demo/`：电商流程配置、业务 Action 与 GraphRAG 示例。
- `项目一代码导读-框架图与文件说明.md`：整体架构及文件职责。
- `项目一面试稿-移动电信华为ICT.md`：基于代码整理的面试准备。

## 配置说明

依赖见 `requirements-atguigu.txt` 和 `setup.py`。运行前需自行准备 MySQL、Neo4j、模型服务及所需数据，按照配置加载逻辑创建本地 `ecs_demo/endpoints.yml` 与环境变量。代码包含演示功能，不代表具备生产环境的完整权限、幂等与高可用保障。

仓库排除了本地 `.env`、连接配置、模型文件、会话数据、压缩包与个人简历。上传副本中的硬编码演示密码已移除，请通过环境变量配置数据库密码。

## 本地增强与验证

新增取消订单的服务端身份检查、条件状态更新与重复取消保护；同会话消息串行处理；整轮和逐节点耗时追踪。配置方式与适用边界见 `项目增强实施记录.md`。

测试：`python -m pip install -r requirements-test.txt`，然后运行 `python -m unittest discover -s tests -v`。

离线评测工具见 `evaluation/README.md`。六条冒烟样本不代表真实模型评测结果。
