import numpy as np # 导入数值计算模块
import pandas as pd # 导入表格处理模块
import statsmodels.api as sm # 导入统计模型基础接口
import statsmodels.formula.api as smf # 导入公式模型接口
from scipy.stats import chi2 # 导入卡方分布用于置信区间
from statsmodels.discrete.conditional_models import ConditionalLogit # 导入条件Logit病例交叉模型
from statsmodels.stats.multitest import multipletests # 导入多重检验校正函数
def robust_scale(series): # 定义稳健标准化函数
    values=pd.to_numeric(series,errors="coerce") # 将输入转换为数值
    median=values.median() # 计算样本中位数
    scale=values.quantile(0.75)-values.quantile(0.25) # 计算四分位距
    scale=scale if np.isfinite(scale) and scale>0 else values.std() # 在四分位距无效时使用标准差
    return (values-median)/scale if np.isfinite(scale) and scale>0 else values*0 # 返回稳健标准分数
def conditional_heat_model(case_control,exposure="heatwave_indicator",covariates=("dewpoint_c","precipitation_mm","wind_speed_ms"),binary_exposures=("heatwave_indicator","hw_p85_3d","hw_p90_2d","hw_p90_3d","hw_p90_4d","hw_p95_3d","hw_p90_3d_no_floor")): # 定义时间分层病例交叉主模型
    exposures=[exposure,*covariates] # 合并主暴露与协变量字段
    data=case_control.dropna(subset=["case","stratum_id",*exposures]).copy() # 保留模型所需完整观测
    design_columns=[] # 初始化条件Logit设计矩阵字段
    scales={} # 初始化效应量尺度说明
    for column in exposures: # 遍历主暴露与协变量
        if column in binary_exposures: data[f"x_{column}"]=pd.to_numeric(data[column],errors="coerce").astype(float); scales[f"x_{column}"]="1 versus 0" # 保持二元热浪指标原始尺度以得到暴露对未暴露优势比
        else: data[f"x_{column}"]=robust_scale(data[column]); scales[f"x_{column}"]="per IQR" # 将连续变量按四分位距缩放以便比较效应量
        design_columns.append(f"x_{column}") # 记录当前设计矩阵字段
    design=data[design_columns].astype(float) # 构造模型设计矩阵
    model=ConditionalLogit(data["case"].astype(int),design,groups=data["stratum_id"]) # 构造按事件分层的条件Logit模型
    fit=model.fit(disp=False) # 拟合条件Logit模型
    table=pd.DataFrame({"term":fit.params.index,"log_odds":fit.params.values,"std_error":fit.bse.values}) # 整理模型系数与标准误
    table["variable"]=table["term"].str.removeprefix("x_") # 恢复便于解读的原始变量名称
    table["effect_scale"]=table["term"].map(scales) # 写入每个效应量的解释尺度
    table["odds_ratio"]=np.exp(table["log_odds"]) # 转换为优势比
    table["ci_low"]=np.exp(table["log_odds"]-1.96*table["std_error"]) # 计算95%置信区间下限
    table["ci_high"]=np.exp(table["log_odds"]+1.96*table["std_error"]) # 计算95%置信区间上限
    table["p_value"]=fit.pvalues.values # 保存双侧检验P值
    return fit,table,data # 返回拟合对象、结果表与实际分析样本
