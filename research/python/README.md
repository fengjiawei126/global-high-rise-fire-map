# Global High-Rise Fire–Heatwave

这是全球高层建筑火灾与极端热暴露研究的唯一 Python 代码项目。项目以更新的 2000–2026 年事件数据库为核心事实表，通过 Earth Engine 补充气象、1 km 人口和建成环境变量，并生成论文统计结果、源数据表和 Nature Cities 风格图件。

## 模块

1. `STEP_1.0_数据审计与事件队列.ipynb`：字段标准化、重复与来源审计、核心/扩展队列。
2. `STEP_2.0_GEE外部数据增强.ipynb`：ERA5-Land、GPWv4.11、GHSL、NASA POWER、世界银行与 CTIF 国家消防服务能力背景的自动化提取和匹配。
3. `STEP_3.0_统计建模与稳健性分析.ipynb`：时间分层病例交叉、报告过程、人员后果异质性、消防服务能力、热浪定义、证据窗口和逐洲留一敏感性分析。
4. `STEP_4.0_Nature图件与源数据.ipynb`：全球分布图、ERA5-Land 主分析图、观察过程图、人员后果集中度图、独立产品森林图、匹配天气诊断图、消防能力覆盖图、证据窗口稳健性图及全部逐板源数据。

## 数据边界

- 原始工作簿快照保存在 `data/raw`，只读使用。
- `data/interim/legacy_events_gee_enriched_20260826.csv` 仅用于增量核验，不能替代更新数据库。
- 事件库记录的是“公开资料中被记录的事件”，不是全球完整火灾登记系统。
- 年度记录数量受检索强度、语言、来源与近期报道偏差影响，不能直接解释为真实发生率趋势。
- 外部航空事故、武装冲突、纵火和在建工程均保留在全量队列，并通过事件类型变量与敏感性队列区分。
- “热浪”主分析采用事件日期同地点、同月、同星期的时间分层病例交叉设计；真实 ERA5-Land 主估计为 OR 0.72（95% CI 0.24–2.18；P=0.563），六种定义与独立气象产品的估计均不精确，数据不支持声称热浪提高已记录高层火灾发生几率。
- NASA POWER Release 10 的 MERRA-2/GEOS-IT 日尺度数据只作为独立气象产品敏感性分析；其约 0.5°×0.625°网格和地方太阳时不能替代 ERA5-Land 主暴露。
- 世界银行 GDP、城市化率、用电可及性和国家人口仅用于报告环境、发展背景和严重度敏感性分析，不用作火灾发生率分母。
- CTIF 第30号报告表1.13是各国在2010–2023年间“最近一次报告值”的横截面资源背景，不是共同年份序列，也不代表事故现场实际投入；所有能力模型均为覆盖受限的探索性敏感性分析。

## 服务账号

本地电脑在系统环境变量中设置 `GEE_PROJECT_ID` 和 `GOOGLE_APPLICATION_CREDENTIALS`；服务器可直接使用 Application Default Credentials。JSON 密钥不进入项目、不进入 Notebook、不提交 Git。完整权限和运行说明见 `GEE_SETUP.md`。

## 运行

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name global-fire-heatwave --display-name "Python (Global Fire Heatwave)"
.\.venv\Scripts\jupyter-lab
```

在 Jupyter 中选择 `Python (Global Fire Heatwave)` 内核并按 STEP 顺序运行。STEP 2 默认不调用远程接口；设置 `RUN_POWER=1` 可生成无需密钥的 NASA POWER 独立产品表，设置 `RUN_GEE=1` 可生成 ERA5-Land 主分析表。GEE 基线按五年块缓存，事件和病例交叉记录支持断点续跑；海岸像元无值时使用显式记录的 20 km 空间均值回退。NASA POWER 请求按坐标串行执行并缓存，避免重复请求同一地点。

## 复现原则

每次运行写入源文件 SHA-256、软件版本、数据集 ID、数据获取日期和参数快照。所有统计表与图均从 `data/processed` 和 `outputs/tables` 生成，禁止手工改图中的数字。
