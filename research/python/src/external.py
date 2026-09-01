import hashlib,json,subprocess,time # 导入哈希、元数据序列化、外部文本提取与接口限速模块
from pathlib import Path # 导入跨平台路径工具
import country_converter as coco # 导入国家名称与ISO代码转换工具
import numpy as np # 导入数值计算模块
import pandas as pd # 导入表格处理模块
import requests # 导入官方接口请求模块
WORLD_BANK_INDICATORS={"gdp_per_capita_ppp_constant_2021":"NY.GDP.PCAP.PP.KD","urban_population_percent":"SP.URB.TOTL.IN.ZS","electricity_access_percent":"EG.ELC.ACCS.ZS","national_population":"SP.POP.TOTL"} # 定义事件年份国家背景指标
NASA_POWER_URL="https://power.larc.nasa.gov/api/temporal/daily/point" # 定义NASA POWER日尺度单点官方接口
NASA_POWER_PARAMETERS={"T2M_MAX":"tmax_c","T2MDEW":"dewpoint_c","PRECTOTCORR":"precipitation_mm","WS10M":"wind_speed_ms"} # 定义POWER参数及分析字段映射
CTIF_REPORT_URL="https://ctif.org/sites/default/files/2025-08/CTIF_Report30.pdf" # 定义CTIF世界火灾统计第30号报告官方地址
ISO3_OVERRIDES={"Hong Kong SAR, China":"HKG","Taiwan, China":"TWN","Taiwan":"TWN","Palestine":"PSE","State of Palestine":"PSE","South Korea":"KOR","Korea (South)":"KOR","North Korea":"PRK","Russia":"RUS","Iran":"IRN","Syria":"SYR","Venezuela":"VEN","Bolivia":"BOL","Türkiye":"TUR","Turkey":"TUR","United States":"USA","USA":"USA","United Kingdom":"GBR","Great Britain":"GBR","United Arab Emirates":"ARE","Laos":"LAO","Luxemburg":"LUX","Moldova":"MDA","Brunei":"BRN"} # 定义双语事件库与CTIF表中的常见国家名称兼容映射
DATA_REGISTRY=[{"dataset":"Updated documented high-rise fire events","provider":"Author-compiled multisource database","spatial_temporal_support":"Event point and date, 2000-2026","role":"Outcome and reported severity","identifier":"SHA-256 recorded at runtime","license_or_terms":"Source-specific; redistribution requires source review"},{"dataset":"ERA5-Land Daily Aggregated","provider":"Copernicus Climate Change Service via Google Earth Engine","spatial_temporal_support":"Daily, about 11.1 km, 1950-present","role":"Primary Tmax, dewpoint, precipitation and wind exposure","identifier":"ECMWF/ERA5_LAND/DAILY_AGGR; doi:10.24381/cds.68d2bb30","license_or_terms":"Copernicus acknowledgement required"},{"dataset":"NASA POWER daily meteorology","provider":"NASA Langley Research Center POWER project","spatial_temporal_support":"Daily local solar time, 0.5 by 0.625 degree, 1981 to near-real-time","role":"Independent MERRA-2/GEOS-IT weather-product sensitivity","identifier":"POWER Daily API; service version and access date captured at runtime","license_or_terms":"NASA POWER acknowledgement, service version and access date required"},{"dataset":"GPWv4.11 Population Count and Density","provider":"CIESIN via Google Earth Engine","spatial_temporal_support":"2020 epoch, 30 arc-second, about 1 km","role":"Population count per native cell and density","identifier":"CIESIN/GPWv411; doi:10.7927/H4JW8BX5","license_or_terms":"CC BY 4.0"},{"dataset":"GHSL P2023A built environment","provider":"European Commission Joint Research Centre via Google Earth Engine","spatial_temporal_support":"Built surface and volume 2020, height 2018, 100 m; urbanisation 2020, 1 km","role":"Local built exposure, verticality and settlement class","identifier":"JRC/GHSL/P2023A","license_or_terms":"European Commission reuse notice and dataset citations"},{"dataset":"World Development Indicators","provider":"World Bank","spatial_temporal_support":"Country-year, 2000-2026 where available","role":"GDP, urbanisation, electricity access and national population context","identifier":"World Bank Indicators API v2","license_or_terms":"CC BY 4.0"},{"dataset":"World Fire Statistics Report No. 30, Table 1.13","provider":"CTIF Center for Fire Statistics","spatial_temporal_support":"Most recent national fire-service statistics reported during 2010-2023","role":"Cross-sectional fire-service capacity context","identifier":CTIF_REPORT_URL,"license_or_terms":"CTIF copyright; derived-table redistribution requires provider-terms review"}] # 定义可审计外部数据源登记表
def _write_csv_retry(frame,path,retries=20,delay=0.5): # 定义适配Windows瞬时文件锁的CSV写入函数
    for attempt in range(1,retries+1): # 按限制次数尝试写入目标表
        try: frame.to_csv(path,index=False,encoding="utf-8-sig"); return # 成功写入后立即返回
        except PermissionError: # 捕获索引、同步或预览程序造成的瞬时占用
            if attempt==retries: raise # 重试耗尽后保留原始权限异常
            time.sleep(delay*attempt) # 递增等待以允许外部文件句柄释放
