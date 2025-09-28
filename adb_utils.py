"""
ADB工具类模块
提供Android设备检测和APK安装功能
"""

import subprocess
import os
import logging
from enum import Enum
from typing import List, Optional, Tuple

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
STARTF_USESHOWWINDOW = getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
STARTUPINFO = getattr(subprocess, "STARTUPINFO", None)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)

# 配置ADB模块专用日志
adb_logger = logging.getLogger('adb_utils')
adb_logger.setLevel(logging.INFO)

# 创建文件处理器，日志输出到文件
log_handler = logging.FileHandler('android_installer.log', encoding='utf-8')
log_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

# 添加处理器到logger
adb_logger.addHandler(log_handler)


class DeviceStatus(Enum):
    """设备连接状态枚举"""
    DISCONNECTED = "disconnected"  # 未连接设备
    CONNECTED = "connected"        # 设备正常连接
    ADB_ERROR = "adb_error"       # ADB调用失败


class ADBManager:
    """ADB管理器类"""
    
    def __init__(self):
        self._cached_adb_path = None  # ADB路径缓存
        self.adb_path = self._find_adb_path()

    def _run_subprocess(self, cmd, **kwargs):
        if os.name == "nt":
            flags = kwargs.get("creationflags", 0)
            if CREATE_NO_WINDOW:
                flags |= CREATE_NO_WINDOW
            if DETACHED_PROCESS:
                flags |= DETACHED_PROCESS
            kwargs["creationflags"] = flags
            if STARTUPINFO and STARTF_USESHOWWINDOW:
                startupinfo = kwargs.get("startupinfo")
                if startupinfo is None:
                    startupinfo = STARTUPINFO()
                startupinfo.dwFlags |= STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                kwargs["startupinfo"] = startupinfo
            kwargs.setdefault("stdin", subprocess.DEVNULL)
        return subprocess.run(cmd, **kwargs)

    def _get_portable_adb_path(self) -> Optional[str]:
        """
        获取便携版ADB路径
        
        Returns:
            Optional[str]: 便携版ADB路径，如果不存在则返回None
        """
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 便携版ADB路径
        portable_adb_path = os.path.join(current_dir, "platform-tools", "adb.exe")
        
        if os.path.exists(portable_adb_path):
            return portable_adb_path
        
        return None
    
    def _find_adb_path(self) -> Optional[str]:
        """查找ADB可执行文件路径"""
        # 如果已有缓存路径，直接返回
        if self._cached_adb_path:
            return self._cached_adb_path
            
        # 首先尝试从PATH环境变量中查找
        try:
            result = self._run_subprocess(['where', 'adb'], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                adb_path = result.stdout.strip().split('\n')[0]
                self._cached_adb_path = adb_path
                return adb_path
        except Exception:
            pass
        
        # 尝试常见的Android SDK路径
        common_paths = [
            os.path.expanduser("~/AppData/Local/Android/Sdk/platform-tools/adb.exe"),
            "C:/Android/Sdk/platform-tools/adb.exe",
            "C:/Program Files/Android/Sdk/platform-tools/adb.exe",
            "C:/Users/%USERNAME%/AppData/Local/Android/Sdk/platform-tools/adb.exe"
        ]
        
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                self._cached_adb_path = expanded_path
                return expanded_path
        
        # 最后尝试便携版ADB路径
        portable_adb = self._get_portable_adb_path()
        if portable_adb:
            self._cached_adb_path = portable_adb
            return portable_adb
        
        return None
    
    def is_adb_available(self) -> bool:
        """检查ADB是否可用"""
        if not self.adb_path:
            print("ADB路径未找到，请检查Android SDK安装或确保便携版ADB存在")
            return False
        
        try:
            result = self._run_subprocess([self.adb_path, 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                print(f"ADB可用，路径: {self.adb_path}")
                return True
            else:
                print(f"ADB版本检查失败，返回码: {result.returncode}")
                print(f"错误输出: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("ADB版本检查超时")
            return False
        except Exception as e:
            print(f"ADB可用性检查异常: {e}")
            return False
    
    def get_connected_devices(self) -> Tuple[DeviceStatus, List[str]]:
        """
        获取连接的设备列表
        
        Returns:
            Tuple[DeviceStatus, List[str]]: (状态, 设备列表)
        """
        if not self.is_adb_available():
            return DeviceStatus.ADB_ERROR, []
        
        try:
            result = self._run_subprocess([self.adb_path, 'devices'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode != 0:
                return DeviceStatus.ADB_ERROR, []
            
            # 解析设备列表
            lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
            devices = []
            
            for line in lines:
                line = line.strip()
                if line and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            if devices:
                return DeviceStatus.CONNECTED, devices
            else:
                return DeviceStatus.DISCONNECTED, []
                
        except Exception as e:
            print(f"获取设备列表时出错: {e}")
            return DeviceStatus.ADB_ERROR, []
    
    def install_apk(self, apk_path: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        安装APK文件
        
        Args:
            apk_path: APK文件路径
            device_id: 目标设备ID（可选，如果有多个设备）
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        if not self.is_adb_available():
            return False, "ADB不可用，请检查Android SDK是否正确安装"
        
        if not os.path.exists(apk_path):
            return False, f"APK文件不存在: {apk_path}"
        
        try:
            # 构建安装命令
            cmd = [self.adb_path]
            if device_id:
                cmd.extend(['-s', device_id])
            cmd.extend(['install', '-r', apk_path])  # -r 表示替换已存在的应用
            
            result = self._run_subprocess(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=60)  # 安装可能需要较长时间
            
            if result.returncode == 0 and 'Success' in result.stdout:
                return True, "APK安装成功"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"安装失败: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "安装超时，请检查设备连接和APK文件"
        except Exception as e:
            return False, f"安装过程中出错: {str(e)}"
    
    def get_device_status(self) -> DeviceStatus:
        """
        获取设备连接状态
        
        Returns:
            DeviceStatus: 设备状态
        """
        status, devices = self.get_connected_devices()
        return status


# 全局ADB管理器实例
adb_manager = ADBManager()