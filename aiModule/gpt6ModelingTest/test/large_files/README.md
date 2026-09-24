# 大文件还原

本目录无损保存三个大文件，每块最多 32 MiB。GitHub 公开 fork 拒绝了新的 Git LFS 对象，因此使用普通 Git 文件块。

克隆仓库后，在本目录运行（需要 Python 3.9 或更新版本）：

```powershell
python restore.py
```

脚本将模型、FreeCAD 备份及日志还原到原来的 `test` 路径。还原前后均检查 SHA-256；已有文件相同则跳过，不同则停止，避免覆盖本地修改。还原后即可照常打开 FreeCAD 文档。

原文件在当前工作区保留，但由 `.gitignore` 排除。若以后修改这三个文件，需要重新生成对应文件块及 `manifest.json` 后再提交。
