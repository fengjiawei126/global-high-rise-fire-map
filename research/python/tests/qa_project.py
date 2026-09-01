import ast,json,re,sys # 导入语法、序列化、正则和退出状态模块
from pathlib import Path # 导入跨平台路径工具
import pandas as pd # 导入表格质量检查模块
ROOT=Path(__file__).resolve().parents[1] # 定位当前项目根目录
CHINESE=re.compile(r"[\u4e00-\u9fff]") # 定义中文字符检查模式
def check_lines(lines,label): # 定义逐行格式审计函数
    errors=[] # 初始化格式错误列表
    for number,line in enumerate(lines,1): # 遍历代码行及其一基序号
        if not line.strip(): errors.append(f"{label}:{number}:空代码行") # 标记任何空白代码行
        elif "#" not in line or not CHINESE.search(line.rsplit("#",1)[-1]): errors.append(f"{label}:{number}:缺少中文行尾注释") # 标记缺少中文行尾注释的代码行
    return errors # 返回当前代码块格式错误
def audit_python(): # 定义Python模块语法与格式审计函数
    errors=[] # 初始化Python错误列表
    for path in sorted((ROOT/"src").glob("*.py"))+sorted((ROOT/"tests").glob("*.py")): # 遍历源代码与测试模块
        text=path.read_text(encoding="utf-8") # 读取UTF-8代码文本
        ast.parse(text,filename=str(path)) # 使用抽象语法树验证Python语法
        if text: errors.extend(check_lines(text.splitlines(),str(path.relative_to(ROOT)))) # 对非空模块执行逐行格式审计
    return errors # 返回Python模块审计错误
def audit_notebooks(): # 定义Notebook语法与格式审计函数
    errors=[] # 初始化Notebook错误列表
    for path in sorted((ROOT/"notebooks").glob("*.ipynb")): # 遍历STEP命名Notebook
        notebook=json.loads(path.read_text(encoding="utf-8")) # 读取Notebook JSON结构
        for index,cell in enumerate(notebook.get("cells",[]),1): # 遍历Notebook单元格
            if cell.get("cell_type")!="code": continue # 跳过Markdown等非代码单元格
            source="".join(cell.get("source",[])).rstrip("\n") # 合并代码单元格源文本并忽略文件末尾换行
            ast.parse(source,filename=f"{path.name}:cell{index}") if source else None # 验证非空代码单元格语法
            errors.extend(check_lines(source.splitlines(),f"{path.name}:cell{index}")) if source else None # 审计非空代码单元格逐行格式
    return errors # 返回Notebook审计错误