def casualty_severity_model(events,outcome="casualties_total"): # 定义事件严重度探索模型
    data=events.loc[events["analysis_core"]].copy() # 使用核心分析队列
    data["casualties_total"]=pd.to_numeric(data["deaths"],errors="coerce")+pd.to_numeric(data["injuries"],errors="coerce") # 仅在死亡与受伤均有数值报告时计算总伤亡以避免把缺失误作零
    data["log_population"]=np.log1p(pd.to_numeric(data["population_count_2020_1km_cell"],errors="coerce")) # 对一公里人口数量取对数
    data["log_built_volume"]=np.log1p(pd.to_numeric(data["ghsl_built_volume_m3_1km"],errors="coerce")) # 对一公里建筑体量取对数
    data["heatwave_score_per_10"]=pd.to_numeric(data["heatwave_score_0_100"],errors="coerce")/10 # 将七日累计超阈热评分转换为每十分效应尺度
    data["event_year_10y"]=(pd.to_numeric(data["event_year"],errors="coerce")-2000)/10 # 将事件年份转换为每十年效应尺度以控制报告时期变化
    formula=f"{outcome} ~ heatwave_score_per_10 + log_population + log_built_volume + event_year_10y" # 定义避免稀疏结构类别过拟合的精简探索模型公式
    data=data.dropna(subset=[outcome,"heatwave_score_per_10","log_population","log_built_volume","event_year_10y"]) # 保留死亡受伤及全部调整变量均已报告的完整案例
    fit=smf.glm(formula=formula,data=data,family=sm.families.NegativeBinomial(alpha=1.0)).fit(cov_type="HC3") # 使用负二项GLM与稳健标准误拟合计数结局
    table=pd.DataFrame({"term":fit.params.index,"log_rate_ratio":fit.params.values,"std_error":fit.bse.values}) # 整理严重度模型系数
    table["rate_ratio"]=np.exp(table["log_rate_ratio"]) # 转换为发生率比
    table["ci_low"]=np.exp(table["log_rate_ratio"]-1.96*table["std_error"]) # 计算95%置信区间下限
    table["ci_high"]=np.exp(table["log_rate_ratio"]+1.96*table["std_error"]) # 计算95%置信区间上限
    table["p_value"]=fit.pvalues.values # 保存双侧检验P值
    table["effect_scale"]=table["term"].map({"heatwave_score_per_10":"per 10 heat-score points","log_population":"per natural-log unit","log_built_volume":"per natural-log unit","event_year_10y":"per decade"}).fillna("intercept") # 写入各系数的可解释效应尺度
    table["n_observations"]=len(data) # 写入死亡与受伤均报告的实际模型样本量
    return fit,table,data # 返回模型、结果表与分析样本
def heat_definition_sensitivity(case_control,definitions=("heatwave_indicator","hw_p85_3d","hw_p90_2d","hw_p90_4d","hw_p95_3d","hw_p90_3d_no_floor"),covariates=("dewpoint_c","precipitation_mm","wind_speed_ms")): # 定义多热浪阈值病例交叉敏感性分析
    rows=[] # 初始化多定义效应量结果
    for exposure in definitions: # 遍历预设热浪定义
        if exposure not in case_control: continue # 跳过尚未由GEE生成的暴露字段
        fit,table,sample=conditional_heat_model(case_control,exposure=exposure,covariates=covariates) # 拟合当前热浪定义的条件Logit模型
        result=table.loc[table["variable"].eq(exposure)].iloc[0].to_dict() # 提取当前定义的热浪效应量
        result.update({"definition":exposure,"n_observations":int(len(sample)),"n_strata":int(sample["stratum_id"].nunique()),"n_informative_strata":int(sample.groupby("stratum_id")[exposure].nunique().gt(1).sum()),"converged":bool(getattr(fit,"mle_retvals",{}).get("converged",True))}) # 补充样本量、有效分层数与收敛状态
        rows.append(result) # 保存当前定义结果
    return pd.DataFrame(rows) # 返回多定义稳健性效应量表
