import hashlib,json,os,re,time # 导入哈希、序列化、环境变量、正则和计时模块
from concurrent.futures import ThreadPoolExecutor,as_completed # 导入受控并发工具
from pathlib import Path # 导入跨平台路径工具
from urllib.parse import urlparse # 导入网址域名解析工具
import numpy as np # 导入数值计算模块
import pandas as pd # 导入表格处理模块
COLUMN_MAP={"洲":"continent","国家/地区":"country","事件地点":"location","事件名称":"event_name","发生日期":"event_date","事件摘要":"event_summary","URL":"source_url","纬度":"latitude","经度":"longitude","火灾类型":"fire_type","建筑用途":"building_use","建筑总层数/高度":"building_height_or_floors","受影响楼层":"affected_floors","建筑年代":"building_age_status","死亡人数":"deaths","受伤人数":"injuries","疏散人数":"evacuated","原因":"cause","火势扩散":"fire_spread","城市系统/消防韧性薄弱环节":"urban_fire_resilience_gap","影响":"impact"} # 定义中英文字段映射
EXTERNAL_PATTERN=r"plane crash|aircraft|c-130|rocket|missile|bomb|terror|warfare|坠机|坠撞|导弹|火箭|轰炸|恐怖袭击|武装冲突" # 定义外部灾害触发词
ARSON_PATTERN=r"arson|纵火|蓄意点火" # 定义纵火触发词
CONSTRUCTION_PATTERN=r"construction|under construction|在建|施工|脚手架|电焊|焊接" # 定义在建与施工触发词
FACADE_PATTERN=r"facade|cladding|external wall|exterior|外立面|外墙|幕墙|保温材料" # 定义外立面火灾触发词
OFFICIAL_DOMAINS=("gov","fire.gov","gov.uk","info.gov.hk","cctv.com","doi.org","nist.gov","nfpa.org") # 定义官方或可追溯专业来源域名片段
COMPENDIUM_DOMAINS=("wikipedia.org","ctif.org") # 定义专题汇编来源域名片段
GEE_METRIC_COLUMNS=["population_count_2020_1km_cell","population_density_2020_per_km2","heatwave_days_7d","heatwave_degree_days_c","heatwave_max_t2m_c","heatwave_p90_t2m_c","heatwave_score_0_100","tmax_percentile_0_100","ghsl_built_surface_m2_1km","ghsl_built_volume_m3_1km","ghsl_mean_building_height_m_1km","ghsl_urbanisation_code_2020","era5_sampling_radius_km","gee_enrichment_status"] # 定义GEE增强字段
def _write_csv_with_retry(frame,path): # 定义适配Windows短时文件锁的检查点写入函数
    for attempt in range(1,6): # 最多尝试五次检查点写入
        try: frame.to_csv(path,index=False,encoding="utf-8-sig");return # 成功写入后立即返回
        except PermissionError: # 捕获监控读取或同步软件造成的短时文件锁
            if attempt==5: raise # 最后一次仍失败时保留真实异常
            time.sleep(attempt) # 递增等待后重试写入
def sha256_file(path): # 定义源文件哈希函数
    digest=hashlib.sha256() # 初始化SHA-256对象
    with Path(path).open("rb") as stream: # 以只读二进制方式打开文件
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block) # 分块更新哈希以控制内存
    return digest.hexdigest() # 返回源文件完整哈希
def first_number(value): # 定义文本首个数值提取函数
    match=re.search(r"-?\d+(?:\.\d+)?",str(value)) # 查找首个整数或小数
    return float(match.group()) if match else np.nan # 返回数值或缺失值
def explicit_metric_height(value): # 定义仅识别明确米制单位的建筑高度函数
    text=str(value).lower().replace(",","") # 标准化高度描述并移除千位分隔符
    match=re.search(r"(\d+(?:\.\d+)?)\s*(?:m(?![²2])|metres?|meters?|米)",text) # 匹配米、metre或meter且排除平方米单位
    height=float(match.group(1)) if match else np.nan # 提取明确米制高度或返回缺失
    return height if np.isfinite(height) and 1<=height<=1000 else np.nan # 将物理不合理候选值保留为缺失
def explicit_storeys(value): # 定义仅识别明确楼层单位的建筑层数函数
    text=str(value).lower().replace(",","") # 标准化楼层描述并移除千位分隔符
    match=re.search(r"(\d+(?:\.\d+)?)\s*(?:层|storeys?|stories?|floors?)",text) # 匹配中文层或英文楼层单位
    storeys=float(match.group(1)) if match else np.nan # 提取明确楼层数或返回缺失
    return storeys if np.isfinite(storeys) and 1<=storeys<=250 else np.nan # 将物理不合理候选值保留为缺失