def write_data_registry(output_path): # 定义数据源登记表输出函数
    frame=pd.DataFrame(DATA_REGISTRY) # 将数据源字典转换为表格
    Path(output_path).parent.mkdir(parents=True,exist_ok=True) # 确保登记表输出目录存在
    frame.to_csv(output_path,index=False,encoding="utf-8-sig") # 保存可直接纳入补充材料的UTF-8表格
    return frame # 返回数据源登记表
def fetch_world_bank_indicator(indicator,start_year=2000,end_year=2026,timeout=60): # 定义世界银行指标下载函数
    url=f"https://api.worldbank.org/v2/country/all/indicator/{indicator}" # 构造世界银行官方接口地址
    params={"format":"json","date":f"{start_year}:{end_year}","per_page":20000,"source":2} # 限定世界发展指标和研究年份
    response=requests.get(url,params=params,timeout=timeout) # 请求官方JSON数据
    response.raise_for_status() # 在接口错误时立即停止并保留状态信息
    payload=response.json() # 解析接口返回内容
    records=payload[1] if isinstance(payload,list) and len(payload)>1 else [] # 提取指标观测列表
    rows=[{"iso3":record.get("countryiso3code"),"event_year":pd.to_numeric(record.get("date"),errors="coerce"),"value":pd.to_numeric(record.get("value"),errors="coerce")} for record in records] # 规范化国家代码、年份与数值
    frame=pd.DataFrame(rows).dropna(subset=["iso3","event_year"]) # 移除缺少国家代码或年份的接口记录
    frame=frame.loc[frame["iso3"].str.len().eq(3)&~frame["iso3"].isin(["AFE","AFW","ARB","CSS","CEB","EAR","EAS","EAP","TEA","EMU","ECS","ECA","TEC","EUU","FCS","HPC","HIC","IBD","IBT","IDB","IDX","IDA","LTE","LCN","LAC","TLA","LDC","LMY","LIC","LMC","MEA","MNA","TMN","MIC","NAC","INX","OED","OSS","PSS","PST","PRE","SST","SAS","TSA","SSF","SSA","TSS","UMC","WLD"])] # 排除世界银行聚合区域
    frame["event_year"]=frame["event_year"].astype(int) # 将年份统一为整数
    return frame.drop_duplicates(["iso3","event_year"],keep="first") # 返回唯一国家年份指标表
def download_world_bank_context(output_path,start_year=2000,end_year=2026): # 定义国家背景指标批量下载流程
    merged=None # 初始化国家年份宽表
    for name,indicator in WORLD_BANK_INDICATORS.items(): # 遍历预设世界银行指标
        current=fetch_world_bank_indicator(indicator,start_year,end_year).rename(columns={"value":name}) # 下载并重命名当前指标
        merged=current if merged is None else merged.merge(current,on=["iso3","event_year"],how="outer",validate="one_to_one") # 按国家年份合并全部指标
    merged=merged.sort_values(["iso3","event_year"]).reset_index(drop=True) # 生成稳定国家年份顺序
    Path(output_path).parent.mkdir(parents=True,exist_ok=True) # 确保国家背景数据目录存在
    merged.to_csv(output_path,index=False,encoding="utf-8-sig") # 保存世界银行国家年份数据
    return merged # 返回国家年份背景表
def country_to_iso3(value): # 定义双语国家名称到ISO3代码转换函数
    name=str(value).split("/")[-1].strip() # 优先提取斜杠后的英文国家名称
    if name in ISO3_OVERRIDES: return ISO3_OVERRIDES[name] # 优先使用人工核验的名称兼容映射
    converted=coco.convert(names=name,to="ISO3",not_found="") # 对单个英文名称执行静默标准转换
    return converted if isinstance(converted,str) and len(converted)==3 else np.nan # 仅接受合法三字符ISO代码
