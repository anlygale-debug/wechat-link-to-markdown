# Windows 安装说明

## 一次性安装

1. 安装 Node.js 20+ 和 Python 3.10+。
2. 解压 Windows 安装包。
3. 在解压目录打开 PowerShell，执行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
   ```

4. 在 Chrome 安装并启用 OpenCLI Browser Bridge：

   <https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk>

5. 保持 Chrome 打开，执行：

   ```powershell
   opencli doctor
   ```

看到 Browser Bridge 已连接即可。如果 Codex 没发现新 Skill，重启一次 Codex。

## 日常使用

在 Codex 中直接发送公众号链接，并说：

> 把这篇公众号文章保存为原文 Markdown。

默认会保存到当前工作区的 `公众号原文/文章标题/`，其中包含 Markdown 文件和本地图片。

