#!/bin/bash

# N8N 穷逼卡项目 Docker 部署脚本
# 适用于中国大陆环境

set -e

echo "🚀 开始部署 N8N 穷逼卡项目..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
}

# 创建必要的目录
create_directories() {
    echo -e "${BLUE}📁 创建必要的目录...${NC}"
    
    # 创建宿主机挂载目录
    sudo mkdir -p /home/n8n_qiongbika/code
    sudo mkdir -p /home/n8n_qiongbika/nginx_config
    
    # 复制当前项目代码到挂载目录
    echo -e "${YELLOW}📋 复制项目代码到挂载目录...${NC}"
    sudo cp -r . /home/n8n_qiongbika/code/
    
    # 复制Nginx配置文件
    echo -e "${YELLOW}📋 复制Nginx配置文件...${NC}"
    sudo cp docker/nginx/default.conf /home/n8n_qiongbika/nginx_config/
    
    # 设置目录权限
    sudo chown -R $USER:$USER /home/n8n_qiongbika/
    
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 停止并清理旧容器
cleanup_old_containers() {
    echo -e "${YELLOW}🧹 清理旧容器...${NC}"
    
    # 停止容器
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 清理MySQL数据卷以确保初始化脚本能够执行
    echo -e "${YELLOW}🗑️  清理MySQL数据卷...${NC}"
    docker volume rm n8n_qiongbi_ka_mysql_data 2>/dev/null || true
    
    # 清理未使用的镜像和容器
    docker system prune -f 2>/dev/null || true
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 构建和启动服务
start_services() {
    echo -e "${BLUE}🔨 构建和启动服务...${NC}"
    
    # 使用Docker环境配置文件
    export ENV_FILE=.env.docker
    
    # 构建镜像
    echo -e "${YELLOW}📦 构建Python应用镜像...${NC}"
    docker-compose build --no-cache n8n_app
    
    # 启动所有服务
    echo -e "${YELLOW}🚀 启动所有服务...${NC}"
    docker-compose up -d
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${BLUE}⏳ 等待服务就绪...${NC}"
    
    # 等待MySQL就绪
    echo -e "${YELLOW}🗄️  等待MySQL服务就绪...${NC}"
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T n8n_mysql mysqladmin ping -h localhost -u root -p123456 --silent; then
            echo -e "${GREEN}✅ MySQL服务就绪${NC}"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ MySQL服务启动超时${NC}"
        exit 1
    fi
    
    # 等待Python应用就绪
    echo -e "${YELLOW}🐍 等待Python应用就绪...${NC}"
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8100/health &>/dev/null; then
            echo -e "${GREEN}✅ Python应用就绪${NC}"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ Python应用启动超时${NC}"
        exit 1
    fi
    
    # 等待Nginx就绪
    echo -e "${YELLOW}🌐 等待Nginx服务就绪...${NC}"
    timeout=30
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost/ &>/dev/null; then
            echo -e "${GREEN}✅ Nginx服务就绪${NC}"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ Nginx服务启动超时${NC}"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    echo -e "${GREEN}"
    echo "🎉 部署完成！"
    echo "=================================="
    echo "📊 服务状态："
    docker-compose ps
    echo ""
    echo "🌐 访问地址："
    echo "  - Nginx (主入口): http://localhost"
    echo "  - Python API: http://localhost:8100"
    echo "  - 卡片接口: http://localhost/card"
    echo "  - 静态文件: http://localhost/static/"
    echo ""
    echo "🗄️  数据库信息："
    echo "  - 主机: localhost:3306"
    echo "  - 数据库: n8n_mobile_cards"
    echo "  - 用户名: root"
    echo "  - 密码: 123456"
    echo ""
    echo "📁 挂载目录："
    echo "  - 代码目录: /home/n8n_qiongbika/code"
    echo "  - Nginx配置: /home/n8n_qiongbika/nginx_config"
    echo ""
    echo "🔧 管理命令："
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart"
    echo "=================================="
    echo -e "${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}🐳 N8N 穷逼卡项目 Docker 部署脚本${NC}"
    echo -e "${BLUE}适用于中国大陆环境${NC}"
    echo ""
    
    check_docker
    cleanup_old_containers
    create_directories
    start_services
    wait_for_services
    show_deployment_info
    
    echo -e "${GREEN}🎊 部署成功完成！${NC}"
}

# 执行主函数
main "$@"