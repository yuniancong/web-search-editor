#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import json
import os
import re
import shutil
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import webbrowser
import threading

PORT = 8080
PLUGIN_FILE = os.path.expanduser('~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh')

def read_plugin_file():
    """读取插件文件并解析配置"""
    with open(PLUGIN_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析 URLs
    urls = {}
    url_pattern = r'^\s*(\w+)\s+"([^"]+)"'
    in_urls_section = False

    for line in content.split('\n'):
        if 'urls=(' in line:
            in_urls_section = True
            continue
        if in_urls_section and ')' in line and 'urls=' not in line:
            in_urls_section = False
            break
        if in_urls_section:
            match = re.match(url_pattern, line)
            if match:
                urls[match.group(1)] = match.group(2)

    # 解析 Aliases
    aliases = {}
    alias_pattern = r'^alias\s+(\w+)=\'web_search\s+(\w+)\''

    for line in content.split('\n'):
        match = re.match(alias_pattern, line)
        if match:
            alias_name = match.group(1)
            engine_name = match.group(2)
            if engine_name in urls:
                aliases[alias_name] = {
                    'engine': engine_name,
                    'url': urls[engine_name]
                }

    return urls, aliases

def backup_plugin_file():
    """备份插件文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{PLUGIN_FILE}.backup_{timestamp}"
    shutil.copy2(PLUGIN_FILE, backup_path)
    return backup_path

def write_plugin_file(urls_dict, aliases_dict):
    """写入新的配置到插件文件"""
    # 先备份
    backup_path = backup_plugin_file()

    # 读取原文件
    with open(PLUGIN_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    urls_written = False
    aliases_written = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # 处理 URLs 部分
        if 'urls=(' in line:
            new_lines.append(line)
            i += 1

            # 跳过原有的 URL 定义
            while i < len(lines) and ')' not in lines[i]:
                i += 1

            # 写入新的 URLs
            for key, url in sorted(urls_dict.items()):
                new_lines.append(f"    {key:<16} \"{url}\"\n")
            urls_written = True

            # 添加右括号
            if i < len(lines):
                new_lines.append(lines[i])
                i += 1
            continue

        # 检测到 alias 行且还没写入 aliases
        if line.startswith('alias ') and 'web_search' in line and not aliases_written:
            # 跳过所有原有的 web_search aliases
            while i < len(lines) and (lines[i].startswith('alias ') and 'web_search' in lines[i]):
                i += 1

            # 写入新的 aliases
            for alias_name, info in sorted(aliases_dict.items()):
                new_lines.append(f"alias {alias_name}='web_search {info['engine']}'\n")
            aliases_written = True
            continue

        new_lines.append(line)
        i += 1

    # 写入文件
    with open(PLUGIN_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return backup_path

class WebSearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/config':
            try:
                urls, aliases = read_plugin_file()
                response = {
                    'success': True,
                    'urls': urls,
                    'aliases': aliases
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            try:
                urls_dict = data.get('urls', {})
                aliases_dict = data.get('aliases', {})
                backup_path = write_plugin_file(urls_dict, aliases_dict)

                response = {
                    'success': True,
                    'message': '保存成功',
                    'backup': backup_path
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

        elif self.path == '/api/reload':
            response = {
                'success': True,
                'command': 'source ~/.zshrc'
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # 简化日志输出
        pass

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Search 插件编辑器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f7; padding: 20px;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white;
            border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .status-badge {
            display: inline-block; background: rgba(255,255,255,0.2);
            padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-top: 10px;
        }
        .content { padding: 30px; }
        .add-section { background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 30px; }
        .add-section h2 { font-size: 18px; margin-bottom: 20px; color: #333; }
        .form-group {
            display: grid; grid-template-columns: 1fr 2fr auto;
            gap: 15px; align-items: start;
        }
        .input-wrapper { display: flex; flex-direction: column; }
        .input-wrapper label { font-size: 13px; color: #666; margin-bottom: 6px; font-weight: 500; }
        input[type="text"] {
            padding: 10px 14px; border: 2px solid #e0e0e0; border-radius: 6px;
            font-size: 14px; transition: all 0.3s;
        }
        input[type="text"]:focus {
            outline: none; border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            padding: 10px 24px; border: none; border-radius: 6px;
            font-size: 14px; font-weight: 500; cursor: pointer;
            transition: all 0.3s; align-self: end;
        }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-add { background: #667eea; color: white; }
        .btn-add:hover:not(:disabled) { background: #5568d3; transform: translateY(-1px); }
        .entries-section h2 { font-size: 18px; margin-bottom: 20px; color: #333; }
        .entries-list {
            border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;
            max-height: 500px; overflow-y: auto;
        }
        .entry-item {
            display: grid; grid-template-columns: 150px 1fr auto; gap: 15px;
            padding: 15px 20px; border-bottom: 1px solid #e0e0e0;
            align-items: center; transition: background 0.2s;
        }
        .entry-item:last-child { border-bottom: none; }
        .entry-item:hover { background: #f8f9fa; }
        .entry-alias {
            font-family: 'Monaco', 'Menlo', monospace; font-size: 14px;
            font-weight: 600; color: #667eea;
        }
        .entry-url {
            font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; color: #666;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .btn-delete { background: #ff6b6b; color: white; padding: 6px 16px; font-size: 13px; }
        .btn-delete:hover:not(:disabled) { background: #ff5252; }
        .actions {
            margin-top: 30px; padding-top: 30px; border-top: 2px solid #e0e0e0;
            display: flex; gap: 15px;
        }
        .btn-save, .btn-reload, .btn-refresh { flex: 1; padding: 14px; font-size: 15px; }
        .btn-save { background: #48bb78; color: white; }
        .btn-save:hover:not(:disabled) { background: #38a169; }
        .btn-reload { background: #f6ad55; color: white; }
        .btn-reload:hover:not(:disabled) { background: #ed8936; }
        .btn-refresh { background: #667eea; color: white; }
        .btn-refresh:hover:not(:disabled) { background: #5568d3; }
        .toast {
            position: fixed; bottom: 30px; right: 30px; background: #333;
            color: white; padding: 15px 25px; border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: none;
            z-index: 2000; animation: slideIn 0.3s ease; max-width: 400px;
        }
        .toast.active { display: block; }
        .toast.success { background: #48bb78; }
        .toast.error { background: #ff6b6b; }
        .toast.info { background: #4299e1; }
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .file-path {
            background: #f8f9fa; padding: 10px 15px; border-radius: 6px;
            font-family: 'Monaco', 'Menlo', monospace; font-size: 12px;
            color: #666; margin-bottom: 20px; border-left: 3px solid #667eea;
        }
        .loading {
            display: inline-block; width: 14px; height: 14px;
            border: 2px solid rgba(255,255,255,0.3); border-radius: 50%;
            border-top-color: white; animation: spin 1s linear infinite; margin-left: 8px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .empty-state { text-align: center; padding: 60px 20px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web Search 插件编辑器</h1>
            <p>实时读写本地配置文件</p>
            <span class="status-badge">● 已连接</span>
        </div>
        <div class="content">
            <div class="file-path">📁 文件: ~/.oh-my-zsh/plugins/web-search/web-search.plugin.zsh</div>
            <div class="add-section">
                <h2>添加新的搜索引擎</h2>
                <div class="form-group">
                    <div class="input-wrapper">
                        <label>快捷码</label>
                        <input type="text" id="aliasInput" placeholder="例如: claude" />
                    </div>
                    <div class="input-wrapper">
                        <label>搜索 URL</label>
                        <input type="text" id="urlInput" placeholder="例如: https://claude.ai/new?q=" />
                    </div>
                    <button class="btn-add" onclick="addEntry()">添加</button>
                </div>
            </div>
            <div class="entries-section">
                <h2>当前配置 (<span id="entryCount">0</span> 项)</h2>
                <div class="entries-list" id="entriesList"></div>
            </div>
            <div class="actions">
                <button class="btn-refresh" onclick="loadConfig()">刷新配置</button>
                <button class="btn-save" onclick="saveConfig()">保存到文件</button>
                <button class="btn-reload" onclick="reloadZsh()">重新加载 Zsh</button>
            </div>
        </div>
    </div>
    <div class="toast" id="toast"></div>
    <script>
        let urls = {}, aliases = {};
        window.addEventListener('DOMContentLoaded', loadConfig);

        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                if (data.success) {
                    urls = data.urls;
                    aliases = data.aliases;
                    renderEntries();
                    showToast('配置加载成功', 'success');
                } else {
                    showToast('加载失败: ' + data.error, 'error');
                }
            } catch (error) {
                showToast('连接服务器失败', 'error');
            }
        }

        function addEntry() {
            const aliasInput = document.getElementById('aliasInput');
            const urlInput = document.getElementById('urlInput');
            const aliasName = aliasInput.value.trim();
            const url = urlInput.value.trim();

            if (!aliasName || !url) {
                showToast('请填写快捷码和 URL', 'error');
                return;
            }
            if (aliases[aliasName]) {
                showToast('该快捷码已存在', 'error');
                return;
            }

            urls[aliasName] = url;
            aliases[aliasName] = { engine: aliasName, url: url };
            renderEntries();
            aliasInput.value = '';
            urlInput.value = '';
            showToast('添加成功（未保存）', 'info');
        }

        function deleteEntry(aliasName) {
            if (confirm(`确定要删除 "${aliasName}" 吗?`)) {
                const engine = aliases[aliasName].engine;
                delete aliases[aliasName];
                const stillUsed = Object.values(aliases).some(a => a.engine === engine);
                if (!stillUsed) delete urls[engine];
                renderEntries();
                showToast('删除成功（未保存）', 'info');
            }
        }

        function renderEntries() {
            const list = document.getElementById('entriesList');
            const count = document.getElementById('entryCount');
            const entries = Object.entries(aliases);
            count.textContent = entries.length;

            if (entries.length === 0) {
                list.innerHTML = '<div class="empty-state"><p>暂无配置项</p></div>';
                return;
            }

            list.innerHTML = entries.map(([aliasName, info]) => `
                <div class="entry-item">
                    <div class="entry-alias">${aliasName}</div>
                    <div class="entry-url">${info.url}</div>
                    <button class="btn-delete" onclick="deleteEntry('${aliasName}')">删除</button>
                </div>
            `).join('');
        }

        async function saveConfig() {
            const saveBtn = event.target;
            saveBtn.disabled = true;
            saveBtn.innerHTML = '保存中<span class="loading"></span>';

            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls, aliases })
                });
                const data = await response.json();

                if (data.success) {
                    showToast('保存成功！备份: ' + data.backup.split('/').pop(), 'success');
                } else {
                    showToast('保存失败: ' + data.error, 'error');
                }
            } catch (error) {
                showToast('保存失败: ' + error.message, 'error');
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '保存到文件';
            }
        }

        async function reloadZsh() {
            try {
                const response = await fetch('/api/reload', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    await navigator.clipboard.writeText(data.command);
                    showToast('命令已复制: ' + data.command, 'info');
                }
            } catch (error) {
                showToast('操作失败', 'error');
            }
        }

        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast active ' + type;
            setTimeout(() => toast.classList.remove('active'), 4000);
        }

        document.getElementById('aliasInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') document.getElementById('urlInput').focus();
        });
        document.getElementById('urlInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addEntry();
        });
    </script>
</body>
</html>'''

def open_browser():
    """延迟打开浏览器"""
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    print("🚀 Web Search 插件编辑器启动中...")
    print(f"📁 配置文件: {PLUGIN_FILE}")
    print(f"🌐 服务地址: http://localhost:{PORT}")
    print("⌨️  按 Ctrl+C 停止服务\n")

    # 在后台线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("127.0.0.1", PORT), WebSearchHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 服务已停止")
