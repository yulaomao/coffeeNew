# 智能咖啡机 Web 应用

## 概述

这是智能咖啡机的Flask Web版本，将原来的PySide6桌面应用转换为现代化的Web浏览器界面。

## 功能特点

### 🌐 Web界面
- 响应式设计，适配各种屏幕尺寸
- 现代化UI设计，渐变背景和流畅动画
- 实时状态更新（通过WebSocket）
- 触屏友好的界面设计

### ☕ 完整订单流程
- **欢迎页面** - 动画咖啡杯和功能介绍
- **菜单选择** - 产品卡片展示价格和可用性
- **产品定制** - 杯型、温度、糖分、奶类选择
- **订单确认** - 详细订单信息和价格
- **支付方式** - 微信支付、支付宝、银行卡
- **二维码支付** - 生成移动支付二维码
- **制作进度** - 动画进度指示器
- **完成评分** - 订单完成和评分系统

### 🔧 技术特性
- Flask Web框架 + SocketIO实时通信
- Jinja2模板引擎
- 响应式CSS布局（Grid和Flexbox）
- JavaScript交互和API通信
- 二维码生成
- 会话管理

## 安装和运行

### 环境要求
- Python 3.11+
- 现代化Web浏览器

### 安装依赖
```bash
cd device
pip install -r requirements.txt
```

### 启动应用
```bash
# 运行简化版Flask应用（推荐用于演示）
python simple_app.py

# 或运行完整版（需要解决导入依赖）
python app.py
```

### 访问应用
- 本地访问: http://localhost:5000
- 网络访问: http://your-ip:5000

## 文件结构

```
device/
├── simple_app.py              # 简化的Flask应用（独立运行）
├── app.py                     # 主应用入口（Flask版本）
├── web_app.py                 # 完整Flask应用模块
├── requirements.txt           # 依赖列表（已更新Flask）
├── config.py                  # 配置文件（已添加Web配置）
└── web/                       # Web资源目录
    ├── templates/             # HTML模板
    │   ├── base.html         # 基础模板
    │   ├── idle.html         # 欢迎页面
    │   ├── menu.html         # 菜单页面
    │   ├── product_detail.html # 产品详情
    │   ├── confirm.html      # 订单确认
    │   ├── payment.html      # 支付选择
    │   ├── qr.html          # 二维码支付
    │   ├── brewing.html      # 制作进度
    │   ├── done.html         # 完成页面
    │   ├── maintenance.html  # 维护管理
    │   └── maintenance_login.html # 维护登录
    └── static/
        └── css/
            └── style.css     # 完整样式表
```

## API端点

- `GET /` - 主页重定向
- `GET /idle` - 欢迎页面
- `GET /menu` - 菜单页面
- `GET /product/<id>` - 产品详情
- `POST /confirm` - 确认订单
- `GET /payment` - 支付选择
- `GET /qr/<method>` - 二维码支付
- `GET /brewing` - 制作进度
- `GET /done` - 完成页面
- `GET /maintenance` - 维护管理
- `POST /api/*` - 各种API接口

## 维护功能

在欢迎页面右上角快速点击3次可进入维护模式：
- 默认密码: `0000`
- 功能: 设备状态、物料管理、系统测试等

## 开发说明

### 从PySide6转换的主要变化：
1. **UI框架**: PySide6 → Flask + HTML/CSS/JavaScript  
2. **架构**: 桌面应用 → Web服务器
3. **交互**: Qt信号槽 → HTTP请求/WebSocket
4. **布局**: Qt布局 → CSS Grid/Flexbox
5. **状态管理**: Qt属性 → 会话和全局变量

### 保留的功能：
- 完整的业务逻辑和订单流程
- 设备代理和后台集成架构
- 支付系统集成接口
- 硬件抽象层接口
- 多语言支持框架

## 截图展示

应用包含完整的用户界面，从欢迎页面到订单完成的全流程。界面设计现代化，支持触屏操作，适合商业环境使用。