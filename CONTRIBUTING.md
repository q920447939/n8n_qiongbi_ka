# 贡献指南

感谢您对 N8N 穷逼卡项目的关注！我们欢迎所有形式的贡献，无论是代码、文档、bug 报告还是功能建议。

## 🤝 贡献方式

### 🐛 报告 Bug
- 使用 [Bug 报告模板](.github/ISSUE_TEMPLATE/bug_report.md) 创建 issue
- 提供详细的复现步骤和环境信息
- 包含相关的错误日志和截图

### 💡 功能建议
- 使用 [功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md) 创建 issue
- 详细描述功能需求和使用场景
- 说明功能的优先级和重要性

### ❓ 提问
- 使用 [问题咨询模板](.github/ISSUE_TEMPLATE/question.md) 创建 issue
- 先搜索现有 issues 避免重复提问
- 提供足够的上下文信息

### 🔧 代码贡献
- Fork 项目到你的 GitHub 账户
- 创建功能分支进行开发
- 提交 Pull Request

## 🚀 开发环境设置

### 前置要求
- Python 3.12+
- MySQL 8.0+
- Git
- Docker & Docker Compose (可选)

### 本地开发设置

1. **Fork 并克隆项目**
```bash
git clone https://github.com/your-username/n8n_qiongbi_ka.git
cd n8n_qiongbi_ka
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -e .
pip install -e ".[dev]"  # 安装开发依赖
```

4. **配置环境变量**
```bash
cp .env.dev .env
# 根据需要修改 .env 文件中的配置
```

5. **设置数据库**
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE n8n_mobile_cards CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **启动开发服务器**
```bash
python main.py --env dev --reload
```

### Docker 开发环境

```bash
# 启动开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f n8n_app
```

## 📝 代码规范

### Python 代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码风格
- 使用类型注解 (Type Hints)
- 函数和类必须有文档字符串
- 变量和函数名使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_CASE

### 代码示例
```python
from typing import List, Optional
from pydantic import BaseModel

class MobileCard(BaseModel):
    """手机卡数据模型
    
    Attributes:
        card_id: 卡片ID
        product_name: 产品名称
        monthly_rent: 月租费用
    """
    card_id: str
    product_name: str
    monthly_rent: Optional[str] = None
    
    def get_display_name(self) -> str:
        """获取显示名称
        
        Returns:
            格式化的显示名称
        """
        return f"{self.product_name} ({self.monthly_rent})"
```

### 提交信息规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档变更
- `style`: 代码格式化
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `build`: 构建系统
- `ci`: CI/CD 相关
- `chore`: 其他变更

**示例:**
```
feat(api): 添加手机卡数据导出功能

- 支持 CSV 和 JSON 格式导出
- 添加数据过滤和排序选项
- 包含完整的 API 文档

Closes #123
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_card_service.py

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 编写测试
- 为新功能编写单元测试
- 测试文件命名为 `test_*.py`
- 使用 pytest 框架
- 测试覆盖率应保持在 80% 以上

```python
import pytest
from card_service import MobileCardService

class TestMobileCardService:
    """手机卡服务测试类"""
    
    def test_save_mobile_cards(self):
        """测试保存手机卡数据"""
        service = MobileCardService()
        cards = [...]  # 测试数据
        
        result = service.save_mobile_cards(cards)
        
        assert result > 0
        assert service.get_card_count() == len(cards)
```

## 📚 文档

### API 文档
- 使用 FastAPI 自动生成的文档
- 为所有 API 端点添加详细描述
- 包含请求/响应示例

### 代码文档
- 所有公共函数和类必须有文档字符串
- 使用 Google 风格的文档字符串
- 包含参数、返回值和异常说明

```python
def save_mobile_cards(self, cards: List[MobileCardData]) -> int:
    """保存手机卡数据
    
    Args:
        cards: 手机卡数据列表
        
    Returns:
        成功保存的记录数
        
    Raises:
        ValueError: 当数据格式不正确时
        DatabaseError: 当数据库操作失败时
    """
    pass
```

## 🔄 Pull Request 流程

### 1. 创建分支
```bash
# 从 main 分支创建新分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. 开发和测试
- 编写代码
- 添加测试
- 运行测试确保通过
- 更新文档

### 3. 提交代码
```bash
git add .
git commit -m "feat: 添加新功能描述"
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request
- 使用 [PR 模板](.github/pull_request_template.md)
- 填写详细的变更描述
- 关联相关的 issue
- 请求代码审查

### 5. 代码审查
- 响应审查意见
- 根据反馈修改代码
- 确保 CI/CD 检查通过

### 6. 合并
- 维护者会在审查通过后合并 PR
- 删除功能分支

## 🏷️ 版本发布

### 版本号规范
使用 [语义化版本](https://semver.org/) (SemVer):
- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的 API 变更
- `MINOR`: 向后兼容的功能新增
- `PATCH`: 向后兼容的问题修正

### 发布流程
1. 更新 `CHANGELOG.md`
2. 更新版本号
3. 创建 Git 标签
4. 发布 GitHub Release

## 🏆 贡献者认可

### 贡献者类型
- **代码贡献者**: 提交代码的开发者
- **文档贡献者**: 改进文档的贡献者
- **测试贡献者**: 编写测试的贡献者
- **设计贡献者**: 提供设计的贡献者
- **社区贡献者**: 帮助社区建设的贡献者

### 认可方式
- 在 README.md 中列出贡献者
- 在发布说明中感谢贡献者
- 为重要贡献者提供项目权限

## 📞 联系我们

- **GitHub Issues**: 技术问题和 bug 报告
- **GitHub Discussions**: 功能讨论和社区交流
- **Email**: 敏感问题和安全报告

## 📋 行为准则

### 我们的承诺
我们致力于为每个人提供友好、安全和欢迎的环境，无论年龄、身体大小、残疾、种族、性别认同和表达、经验水平、教育、社会经济地位、国籍、个人外貌、种族、宗教或性取向如何。

### 我们的标准
**积极行为包括:**
- 使用欢迎和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

**不可接受的行为包括:**
- 使用性化的语言或图像
- 恶意评论、侮辱/贬损评论和人身或政治攻击
- 公开或私人骚扰
- 未经明确许可发布他人的私人信息
- 在专业环境中可能被认为不当的其他行为

### 执行
项目维护者有权利和责任删除、编辑或拒绝不符合本行为准则的评论、提交、代码、wiki 编辑、问题和其他贡献。

---

再次感谢您的贡献！🎉