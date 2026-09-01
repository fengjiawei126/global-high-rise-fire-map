# Global High-Rise Fire–Heatwave — Nature Cities Article

本目录是论文项目，与 `D:\PersData\4.coding\python_projects\Global_HighRise_Fire_Heatwave` 一一对应。目标文稿类型为 Nature Cities Article：标题不超过 90 个字符，摘要不超过 150 词，正文不超过 3,500 词，Methods 不超过 3,000 词，主文展示项不超过 8 个；当前 SI 含 12 张补充表和 6 张补充图。

## 文件

- `manuscript.tex`：主文、Methods、声明和图注。
- `SI.tex`：补充方法、队列审计、敏感性与数据字典。
- `references.bib`：已核验 DOI 的工作文献库；最终接收前需将 `.bbl` 内容嵌回主文。
- `claim_evidence_ledger.csv`：主张—证据—边界台账。
- `NOVELTY_AND_FALSIFICATION_AUDIT.md`：与最近邻文献逐项对照的创新性、边界和可证伪性审计。
- `PRESUBMISSION_RISK_AUDIT.md`：投稿前主要风险、允许/禁止措辞与未完成硬门槛。
- `citation_review/`：2015--2026 年 Nature Portfolio/CNS 范围的候选文献检索、出版商页面核验和引文管理导出。
- `figures/`：由 Python 项目导出的矢量/位图图件，禁止手工修改数据值。

## 当前证据状态

事件库审计、全球地图、完整 ERA5-Land 病例交叉分析、NASA POWER 独立天气产品、连续温度与滞后敏感性、观察过程、记录人员后果异质性、证据窗口与逐洲留一敏感性、沿海回退排除以及 CTIF 国家消防服务能力分析均已完成。阈值热浪主分析为 OR 0.72（95% CI 0.24–2.18；P=0.563），六种 ERA5-Land 定义和 NASA POWER 阈值结果均不精确，因此稿件明确报告“不支持正向关联”。连续温度异常在天气调整模型中呈正向条件关联，但在仅温度模型中明显衰减，不能解释为热浪或总温度因果效应。创新性审计确认：最接近的既有工作已建立全球城市温度与建筑火灾频次关系，因此本研究不使用“首次发现全球温度—建筑火灾关系”的措辞；本项目的可检验增量定位为可审计事件库、事件级急性暴露、观察过程建模、人员后果与跨国资源敏感性的一体化证据链。当前主文含四张主图，SI 含六张补充图和十二张补充表。

## 编译

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error SI.tex
```

提交前还需补充真实作者、单位、资助、贡献、代码仓库 DOI 和数据仓库 DOI。
