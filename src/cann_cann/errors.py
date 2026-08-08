"""cann-cann 的公开异常"""


class CannCannError(Exception):
    """cann-cann 公开异常的基类"""


class CANNNotFoundError(CannCannError):
    """找不到可用的 CANN 安装时抛出"""


class NPUDetectionError(CannCannError):
    """无法探测当前 NPU 名称时抛出"""


class PlatformConfigError(CannCannError):
    """无法使用 CANN 平台配置时抛出"""


class PlatformConfigNotFoundError(PlatformConfigError, FileNotFoundError):
    """找不到所需的平台配置文件时抛出"""
