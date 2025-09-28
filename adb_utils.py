"""
ADB工具类模块
提供Android设备检测和APK安装功能
"""

import subprocess
import os
from enum import Enum
from typing import List, Optional, Tuple


class DeviceStatus(Enum):
    """设备连接状态枚举"""
    DISCONNECTED = "disconnected"  # 未连接设备
    CONNECTED = "connected"        # 设备正常连接
    ADB_ERROR = "adb_error"       # ADB调用失败


class ADBManager:
    """ADB管理器类"""
    
    def __init__(self):
        self.adb_path = self._find_adb_path()
    
    def _find_adb_path(self) -> Optional[str]:
        """查找ADB可执行文件路径"""
        # 首先尝试从PATH环境变量中查找
        try:
            result = subprocess.run(['where', 'adb'], 
                                  capture_output=True, 
                                  text=True, 
                                  shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
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
                return expanded_path
        
        return None
    
    def is_adb_available(self) -> bool:
        """检查ADB是否可用"""
        if not self.adb_path:
            return False
        
        try:
            result = subprocess.run([self.adb_path, 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except Exception:
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
            result = subprocess.run([self.adb_path, 'devices'], 
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
            
            result = subprocess.run(cmd, 
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