def audit_data_and_artifacts(): # 定义核心数据与输出制品审计函数
    errors=[] # 初始化数据与制品错误列表
    events_path=ROOT/"data/processed/events_standardised.csv" # 定位标准化事件表
    audit_path=ROOT/"outputs/tables/event_audit.json" # 定位事件审计清单
    if not events_path.is_file(): errors.append("缺少标准化事件表") # 标记标准化事件表缺失
    if not audit_path.is_file(): errors.append("缺少事件审计清单") # 标记事件审计清单缺失
    if events_path.is_file(): # 在标准化事件表存在时执行内容核验
        events=pd.read_csv(events_path,encoding="utf-8-sig") # 读取标准化事件表
        if len(events)!=239: errors.append(f"事件行数异常:{len(events)}") # 核验更新数据库总事件数
        if int(events.get("analysis_core",pd.Series(dtype=bool)).sum())!=191: errors.append("核心队列数量异常") # 核验核心队列事件数
        if pd.to_numeric(events.get("building_height_m_reported"),errors="coerce").max()>1000: errors.append("建筑高度包含面积或其他异常数值") # 防止面积或楼层数字误进入米制高度字段
        area_rows=events["building_height_or_floors"].astype(str).str.contains("10000",na=False) # 定位已知含一万平方米描述的回归测试记录
        if area_rows.any() and events.loc[area_rows,"building_height_m_reported"].notna().any(): errors.append("平方米数值被误识别为建筑高度") # 核验面积字段不会再次污染高度
    if audit_path.is_file(): # 在审计清单存在时核验源文件摘要
        audit=json.loads(audit_path.read_text(encoding="utf-8")) # 读取事件审计清单
        if audit.get("source_sha256")!="386eb556101286e4dce89060d1d60ca105f5f54e97db3d3f297bcc2be6c291e5": errors.append("源工作簿SHA-256异常") # 核验源工作簿不可变摘要
    power_path=ROOT/"data/processed/case_control_weather_nasa_power_v10.csv" # 定位独立气象产品病例对照表
    manifest_path=ROOT/"data/processed/nasa_power_request_manifest.csv" # 定位独立气象产品请求清单
    if power_path.is_file(): # 在独立产品表存在时核验完整性
        power=pd.read_csv(power_path,encoding="utf-8-sig") # 读取NASA POWER病例对照表
        if len(power)!=1004 or power["stratum_id"].nunique()!=228 or int(power["case"].sum())!=228: errors.append("NASA POWER病例对照样本结构异常") # 核验匹配日、分层与病例数量
        if not power["weather_status"].eq("completed").all(): errors.append("NASA POWER存在未完成气象请求") # 防止失败请求静默进入模型
        if power[["tmax_p85_c","tmax_p90_c","tmax_p95_c"]].notna().all(axis=1).sum()!=1004: errors.append("NASA POWER热浪阈值不完整") # 核验全部匹配日具备固定基线阈值
    if manifest_path.is_file() and len(pd.read_csv(manifest_path,encoding="utf-8-sig"))!=159: errors.append("NASA POWER请求清单坐标数量异常") # 核验每个唯一坐标均有来源元数据
    power_window_path=ROOT/"outputs/tables/nasa_power_event_window_sensitivity.csv" # 定位独立产品队列排除与逐洲留一敏感性结果
    if power_window_path.is_file(): # 在独立产品证据窗口结果存在时核验模型家族
        power_windows=pd.read_csv(power_window_path,encoding="utf-8-sig") # 读取十二个队列与地理敏感性模型
        intervals_include_one=(power_windows["ci_low"]<=1)&(power_windows["ci_high"]>=1) # 标记置信区间是否覆盖无效值一
        if len(power_windows)!=12 or not power_windows["status"].eq("completed").all() or not intervals_include_one.all(): errors.append("NASA POWER证据窗口模型数量收敛或区间边界异常") # 核验十二个模型完成且不夸大不精确结果
    capacity_path=ROOT/"data/interim/ctif_fire_service_capacity_2010_2023.csv" # 定位CTIF国家消防服务能力派生表
    capacity_model_path=ROOT/"outputs/tables/ctif_fire_service_capacity_sensitivity.csv" # 定位CTIF消防服务能力敏感性模型表
    enriched_path=ROOT/"data/processed/events_enriched.csv" # 定位已附加外部背景指标的事件表
    if capacity_path.is_file(): # 在CTIF派生表存在时核验完整性
        capacity=pd.read_csv(capacity_path,encoding="utf-8-sig") # 读取CTIF国家消防服务能力派生表
        if len(capacity)!=65 or capacity["ctif_row"].tolist()!=list(range(1,66)) or capacity["iso3"].nunique()!=65: errors.append("CTIF表1.13国家行或ISO3映射异常") # 核验65个连续国家行及唯一国家代码
    if enriched_path.is_file(): # 在外部增强事件表存在时核验CTIF匹配覆盖
        enriched=pd.read_csv(enriched_path,encoding="utf-8-sig") # 读取附加国家能力背景的事件表
        capacity_available=pd.to_numeric(enriched["ctif_career_firefighters_per_100k"],errors="coerce").notna() # 标记职业消防员能力值可用事件
        if int(capacity_available.sum())!=150 or int((capacity_available&enriched["analysis_extended"].astype(bool)).sum())!=141: errors.append("CTIF事件级匹配覆盖异常") # 核验全量与扩展队列消防能力覆盖数量
    if capacity_model_path.is_file(): # 在消防能力敏感性结果存在时核验模型家族
        capacity_models=pd.read_csv(capacity_model_path,encoding="utf-8-sig") # 读取八个能力敏感性模型结果
        intervals_include_one=(capacity_models["ci_low"]<=1)&(capacity_models["ci_high"]>=1) # 标记置信区间是否覆盖无效值一
        if len(capacity_models)!=8 or not intervals_include_one.all(): errors.append("CTIF敏感性模型数量或区间边界异常") # 核验八个预设模型且不夸大不精确结果
    death_model_path=ROOT/"outputs/tables/death_consequence_association_model.csv" # 指定死亡后果探索模型结果
    injury_model_path=ROOT/"outputs/tables/injury_consequence_association_model.csv" # 指定受伤后果探索模型结果
    if death_model_path.is_file() and int(pd.read_csv(death_model_path,encoding="utf-8-sig")["n_observations"].iloc[0])!=177: errors.append("死亡后果探索模型样本量异常") # 核验死亡后果探索模型分析样本
    if injury_model_path.is_file() and int(pd.read_csv(injury_model_path,encoding="utf-8-sig")["n_observations"].iloc[0])!=127: errors.append("受伤后果探索模型样本量异常") # 核验受伤后果探索模型分析样本
    required=[ROOT/f"outputs/figures/{figure}.{suffix}" for figure in ["Figure_1","Figure_2","Figure_3","Figure_4","Figure_S1","Figure_S2","Figure_S3","Figure_S4","Figure_S5","Figure_S6"] for suffix in ["svg","pdf","png"]]+[ROOT/f"outputs/tables/Figure_1{panel}_{name}.csv" for panel,name in [("a","event_map"),("b","annual_records"),("c","heat_exposure"),("d","cohort")]]+[ROOT/f"outputs/tables/{name}.csv" for name in ["Figure_2a_matched_exposure","Figure_2b_primary_model","Figure_2c_heat_definitions","Figure_3a_outcome_observability","Figure_3b_geographic_reporting","Figure_3c_observation_process","Figure_4a_consequence_concentration","Figure_4b_building_scale_profile","Figure_4c_consequence_associations","Figure_S1a_geographic_coverage","Figure_S1b_source_grade","Figure_S1c_missingness","Figure_S2_weather_product_sensitivity","Figure_S3a_temperature_anomaly","Figure_S3b_within_stratum_difference","Figure_S3c_definition_diagnostics","Figure_S4a_capacity_coverage","Figure_S4b_capacity_sensitivity","Figure_S5_event_window_sensitivity","Figure_S6_continuous_temperature_sensitivity"]]+[power_path,manifest_path,power_window_path,capacity_path,capacity_model_path,enriched_path,death_model_path,injury_model_path,ROOT/"outputs/tables/conditional_heat_model.csv",ROOT/"outputs/tables/heat_definition_sensitivity.csv",ROOT/"outputs/tables/continuous_temperature_sensitivity.csv",ROOT/"outputs/tables/era5_event_window_sensitivity.csv",ROOT/"outputs/tables/era5_coastal_exclusion_sensitivity.csv",ROOT/"outputs/tables/casualty_severity_model.csv",ROOT/"outputs/tables/nasa_power_conditional_heat_model.csv",ROOT/"outputs/tables/nasa_power_heat_definition_sensitivity.csv",ROOT/"outputs/tables/nasa_power_continuous_temperature_sensitivity.csv"] # 定义公开仓库保留的十组PDF/PNG/SVG图件、真实主分析、连续温度结果、外部产品、能力背景、后果模型与全部逐板源数据制品
    errors.extend(f"缺少制品:{path.relative_to(ROOT)}" for path in required if not path.is_file()) # 标记任何缺失的主图制品
    return errors # 返回数据与制品审计错误