def continuous_temperature_sensitivity(case_control,covariates=("dewpoint_c","precipitation_mm","wind_speed_ms")): # 定义连续温度异常与有序滞后敏感性分析
    data=case_control.copy() # 复制病例交叉表避免修改原始输入
    data["tmax_lag0_anomaly_c"]=pd.to_numeric(data["tmax_c"],errors="coerce")-pd.to_numeric(data["tmax_p90_c"],errors="coerce") # 计算事件或对照当日相对局地月度P90的温度异常
    for lag in [1,2,3]: data[f"tmax_lag{lag}_anomaly_c"]=pd.to_numeric(data[f"tmax_lag{lag}_c"],errors="coerce")-pd.to_numeric(data["tmax_p90_c"],errors="coerce") # 计算前三日相对同一局地月度P90的有序温度异常
    data["tmax_mean_lag0_3_anomaly_c"]=data[[f"tmax_lag{lag}_anomaly_c" for lag in [0,1,2,3]]].mean(axis=1) # 计算当日及前三日平均温度异常以表示连续累积热暴露
    specifications=[("Current day",0,"tmax_lag0_anomaly_c"),("Lag 1 day",1,"tmax_lag1_anomaly_c"),("Lag 2 days",2,"tmax_lag2_anomaly_c"),("Lag 3 days",3,"tmax_lag3_anomaly_c"),("Mean lag 0–3 days",-1,"tmax_mean_lag0_3_anomaly_c")] # 固定连续暴露与滞后分析顺序
    rows=[] # 初始化连续温度敏感性结果容器
    for order,(label,lag_days,exposure) in enumerate(specifications,1): # 遍历当日三个单日滞后与四日平均暴露
        fit,table,sample=conditional_heat_model(data,exposure=exposure,covariates=covariates,binary_exposures=()) # 按连续变量每四分位距尺度拟合相同条件Logit模型
        estimate=table.loc[table["variable"].eq(exposure)].iloc[0].to_dict() # 提取当前连续温度暴露效应量
        exposure_values=pd.to_numeric(sample[exposure],errors="coerce") # 读取实际模型样本中的连续温度异常
        estimate.update({"display_order":order,"specification":label,"lag_days":lag_days,"temperature_column":exposure,"temperature_iqr_c":exposure_values.quantile(0.75)-exposure_values.quantile(0.25),"n_observations":len(sample),"n_strata":sample["stratum_id"].nunique(),"n_informative_strata":sample.groupby("stratum_id")[exposure].nunique().gt(1).sum(),"converged":bool(getattr(fit,"mle_retvals",{}).get("converged",True))}) # 保存可解释温度尺度样本量有效分层与收敛状态
        rows.append(estimate) # 追加当前连续温度结果
    results=pd.DataFrame(rows) # 汇总全部连续温度与滞后敏感性结果
    results["p_value_holm"]=multipletests(results["p_value"],method="holm")[1] # 在五个预设相关温度规格内计算Holm校正P值
    return results # 返回包含原始与校正P值的连续温度敏感性结果
def event_window_sensitivity(case_control,events,exposure="heatwave_indicator",covariates=("dewpoint_c","precipitation_mm","wind_speed_ms")): # 定义来源时期事件类型与逐洲留一病例交叉敏感性分析
    event_data=events.drop_duplicates("event_id").set_index("event_id") # 将事件属性整理为按稳定事件编号索引的事实表
    extended=event_data["analysis_extended"].astype(bool) # 定义主分析扩展队列掩码
    cohorts={"Extended cohort":extended,"Core cohort":event_data["analysis_core"].astype(bool),"Exclude 2025–2026":extended&event_data["event_year"].le(2024),"Exclude construction":extended&~event_data["construction_related"].astype(bool),"Exclude façade":extended&~event_data["facade_fire"].astype(bool),"Exclude arson":extended&~event_data["arson_trigger"].astype(bool)} # 定义预设证据来源时期与事件类型排除队列
    continent_labels={"亚洲":"Asia","欧洲":"Europe","北美洲":"North America","南美洲":"South America","非洲":"Africa","大洋洲":"Oceania"} # 定义逐洲留一英文显示标签
    for continent in event_data.loc[extended,"continent"].dropna().drop_duplicates(): cohorts[f"Leave out {continent_labels.get(continent,continent)}"]=extended&event_data["continent"].ne(continent) # 为每个洲追加一次逐洲留一队列
    rows=[] # 初始化队列敏感性效应量记录
    for order,(label,mask) in enumerate(cohorts.items(),1): # 按预设顺序遍历全部队列定义
        event_ids=event_data.index[mask] # 提取当前队列允许进入模型的事件编号
        subset=case_control.loc[case_control["event_id"].isin(event_ids)].copy() # 按稳定事件编号筛选完整匹配日分层
        analysis_family="Cohort and event exclusions" if order<=6 else "Leave-one-continent-out" # 标记来源事件排除与逐洲留一两类检验
        try: # 捕获极少有效分层导致的数值不可识别问题
            fit,table,sample=conditional_heat_model(subset,exposure=exposure,covariates=covariates) # 使用相同主定义与协变量拟合当前队列模型
            estimate=table.loc[table["variable"].eq(exposure)].iloc[0] # 提取当前队列热浪效应量
            rows.append({"display_order":order,"analysis_family":analysis_family,"restriction":label,"exposure":exposure,"odds_ratio":estimate["odds_ratio"],"ci_low":estimate["ci_low"],"ci_high":estimate["ci_high"],"p_value":estimate["p_value"],"n_observations":len(sample),"n_strata":sample["stratum_id"].nunique(),"n_informative_strata":sample.groupby("stratum_id")[exposure].nunique().gt(1).sum(),"converged":bool(getattr(fit,"mle_retvals",{}).get("converged",True)),"status":"completed"}) # 保存效应量样本量有效分层与收敛状态
        except Exception as error: rows.append({"display_order":order,"analysis_family":analysis_family,"restriction":label,"exposure":exposure,"odds_ratio":np.nan,"ci_low":np.nan,"ci_high":np.nan,"p_value":np.nan,"n_observations":len(subset),"n_strata":subset["stratum_id"].nunique(),"n_informative_strata":subset.groupby("stratum_id")[exposure].nunique().gt(1).sum(),"converged":False,"status":f"failed:{type(error).__name__}"}) # 显式保留不可识别模型而不静默删除
    return pd.DataFrame(rows) # 返回全部队列与逐洲留一稳健性结果