def _parse_ctif_integer(value): # 定义CTIF固定宽度数字解析函数
    compact=str(value).strip().replace(" ","") # 移除千位分组空格和字段边缘空白
    return np.nan if compact in ["","-"] else int(compact) # 将连字符保留为缺失并解析其余整数
def extract_ctif_fire_service_capacity(pdf_path,output_path,page_number=49): # 定义CTIF第30号报告国家消防服务能力表提取流程
    pdf_path=Path(pdf_path) # 标准化本地CTIF报告路径
    if not pdf_path.is_file(): raise FileNotFoundError(f"未找到CTIF报告：{pdf_path}") # 在报告缺失时立即停止并给出明确路径
    command=["pdftotext","-f",str(page_number),"-l",str(page_number),"-layout",str(pdf_path),"-"] # 构造保持固定表格布局的文本提取命令
    completed=subprocess.run(command,capture_output=True,check=True) # 调用Poppler读取指定表格页并捕获标准输出
    text=completed.stdout.decode("utf-8",errors="replace") # 将报告页文本按UTF-8容错解码
    rows=[] # 初始化65个国家的消防服务记录
    slices=[(26,37),(37,50),(50,63),(63,76),(76,89),(89,107),(107,119),(119,131)] # 固定人口、站点、车辆、云梯和消防员列边界
    columns=["population_thousands","fire_stations","fire_engines","ladders","career_firefighters","part_time_firefighters","volunteer_firefighters","total_firefighters"] # 定义CTIF表格数值字段
    for line in text.splitlines(): # 遍历保持布局的报告页文本行
        number=str(line[0:2]).strip() if len(line)>=2 else "" # 读取表格左侧国家序号
        if not number.isdigit(): continue # 跳过多语标题、表头与合计行
        country=str(line[2:26]).strip() # 读取固定宽度国家名称字段
        values={column:_parse_ctif_integer(line[start:end] if len(line)>start else "") for column,(start,end) in zip(columns,slices)} # 按固定边界解析八个数值字段
        rows.append({"ctif_row":int(number),"country_ctif":country,"iso3":country_to_iso3(country),**values}) # 保存国家名称、ISO3和消防服务能力原值
    frame=pd.DataFrame(rows).sort_values("ctif_row").reset_index(drop=True) # 生成稳定的国家消防服务能力表
    if len(frame)!=65 or frame["ctif_row"].tolist()!=list(range(1,66)): raise ValueError("CTIF表1.13未完整解析为连续65行") # 以行数和序号双重核验表格完整性
    frame["fire_stations_per_100k"]=frame["fire_stations"]/frame["population_thousands"]*100 # 计算每十万人消防站数量
    frame["fire_engines_per_100k"]=frame["fire_engines"]/frame["population_thousands"]*100 # 计算每十万人消防车数量
    frame["ladders_per_100k"]=frame["ladders"]/frame["population_thousands"]*100 # 计算每十万人云梯车辆数量
    frame["career_firefighters_per_100k"]=frame["career_firefighters"]/frame["population_thousands"]*100 # 计算每十万人职业消防员数量
    frame["total_firefighters_per_100k"]=frame["total_firefighters"]/frame["population_thousands"]*100 # 计算每十万人全部消防员数量
    frame["volunteer_share_percent"]=frame["volunteer_firefighters"]/frame["total_firefighters"]*100 # 计算志愿消防员占全部消防员比例
    frame["reference_period"]="most recent national data reported during 2010-2023" # 明确各国统计并非同一年度
    frame["source_report"]="CTIF World Fire Statistics Report No. 30 (2025), Table 1.13" # 写入报告和表格标识
    frame["source_page_pdf"]=page_number # 写入PDF物理页码便于人工复核
    frame["source_url"]=CTIF_REPORT_URL # 写入官方报告地址
    frame["source_file_sha256"]=hashlib.sha256(pdf_path.read_bytes()).hexdigest() # 计算本地报告哈希锁定输入版本
    output_path=Path(output_path) # 标准化派生能力表输出路径
    output_path.parent.mkdir(parents=True,exist_ok=True) # 确保派生能力表目录存在
    _write_csv_retry(frame,output_path) # 保存UTF-8派生消防服务能力表
    return frame # 返回经完整性核验的CTIF国家能力表
