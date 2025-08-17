# 安全政策


## 🚨 报告安全漏洞

我们非常重视项目的安全性。如果您发现了安全漏洞，请负责任地向我们报告。

### 报告流程

**请不要在公开的 GitHub Issues 中报告安全漏洞。**

1. **私密报告**: 请通过以下方式之一私密报告安全问题：
   - 发送邮件至: [security@yourproject.com](mailto:security@yourproject.com)
   - 使用 GitHub 的私密安全报告功能
   - 通过项目维护者的私人联系方式

2. **报告内容**: 请在报告中包含以下信息：
   - 漏洞的详细描述
   - 重现步骤
   - 潜在的影响范围
   - 建议的修复方案（如果有）
   - 您的联系信息

3. **响应时间**: 我们承诺：
   - 24 小时内确认收到报告
   - 72 小时内提供初步评估
   - 7 天内提供详细的响应计划

### 安全报告模板

```
**漏洞类型**: [例如: SQL注入, XSS, 认证绕过等]

**影响版本**: [受影响的版本范围]

**严重程度**: [低/中/高/严重]

**漏洞描述**:
[详细描述漏洞的性质和工作原理]

**重现步骤**:
1. 步骤 1
2. 步骤 2
3. 步骤 3

**影响范围**:
[描述漏洞可能造成的影响]

**修复建议**:
[如果有修复建议，请在此描述]

**附加信息**:
[任何其他相关信息]
```

## 🛡️ 安全最佳实践

### 部署安全

#### 环境配置
- **环境变量**: 所有敏感信息（数据库密码、API密钥等）必须通过环境变量配置
- **配置文件**: 不要在代码仓库中提交包含敏感信息的配置文件
- **权限控制**: 使用最小权限原则配置数据库用户和系统权限

#### 网络安全
- **HTTPS**: 生产环境必须使用 HTTPS
- **CORS**: 正确配置 CORS 策略，不要使用 `allow_origins=["*"]`
- **防火墙**: 配置适当的防火墙规则，只开放必要的端口

#### 数据库安全
- **连接加密**: 使用 SSL/TLS 加密数据库连接
- **访问控制**: 限制数据库访问权限
- **备份加密**: 对数据库备份进行加密

### 应用安全

#### 认证和授权
```python
# 示例：安全的 API 认证
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    """验证 API Token"""
    if not token or not verify_api_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token
```

#### 输入验证
```python
# 示例：使用 Pydantic 进行输入验证
from pydantic import BaseModel, validator
from typing import Optional

class MobileCardData(BaseModel):
    card_id: str
    product_name: str
    monthly_rent: Optional[str] = None
    
    @validator('card_id')
    def validate_card_id(cls, v):
        if not v or len(v) > 50:
            raise ValueError('Card ID must be 1-50 characters')
        return v.strip()
```

#### SQL 注入防护
- 使用 SQLAlchemy ORM 而不是原生 SQL
- 对所有用户输入进行验证和清理
- 使用参数化查询

```python
# 安全的数据库查询示例
def get_cards_by_operator(operator: str) -> List[MobileCard]:
    """安全的数据库查询"""
    return session.query(MobileCard).filter(
        MobileCard.operator == operator
    ).all()
```

#### 错误处理
```python
# 安全的错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 不泄露敏感信息"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )
```

### Docker 安全

#### 镜像安全
```dockerfile
# 使用非 root 用户运行应用
FROM python:3.12-slim

# 创建非特权用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 复制文件并设置权限
COPY --chown=appuser:appuser . .

# 切换到非特权用户
USER appuser

# 启动应用
CMD ["python", "main.py"]
```

#### 容器配置
```yaml
# docker-compose.yml 安全配置示例
services:
  n8n_app:
    build: .
    # 只读根文件系统
    read_only: true
    # 临时文件系统
    tmpfs:
      - /tmp
    # 安全选项
    security_opt:
      - no-new-privileges:true
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## 🔍 安全审计

### 依赖安全
定期检查依赖包的安全漏洞：

```bash
# 使用 pip-audit 检查依赖安全
pip install pip-audit
pip-audit

# 使用 safety 检查已知漏洞
pip install safety
safety check
```

### 代码安全扫描
```bash
# 使用 bandit 进行 Python 代码安全扫描
pip install bandit
bandit -r . -f json -o security-report.json
```

### 定期安全检查清单
- [ ] 依赖包安全扫描
- [ ] 代码安全审计
- [ ] 配置安全检查
- [ ] 访问日志审查
- [ ] 权限配置审查
- [ ] 备份和恢复测试

## 🚨 安全事件响应

### 事件分类
- **P0 - 严重**: 数据泄露、系统完全不可用
- **P1 - 高**: 权限提升、部分功能不可用
- **P2 - 中**: 信息泄露、性能问题
- **P3 - 低**: 配置问题、轻微漏洞

### 响应流程
1. **检测和报告** (0-1小时)
   - 确认安全事件
   - 评估影响范围
   - 通知相关人员

2. **遏制** (1-4小时)
   - 隔离受影响系统
   - 阻止进一步损害
   - 保护证据

3. **调查** (4-24小时)
   - 分析攻击向量
   - 确定根本原因
   - 评估损害程度

4. **恢复** (24-72小时)
   - 修复漏洞
   - 恢复服务
   - 验证系统安全

5. **总结** (1周内)
   - 编写事件报告
   - 改进安全措施
   - 更新安全政策

## 📋 安全配置检查清单

### 生产环境部署前检查
- [ ] 所有默认密码已更改
- [ ] 启用 HTTPS 和 SSL/TLS
- [ ] 配置适当的 CORS 策略
- [ ] 设置安全的 Cookie 属性
- [ ] 启用安全头部 (HSTS, CSP 等)
- [ ] 配置日志记录和监控
- [ ] 设置备份和恢复策略
- [ ] 进行渗透测试

### 定期维护检查
- [ ] 更新依赖包到最新安全版本
- [ ] 审查访问日志
- [ ] 检查系统补丁
- [ ] 验证备份完整性
- [ ] 测试灾难恢复计划

## 🏆 安全致谢

我们感谢以下安全研究人员的负责任披露：

<!-- 
格式：
- [研究人员姓名](链接) - 漏洞描述 - 报告日期
-->

*目前还没有安全报告记录*

## 📞 联系信息

**安全团队邮箱**: security@yourproject.com

**PGP 公钥**: 
```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[您的 PGP 公钥]
-----END PGP PUBLIC KEY BLOCK-----
```

**响应时间承诺**:
- 确认收到: 24 小时内
- 初步评估: 72 小时内
- 详细响应: 7 天内

---

感谢您帮助保护 N8N 穷逼卡项目的安全！🔒