def audit_credentials(): # 定义凭据泄露审计函数
    errors=[] # 初始化凭据错误列表
    allowed_suffixes={".py",".ipynb",".md",".yaml",".yml",".csv",".txt"} # 定义需要扫描的文本文件类型
    excluded={".venv",".git",".jupyter_clean","__pycache__"} # 定义无需扫描的生成目录
    for path in ROOT.rglob("*"): # 遍历项目文件树
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes or excluded.intersection(path.parts): continue # 跳过非文本文件和生成目录
        text=path.read_text(encoding="utf-8",errors="ignore") # 读取候选文本文件
        pem_marker="-----BEGIN"+" PRIVATE KEY-----" # 动态构造PEM私钥标记以避免审计脚本自匹配
        json_marker=re.compile(chr(34)+"private_"+"key"+chr(34)+r"\s*:") # 动态构造JSON私钥字段模式以避免审计脚本自匹配
        if pem_marker in text or json_marker.search(text): errors.append(f"检测到私钥内容:{path.relative_to(ROOT)}") # 标记任何实际私钥字段或PEM内容
    return errors # 返回凭据泄露审计错误
def main(): # 定义质量审计入口函数
    errors=audit_python()+audit_notebooks()+audit_data_and_artifacts()+audit_credentials() # 汇总代码、数据、制品与凭据错误
    print(json.dumps({"status":"passed" if not errors else "failed","error_count":len(errors),"errors":errors},ensure_ascii=False,indent=2)) # 输出机器可读审计报告
    return 1 if errors else 0 # 以退出状态表示审计结果
if __name__=="__main__": sys.exit(main()) # 运行项目质量审计入口
