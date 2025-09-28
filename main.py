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

from adb_utils import adb_manager, DeviceStatus

CONNECTED_BG = "#E8F5E8" # 连接状态背景颜色
DISCONNECTED_BG = "#FFE8E8" # 未连接状态背景颜色

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
        
        # 创建UI组件
        self.setup_ui()
        
        # 配置拖拽功能
        self.setup_drag_drop()
        
        # 启动状态检测线程
        self.start_status_monitoring()
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title("Android APK安装器")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # 设置窗口背景为深色
        self.root.configure(bg="#212121")
        
        # 尝试设置无边框窗口以获得完全的深色外观
        try:
            # 设置窗口属性
            self.root.overrideredirect(True)  # 移除标题栏
            
            # 创建自定义标题栏
            self.title_frame = ctk.CTkFrame(self.root, height=30, fg_color="#2b2b2b")
            self.title_frame.pack(fill="x", padx=0, pady=0)
            self.title_frame.pack_propagate(False)
            
            # 标题文本
            self.title_label = ctk.CTkLabel(
                self.title_frame, 
                text="Android APK安装器 by hwj",
                font=ctk.CTkFont(size=12),
                text_color="white"
            )
            self.title_label.pack(side="left", padx=10, pady=5)
            
            # 关闭按钮
            self.close_button = ctk.CTkButton(
                self.title_frame,
                text="×",
                width=30,
                height=20,
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color="transparent",
                hover_color="#ff4444",
                command=self.on_closing
            )
            self.close_button.pack(side="right", padx=5, pady=5)
            
            # 使标题栏可拖拽
            self.title_frame.bind("<Button-1>", self.start_move)
            self.title_frame.bind("<B1-Motion>", self.do_move)
            self.title_label.bind("<Button-1>", self.start_move)
            self.title_label.bind("<B1-Motion>", self.do_move)
            
        except Exception as e:
            print(f"创建自定义标题栏失败，使用默认窗口: {e}")
            self.root.overrideredirect(False)
        
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
        """应用深色主题到窗口标题栏（现在不需要了，因为使用自定义标题栏）"""
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
            self.device_status_label.configure(text="设备已连接", text_color="green")
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
        files = self.root.tk.splitlist(event.data)
        
        if not files:
            return
        
        file_path = files[0]  # 只处理第一个文件
        
        # 验证是否为APK文件
        if not self.is_valid_apk(file_path):
            self.show_message("错误", "请拖拽有效的APK文件！", "error")
            return
        
        # 检查设备连接状态
        if self.current_status != DeviceStatus.CONNECTED:
            if self.current_status == DeviceStatus.ADB_ERROR:
                self.show_message("错误", "ADB调用失败，请检查Android SDK安装", "error")
            else:
                self.show_message("错误", "未检测到连接的Android设备", "error")
            return
        
        # 在新线程中执行安装，避免阻塞UI
        threading.Thread(target=self.install_apk_async, args=(file_path,), daemon=True).start()
    
    def is_valid_apk(self, file_path: str) -> bool:
        """验证是否为有效的APK文件"""
        if not os.path.exists(file_path):
            return False
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.apk'):
            return False
        
        # 可以添加更多验证逻辑，比如检查文件头等
        return True
    
    def install_apk_async(self, apk_path: str):
        """异步安装APK文件"""
        # 在主线程中显示安装中状态
        self.root.after(0, lambda: self.status_label.configure(text="正在安装APK..."))
        
        try:
            # 获取连接的设备
            status, devices = adb_manager.get_connected_devices()
            
            if status != DeviceStatus.CONNECTED or not devices:
                self.root.after(0, lambda: self.show_message("错误", "设备连接已断开", "error"))
                return
            
            # 如果有多个设备，使用第一个
            device_id = devices[0] if len(devices) == 1 else None
            
            # 执行安装
            success, message = adb_manager.install_apk(apk_path, device_id)
            
            # 在主线程中显示结果
            if success:
                self.root.after(0, lambda: self.show_message("成功", message, "info"))
            else:
                self.root.after(0, lambda: self.show_message("安装失败", message, "error"))
                
        except Exception as e:
            error_msg = f"安装过程中出现异常: {str(e)}"
            self.root.after(0, lambda: self.show_message("错误", error_msg, "error"))
        
        finally:
            # 恢复原始提示文本
            self.root.after(0, lambda: self.status_label.configure(text="请拖拽APK文件到窗体"))
    
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