def poisson_exact_interval(count,exposure,alpha=0.05,scale=100000): # 定义泊松精确率及区间函数
    count=float(count) # 将事件数转换为浮点数
    exposure=float(exposure) # 将暴露量转换为浮点数
    rate=count/exposure*scale # 计算指定尺度事件率
    low=0.0 if count==0 else 0.5*chi2.ppf(alpha/2,2*count)/exposure*scale # 计算精确置信区间下限
    high=0.5*chi2.ppf(1-alpha/2,2*(count+1))/exposure*scale # 计算精确置信区间上限
    return {"count":int(count),"exposure":exposure,"rate_per_100k_grid_days":rate,"ci_low":low,"ci_high":high} # 返回率与置信区间
def compare_grid_day_rates(grid_days): # 定义热浪与非热浪网格日率比较函数
    required={"heatwave","fire_event","grid_day_weight"} # 声明率比较所需字段
    missing=required.difference(grid_days.columns) # 检查输入字段完整性
    if missing: raise ValueError(f"网格日表缺少字段：{sorted(missing)}") # 字段缺失时立即停止
    rows=[] # 初始化分组率结果
    for label,group in grid_days.groupby("heatwave",dropna=False): # 按热浪状态汇总
        rows.append({"heatwave":bool(label),**poisson_exact_interval(group["fire_event"].sum(),group["grid_day_weight"].sum())}) # 计算当前状态精确率
    table=pd.DataFrame(rows) # 生成率比较表
    if len(table)==2: # 仅在两组均存在时计算率比
        hot=table.loc[table["heatwave"]].iloc[0] # 读取热浪组
        cool=table.loc[~table["heatwave"]].iloc[0] # 读取非热浪组
        table.attrs["rate_ratio"]=hot["rate_per_100k_grid_days"]/cool["rate_per_100k_grid_days"] # 计算热浪与非热浪率比
    return table # 返回率比较结果