def source_domain(url): # 定义来源域名标准化函数
    return urlparse(str(url)).netloc.lower().removeprefix("www.") # 移除常见www前缀
def source_grade(domain): # 定义来源等级函数
    if any(token in domain for token in OFFICIAL_DOMAINS): return "A" # 将官方、调查或论文来源标为A级
    if any(token in domain for token in COMPENDIUM_DOMAINS): return "C" # 将专题汇编来源标为C级
    return "B" if domain else "C" # 将可访问新闻与机构来源暂标为B级
def english_label(value): # 定义双语字段英文标签提取函数
    text=str(value).strip() # 标准化原始文本
    candidate=text.split("/")[-1].strip() if "/" in text else text # 优先保留斜杠后的英文部分
    if "hong kong" in candidate.lower(): return "Hong Kong" # 将香港地点统一为城市标签
    parts=[part.strip() for part in candidate.split(",") if part.strip()] # 将英文地点拆分为层级片段
    reject=r"tower|building|hotel|centre|center|complex|apartment|hospital|mall|road|street|intersection|district|area|airport|factory|warehouse|residence|plaza" # 定义非城市设施与次级区划词
    geographic=[part for part in parts if not re.search(reject,part.lower())] # 筛选可能的城市名称片段
    return geographic[0] if geographic else parts[0] if parts else candidate # 优先返回首个地理片段
def building_use_group(value): # 定义建筑用途归类函数
    text=str(value).lower() # 转换为小写文本
    if re.search(r"residen|apartment|housing|住宅|公寓|宿舍",text): return "Residential" # 归类住宅建筑
    if re.search(r"hotel|酒店|宾馆|旅馆",text): return "Hotel" # 归类酒店建筑
    if re.search(r"office|government|办公|政府",text): return "Office/government" # 归类办公与政府建筑
    if re.search(r"hospital|health|医院|医疗",text): return "Healthcare" # 归类医疗建筑
    if re.search(r"commercial|retail|mall|商场|商业",text): return "Commercial" # 归类商业建筑
    if re.search(r"mixed|综合",text): return "Mixed use" # 归类综合用途建筑
    return "Unknown/other" # 保留未知或其他用途
def prepare_events(workbook_path): # 定义更新事件表标准化流程
    raw=pd.read_excel(workbook_path,engine="openpyxl") # 只读载入原始工作簿
    events=raw.rename(columns=COLUMN_MAP).copy() # 将字段统一为英文机器可读名称
    events["event_date"]=pd.to_datetime(events["event_date"],errors="coerce") # 标准化事件日期
    events["latitude"]=pd.to_numeric(events["latitude"],errors="coerce") # 标准化纬度
    events["longitude"]=pd.to_numeric(events["longitude"],errors="coerce") # 标准化经度
    for column in ["deaths","injuries","evacuated"]: events[column]=events[column].map(first_number) # 提取伤亡和疏散字段首个可确认数值
    events=events.sort_values(["event_date","country","event_name"],kind="stable").reset_index(drop=True) # 生成稳定的事件顺序
    events.insert(0,"event_id",[f"HRF-{index:04d}" for index in range(1,len(events)+1)]) # 生成稳定顺序事件编号
    events["event_year"]=events["event_date"].dt.year.astype("Int64") # 提取事件年份
    events["source_domain"]=events["source_url"].map(source_domain) # 提取来源域名
    events["source_grade"]=events["source_domain"].map(source_grade) # 计算初步来源等级
    events["city_label_en"]=events["location"].map(english_label) # 提取英文城市短标签
    events["building_use_group"]=events["building_use"].map(building_use_group) # 归并建筑用途
    events["building_height_m_reported"]=events["building_height_or_floors"].map(explicit_metric_height) # 仅提取带明确米制单位的建筑高度
    events["building_storeys_reported"]=events["building_height_or_floors"].map(explicit_storeys) # 仅提取带明确楼层单位的建筑层数
    evidence=(events["cause"].fillna("")+" "+events["event_summary"].fillna("")+" "+events["fire_type"].fillna("")).str.lower() # 合并事件定义证据文本
    events["external_trigger"]=evidence.str.contains(EXTERNAL_PATTERN,regex=True) # 标记航空、战争或其他外部触发
    events["arson_trigger"]=evidence.str.contains(ARSON_PATTERN,regex=True) # 标记纵火事件
    events["construction_related"]=evidence.str.contains(CONSTRUCTION_PATTERN,regex=True) # 标记在建或施工相关事件
    events["facade_fire"]=evidence.str.contains(FACADE_PATTERN,regex=True) # 标记外立面相关事件
    events["valid_geocode"]=events["latitude"].between(-90,90)&events["longitude"].between(-180,180) # 标记合法地理坐标
    events["possible_duplicate"]=events.duplicated(["event_date","latitude","longitude","event_name"],keep=False) # 标记完全同日同地同名记录
    events["analysis_extended"]=events["valid_geocode"]&events["event_date"].notna()&~events["external_trigger"] # 定义排除外部触发的扩展分析队列
    events["analysis_core"]=events["analysis_extended"]&events["source_grade"].isin(["A","B"])&~events["possible_duplicate"] # 定义来源可追溯且非重复的核心分析队列
    events["cohort_reason"]=np.select([~events["valid_geocode"],events["external_trigger"],events["possible_duplicate"],events["source_grade"].eq("C")],["invalid_or_missing_geocode","external_disaster_trigger","possible_duplicate","compendium_only_source"],default="core_eligible") # 记录队列纳入或排除原因
    events["source_file_sha256"]=sha256_file(workbook_path) # 写入原始工作簿哈希
    return events # 返回标准化事件表