def attach_country_context(events,context,max_lag_years=3): # 定义事件与国家年份背景的保守匹配函数
    result=events.copy() # 复制事件表以避免修改原对象
    result["iso3"]=result["country"].map(country_to_iso3) # 将双语国家名称逐条转换为ISO3代码
    context=context.copy().sort_values(["iso3","event_year"]) # 标准化国家背景表顺序
    value_columns=[column for column in context.columns if column not in ["iso3","event_year"]] # 识别需要匹配的背景指标
    rows=[] # 初始化逐事件背景匹配记录
    for event in result[["event_id","iso3","event_year"]].itertuples(index=False): # 遍历事件国家和年份
        candidates=context.loc[context["iso3"].eq(event.iso3)&context["event_year"].le(event.event_year)].copy() if pd.notna(event.event_year) else context.iloc[0:0].copy() # 仅允许使用事件当年或之前的背景数据
        candidate=candidates.iloc[-1] if len(candidates) else None # 选择最近可用历史年份
        lag=int(event.event_year-candidate["event_year"]) if candidate is not None else np.nan # 计算背景指标年份滞后
        values={column:candidate[column] if candidate is not None and lag<=max_lag_years else np.nan for column in value_columns} # 超过最大滞后时保持缺失
        rows.append({"event_id":event.event_id,"context_year":int(candidate["event_year"]) if candidate is not None and lag<=max_lag_years else np.nan,"context_year_lag":lag if candidate is not None and lag<=max_lag_years else np.nan,**values}) # 保存事件背景匹配结果
    return result.merge(pd.DataFrame(rows),on="event_id",how="left",validate="one_to_one") # 返回附加国家背景指标的事件表
def attach_fire_service_capacity(events,capacity): # 定义事件与CTIF国家消防服务能力背景匹配函数
    fields=["iso3","population_thousands","fire_stations_per_100k","fire_engines_per_100k","ladders_per_100k","career_firefighters_per_100k","total_firefighters_per_100k","volunteer_share_percent","reference_period","source_page_pdf","source_file_sha256"] # 选择可解释的国家能力与来源字段
    context=capacity[fields].dropna(subset=["iso3"]).drop_duplicates("iso3").copy() # 保留ISO3唯一的CTIF国家能力记录
    context=context.rename(columns={column:f"ctif_{column}" for column in fields if column!="iso3"}) # 为全部CTIF字段增加来源前缀防止名称冲突
    return events.merge(context,on="iso3",how="left",validate="many_to_one") # 按事件ISO3附加静态消防服务能力背景
def _power_cache_stem(latitude,longitude): # 定义POWER地点缓存文件名函数
    key=f"{float(latitude):.5f}|{float(longitude):.5f}" # 构造稳定的五位坐标缓存键
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16] # 使用短哈希避免负号与小数点文件名歧义
def fetch_nasa_power_daily(latitude,longitude,start_date,end_date,timeout=120,retries=3): # 定义NASA POWER单地点日序列下载函数
    params={"parameters":",".join(NASA_POWER_PARAMETERS),"community":"SB","longitude":float(longitude),"latitude":float(latitude),"start":pd.Timestamp(start_date).strftime("%Y%m%d"),"end":pd.Timestamp(end_date).strftime("%Y%m%d"),"format":"JSON"} # 构造官方日尺度接口参数
    for attempt in range(1,retries+1): # 按限制次数重试当前地点
        try: # 尝试请求并解析当前地点
            response=requests.get(NASA_POWER_URL,params=params,timeout=timeout) # 串行请求NASA POWER官方接口
            response.raise_for_status() # 对接口错误或限流状态立即抛出异常
            payload=response.json() # 解析JSON响应
            values=payload.get("properties",{}).get("parameter",{}) # 读取各气象参数的日期字典
            frame=pd.DataFrame({target:pd.Series(values.get(source,{}),dtype=float) for source,target in NASA_POWER_PARAMETERS.items()}) # 将气象参数整理为日期索引表
            frame.index=pd.to_datetime(frame.index,format="%Y%m%d",errors="coerce") # 将紧凑日期键转换为时间索引
            fill=float(payload.get("header",{}).get("fill_value",-999.0)) # 读取接口声明的缺失值编码
            frame=frame.replace(fill,np.nan).sort_index().rename_axis("date").reset_index() # 将缺失码替换为空值并恢复日期列
            metadata={"latitude":float(latitude),"longitude":float(longitude),"api_version":payload.get("header",{}).get("api",{}).get("version"),"api_name":payload.get("header",{}).get("api",{}).get("name"),"sources":";".join(payload.get("header",{}).get("sources",[])),"time_standard":payload.get("header",{}).get("time_standard"),"fill_value":fill,"request_start":params["start"],"request_end":params["end"],"accessed_utc":pd.Timestamp.now(tz="UTC").isoformat(),"request_url":response.url} # 保存可复核接口元数据
            return frame,metadata # 返回日序列和来源元数据
        except Exception: # 捕获网络、限流或解析错误
            if attempt==retries: raise # 重试耗尽后保留原始异常
            time.sleep(attempt*5) # 使用递增等待避免连续冲击接口