def source_sensitivity(events,metric="heatwave_score_0_100"): # 定义来源与队列敏感性摘要
    cohorts={"all_geocoded":events["valid_geocode"],"extended_no_external":events["analysis_extended"],"core_verified":events["analysis_core"],"exclude_2025_2026":events["analysis_core"]&events["event_year"].le(2024),"exclude_construction":events["analysis_core"]&~events["construction_related"],"exclude_arson":events["analysis_core"]&~events["arson_trigger"]} # 定义预设敏感性队列
    rows=[] # 初始化敏感性摘要容器
    for name,mask in cohorts.items(): # 遍历所有敏感性队列
        values=pd.to_numeric(events.loc[mask,metric],errors="coerce").dropna() # 提取当前队列有效指标
        rows.append({"cohort":name,"n_events":int(mask.sum()),"n_metric":int(values.size),"mean":values.mean(),"median":values.median(),"q25":values.quantile(0.25),"q75":values.quantile(0.75)}) # 汇总当前队列分布
    return pd.DataFrame(rows) # 返回敏感性摘要表
def reporting_completeness_model(events,outcome_field="injuries"): # 定义报告完整性观察过程模型
    data=events.loc[events["analysis_extended"]].copy() # 使用排除外部触发且日期坐标有效的扩展队列
    data["outcome_reported"]=pd.to_numeric(data[outcome_field],errors="coerce").notna().astype(int) # 将目标字段是否有数值记录编码为二元结局
    data["event_year_scaled"]=robust_scale(data["event_year"]) # 按四分位距标准化事件年份
    data["log_gdp_scaled"]=robust_scale(np.log1p(pd.to_numeric(data["gdp_per_capita_ppp_constant_2021"],errors="coerce"))) # 对人均GDP取对数后按四分位距标准化
    data["source_grade"]=data["source_grade"].fillna("Missing").astype(str) # 显式保留缺失来源等级类别
    data["continent"]=data["continent"].fillna("Missing").astype(str) # 显式保留缺失洲际类别
    data=data.dropna(subset=["outcome_reported","event_year_scaled","log_gdp_scaled"]).copy() # 保留观察过程模型完整协变量样本
    formula="outcome_reported ~ event_year_scaled + log_gdp_scaled + C(source_grade) + C(continent)" # 定义报告完整性Logistic模型公式
    fit=smf.glm(formula=formula,data=data,family=sm.families.Binomial()).fit(cov_type="HC3") # 使用二项GLM与稳健标准误拟合观察过程模型
    table=pd.DataFrame({"term":fit.params.index,"log_odds":fit.params.values,"std_error":fit.bse.values}) # 整理报告完整性模型系数
    table["odds_ratio"]=np.exp(table["log_odds"]) # 转换为报告完整性优势比
    table["ci_low"]=np.exp(table["log_odds"]-1.96*table["std_error"]) # 计算95%置信区间下限
    table["ci_high"]=np.exp(table["log_odds"]+1.96*table["std_error"]) # 计算95%置信区间上限
    table["p_value"]=fit.pvalues.values # 保存双侧检验P值
    table["outcome_field"]=outcome_field # 标记当前模型对应的报告字段
    table["n_observations"]=len(data) # 写入观察过程模型样本量
    table["n_reported"]=int(data["outcome_reported"].sum()) # 写入目标字段有值记录数
    table["event_year_iqr"]=pd.to_numeric(data["event_year"],errors="coerce").quantile(0.75)-pd.to_numeric(data["event_year"],errors="coerce").quantile(0.25) # 写入年份效应对应的原始四分位距
    log_gdp=np.log1p(pd.to_numeric(data["gdp_per_capita_ppp_constant_2021"],errors="coerce")) # 计算分析样本对数人均GDP
    table["log_gdp_iqr"]=log_gdp.quantile(0.75)-log_gdp.quantile(0.25) # 写入对数人均GDP效应对应的原始四分位距
    table["reference_source_grade"]="A" # 声明来源等级效应的参考类别
    table["reference_continent"]="Asia" # 声明洲际效应的参考类别
    return fit,table,data # 返回模型、结果表与观察过程分析样本