def _match_key(frame): # 定义旧新数据联合匹配键
    date=pd.to_datetime(frame["event_date"],errors="coerce").dt.strftime("%Y-%m-%d") # 生成标准日期文本
    latitude=pd.to_numeric(frame["latitude"],errors="coerce").round(4).astype(str) # 将纬度舍入到约十米尺度
    longitude=pd.to_numeric(frame["longitude"],errors="coerce").round(4).astype(str) # 将经度舍入到约十米尺度
    return date+"|"+latitude+"|"+longitude # 返回日期与坐标联合键
def merge_legacy_metrics(events,legacy_csv_path): # 定义旧GEE结果增量继承函数
    legacy=pd.read_csv(legacy_csv_path,encoding="utf-8-sig") # 读取旧GEE增强表
    legacy["legacy_match_key"]=_match_key(legacy) # 构造旧表匹配键
    rename={"population_count_2020":"population_count_2020_1km_cell"} # 定义旧人口字段名称兼容映射
    legacy=legacy.rename(columns=rename) # 统一旧增强字段名称
    usable=[column for column in GEE_METRIC_COLUMNS if column in legacy.columns] # 筛选重命名后实际存在的增强字段
    legacy=legacy.groupby("legacy_match_key",as_index=False)[usable].first() # 将同日同地旧记录聚合为唯一匹配行
    result=events.copy() # 复制标准化事件表
    result["legacy_match_key"]=_match_key(result) # 构造更新表匹配键
    result=result.merge(legacy,on="legacy_match_key",how="left",validate="many_to_one") # 按联合键继承可复用指标
    for column in GEE_METRIC_COLUMNS: # 遍历全部预期GEE增强字段
        if column not in result: result[column]=np.nan # 为旧表尚未包含的指标显式创建缺失列
    result["metric_provenance"]=np.where(result.get("heatwave_score_0_100",pd.Series(index=result.index,dtype=float)).notna(),"legacy_exact_date_geo_match","requires_current_gee") # 标记指标来源或待处理状态
    return result # 返回增量合并后的事件表
def build_case_control_calendar(events): # 定义时间分层病例交叉日历
    rows=[] # 初始化病例与对照日期容器
    for event in events.loc[events["analysis_extended"]].itertuples(index=False): # 遍历扩展分析队列
        date=pd.Timestamp(event.event_date) # 读取病例事件日期
        month_start=date.replace(day=1) # 定位事件月份首日
        month_end=month_start+pd.offsets.MonthEnd(0) # 定位事件月份末日
        candidates=pd.date_range(month_start,month_end,freq="D") # 生成事件月份全部日期
        controls=[value for value in candidates if value.weekday()==date.weekday() and value.date()!=date.date()] # 选择同月同星期对照日
        rows.append({"event_id":event.event_id,"stratum_id":event.event_id,"date":date,"case":1,"latitude":event.latitude,"longitude":event.longitude}) # 添加病例日
        rows.extend({"event_id":event.event_id,"stratum_id":event.event_id,"date":value,"case":0,"latitude":event.latitude,"longitude":event.longitude} for value in controls) # 添加匹配对照日
    return pd.DataFrame(rows) # 返回病例交叉长表日历
