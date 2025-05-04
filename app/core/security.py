from passlib.context import CryptContext

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """验证密码"""
    # 如果哈希密码以$开头，说明已经被哈希过
    if hashed_password.startswith('$'):
        return pwd_context.verify(plain_password, hashed_password)
    # 否则是明文密码（兼容旧数据）
    return plain_password == hashed_password

def get_password_hash(password):
    """哈希密码"""
    return pwd_context.hash(password)
