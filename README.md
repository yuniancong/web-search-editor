# Web Search 插件编辑器

一个用于可视化编辑 zsh web-search 插件配置的本地 Web 工具。

## 功能特点

✅ **实时读写本地文件** - 直接修改 `~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh`
✅ **自动备份** - 每次保存前自动创建带时间戳的备份文件
✅ **可视化界面** - 简洁直观的 Web 界面管理配置
✅ **一键操作** - 添加、删除、保存、重载一气呵成
✅ **零依赖** - 仅使用 Python 标准库，无需安装额外包

## 快速开始

### 1. 启动服务（查看配置：vim ~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh）

```bash
cd /Users/web-search-editor
python3 web-search-editor.py
```

启动成功后会显示：

```
🚀 Web Search 插件编辑器启动中...
📁 配置文件: /Users/username/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh
🌐 服务地址: http://localhost:8080
⌨️  按 Ctrl+C 停止服务
```

### 2. 打开浏览器

访问：**http://localhost:8080**

浏览器会自动打开（或手动访问上述地址）

### 3. 使用工具

#### 添加新的搜索引擎

1. 在"快捷码"输入框填写快捷命令（如：`claude`）
2. 在"搜索 URL"输入框填写完整 URL（如：`https://claude.ai/new?q=`）
3. 点击"添加"按钮或按回车键

#### 删除搜索引擎

- 在配置列表中，点击对应项目的"删除"按钮

#### 保存配置

- 点击"保存到文件"按钮
- 系统会自动备份原文件，然后写入新配置
- 成功后会显示备份文件名

#### 重新加载 Zsh

- 点击"重新加载 Zsh"按钮
- 命令 `source ~/.zshrc` 会自动复制到剪贴板
- 在任意终端粘贴并执行即可生效

#### 刷新配置

- 点击"刷新配置"按钮可以重新从文件加载最新配置

## 配置示例

### 添加 Claude AI 搜索

- **快捷码**: `claude`
- **URL**: `https://claude.ai/new?q=`

使用方式：
```bash
claude AI编程助手  # 在 Claude AI 中搜索"AI编程助手"
```

### 添加淘宝搜索

- **快捷码**: `taobao`
- **URL**: `https://s.taobao.com/search?q=`

使用方式：
```bash
taobao 机械键盘  # 在淘宝搜索"机械键盘"
```

### 添加 Perplexity AI

- **快捷码**: `py`
- **URL**: `https://www.perplexity.ai/search?s=o&q=`

使用方式：
```bash
py 量子计算原理  # 在 Perplexity 搜索"量子计算原理"
```

## 文件说明

### 主程序
- **web-search-editor.py** - Python Web 服务器主程序

### 配置文件
- **~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh** - web-search 插件配置文件

### 备份文件
保存配置时会自动创建备份，格式为：
```
web-search.plugin.zsh.backup_20251005_101530
```

## 停止服务

### 方法 1：终端中断
在运行服务的终端按 `Ctrl+C`

### 方法 2：命令行停止
```bash
pkill -f web-search-editor.py
```

## 技术架构

- **后端**: Python 3 + http.server (标准库)
- **前端**: 原生 HTML + CSS + JavaScript
- **通信**: RESTful API (JSON)

## API 接口

### GET /api/config
获取当前配置

**响应示例**:
```json
{
  "success": true,
  "urls": {
    "claude": "https://claude.ai/new?q=",
    "py": "https://www.perplexity.ai/search?s=o&q="
  },
  "aliases": {
    "claude": {
      "engine": "claude",
      "url": "https://claude.ai/new?q="
    }
  }
}
```

### POST /api/config
保存配置到文件

**请求体**:
```json
{
  "urls": {...},
  "aliases": {...}
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "保存成功",
  "backup": "/Users/xxx/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh.backup_20251005_101530"
}
```

### POST /api/reload
获取重载命令

**响应示例**:
```json
{
  "success": true,
  "command": "source ~/.zshrc"
}
```

## 常见问题

### Q: 端口被占用怎么办？
A: 编辑 `web-search-editor.py`，修改 `PORT = 8080` 为其他端口号

### Q: 配置没有生效？
A: 保存后需要执行 `source ~/.zshrc` 重新加载配置

### Q: 如何恢复备份？
A: 找到备份文件，复制内容覆盖原文件：
```bash
cp ~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh.backup_XXXXXX \
   ~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh
```

### Q: 浏览器无法访问？
A: 检查防火墙设置，确保允许本地 8080 端口访问

## 安全说明

- 服务仅绑定到 127.0.0.1（localhost），外网无法访问
- 所有操作均在本地进行，不涉及网络传输
- 每次保存前自动创建备份，可随时恢复

## 许可证

MIT License
