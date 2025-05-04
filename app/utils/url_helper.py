from ..core.config import BASE_PATH, get_prefixed_url

def get_url_with_prefix(path: str, prefix: str = None) -> str:
    """
    为静态资源路径添加适当的前缀
    
    Args:
        path: 原始路径，例如 "/static/image.jpg"
        prefix: 应用前缀，默认使用配置中的BASE_PATH
        
    Returns:
        带前缀的完整路径
    """
    # 使用传入的prefix或默认的BASE_PATH
    actual_prefix = prefix if prefix is not None else BASE_PATH
    
    # 如果路径已经包含前缀或者是完整URL，直接返回
    if path.startswith(actual_prefix) or path.startswith("http"):
        return path
        
    # 如果路径以斜杠开头，确保不会有双斜杠
    if path.startswith("/"):
        return f"{actual_prefix}{path}"
    else:
        return f"{actual_prefix}/{path}"

# 提供更短的别名函数
url_for = get_prefixed_url = get_url_with_prefix