def initialize_earth_engine(): # 定义Earth Engine服务账号初始化函数
    import ee # 延迟导入Earth Engine以允许本地审计
    import google.auth # 延迟导入Google默认凭据工具
    from google.auth.exceptions import DefaultCredentialsError # 导入默认凭据缺失异常
    from google.oauth2 import service_account # 导入服务账号JSON凭据工具
    project=os.getenv("GEE_PROJECT_ID","graceful-fold-465505-i5") # 读取或使用已知Cloud项目ID
    key_value=os.getenv("GOOGLE_APPLICATION_CREDENTIALS","").strip() # 读取可选本地服务账号JSON路径
    scopes=["https://www.googleapis.com/auth/earthengine","https://www.googleapis.com/auth/cloud-platform"] # 定义Earth Engine与Cloud项目访问范围
    if key_value: # 在显式提供本地密钥路径时进入JSON认证流程
        key_path=Path(key_value).expanduser().resolve() # 解析本地密钥绝对路径
        if not key_path.is_file(): raise FileNotFoundError(f"未找到服务账号JSON：{key_path}") # 在密钥路径无效时明确停止
        credentials=service_account.Credentials.from_service_account_file(str(key_path),scopes=scopes) # 从本地JSON构造服务账号凭据
    else: # 在服务器或已配置开发环境中尝试默认凭据
        try: credentials,_=google.auth.default(scopes=scopes) # 读取Compute Engine或本机ADC凭据
        except DefaultCredentialsError as error: raise RuntimeError("未找到Earth Engine凭据：请设置GOOGLE_APPLICATION_CREDENTIALS或配置Application Default Credentials") from error # 在无任何凭据时给出可执行提示
    ee.Initialize(credentials=credentials,project=project) # 使用服务账号和Cloud项目初始化
    ee.data.setDeadline(float(os.getenv("GEE_DEADLINE_MS","180000"))) # 将单次交互请求硬截止设为默认三分钟以避免无限挂起
    return ee # 返回已初始化Earth Engine模块
def build_gee_sources(ee): # 定义外部栅格数据源集合
    sources={} # 初始化数据源字典
    sources["population"]=ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Count").filterDate("2020-01-01","2021-01-01").first().select("population_count") # 读取GPW 2020约1公里人口数量
    sources["population_density"]=ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density").filterDate("2020-01-01","2021-01-01").first().select("population_density") # 读取GPW 2020人口密度
    sources["built_surface"]=ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020").select("built_surface") # 读取GHSL 2020建成面积
    sources["built_volume"]=ee.Image("JRC/GHSL/P2023A/GHS_BUILT_V/2020").select("built_volume_total") # 读取GHSL 2020建筑体量
    sources["built_height"]=ee.Image("JRC/GHSL/P2023A/GHS_BUILT_H/2018").select("built_height") # 读取GHSL 2018平均建筑高度
    sources["urbanisation"]=ee.Image("JRC/GHSL/P2023A/GHS_SMOD_V2-0/2020").select("smod_code") # 读取GHSL 2020城市化等级
    sources["climate"]=ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") # 读取ERA5-Land日尺度再分析
    return sources # 返回数据源字典
def _local_daily_frame(ee,collection,bands,start,end,region,spatial_mean=False): # 定义低内存局地日序列提取函数
    selected=collection.filterDate(start,end).sort("system:time_start").select(bands).toBands() # 将时间维转换为有限多波段以避免逐日计算图展开
    reducer=ee.Reducer.mean() if spatial_mean else ee.Reducer.first() # 根据常规点采样或沿海回退选择空间归约器
    values=selected.reduceRegion(reducer,region,11132,bestEffort=True,maxPixels=100000,tileScale=8 if spatial_mean else 4).getInfo() # 读取事件像元或沿海缓冲区全部日值
    rows={} # 初始化按日期组织的局地记录
    for key,value in values.items(): # 遍历日期前缀波段值
        date_match=re.search(r"(\d{8})",key) # 从波段名称提取年月日
        band=next((candidate for candidate in bands if key.endswith("_"+candidate)),None) # 从波段名称识别原始变量
        if date_match and band and value is not None: rows.setdefault(pd.Timestamp(date_match.group(1)),{})[band]=float(value) # 保存非缺失日期变量值
    return pd.DataFrame.from_dict(rows,orient="index").sort_index() # 返回日期索引局地气象表
