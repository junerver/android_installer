"""
Android APK安装器主程序
基于customtkinter的GUI应用，支持拖拽APK文件安装到Android设备
"""

import customtkinter as ctk
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
import time
import sys
import ctypes
import queue
from ctypes import wintypes
from pathlib import Path

from adb_utils import adb_manager, DeviceStatus


def resolve_assets_dir() -> Path:
    """解析资源目录（兼容PyInstaller运行环境）"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def resolve_icon_path(assets_dir: Path) -> Path:
    """解析图标路径，优先使用当前目录以适配便携版"""
    candidate_paths = [
        Path.cwd() / "icon.ico",
        assets_dir / "icon.ico",
    ]

    for path in candidate_paths:
        if path.exists():
            return path

    # 默认返回当前目录下的路径，确保后续构建流程可落到 dist 根目录
    return candidate_paths[0]


CONNECTED_BG = "#E8F5E8" # 连接状态背景颜色
DISCONNECTED_BG = "#FFE8E8" # 未连接状态背景颜色
APP_TITLE = "Android APK安装器 by hwj"
ASSETS_DIR = resolve_assets_dir()
ICON_PATH = resolve_icon_path(ASSETS_DIR) # 同时兼容调试运行与打包便携

class AndroidInstallerApp:
    """Android APK安装器主应用类"""
    
    def __init__(self):
        # 设置customtkinter主题
        ctk.set_appearance_mode("dark")  # 强制深色主题
        ctk.set_default_color_theme("blue")  # 蓝色主题
        
        # 创建主窗口
        self.root = TkinterDnD.Tk()  # 使用TkinterDnD支持拖拽
        self.setup_window()
        
        # 状态变量
        self.current_status = DeviceStatus.DISCONNECTED
        self.status_check_running = True
        self.install_worker_running = True
        self.install_queue = queue.Queue()

        # 创建UI组件
        self.setup_ui()

        # 配置拖拽功能
        self.setup_drag_drop()

        # 启动安装任务队列
        self.start_install_worker()

        # 启动状态检测线程
        self.start_status_monitoring()
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title(APP_TITLE)
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # 设置窗口背景为深色
        self.root.configure(bg="#212121")
        self.root.overrideredirect(False)

        # 设置窗口图标
        if ICON_PATH.exists():
            try:
                self.root.iconbitmap(default=str(ICON_PATH))
            except Exception:
                pass

        # 强制标题栏为深色（Windows专用）
        if sys.platform == "win32":
            self.root.after(0, self._apply_dark_theme)
            self.root.bind("<Map>", lambda _: self._apply_dark_theme(), add="+")
        
        # 窗口居中
        self.center_window()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_move(self, event):
        """开始拖拽窗口"""
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        """拖拽窗口"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def _apply_dark_theme(self):
        """应用深色标题栏（仅Windows有效）"""
        if sys.platform != "win32":
            return

        self.root.update_idletasks()

        try:
            user32 = ctypes.windll.user32
            dwmapi = ctypes.windll.dwmapi
        except AttributeError:
            return

        hwnd = self.root.winfo_id()
        if not hwnd:
            return

        # 获取包含标题栏的顶层窗口
        user32.GetAncestor.restype = wintypes.HWND
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        GA_ROOT = 2
        top_hwnd = user32.GetAncestor(wintypes.HWND(hwnd), GA_ROOT)
        if top_hwnd:
            hwnd = top_hwnd

        attr_ids = (20, 19)  # Windows 10 20H1及以上优先，回退到1809常量
        enable = ctypes.c_int(1)

        dwmapi = ctypes.WinDLL("dwmapi")
        for attr in attr_ids:
            if dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(attr),
                ctypes.byref(enable),
                ctypes.sizeof(enable),
            ) == 0:
                break
        else:
            # 所有属性设置失败，退出
            return

        # 设置标题栏颜色和文字颜色，确保呈现深色效果
        caption_color = ctypes.c_int(0x00212121)  # 深灰色
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(35),  # DWMWA_CAPTION_COLOR
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color),
        )

        text_color = ctypes.c_int(0x00FFFFFF)  # 白色文字
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(36),  # DWMWA_TEXT_COLOR
            ctypes.byref(text_color),
            ctypes.sizeof(text_color),
        )

        # 尝试使用Win11新的系统背景样式获得更暗的标题栏
        try:
            backdrop_type = ctypes.c_int(2)  # DWMSBT_MAINWINDOW = 2
            dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(38),  # DWMWA_SYSTEMBACKDROP_TYPE
                ctypes.byref(backdrop_type),
                ctypes.sizeof(backdrop_type),
            )
        except Exception:
            pass

        # 应用深色主题到窗口（Explorer风格）
        try:
            set_window_theme = ctypes.windll.uxtheme.SetWindowTheme
            set_window_theme.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
            set_window_theme.restype = ctypes.HRESULT
            set_window_theme(wintypes.HWND(hwnd), "DarkMode_Explorer", None)
        except Exception:
            pass
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架（调整上边距以适应自定义标题栏）
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # 创建提示标签
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="请拖拽APK文件到窗体",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="gray"
        )
        self.status_label.pack(expand=True)
        
        # 创建设备状态指示标签（小字体，底部显示）
        self.device_status_label = ctk.CTkLabel(
            self.main_frame,
            text="检测设备中...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.device_status_label.pack(side="bottom", pady=(0, 10))
    
    def setup_drag_drop(self):
        """配置文件拖拽功能"""
        # 为主窗口和框架都注册拖拽事件
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_file_drop)

        # 为主框架也注册拖拽事件
        self.main_frame.drop_target_register(DND_FILES)
        self.main_frame.dnd_bind('<<Drop>>', self.on_file_drop)

    def start_install_worker(self):
        """启动安装任务队列线程"""
        self.install_worker_thread = threading.Thread(target=self._process_install_queue, daemon=True)
        self.install_worker_thread.start()

    def _process_install_queue(self):
        """后台处理安装任务队列"""
        while self.install_worker_running:
            try:
                apk_path = self.install_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self._install_single_apk(apk_path)
            finally:
                self.install_queue.task_done()

    def _install_single_apk(self, apk_path: str):
        """逐个执行APK安装任务"""
        apk_name = Path(apk_path).name
        self.root.after(0, lambda: self.status_label.configure(text=f"正在安装：{apk_name}"))

        try:
            status, devices = adb_manager.get_connected_devices()
            if status != DeviceStatus.CONNECTED or not devices:
                self.root.after(0, lambda: self.show_message("错误", f"{apk_name} 安装已取消，设备连接已断开", "error"))
                return

            device_id = devices[0] if len(devices) == 1 else None

            success, message = adb_manager.install_apk(apk_path, device_id)
            if success:
                self.root.after(0, lambda: self.show_message("成功", f"{apk_name} 安装完成：{message}", "info"))
            else:
                self.root.after(0, lambda: self.show_message("安装失败", f"{apk_name} 安装失败：{message}", "error"))
        except Exception as e:
            error_msg = f"{apk_name} 安装过程中出现异常: {str(e)}"
            self.root.after(0, lambda: self.show_message("错误", error_msg, "error"))
        finally:
            self.root.after(0, self._refresh_idle_status_text)

    def _refresh_idle_status_text(self):
        """根据队列状态刷新提示文本"""
        if self.install_queue.empty():
            self.status_label.configure(text="请拖拽APK文件到窗体")
        else:
            self.status_label.configure(text="安装队列处理中，请稍候...")

    def enqueue_install_tasks(self, apk_paths):
        """将APK路径列表加入安装队列"""
        if not apk_paths:
            return

        for apk_path in apk_paths:
            self.install_queue.put(apk_path)

        task_count = len(apk_paths)
        self.root.after(0, lambda: self.status_label.configure(text=f"已加入{task_count}个安装任务，等待执行..."))
    
    def start_status_monitoring(self):
        """启动设备状态监控线程"""
        def monitor_status():
            while self.status_check_running:
                try:
                    status = adb_manager.get_device_status()
                    if status != self.current_status:
                        self.current_status = status
                        # 在主线程中更新UI
                        self.root.after(0, self.update_status_ui)
                    time.sleep(2)  # 每2秒检查一次
                except Exception as e:
                    print(f"状态监控出错: {e}")
                    time.sleep(5)  # 出错时等待更长时间
        
        # 启动监控线程
        self.status_thread = threading.Thread(target=monitor_status, daemon=True)
        self.status_thread.start()
    
    def update_status_ui(self):
        """更新状态UI（在主线程中调用）"""
        # 根据设备状态更新背景色和文本
        if self.current_status == DeviceStatus.CONNECTED:
            # 浅绿色背景
            self.main_frame.configure(fg_color=CONNECTED_BG)
            # 获取设备名称并显示
            try:
                status, devices = adb_manager.get_connected_devices()
                device_name = None
                if status == DeviceStatus.CONNECTED and devices:
                    # 使用第一个设备名称
                    device_name = adb_manager.get_device_name(devices[0])
                display_name = device_name or "未知设备"
                self.device_status_label.configure(text=f"设备已连接：{display_name}", text_color="green")
            except Exception:
                self.device_status_label.configure(text="设备已连接：未知设备", text_color="green")
        elif self.current_status == DeviceStatus.ADB_ERROR:
            # 浅红色背景
            self.main_frame.configure(fg_color=DISCONNECTED_BG)
            self.device_status_label.configure(text="ADB调用失败", text_color="red")
        else:  # DISCONNECTED
            # 默认背景色
            self.main_frame.configure(fg_color=["gray92", "gray14"])  # customtkinter默认色
            self.device_status_label.configure(text="未连接设备", text_color="gray")
    
    def on_file_drop(self, event):
        """处理文件拖拽事件"""
        raw_files = self.root.tk.splitlist(event.data)

        if not raw_files:
            return

        normalized_files = []
        for raw_path in raw_files:
            path = raw_path.strip()
            if path.startswith("{") and path.endswith("}"):
                path = path[1:-1]
            path = path.strip('"')
            normalized_files.append(path)

        valid_apks = []
        invalid_paths = []

        for file_path in normalized_files:
            if self.is_valid_apk(file_path):
                valid_apks.append(file_path)
            else:
                invalid_paths.append(file_path)

        if invalid_paths:
            invalid_names = "\n".join(Path(p).name for p in invalid_paths)
            self.show_message("错误", f"以下文件不是有效的APK，将不会加入队列：\n{invalid_names}", "error")

        if not valid_apks:
            return

        # 检查设备连接状态
        if self.current_status != DeviceStatus.CONNECTED:
            if self.current_status == DeviceStatus.ADB_ERROR:
                self.show_message("错误", "ADB调用失败，请检查Android SDK安装", "error")
            else:
                self.show_message("错误", "未检测到连接的Android设备", "error")
            return

        self.enqueue_install_tasks(valid_apks)
    
    def is_valid_apk(self, file_path: str) -> bool:
        """验证是否为有效的APK文件"""
        if not os.path.exists(file_path):
            return False
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.apk'):
            return False
        
        # 可以添加更多验证逻辑，比如检查文件头等
        return True
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息对话框"""
        if msg_type == "error":
            tk.messagebox.showerror(title, message)
        elif msg_type == "warning":
            tk.messagebox.showwarning(title, message)
        else:
            tk.messagebox.showinfo(title, message)
    
    def on_closing(self):
        """窗口关闭事件处理"""
        self.status_check_running = False
        self.install_worker_running = False
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = AndroidInstallerApp()
        app.run()
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