def consequence_association_model(events,outcome_field="injuries"): # 定义数值后果与建筑及事件属性的探索关联模型
    data=events.loc[events["analysis_extended"]].copy() # 使用扩展队列避免外部灾害触发事件
    height=pd.to_numeric(data["building_height_m_reported"],errors="coerce") # 读取明确报告的建筑高度
    storeys=pd.to_numeric(data["building_storeys_reported"],errors="coerce") # 读取明确报告的建筑层数
    data["height_rank"]=height.rank(pct=True) # 将高度转换为样本内百分位以消除单位差异
    data["storeys_rank"]=storeys.rank(pct=True) # 将层数转换为样本内百分位以消除单位差异
    data["building_scale_rank"]=data[["height_rank","storeys_rank"]].mean(axis=1,skipna=True) # 对可用高度和层数百分位取均值得到报告建筑规模指标
    data["building_scale_scaled"]=robust_scale(data["building_scale_rank"]) # 按四分位距缩放报告建筑规模指标
    data["event_year_10y"]=(pd.to_numeric(data["event_year"],errors="coerce")-2000)/10 # 将事件年份换算为每十年效应尺度
    data["log_gdp_scaled"]=robust_scale(np.log1p(pd.to_numeric(data["gdp_per_capita_ppp_constant_2021"],errors="coerce"))) # 将对数人均GDP按四分位距缩放
    data["outcome_numeric"]=pd.to_numeric(data[outcome_field],errors="coerce") # 将目标后果字段转换为数值
    data["log1p_outcome"]=np.log1p(data["outcome_numeric"]) # 对零值友好的后果计数取对数
    data["source_grade"]=data["source_grade"].fillna("Missing").astype(str) # 显式保留缺失来源等级
    data["continent"]=data["continent"].fillna("Missing").astype(str) # 显式保留缺失洲际类别
    data["construction_related"]=data["construction_related"].astype(int) # 将在建相关标志转换为模型数值
    data["facade_fire"]=data["facade_fire"].astype(int) # 将外立面火灾标志转换为模型数值
    data["arson_trigger"]=data["arson_trigger"].astype(int) # 将纵火触发标志转换为模型数值
    reporting_rate=float(data["outcome_numeric"].notna().mean()) # 计算扩展队列中的数值报告率
    if reporting_rate<0.95: # 仅在结局缺失足以支持模型时估计报告概率
        reporting_fit,reporting_table,reporting_data=reporting_completeness_model(events,outcome_field) # 拟合已验证的观察过程模型
        data.loc[reporting_data.index,"reporting_probability"]=reporting_fit.predict(reporting_data).clip(0.05,0.995) # 预测并截断数值报告概率以限制极端权重
        data["reporting_weight"]=reporting_rate/data["reporting_probability"] # 构造稳定化逆概率权重
        weighting="stabilized inverse-probability weighting" # 标记当前模型使用报告概率加权
    else: # 对接近完整报告的结局避免不稳定的稀少缺失模型
        data["reporting_probability"]=reporting_rate # 记录近完整的总体报告概率
        data["reporting_weight"]=1.0 # 对近完整报告结局使用等权分析
        weighting="unweighted because numeric reporting exceeded 95%" # 标记近完整结局不进行权重估计
    required=["log1p_outcome","building_scale_scaled","event_year_10y","log_gdp_scaled","reporting_weight","continent","source_grade"] # 声明探索模型完整案例字段
    sample=data.dropna(subset=required).copy() # 保留后果、建筑规模、时间和背景变量完整的记录
    lower=float(sample["reporting_weight"].quantile(0.01)) # 计算报告权重百分之一分位
    upper=float(sample["reporting_weight"].quantile(0.99)) # 计算报告权重百分之九十九分位
    sample["reporting_weight"]=sample["reporting_weight"].clip(lower,upper) # 截断极端报告权重以降低有限样本方差
    formula="log1p_outcome ~ building_scale_scaled + event_year_10y + log_gdp_scaled + construction_related + facade_fire + arson_trigger + C(source_grade) + C(continent)" # 定义预设的探索性关联模型
    fit=smf.wls(formula=formula,data=sample,weights=sample["reporting_weight"]).fit(cov_type="HC3") # 使用稳定化权重和异方差稳健标准误拟合对数线性模型
    table=pd.DataFrame({"term":fit.params.index,"log_ratio":fit.params.values,"std_error":fit.bse.values}) # 整理模型系数与稳健标准误
    table["multiplicative_ratio"]=np.exp(table["log_ratio"]) # 转换为报告后果加一几何均值比
    table["ci_low"]=np.exp(table["log_ratio"]-1.96*table["std_error"]) # 计算95%置信区间下限
    table["ci_high"]=np.exp(table["log_ratio"]+1.96*table["std_error"]) # 计算95%置信区间上限
    table["p_value"]=fit.pvalues.values # 保存双侧稳健检验P值
    table["outcome_field"]=outcome_field # 标记当前模型后果字段
    table["n_observations"]=len(sample) # 写入完整案例样本量
    table["n_positive"]=int(sample["outcome_numeric"].gt(0).sum()) # 写入正后果记录数
    table["reporting_rate"]=reporting_rate # 写入扩展队列数值报告率
    table["weighting"]=weighting # 写入观察过程处理方式
    table["effective_sample_size"]=float(sample["reporting_weight"].sum()**2/sample["reporting_weight"].pow(2).sum()) # 计算加权有效样本量
    table["outcome_transform"]="log(outcome + 1)" # 声明零值友好的结局变换
    table["building_scale_definition"]="mean percentile rank of reported height and storeys" # 声明报告建筑规模构造规则
    return fit,table,sample # 返回探索模型、效应量表与实际分析样本