def _climatology_values(ee,climate,latitude,longitude,month): # 定义带磁盘缓存的1991至2020同月基线提取函数
    cache_dir=Path(__file__).resolve().parents[1]/"data/interim/era5_climatology_cache" # 定位项目内可恢复阈值缓存目录
    cache_dir.mkdir(parents=True,exist_ok=True) # 确保阈值缓存目录存在
    cache_file=cache_dir/f"lat{float(latitude):.4f}_lon{float(longitude):.4f}_m{int(month):02d}.csv" # 按坐标和月份生成稳定缓存名
    if cache_file.is_file(): # 在已有缓存时进入直接复用流程
        cached=pd.read_csv(cache_file,encoding="utf-8-sig") # 读取局地气候基线缓存
        radius=float(cached["sampling_radius_km"].iloc[0]) if "sampling_radius_km" in cached else 0.0 # 读取或兼容补充沿海采样半径
        return cached["tmax_c"].dropna().to_numpy(dtype=float),radius # 返回缓存最高温基线与采样半径
    point=ee.Geometry.Point([float(longitude),float(latitude)]) # 构造局地基线采样点
    climatology=climate.filter(ee.Filter.calendarRange(int(month),int(month),"month")) # 保留事件同月影像
    frames=[] # 初始化六个五年基线分块
    sampling_radius_km=0.0 # 默认记录事件坐标像元采样
    for year in range(1991,2021,5): # 遍历1991至2020六个五年区间
        frame=_local_daily_frame(ee,climatology,["temperature_2m_max"],f"{year}-01-01",f"{min(year+5,2021)}-01-01",point) # 优先读取事件坐标所在ERA5-Land像元
        if len(frame)<135: frame=_local_daily_frame(ee,climatology,["temperature_2m_max"],f"{year}-01-01",f"{min(year+5,2021)}-01-01",point.buffer(20000),spatial_mean=True);sampling_radius_km=20.0 # 沿海掩膜缺值时回退至20公里内陆地像元均值
        frames.append(frame) # 保存当前五年基线分块
    frame=pd.concat(frames).sort_index() # 在本地合并为完整1991至2020同月序列
    values=frame["temperature_2m_max"].dropna().to_numpy(dtype=float)-273.15 # 将完整基线转换为摄氏度数组
    pd.DataFrame({"tmax_c":values,"sampling_radius_km":sampling_radius_km}).to_csv(cache_file,index=False,encoding="utf-8-sig") # 写出可恢复且可审计的基线与采样模式缓存
    return values,sampling_radius_km # 返回局地同月最高温基线与采样半径
def enrich_one_event(ee,row,sources): # 定义单个事件的GEE增强函数
    point=ee.Geometry.Point([float(row.longitude),float(row.latitude)]) # 构造事件点
    urban_region=point.buffer(564.19) # 使用面积约一平方公里的圆形邻域
    event_date=pd.Timestamp(row.event_date).normalize() # 标准化事件日期
    event_month=int(event_date.month) # 提取事件月份
    climate_values,sampling_radius_km=_climatology_values(ee,sources["climate"],row.latitude,row.longitude,event_month) # 提取或复用同月局地最高温基线与采样半径
    if len(climate_values)<800: raise RuntimeError(f"ERA5基线日值不足:{len(climate_values)}") # 要求30年同月基线具有足够覆盖
    p90=float(np.percentile(climate_values,90)) # 计算局地同月第90百分位
    threshold=max(p90,30.0) # 采用相对阈值与30摄氏度绝对下限的较高者
    window=_local_daily_frame(ee,sources["climate"],["temperature_2m_max"],(event_date-pd.Timedelta(days=6)).strftime("%Y-%m-%d"),(event_date+pd.Timedelta(days=1)).strftime("%Y-%m-%d"),point) # 在事件坐标所在ERA5像元提取七天最高温
    if "temperature_2m_max" not in window or len(window["temperature_2m_max"].dropna())!=7: window=_local_daily_frame(ee,sources["climate"],["temperature_2m_max"],(event_date-pd.Timedelta(days=6)).strftime("%Y-%m-%d"),(event_date+pd.Timedelta(days=1)).strftime("%Y-%m-%d"),point.buffer(20000),spatial_mean=True);sampling_radius_km=20.0 # 沿海点缺值时回退至20公里陆地像元均值
    event_values=window["temperature_2m_max"].dropna().to_numpy(dtype=float)-273.15 # 将七天最高温转换为摄氏度数组
    if len(event_values)!=7: raise RuntimeError(f"ERA5事件窗口日值不足:{len(event_values)}") # 要求完整七天窗口
    heat_days=int(np.sum(event_values>threshold)) # 统计七天窗口超阈日数
    degree_days=float(np.maximum(event_values-threshold,0).sum()) # 计算累计超阈温度
    max_temp=float(np.max(event_values)) # 计算七天窗口最高温
    event_day=float(event_values[-1]) # 提取事件日最高温
    percentile=float(np.mean(climate_values<=event_day)*100) # 计算事件日最高温局地经验百分位评分
    static=ee.Image.cat([sources["population"],sources["population_density"]]).reduceRegion(ee.Reducer.first(),point,927.67,bestEffort=True,maxPixels=100000,tileScale=4) # 在原生约1公里像元读取人口数量与密度
    built_surface=sources["built_surface"].reduceRegion(ee.Reducer.sum(),urban_region,100,bestEffort=True,maxPixels=100000,tileScale=4).get("built_surface") # 汇总一平方公里邻域建成面积
    built_volume=sources["built_volume"].reduceRegion(ee.Reducer.sum(),urban_region,100,bestEffort=True,maxPixels=100000,tileScale=4).get("built_volume_total") # 汇总一平方公里邻域建筑体量
    built_height=sources["built_height"].reduceRegion(ee.Reducer.mean(),urban_region,100,bestEffort=True,maxPixels=100000,tileScale=4).get("built_height") # 计算一平方公里邻域平均建筑高度
    urbanisation=sources["urbanisation"].reduceRegion(ee.Reducer.mode(),point,1000,bestEffort=True,maxPixels=100000,tileScale=4).get("smod_code") # 读取一公里城市化等级
    static_result=ee.Dictionary({"population_count_2020_1km_cell":static.get("population_count"),"population_density_2020_per_km2":static.get("population_density"),"ghsl_built_surface_m2_1km":built_surface,"ghsl_built_volume_m3_1km":built_volume,"ghsl_mean_building_height_m_1km":built_height,"ghsl_urbanisation_code_2020":urbanisation}).getInfo() # 单独取回人口与建成环境指标以缩小服务端计算图
    return {"event_id":str(row.event_id),**static_result,"heatwave_days_7d":heat_days,"heatwave_degree_days_c":degree_days,"heatwave_max_t2m_c":max_temp,"heatwave_p90_t2m_c":p90,"heatwave_score_0_100":float(np.clip(degree_days*10,0,100)),"tmax_percentile_0_100":percentile,"era5_sampling_radius_km":sampling_radius_km,"gee_enrichment_status":"completed"} # 汇总事件级外部指标并记录沿海回退半径
