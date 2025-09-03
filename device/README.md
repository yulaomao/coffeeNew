# 智能咖啡机设备端

这是智能咖啡机设备端的完整实现，包括触控大屏UI、本地设备代理、硬件抽象层和与管理后台的对接。

## 功能特点

- **触控大屏界面**: 基于PySide6的竖屏触控界面(1080x1920)，支持完整的用户交互流程
- **设备代理**: 完整的本地代理系统，处理心跳、命令轮询、状态上报等
- **硬件抽象层**: 支持真实硬件和模拟器，可扩展的传感器和执行器接口
- **支付集成**: 支持微信支付和支付宝的模拟实现
- **离线模式**: 支持离线操作和数据同步
- **多语言**: 支持中文和英文界面
- **维护功能**: 完整的维护界面，包括物料管理、系统状态、日志查看等

## 目录结构

```
device/
├── app.py                    # 主程序入口
├── config.py                # 配置管理
├── constants.py              # 常量定义
├── requirements.txt          # 依赖列表
├── .env.example             # 环境变量示例
├── utils/                   # 工具模块
│   ├── time.py             # 时间工具
│   ├── crypto.py           # 加密工具
│   ├── net.py              # 网络工具
│   ├── images.py           # 图片管理
│   ├── i18n.py             # 国际化
│   └── sse.py              # 事件总线
├── storage/                 # 存储层
│   ├── db.py               # SQLite数据库
│   ├── models.py           # 数据模型
│   └── queue.py            # 上传队列
├── backend/                 # 后台接口
│   ├── client.py           # HTTP客户端
│   ├── schemas.py          # 接口模式
│   └── adapters.py         # 适配器
├── agent/                   # 代理模块
│   ├── supervisor.py       # 主管理器
│   ├── commands.py         # 命令处理
│   ├── materials.py        # 物料管理
│   ├── recipes.py          # 配方管理
│   ├── orders.py           # 订单管理
│   ├── state.py            # 状态管理
│   └── offline.py          # 离线管理
├── payment/                 # 支付模块
│   ├── provider.py         # 支付接口
│   ├── mock_wechat.py      # 微信支付模拟
│   └── mock_alipay.py      # 支付宝模拟
├── hal/                     # 硬件抽象层
│   ├── base.py             # 基础接口
│   ├── simulator.py        # 模拟器
│   ├── real_stub.py        # 真实硬件占位
│   ├── sensors.py          # 传感器管理
│   └── actuators.py        # 执行器管理
├── kiosk/                   # 触控界面
│   ├── main_window.py      # 主窗口
│   ├── widgets/            # 界面组件
│   └── assets/             # 资源文件
├── assets/                  # 本地资产
└── tests/                   # 测试文件
```

## 技术栈

- **Python 3.11+**: 主要开发语言
- **PySide6**: Qt6图形界面框架
- **SQLite**: 本地数据存储
- **httpx**: 异步HTTP客户端
- **pydantic**: 数据验证
- **loguru**: 结构化日志
- **tenacity**: 重试机制
- **qrcode**: 二维码生成

## 核心组件

### 1. 配置管理 (config.py)
- 支持环境变量配置
- 自动创建必需目录
- 默认值设置

### 2. 存储层 (storage/)
- SQLite数据库管理
- Pydantic数据模型
- 异步上传队列

### 3. 后台客户端 (backend/)
- 异步HTTP通信
- 自动重试和退避
- 统一错误处理

### 4. 硬件抽象层 (hal/)
- 统一的传感器和执行器接口
- 模拟器实现用于开发和测试
- 真实硬件接口占位

### 5. 代理系统 (agent/)
- 设备状态管理
- 物料监控和上报
- 命令接收和执行
- 订单处理
- 离线模式支持

### 6. 支付系统 (payment/)
- 抽象支付接口
- 微信支付和支付宝模拟
- 二维码生成

### 7. 用户界面 (kiosk/)
- 响应式触控界面
- 页面导航管理
- 实时状态更新
- 维护界面

## API对接

设备端与管理后台的API对接包括：

- `POST /devices/{device_id}/status` - 状态上报
- `POST /devices/{device_id}/materials/report` - 物料上报
- `GET /devices/{device_id}/commands/pending` - 拉取待执行命令
- `POST /devices/{device_id}/command_result` - 命令执行结果上报
- `POST /devices/{device_id}/orders/create` - 订单上报

所有API请求支持自动重试、错误处理和离线队列。

## 主要流程

### 用户购买流程
1. 待机页面 → 点击"开始点单"
2. 菜单页面 → 选择商品
3. 商品详情 → 定制选项
4. 确认订单 → 确认商品和价格
5. 支付选择 → 选择支付方式
6. 扫码支付 → 显示二维码
7. 制作过程 → 实时进度显示
8. 完成取杯 → 提示取杯

### 维护流程
1. 待机页面右上角长按3秒
2. 输入维护密码(默认0000)
3. 进入维护菜单
4. 支持物料管理、系统状态、日志查看、设置等

### 离线处理
- 网络中断时自动进入离线模式
- 禁用在线功能(点单、支付)
- 本地数据排队等待网络恢复
- 网络恢复后自动同步数据

## 开发和测试

设备端内置完整的模拟器，支持：
- 硬件操作模拟
- 支付过程模拟  
- 网络状态模拟
- 物料消耗模拟

这使得无需真实硬件即可进行完整的功能测试和演示。