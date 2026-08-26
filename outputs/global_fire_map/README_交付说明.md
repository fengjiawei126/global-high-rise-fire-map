# 全球高层建筑火灾地图项目交付包

## 目录

- `data/`：原始事件工作簿、标准化 CSV 和 GEE 增强 CSV。
- `code/`：Earth Engine Python API Notebook、原始 GPW 2020 Earth Engine JavaScript 和 Python 依赖清单。
- `figures/`：PNG、SVG、PDF、TIFF 地图以及全球人口栅格预览。
- `references/`：项目参考资料和热浪评分方法文献的 EndNote 文件。

## 快速复现现有地图

1. 安装 Python 3.11。
2. 进入 `code/` 后运行 `pip install -r requirements.txt`。
3. 在 Jupyter 中打开 `global_fire_map_gee.ipynb`。
4. 将 `data/global_fire_events_2000_2026.csv`、`data/global_fire_events_2000_2026_gee_enriched.csv` 和 `figures/gpw2020_population_count_global.png` 复制到 Notebook 当前目录，或修改 Notebook 中的对应路径。
5. 设置 `RUN_GEE=0` 和 `USE_EXISTING_ENRICHED=1`，即可使用包内增强数据重绘。

## 重新运行 Google Earth Engine

运行前设置以下环境变量：

```powershell
$env:GEE_PROJECT_ID='your-google-cloud-project-id'
$env:GEE_SERVICE_ACCOUNT='your-service-account@your-project.iam.gserviceaccount.com'
$env:GOOGLE_APPLICATION_CREDENTIALS='D:\secure\service-account-key.json'
$env:RUN_GEE='1'
```

服务账号 JSON 私钥未包含在交付包中。请将密钥保存在独立安全目录，不要提交到 Git 或公开分享。

## 热浪评分

评分使用火灾发生当日及此前六日的 ERA5-Land 日最高温。阈值为当地 1991–2020 年同月最高温第 90 百分位与 30°C 中的较高值；七天累计超阈值温度乘以 10，并限制在 0–100。该指标描述时空关联，不代表火灾因果关系。

## 数据边界

部分坐标为城市代表点而非精确火场。地图展示已记录事件的空间分布，不能直接解释为各地区真实火灾发生率。