def _enrich_with_retry(ee,row,sources,retries): # 定义带重试的事件增强函数
    for attempt in range(1,retries+1): # 按配置次数尝试当前事件
        try: return enrich_one_event(ee,row,sources) # 成功时返回当前事件指标
        except Exception as error: # 捕获网络、配额或服务端异常
            if attempt==retries: return {"event_id":str(row.event_id),"gee_enrichment_status":f"failed:{type(error).__name__}"} # 重试耗尽后保留失败类型
            time.sleep(attempt*5) # 递增等待以降低瞬时配额压力
def run_gee_enrichment(events,output_path,only_missing=True): # 定义批量Earth Engine增强流程
    ee=initialize_earth_engine() # 初始化服务账号连接
    sources=build_gee_sources(ee) # 构造外部数据源
    work=events.loc[events["valid_geocode"]&events["event_date"].notna()].copy() # 保留坐标和日期均有效的事件
    if only_missing and "gee_enrichment_status" in work: work=work.loc[work["gee_enrichment_status"].ne("completed")|work["gee_enrichment_status"].isna()] # 默认仅处理当前尚未完成的事件
    existing=pd.read_csv(output_path,encoding="utf-8-sig") if Path(output_path).is_file() else pd.DataFrame() # 读取上次批处理检查点
    existing=existing.loc[existing.get("gee_enrichment_status",pd.Series(index=existing.index,dtype=str)).eq("completed")].copy() # 仅继承已完成事件以便失败记录自动重试
    if not existing.empty: work=work.loc[~work["event_id"].astype(str).isin(existing["event_id"].astype(str))] # 跳过检查点中已完成事件
    workers=int(os.getenv("GEE_WORKERS","2")) # 读取受控并发数
    retries=int(os.getenv("GEE_RETRIES","3")) # 读取单事件重试次数
    rows=list(work.itertuples(index=False)) # 构造待提交事件列表
    records=existing.to_dict("records") # 使用既有成功结果初始化结果容器
    with ThreadPoolExecutor(max_workers=workers) as executor: # 建立受控线程池
        futures={executor.submit(_enrich_with_retry,ee,row,sources,retries):row.event_id for row in rows} # 提交独立事件任务
        for index,future in enumerate(as_completed(futures),1): # 按完成顺序收集结果
            record=future.result() # 读取当前事件结果
            records.append(record) # 追加当前事件结果
            if index%10==0 or index==len(rows): _write_csv_with_retry(pd.DataFrame(records),output_path) # 每十条写入可恢复检查点并处理短时文件锁
            print(f"GEE {index}/{len(rows)} {record['event_id']} {record['gee_enrichment_status']}") # 输出紧凑进度信息
    return pd.DataFrame(records) # 返回本轮GEE结果
