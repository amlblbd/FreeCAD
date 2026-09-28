# 阶段 4 可复现基线

本次结果见 [当前基线报告](当前基线报告.md)。

在仓库根目录运行：

```powershell
python aiModule/gpt6ModelingTest/test/baseline/run.py
```

首次克隆如果缺少 `B_pillar_stage4_working.FCStd`，先运行 `python aiModule/gpt6ModelingTest/test/large_files/restore.py`，按清单校验并还原分块文件。本次工作区已存在该文件，检查器会核对它是否匹配归档哈希，不会自行替换它。

入口仅使用 Python 标准库；几何检查由本仓库 `build/debug/bin/FreeCADCmd.exe` 执行。自动为子进程加入 `.pixi/envs/default` 和 `Library/bin` 依赖路径，不修改系统环境。可用 `--freecad <路径>` 指定其他构建，用 `--timeout 600` 调整每项检查的秒数上限。其他构建的运行依赖需自行准备。

每次运行建立独立的 `runs/<UTC时间>/`，复制工作文档、驱动模块、当前试验曲面/实体、截面数据和历史报告。检查仅使用这些副本，不保存原文档、不覆盖旧报告。原始 STEP 不参与本轮重建：使用 FCStd 中已嵌入的参考几何；文档中遗留的 SourceFile 路径仅作为元数据报告。

`manifest.json` 记录 Git HEAD、输入 SHA-256、检查脚本副本、FreeCAD 可执行文件哈希、各项执行结果、耗时和输入文件未变化核验。各任务报告另含 FreeCAD、OCCT 和 Python 版本。不同内核构建可能得到不同结果，比较时应同时核对输入和环境。

检查项目：

- `document`：加载保存文档，记录主体形状、依赖、耳板表达式和驱动模块恢复情况；与独立 paired 实体比较。导出的 BREP 字节相同可用于确认一致性，字节不同本身不是几何不等价的证明，需结合面数、体积等数据。
- `body`：保存文档主体的基本检查和 `check(True)`；不主动重算文档。
- `paired`：独立 `paired_solid.brep` 的基本检查和增强检查，不能替代保存文档检查。
- `ears`：在文档副本中测试 2.0、2.5、3.0 mm，再恢复 2.5 mm；检查四块独立耳板。不是融合验收，也不证明连续参数区间有效。
- `distance`：按历史方法复算 25×31 个 UV 单元中心到当前内曲面的最近距离；保留全部采样点。不是法向壁厚，也不是保存文档主体壁厚的证明。
- `zone_*`：使用当前内外曲面重新构造并封闭诊断分区，沿用历史边配对方式。它们不是对保存文档的布尔切片；封口也可能引入问题，不能直接把失败归因于原表面。
- `surface_body`：用同一方法连接当前内外曲面的全部区间，检查完整重建体，并与独立 paired 实体比较。

可用 `--tasks surface_body` 等选项仅执行指定检查；这类报告的 `full_suite_requested` 为 false，不能视为全套验收。每次仍保留完整输入清单。

每项检查使用独立 FreeCAD 进程和独立配置文件。超时会终止该检查并继续后续项目，标记 `timeout`，绝不计作通过。`execution_complete` 表示所有检查执行完毕，不代表几何合格；需查看各项 `bop`、`valid` 和耳板 `all_passed`。运行器退出码 0 同样只表示执行完成且源文件未变。

`runs/` 包含较大的输入副本、日志和配置，不进入 Git。正式基线摘要和小型结果保存在同级 `results/`。原阶段 4 工作版仍是冻结试算体，本轮不修改几何、不融合、不建立新的参数特征。