def fire_service_capacity_sensitivity(events,metrics=("ctif_career_firefighters_per_100k","ctif_total_firefighters_per_100k","ctif_fire_stations_per_100k","ctif_fire_engines_per_100k")): # 定义CTIF消防服务能力与报告后果的多指标敏感性分析
    rows=[] # 初始化多后果与多能力指标效应量记录
    for outcome_field in ["deaths","injuries"]: # 分别分析数值死亡与受伤后果
        base_fit,base_table,base_sample=consequence_association_model(events,outcome_field) # 复用已核验的后果变换、协变量和报告权重流程
        for metric in metrics: # 遍历职业人员、全部人员、站点和车辆能力指标
            sample=base_sample.copy() # 复制当前后果的完整建筑与背景分析样本
            raw=pd.to_numeric(sample[metric],errors="coerce") # 读取当前CTIF每十万人能力指标
            sample["resource_capacity_scaled"]=robust_scale(np.log1p(raw)) # 对能力指标取对数并按四分位距缩放
            sample=sample.dropna(subset=["resource_capacity_scaled"]).copy() # 保留当前能力指标可匹配的事件
            formula="log1p_outcome ~ resource_capacity_scaled + building_scale_scaled + event_year_10y + log_gdp_scaled + construction_related + facade_fire + arson_trigger + C(source_grade) + C(continent)" # 定义单项消防服务能力敏感性模型
            fit=smf.wls(formula=formula,data=sample,weights=sample["reporting_weight"]).fit(cov_type="HC3") # 使用既定报告权重与稳健标准误拟合能力敏感性模型
            coefficient=float(fit.params["resource_capacity_scaled"]) # 提取当前能力指标对数线性系数
            standard_error=float(fit.bse["resource_capacity_scaled"]) # 提取当前能力指标稳健标准误
            rows.append({"outcome_field":outcome_field,"capacity_metric":metric,"effect_scale":"per IQR of log1p national capacity","log_ratio":coefficient,"std_error":standard_error,"multiplicative_ratio":float(np.exp(coefficient)),"ci_low":float(np.exp(coefficient-1.96*standard_error)),"ci_high":float(np.exp(coefficient+1.96*standard_error)),"p_value":float(fit.pvalues["resource_capacity_scaled"]),"n_observations":len(sample),"n_positive":int(sample["outcome_numeric"].gt(0).sum()),"n_countries":int(sample["iso3"].nunique()),"effective_sample_size":float(sample["reporting_weight"].sum()**2/sample["reporting_weight"].pow(2).sum()),"weighting":base_table["weighting"].iloc[0],"reference_period":"most recent national data reported during 2010-2023"}) # 保存能力效应、区间、样本和时间边界
    return pd.DataFrame(rows) # 返回全部消防服务能力敏感性结果