def _case_control_stratum(ee,group,climate): # 定义单个病例交叉分层的低内存气象提取函数
    first=group.iloc[0] # 读取当前事件分层首行
    month=int(pd.Timestamp(first["date"]).month) # 读取当前事件月份
    baseline,sampling_radius_km=_climatology_values(ee,climate,first["latitude"],first["longitude"],month) # 提取或复用同月局地最高温基线与采样半径
    if len(baseline)<800: raise RuntimeError(f"ERA5基线日值不足:{len(baseline)}") # 要求30年同月基线具有足够覆盖
    p85,p90,p95=[float(value) for value in np.percentile(baseline,[85,90,95])] # 计算局地第85第90与第95百分位阈值
    threshold85,threshold90,threshold95=max(p85,30.0),max(p90,30.0),max(p95,30.0) # 构造相对阈值与30摄氏度下限的复合阈值
    point=ee.Geometry.Point([float(first["longitude"]),float(first["latitude"])]) # 构造当前事件地点
    dates=pd.to_datetime(group["date"]).dt.normalize() # 标准化病例与对照日期
    bands=["temperature_2m_max","dewpoint_temperature_2m","total_precipitation_sum","u_component_of_wind_10m","v_component_of_wind_10m"] # 定义热湿雨风提取变量
    weather_start=dates.min()-pd.Timedelta(days=3) # 定位病例对照天气窗口起点
    weather_end=dates.max()+pd.Timedelta(days=1) # 定位病例对照天气窗口排他终点
    weather=_local_daily_frame(ee,climate,bands,weather_start.strftime("%Y-%m-%d"),weather_end.strftime("%Y-%m-%d"),point) # 在事件坐标所在ERA5像元一次提取完整天气窗口
    required_dates=set(pd.date_range(weather_start,weather_end-pd.Timedelta(days=1),freq="D")) # 构造天气窗口全部必需日期
    if not required_dates.issubset(set(weather.index)) or not set(bands).issubset(set(weather.columns)): weather=_local_daily_frame(ee,climate,bands,weather_start.strftime("%Y-%m-%d"),weather_end.strftime("%Y-%m-%d"),point.buffer(20000),spatial_mean=True);sampling_radius_km=20.0 # 沿海掩膜缺值时回退至20公里内陆地像元均值
    records=[] # 初始化病例与对照日结果
    for record in group.itertuples(index=False): # 遍历当前分层病例与对照日
        date=pd.Timestamp(record.date).normalize() # 标准化当前观测日期
        daily=weather.loc[date] # 读取当前日热湿雨风数据
        lag0,lag1,lag2,lag3=[float(weather.loc[date-pd.Timedelta(days=lag),"temperature_2m_max"]-273.15) for lag in range(4)] # 读取当前日至前三日最高温
        dewpoint=float(daily["dewpoint_temperature_2m"]-273.15) # 将露点温度转换为摄氏度
        precipitation=float(daily["total_precipitation_sum"]*1000) # 将降水量转换为毫米
        wind=float(np.hypot(daily["u_component_of_wind_10m"],daily["v_component_of_wind_10m"])) # 合成十米风速
        hw_p85_3d=int(lag0>threshold85 and lag1>threshold85 and lag2>threshold85) # 判定连续三日超过第85百分位复合阈值
        hw_p90_2d=int(lag0>threshold90 and lag1>threshold90) # 判定连续两日超过第90百分位复合阈值
        hw_p90_3d=int(lag0>threshold90 and lag1>threshold90 and lag2>threshold90) # 判定连续三日超过第90百分位复合阈值
        hw_p90_4d=int(lag0>threshold90 and lag1>threshold90 and lag2>threshold90 and lag3>threshold90) # 判定连续四日超过第90百分位复合阈值
        hw_p95_3d=int(lag0>threshold95 and lag1>threshold95 and lag2>threshold95) # 判定连续三日超过第95百分位复合阈值
        hw_p90_3d_no_floor=int(lag0>p90 and lag1>p90 and lag2>p90) # 判定不设绝对温度下限的连续三日相对极端热
        percentile=float(np.mean(baseline<=lag0)*100) # 计算当前日最高温局地经验百分位
        records.append({"event_id":str(record.event_id),"stratum_id":str(record.stratum_id),"date":date.strftime("%Y-%m-%d"),"case":int(record.case),"latitude":float(record.latitude),"longitude":float(record.longitude),"tmax_c":lag0,"tmax_lag1_c":lag1,"tmax_lag2_c":lag2,"tmax_lag3_c":lag3,"tmax_p85_c":p85,"tmax_p90_c":p90,"tmax_p95_c":p95,"tmax_anomaly_c":lag0-p90,"tmax_percentile_0_100":percentile,"heatwave_indicator":hw_p90_3d,"hw_p85_3d":hw_p85_3d,"hw_p90_2d":hw_p90_2d,"hw_p90_3d":hw_p90_3d,"hw_p90_4d":hw_p90_4d,"hw_p95_3d":hw_p95_3d,"hw_p90_3d_no_floor":hw_p90_3d_no_floor,"dewpoint_c":dewpoint,"precipitation_mm":precipitation,"wind_speed_ms":wind,"era5_sampling_radius_km":sampling_radius_km,"weather_status":"completed"}) # 汇总当前病例或对照日气象暴露并记录沿海回退半径
    return records # 返回当前分层全部气象记录