def _power_heat_properties(series,date): # 定义POWER日序列的热浪与气象属性函数
    current=pd.Timestamp(date).normalize() # 标准化病例或对照日期
    baseline=series.loc[(series.index.year>=1991)&(series.index.year<=2020)&(series.index.month==current.month),"tmax_c"].dropna() # 提取1991至2020同月最高温基线
    thresholds={level:baseline.quantile(level/100) if len(baseline)>=500 else np.nan for level in [85,90,95]} # 在基线足够时计算P85、P90和P95阈值
    lags=[pd.to_numeric(series["tmax_c"].get(current-pd.Timedelta(days=lag)),errors="coerce") for lag in [0,1,2,3]] # 提取当前日及前三日最高温
    weather={column:pd.to_numeric(series[column].get(current),errors="coerce") for column in ["tmax_c","dewpoint_c","precipitation_mm","wind_speed_ms"]} # 提取当前日热湿雨风指标
    threshold85=max(thresholds[85],30.0) if np.isfinite(thresholds[85]) else np.nan # 构造P85与30摄氏度复合阈值
    threshold90=max(thresholds[90],30.0) if np.isfinite(thresholds[90]) else np.nan # 构造P90与30摄氏度主阈值
    threshold95=max(thresholds[95],30.0) if np.isfinite(thresholds[95]) else np.nan # 构造P95与30摄氏度复合阈值
    complete=all(np.isfinite(value) for value in lags) and all(np.isfinite(value) for value in thresholds.values()) # 检查热浪定义所需序列完整性
    flags={"hw_p85_3d":int(all(value>threshold85 for value in lags[:3])) if complete else np.nan,"hw_p90_2d":int(all(value>threshold90 for value in lags[:2])) if complete else np.nan,"hw_p90_3d":int(all(value>threshold90 for value in lags[:3])) if complete else np.nan,"hw_p90_4d":int(all(value>threshold90 for value in lags[:4])) if complete else np.nan,"hw_p95_3d":int(all(value>threshold95 for value in lags[:3])) if complete else np.nan,"hw_p90_3d_no_floor":int(all(value>thresholds[90] for value in lags[:3])) if complete else np.nan} # 计算全部预设热浪定义
    return {**weather,"tmax_lag1_c":lags[1],"tmax_lag2_c":lags[2],"tmax_lag3_c":lags[3],"tmax_p85_c":thresholds[85],"tmax_p90_c":thresholds[90],"tmax_p95_c":thresholds[95],"tmax_anomaly_c":weather["tmax_c"]-thresholds[90] if np.isfinite(weather["tmax_c"]) and np.isfinite(thresholds[90]) else np.nan,"heatwave_indicator":flags["hw_p90_3d"],**flags} # 返回与GEE病例交叉表兼容的气象字段
