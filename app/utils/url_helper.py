def get_url_with_prefix(path: str, prefix: str = "/mlsp") -> str:
    """
    为静态资源路径添加适当的前缀
    
    Args:
        path: 原始路径，例如 "/static/image.jpg"
        prefix: 应用前缀，默认为 "/mlsp"
        
    Returns:
        带前缀的完整路径
    """
    # 如果路径已经包含前缀或者是完整URL，直接返回
    if path.startswith(prefix) or path.startswith("http"):
        return path
        
    # 如果路径以斜杠开头，确保不会有双斜杠
    if path.startswith("/"):
        return f"{prefix}{path}"
    else:
        return f"{prefix}/{path}"
