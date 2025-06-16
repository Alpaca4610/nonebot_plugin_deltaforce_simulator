from pydantic import BaseModel
from typing import Optional, List

class Config(BaseModel):
    deltaforce_sim_config: Optional[str] = ""  # 自定义容器json的绝对路径

    
class ConfigError(Exception):
    pass