def download_nasa_power_case_control(calendar,output_path,cache_dir,request_delay=1.0): # 定义NASA POWER独立气象敏感性提取流程
    output_path=Path(output_path) # 标准化病例对照输出路径
    checkpoint_path=output_path.with_suffix(".checkpoint.csv") # 使用独立检查点避免被占用的最终文件中断长任务
    cache_dir=Path(cache_dir) # 标准化逐地点原始缓存目录
    output_path.parent.mkdir(parents=True,exist_ok=True) # 确保分析表输出目录存在
    cache_dir.mkdir(parents=True,exist_ok=True) # 确保逐地点缓存目录存在
    work=calendar.copy() # 复制病例对照日历以避免修改原对象
    work["date"]=pd.to_datetime(work["date"],errors="coerce") # 标准化病例与对照日期
    work=work.dropna(subset=["date","latitude","longitude"]).copy() # 保留日期和坐标完整的观测
    groups=list(work.groupby(["latitude","longitude"],sort=False)) # 按事件坐标分组以避免同地点重复下载
    records=[] # 初始化病例对照气象记录容器
    manifest=[] # 初始化逐地点接口元数据清单
    for index,((latitude,longitude),group) in enumerate(groups,1): # 顺序遍历唯一事件地点并遵守官方限速建议
        stem=_power_cache_stem(latitude,longitude) # 生成当前地点稳定缓存名
        cache_csv=cache_dir/f"{stem}.csv" # 定位当前地点日序列缓存
        cache_json=cache_dir/f"{stem}.json" # 定位当前地点来源元数据缓存
        end_date=max(group["date"].max(),pd.Timestamp("2020-12-31")) # 以2020基线终点和当前地点最后分析日的较晚者为请求终点
        try: # 尝试读取缓存或下载当前地点
            cached=pd.read_csv(cache_csv,parse_dates=["date"]) if cache_csv.is_file() else pd.DataFrame() # 优先读取已有逐地点缓存
            usable=len(cached)>0 and cached["date"].min()<=pd.Timestamp("1991-01-01") and cached["date"].max()>=end_date # 检查缓存是否覆盖完整基线与分析日期
            if usable: series=cached.set_index("date").sort_index(); metadata=json.loads(cache_json.read_text(encoding="utf-8")) # 使用覆盖完整的缓存及其元数据
            else: series,metadata=fetch_nasa_power_daily(latitude,longitude,"1991-01-01",end_date); series.to_csv(cache_csv,index=False,encoding="utf-8-sig"); cache_json.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8"); series=series.set_index("date").sort_index(); time.sleep(request_delay) # 下载、缓存并限速当前地点
            manifest.append(metadata) # 将当前地点来源元数据加入清单
            for row in group.itertuples(index=False): records.append({"event_id":str(row.event_id),"stratum_id":str(row.stratum_id),"date":pd.Timestamp(row.date).strftime("%Y-%m-%d"),"case":int(row.case),"latitude":float(row.latitude),"longitude":float(row.longitude),**_power_heat_properties(series,row.date),"weather_status":"completed","weather_source":"NASA_POWER_MERRA2_GEOS_IT","power_api_version":metadata.get("api_version"),"power_time_standard":metadata.get("time_standard"),"power_provisional":bool(pd.Timestamp(row.date)>pd.Timestamp.now().normalize()-pd.DateOffset(months=2))}) # 生成与主模型兼容且含来源状态的病例对照记录
        except Exception as error: # 捕获当前地点下载或解析失败
            for row in group.itertuples(index=False): records.append({"event_id":str(row.event_id),"stratum_id":str(row.stratum_id),"date":pd.Timestamp(row.date).strftime("%Y-%m-%d"),"case":int(row.case),"latitude":float(row.latitude),"longitude":float(row.longitude),"weather_status":f"failed:{type(error).__name__}","weather_source":"NASA_POWER_MERRA2_GEOS_IT"}) # 保留失败观测并避免成功请求定义样本
        _write_csv_retry(pd.DataFrame(records),checkpoint_path) # 每个地点写入独立可恢复分析检查点
        print(f"NASA POWER {index}/{len(groups)} {latitude:.4f},{longitude:.4f} {records[-1]['weather_status']}") # 输出紧凑地点级进度
    _write_csv_retry(pd.DataFrame(records),output_path) # 全部地点完成后一次写入正式分析表
    _write_csv_retry(pd.DataFrame(manifest).drop_duplicates(["latitude","longitude"]),output_path.with_name("nasa_power_request_manifest.csv")) if manifest else None # 保存接口版本、时间标准和访问日期清单
    return pd.DataFrame(records) # 返回NASA POWER病例对照气象表
if __name__=="__main__": # 支持模块方式生成外部数据快照
    registry=write_data_registry("outputs/tables/data_source_registry.csv") # 生成补充材料数据源登记表
    context=download_world_bank_context("data/interim/world_bank_country_year.csv") # 下载世界银行国家年份背景表
    events_path=Path("data/processed/events_enriched.csv") # 定位当前事件增强表
    events=pd.read_csv(events_path,encoding="utf-8-sig") if events_path.is_file() else pd.DataFrame() # 在事件表存在时读取当前版本
    enriched=attach_country_context(events,context) if len(events) else events # 为事件表附加最近三年内的国家背景指标
    enriched.to_csv(events_path,index=False,encoding="utf-8-sig") if len(enriched) else None # 原位更新可复现的事件增强表
    print({"registered_sources":len(registry),"country_year_rows":len(context),"events_with_country_context":int(enriched["context_year"].notna().sum()) if len(enriched) else 0}) # 输出紧凑运行摘要
