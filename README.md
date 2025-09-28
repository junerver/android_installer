# Android APK安装器

一个基于Python和customtkinter的桌面GUI应用程序，用于通过拖拽方式安装APK文件到Android设备。

## 功能特性

- 🔍 **自动设备检测**: 自动检测通过ADB连接的Android设备
- 🎨 **状态指示**: 通过背景色直观显示设备连接状态
  - 无背景色：未连接设备
  - 浅绿色：设备正常连接
  - 浅红色：ADB调用失败
- 📱 **拖拽安装**: 支持将APK文件拖拽到窗体进行安装
- ✅ **文件验证**: 自动验证拖拽的文件是否为有效APK
- 🔄 **异步处理**: 安装过程不会阻塞用户界面

## 系统要求

- Python 3.13+
- Android SDK (包含ADB工具)
- Windows操作系统

## 安装和运行

1. 克隆项目到本地：
```bash
git clone <repository-url>
cd android_installer
```

2. 安装依赖：
```bash
uv sync
```

3. 运行应用：
```bash
uv run python main.py
```

## 使用方法

1. **连接Android设备**：
   - 确保Android设备已开启USB调试
   - 通过USB连接设备到电脑
   - 应用会自动检测设备连接状态

2. **安装APK**：
   - 将APK文件拖拽到应用窗体
   - 应用会自动验证文件并开始安装
   - 安装完成后会显示结果提示

## 项目结构

```
android_installer/
├── main.py              # 主应用程序
├── adb_utils.py         # ADB工具类
├── pyproject.toml       # 项目配置和依赖
├── uv.lock             # 依赖锁定文件
├── README.md           # 项目说明
└── 开发计划.md          # 开发计划文档
```

## 技术栈

- **GUI框架**: customtkinter - 现代化的tkinter主题
- **拖拽支持**: tkinterdnd2 - 文件拖拽功能
- **包管理**: uv - 快速的Python包管理器
- **设备通信**: ADB (Android Debug Bridge)

## 故障排除

### ADB调用失败
- 确保Android SDK已正确安装
- 检查ADB是否在系统PATH中
- 尝试手动运行 `adb devices` 命令

### 设备未检测到
- 确认USB调试已开启
- 检查USB连接线是否正常
- 在设备上确认调试授权

### APK安装失败
- 确认APK文件完整且未损坏
- 检查设备存储空间是否充足
- 确认应用权限设置

## 开发

如需修改或扩展功能，请参考 `开发计划.md` 文件了解项目架构和实现细节。

## 许可证

本项目采用MIT许可证。