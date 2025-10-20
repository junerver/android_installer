# Android APK安装器

一个基于 Python 与 CustomTkinter 的轻量桌面应用，支持通过拖拽方式将 APK 安装到已连接的 Android 设备。

## 主要特性

- 🤖 **设备自动检测**：实时轮询 ADB，自动识别已连接的 Android 设备。
- 🌈 **状态指示**：颜色和提示文案同步展示连接、断开或 ADB 异常等状态。
- 📦 **拖拽安装**：支持一次拖拽多个 APK，自动排队依次安装，过程自动校验文件扩展名。
- 🔄 **异步处理**：安装流程运行在后台线程，避免阻塞界面。
- 🧾 **集中日志**：操作日志统一写入仓库根目录的 `android_installer.log`，便于排查问题。

## 系统要求

- Windows 10/11
- Python 3.13+
- 已正确配置或使用便携版的 Android SDK / ADB

## 安装与运行

1. 克隆仓库：
```bash
git clone <repository-url>
cd android_installer
```

2. 安装依赖：
```bash
uv sync
```

3. 启动桌面应用：
```bash
uv run python src/main.py
```

## 构建发行包

使用 PyInstaller 生成可分发的压缩包和可执行文件：
```bash
uv run python script/release.py
```
打包结果位于 `dist/` 目录，同时压缩为 `android_installer.zip`（在项目根目录），包含可执行文件与必要的 ADB 工具。

## 使用说明

1. **连接设备**：
   - 启用 Android 设备的 USB 调试。
   - 通过 USB 连接到电脑，并在设备端确认调试授权。
   - 应用会自动刷新设备状态。

2. **安装 APK**：
   - 将一个或多个 APK 文件拖入窗口中央区域。
   - 应用会过滤无效文件，将有效 APK 加入安装队列并在后台顺序安装。
   - 每个安装结果会通过弹窗与状态栏提示，窗口文字会指示当前队列进度。

## 项目结构

```
android_installer/
├── src/                 # 应用源码与 ADB 辅助工具
│   ├── __init__.py
│   ├── main.py          # GUI 入口
│   └── adb_utils.py     # ADB 交互与日志
├── script/              # 自动化脚本
│   └── release.py       # PyInstaller 打包脚本
├── platform-tools/      # 随仓库分发的便携版 ADB 工具
├── build/               # PyInstaller 中间产物（忽略）
├── dist/                # 构建结果（忽略）
├── pyproject.toml       # 项目依赖与元数据
├── uv.lock              # 依赖锁定文件
├── README.md            # 使用说明
└── AGENTS.md            # 贡献者指南
```

## 技术栈

- **GUI 框架**：CustomTkinter
- **拖拽能力**：tkinterdnd2
- **依赖管理**：uv
- **设备通信**：Android Debug Bridge (ADB)
- **打包工具**：PyInstaller

## 常见问题

### 无法识别设备
- 确认 USB 调试已开启并授权。
- 使用 `platform-tools/adb.exe devices` 检查是否能看到设备。
- 更换数据线或 USB 接口后重试。

### ADB 报错或安装失败
- 检查 `android_installer.log` 获取详细错误信息。
- 确保设备存储空间充足，APK 未损坏。
- 如需使用系统级 ADB，请将其路径加入 `PATH`。

### 窗口无响应
- 应用安装流程在后台运行，如安装时间过长请查看日志确认是否完成。
- 避免在安装过程中重复拖入多个 APK。

## 许可证

本项目采用 MIT License，详见仓库根目录的 `LICENSE`（若存在）。
