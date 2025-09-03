# 智能咖啡机设备端运行指南

## 快速开始

### 1. 环境准备

确保安装了Python 3.11或更高版本：
```bash
python --version  # 应该显示Python 3.11+
```

### 2. 安装依赖

```bash
cd device
pip install -r requirements.txt
```

主要依赖包括：
- PySide6 (Qt6图形界面)
- httpx (异步HTTP客户端)
- pydantic (数据验证)
- loguru (日志记录)
- 其他工具库

### 3. 配置设备

复制环境变量配置文件：
```bash
cp .env.example .env
```

编辑`.env`文件，配置设备参数：
```env
# 后台服务地址
BACKEND_BASE_URL=https://backend.example.com/api/v1

# 设备标识
DEVICE_ID=D001
DEVICE_TOKEN=

# 界面配置  
UI_LANG=zh-CN
UI_FULLSCREEN=true
UI_SCREEN_WIDTH=1080
UI_SCREEN_HEIGHT=1920

# 代理配置
POLL_INTERVAL_SEC=5
HEARTBEAT_INTERVAL_SEC=30
OFFLINE_THRESHOLD_SEC=600

# 物料配置
LOW_MATERIAL_PCT=20

# 路径配置
ASSETS_DIR=./device/assets
CACHE_DIR=~/.coffee_device/cache
LOG_DIR=~/.coffee_device/logs
```

### 4. 启动设备

```bash
python app.py
```

程序启动后会：
1. 初始化硬件模拟器
2. 启动后台代理服务
3. 显示触控界面
4. 开始定期与后台同步

## 运行模式

### 图形界面模式（推荐）
默认模式，启动完整的触控界面：
```bash
python app.py
```

### 控制台模式
如果没有安装PySide6或在无图形环境下运行：
```bash
# 程序会自动检测并切换到控制台模式
python app.py
```

## 基本操作

### 用户操作流程
1. **开始点单**: 点击主页"开始点单"按钮
2. **选择商品**: 浏览菜单选择咖啡
3. **定制选项**: 选择大小、温度、糖度等
4. **确认订单**: 确认商品和总价
5. **选择支付**: 选择微信或支付宝支付
6. **扫码支付**: 扫描二维码完成支付
7. **等待制作**: 观看制作进度
8. **取走咖啡**: 制作完成后取走

### 维护模式
1. **进入维护**: 在主页右上角长按3秒
2. **输入密码**: 默认密码`0000`
3. **维护操作**:
   - 快捷操作：清洗、冲洗、开门等
   - 物料管理：查看和补充物料
   - 系统状态：查看设备运行状态
   - 日志查看：查看操作日志
   - 系统设置：修改设备配置

## 测试功能

### 模拟支付
设备内置支付模拟功能：
- 微信支付：生成二维码后10秒自动完成支付
- 支付宝：生成二维码后12秒自动完成支付
- 可手动触发支付成功/失败

### 模拟制作
设备使用时间驱动的制作模拟：
- 根据配方步骤模拟制作时间
- 实时显示制作进度
- 自动消耗虚拟物料

### 离线测试
模拟网络断开：
1. 修改`BACKEND_BASE_URL`为无效地址
2. 设备会自动进入离线模式
3. 禁用点单和支付功能
4. 允许维护操作

## 故障排除

### 常见问题

**1. 无法启动图形界面**
```
ImportError: No module named 'PySide6'
```
解决：
```bash
pip install PySide6==6.7.2
```

**2. 数据库错误**
```
sqlite3.OperationalError: database is locked
```
解决：删除缓存目录重新启动
```bash
rm -rf ~/.coffee_device/cache
python app.py
```

**3. 网络连接失败**
检查后台服务地址配置：
```bash
curl https://backend.example.com/api/v1/health
```

**4. 物料显示异常**
重置物料数据：
```bash
# 删除数据库文件
rm ~/.coffee_device/cache/device.db
# 重新启动会初始化默认数据
python app.py
```

### 日志查看

日志文件位置：
- 控制台输出：实时显示INFO级别日志
- 文件日志：`~/.coffee_device/logs/device.log`（DEBUG级别）

查看日志：
```bash
# 实时查看日志
tail -f ~/.coffee_device/logs/device.log

# 查看错误日志
grep ERROR ~/.coffee_device/logs/device.log
```

### 调试模式

开发调试时的有用操作：

**退出全屏模式**：
- 按`Esc`键退出全屏
- 按`F11`切换全屏/窗口模式

**强制同步数据**：
在维护页面点击"立即同步"按钮

**重置设备状态**：
删除缓存目录后重启

## 配置说明

### 重要配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DEVICE_ID | D001 | 设备唯一标识，需与后台配置一致 |
| BACKEND_BASE_URL | https://backend.example.com/api/v1 | 后台API地址 |
| UI_LANG | zh-CN | 界面语言（zh-CN/en-US） |
| UI_FULLSCREEN | true | 是否全屏显示 |
| POLL_INTERVAL_SEC | 5 | 命令轮询间隔（秒） |
| HEARTBEAT_INTERVAL_SEC | 30 | 心跳间隔（秒） |
| LOW_MATERIAL_PCT | 20 | 低物料阈值（百分比） |

### 目录结构

程序运行时会创建以下目录：
- `~/.coffee_device/cache/`: 本地缓存和数据库
- `~/.coffee_device/logs/`: 日志文件
- `./device/assets/`: 配方和资源文件

## 性能优化

### 内存使用
- 图形界面通常使用50-100MB内存
- 控制台模式使用20-30MB内存

### 磁盘使用
- 程序本身：~50MB
- 日志文件：10MB（自动轮转）
- 缓存数据：~5MB

### CPU使用
- 待机时：<5% CPU
- 制作时：10-20% CPU（主要是界面更新）

建议配置：
- CPU：双核1GHz+
- 内存：1GB+
- 磁盘：500MB可用空间

## 部署建议

### 生产环境
1. 使用专用硬件（工控机、平板等）
2. 禁用系统自动更新
3. 配置自动启动脚本
4. 定期备份日志和配置

### 开发环境  
1. 使用虚拟环境隔离依赖
2. 启用调试日志
3. 配置代码热重载
4. 使用测试后台服务

有问题请查看日志文件或联系技术支持。