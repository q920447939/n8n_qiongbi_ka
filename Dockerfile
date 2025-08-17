# 使用官方Python 3.12镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# 安装系统依赖和时区设置
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 配置pip使用中国镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装uv包管理器
RUN pip install uv

# 配置uv使用中国镜像源
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
ENV UV_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 复制项目文件
COPY pyproject.toml ./
COPY uv.lock* ./

# 设置uv环境变量，避免创建虚拟环境
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_SYNC=1

# 使用uv安装依赖到系统Python
RUN uv pip install -r pyproject.toml

# 复制应用代码
COPY . .

# 创建工作目录权限设置脚本
RUN echo '#!/bin/bash\nchmod -R 755 /app\nexec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# 暴露端口
EXPOSE 8100

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# 设置入口点和启动命令
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]