"""
Android APK安装器发布脚本
使用PyInstaller将项目打包为便携可执行程序
"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from textwrap import dedent
import logging

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as tomllib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AndroidInstallerReleaser:
    """Android安装器发布管理器"""
    
    def __init__(self):
        # 项目根目录
        self.project_root = Path(__file__).resolve().parent.parent
        
        # 关键路径
        self.src_dir = self.project_root / "src"
        self.main_script = self.src_dir / "main.py"
        self.platform_tools_dir = self.project_root / "assets" / "platform-tools"
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"

        # 项目元数据
        self.project_metadata = self._load_project_metadata()
        self.project_name = self.project_metadata.get("name", "Android APK Installer")
        self.project_version = self.project_metadata.get("version", "0.0.0")
        self.project_description = self.project_metadata.get("description", self.project_name)
        self.project_author = self._resolve_author(self.project_metadata)
        self._temp_version_file = None
        
        # 输出文件名
        self.exe_name = "android_installer.exe"
        self.zip_name = "android_installer.zip"
        
        logger.info(f"项目根目录: {self.project_root}")
        logger.info(f"源码目录: {self.src_dir}")
        logger.info(f"主脚本: {self.main_script}")
        logger.info(f"Platform-tools目录: {self.platform_tools_dir}")
        logger.info(f"项目名称: {self.project_name}")
        logger.info(f"项目版本: {self.project_version}")
        logger.info(f"作者: {self.project_author}")

    def _load_project_metadata(self) -> dict:
        """读取pyproject.toml中的项目信息"""
        if not self.pyproject_path.exists():
            logger.warning(f"未找到pyproject.toml，使用默认元数据: {self.pyproject_path}")
            return {}

        with self.pyproject_path.open("rb") as fp:
            data = tomllib.load(fp)

        return data.get("project", {})

    @staticmethod
    def _resolve_author(project_metadata: dict) -> str:
        """从pyproject元数据解析作者"""
        authors = project_metadata.get("authors")
        if isinstance(authors, list) and authors:
            first = authors[0]
            if isinstance(first, dict):
                return first.get("name") or first.get("email") or "Junerver"
            return str(first)
        return "Junerver"

    @staticmethod
    def _parse_version_tuple(version: str) -> tuple[int, int, int, int]:
        """将语义化版本转换成Windows资源要求的四段整数"""
        parts = []
        for chunk in version.replace("-", ".").split("."):
            try:
                parts.append(int(chunk))
            except ValueError:
                digits = "".join(filter(str.isdigit, chunk))
                parts.append(int(digits) if digits else 0)

        while len(parts) < 4:
            parts.append(0)

        return tuple(parts[:4])

    def _create_version_file(self) -> Path:
        """生成PyInstaller版本信息所需的临时文件"""
        file_version = self._parse_version_tuple(self.project_version)
        current_year = datetime.now().year

        version_template = dedent(
            f"""
            VSVersionInfo(
                ffi=FixedFileInfo(
                    filevers={file_version},
                    prodvers={file_version},
                    mask=0x3F,
                    flags=0x0,
                    OS=0x40004,
                    fileType=0x1,
                    subtype=0x0,
                    date=(0, 0)
                ),
                kids=[
                    StringFileInfo(
                        [
                            StringTable(
                                '040904B0',
                                [
                                    StringStruct('CompanyName', '{self.project_author}'),
                                    StringStruct('FileDescription', '{self.project_description}'),
                                    StringStruct('FileVersion', '{self.project_version}'),
                                    StringStruct('InternalName', '{self.exe_name}'),
                                    StringStruct('LegalCopyright', 'Copyright (c) {current_year} {self.project_author}'),
                                    StringStruct('OriginalFilename', '{self.exe_name}'),
                                    StringStruct('ProductName', '{self.project_name}'),
                                    StringStruct('ProductVersion', '{self.project_version}'),
                                ]
                            )
                        ]
                    ),
                    VarFileInfo(
                        [VarStruct('Translation', [1033, 1200])]
                    )
                ]
            )
            """
        ).strip()

        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")
        temp_file.write(version_template)
        temp_file.flush()
        temp_file.close()

        temp_path = Path(temp_file.name)
        logger.debug(f"生成版本信息文件: {temp_path}")
        self._temp_version_file = temp_path
        return temp_path
    
    def flatten_dist_structure(self):
        """Flatten dist so the exe sits beside platform-tools."""
        bundle_dir = self.dist_dir / self.exe_name.replace('.exe', '')
        if not bundle_dir.exists():
            raise FileNotFoundError(f"PyInstaller output directory missing: {bundle_dir}")

        exe_path = bundle_dir / self.exe_name
        if not exe_path.exists():
            raise FileNotFoundError(f"Executable missing inside bundle: {exe_path}")

        target_exe_path = self.dist_dir / self.exe_name
        logger.info(f"Moving executable to: {target_exe_path}")
        if target_exe_path.exists():
            if target_exe_path.is_file():
                target_exe_path.unlink()
            else:
                shutil.rmtree(target_exe_path)
        exe_path.replace(target_exe_path)

        remaining_items = list(bundle_dir.iterdir())
        for item in remaining_items:
            target_path = self.dist_dir / item.name
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            logger.debug(f"Relocating runtime file: {item} -> {target_path}")
            item.replace(target_path)

        logger.info(f"Removing temporary runtime directory: {bundle_dir}")
        bundle_dir.rmdir()

    def clean_build_dirs(self):
        """清理构建目录"""
        logger.info("清理构建目录...")
        
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                logger.info(f"删除目录: {dir_path}")
                shutil.rmtree(dir_path)
        
        logger.info("构建目录清理完成")
    
    def build_executable(self):
        """使用PyInstaller构建可执行文件"""
        logger.info("开始构建可执行文件...")
        
        # 检查主脚本是否存在
        if not self.main_script.exists():
            raise FileNotFoundError(f"主脚本不存在: {self.main_script}")
        
        # 添加pywin32依赖到隐藏导入
        hidden_imports = ["win32gui", "win32con"]

        # 生成版本信息文件
        version_file_path = self._create_version_file()

        # PyInstaller命令参数
        pyinstaller_args = [
            "pyinstaller",
            "--onedir",  # 生成目录而不是单文件
            "--windowed",  # 无控制台窗口
            "--name", self.exe_name.replace('.exe', ''),  # 输出文件名
            "--distpath", str(self.dist_dir),  # 输出目录
            "--workpath", str(self.build_dir),  # 工作目录
            "--clean",  # 清理临时文件
            "--paths", str(self.src_dir),  # 确保src目录在模块查找路径
            "--hidden-import", "win32gui",  # 添加win32gui模块
            "--hidden-import", "win32con",  # 添加win32con模块
            "--version-file", str(version_file_path),  # 注入版本信息
            str(self.main_script)  # 主脚本路径
        ]
        
        logger.info(f"执行PyInstaller命令: {' '.join(pyinstaller_args)}")
        
        try:
            result = subprocess.run(
                pyinstaller_args,
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("PyInstaller执行成功")
            logger.debug(f"PyInstaller输出: {result.stdout}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"PyInstaller执行失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            raise
        finally:
            if self._temp_version_file and self._temp_version_file.exists():
                logger.debug(f"删除临时版本信息文件: {self._temp_version_file}")
                self._temp_version_file.unlink(missing_ok=True)
                self._temp_version_file = None
    
    def copy_platform_tools(self):
        """拷贝platform-tools目录到dist"""
        logger.info("拷贝platform-tools目录...")
        
        if not self.platform_tools_dir.exists():
            raise FileNotFoundError(f"Platform-tools目录不存在: {self.platform_tools_dir}")
        
        # 目标路径
        target_platform_tools = self.dist_dir / "platform-tools"
        
        # 拷贝整个目录
        shutil.copytree(self.platform_tools_dir, target_platform_tools)
        
        logger.info(f"Platform-tools拷贝完成: {target_platform_tools}")
    
    def create_zip_package(self):
        """创建zip便携包"""
        logger.info("创建zip便携包...")
        
        # 创建zip文件
        zip_path = self.project_root / self.zip_name
        
        # 如果zip文件已存在，删除它
        if zip_path.exists():
            zip_path.unlink()
            logger.info(f"删除已存在的zip文件: {zip_path}")
        
        # 创建zip文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加dist目录中的所有文件
            for file_path in self.dist_dir.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    arcname = file_path.relative_to(self.dist_dir)
                    zipf.write(file_path, arcname)
                    logger.debug(f"添加文件到zip: {arcname}")
        
        logger.info(f"zip便携包创建完成: {zip_path}")
        
        # 显示zip文件大小
        zip_size = zip_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"便携包大小: {zip_size:.2f} MB")
    
    def verify_build(self):
        """验证构建产物"""
        logger.info("验证构建产物...")
        
        # 检查exe文件 (已扁平化到dist根目录)
        exe_path = self.dist_dir / self.exe_name
        if not exe_path.exists():
            raise FileNotFoundError(f"可执行文件未找到: {exe_path}")
        
        # 检查platform-tools目录
        platform_tools_path = self.dist_dir / "platform-tools"
        if not platform_tools_path.exists():
            raise FileNotFoundError(f"Platform-tools目录未找到: {platform_tools_path}")
        
        # 检查adb.exe
        adb_path = platform_tools_path / "adb.exe"
        if not adb_path.exists():
            raise FileNotFoundError(f"ADB可执行文件未找到: {adb_path}")
        
        # 检查zip文件
        zip_path = self.project_root / self.zip_name
        if not zip_path.exists():
            raise FileNotFoundError(f"zip包未生成: {zip_path}")
        
        logger.info("所有构建项验证通过")
        
        # 输出文件信息
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"可执行文件大小: {exe_size:.2f} MB")
        
        platform_tools_files = list(platform_tools_path.glob('*'))
        logger.info(f"Platform-tools文件数量: {len(platform_tools_files)}")

    def release(self):
        """执行完整的发布流程"""
        logger.info("=" * 50)
        logger.info("开始Android APK安装器打包流程")
        logger.info("=" * 50)
        
        try:
            # 1. 清理构建目录
            self.clean_build_dirs()
            
            # 2. 构建可执行文件
            self.build_executable()
            
            # 3. 扁平化dist目录
            self.flatten_dist_structure()
            
            # 4. 拷贝platform-tools
            self.copy_platform_tools()
            
            # 5. 创建zip包
            self.create_zip_package()
            
            # 6. 校验产物
            self.verify_build()
            
            logger.info("=" * 50)
            logger.info("发布流程完成")
            logger.info(f"压缩包位置: {self.project_root / self.zip_name}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"发布流程失败: {e}")
            sys.exit(1)

def main():
    """主函数"""
    releaser = AndroidInstallerReleaser()
    releaser.release()


if __name__ == "__main__":
    main()