def _case_control_with_retry(ee,group,climate,retries): # 定义带重试的病例交叉分层提取函数
    event_id=str(group.iloc[0]["event_id"]) # 读取当前事件编号
    for attempt in range(1,retries+1): # 按配置次数尝试当前分层
        try: return _case_control_stratum(ee,group,climate) # 成功时返回当前分层全部观测
        except Exception as error: # 捕获服务端、网络或数据覆盖异常
            if attempt==retries: return [{"event_id":event_id,"stratum_id":event_id,"weather_status":f"failed:{type(error).__name__}"}] # 重试耗尽后保留失败状态
            time.sleep(attempt*5) # 使用递增等待降低配额压力
def run_case_control_weather(calendar,output_path): # 定义病例交叉气象暴露批处理流程
    ee=initialize_earth_engine() # 初始化服务账号连接
    climate=ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") # 读取ERA5-Land日尺度数据
    latest=pd.to_datetime(ee.Date(climate.aggregate_max("system:time_start")).format("YYYY-MM-dd").getInfo()) # 查询当前气象数据最新日期
    work=calendar.loc[pd.to_datetime(calendar["date"],errors="coerce").le(latest)].copy() # 排除当前尚未覆盖的未来或近实时日期
    existing=pd.read_csv(output_path,encoding="utf-8-sig") if Path(output_path).is_file() else pd.DataFrame() # 读取上次病例交叉检查点
    existing=existing.loc[existing.get("weather_status",pd.Series(index=existing.index,dtype=str)).eq("completed")].copy() # 仅继承已完成分层记录
    completed=set(existing["stratum_id"].astype(str)) if not existing.empty else set() # 构造已完成分层编号集合
    work=work.loc[~work["stratum_id"].astype(str).isin(completed)] # 跳过检查点中已完成分层
    workers=int(os.getenv("GEE_WORKERS","2")) # 读取受控并发数
    retries=int(os.getenv("GEE_RETRIES","3")) # 读取单分层重试次数
    groups=[group.copy() for _,group in work.groupby("stratum_id",sort=False)] # 构造事件分层任务列表
    records=existing.to_dict("records") # 使用既有成功结果初始化病例交叉气象结果
    with ThreadPoolExecutor(max_workers=workers) as executor: # 建立受控线程池
        futures={executor.submit(_case_control_with_retry,ee,group,climate,retries):str(group.iloc[0]["event_id"]) for group in groups} # 提交独立事件分层任务
        for index,future in enumerate(as_completed(futures),1): # 按完成顺序收集分层结果
            records.extend(future.result()) # 追加当前分层全部病例与对照观测
            if index%10==0 or index==len(groups): _write_csv_with_retry(pd.DataFrame(records),output_path) # 每十个分层写入可恢复检查点并处理短时文件锁
            print(f"病例交叉气象 {index}/{len(groups)} {futures[future]}") # 输出紧凑进度信息
    result=pd.DataFrame(records) # 整理病例交叉气象长表
    if "weather_status" not in result: result["weather_status"]="completed" # 为成功记录补充完成状态
    return result # 返回病例交叉气象暴露表
def write_audit(events,output_json): # 定义事件队列审计报告输出函数
    report={"events_total":int(len(events)),"geocoded":int(events["valid_geocode"].sum()),"analysis_core":int(events["analysis_core"].sum()),"analysis_extended":int(events["analysis_extended"].sum()),"external_trigger":int(events["external_trigger"].sum()),"arson_trigger":int(events["arson_trigger"].sum()),"construction_related":int(events["construction_related"].sum()),"possible_duplicate":int(events["possible_duplicate"].sum()),"countries":int(events["country"].nunique()),"date_min":str(events["event_date"].min().date()),"date_max":str(events["event_date"].max().date()),"source_sha256":str(events["source_file_sha256"].iloc[0])} # 汇总可复核队列指标
    Path(output_json).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8") # 保存UTF-8审计报告
    return report # 返回审计报告字典
