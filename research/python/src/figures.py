from pathlib import Path # 导入跨平台路径工具
import time # 导入短时文件锁重试计时模块
import numpy as np # 导入数值计算模块
import pandas as pd # 导入表格处理模块
import matplotlib as mpl # 导入绘图配置模块
import matplotlib.pyplot as plt # 导入静态绘图模块
from matplotlib.colors import LinearSegmentedColormap,LogNorm,Normalize # 导入颜色映射与归一化工具
import cartopy.crs as ccrs # 导入全球地图投影模块
import cartopy.feature as cfeature # 导入海岸线与国界要素
HEAT_COLORS=["#F6D69A","#F0A66E","#DF705B","#B84850","#702B45"] # 定义克制的热暴露暖色带
POP_COLORS=["#F4F2ED","#D5E2E5","#A7C9D0","#739EAD","#416B82","#173D55"] # 定义低饱和人口蓝灰色带
NEUTRAL="#6F6F6F" # 定义中性文本颜色
def set_nature_style(): # 定义Nature风格全局绘图参数
    mpl.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","Helvetica","DejaVu Sans","sans-serif"],"font.size":7,"axes.titlesize":7,"axes.labelsize":7,"xtick.labelsize":6,"ytick.labelsize":6,"axes.linewidth":0.65,"axes.spines.top":False,"axes.spines.right":False,"legend.frameon":False,"svg.fonttype":"none","pdf.fonttype":42,"savefig.facecolor":"white"}) # 应用字体、线宽和可编辑矢量文本设置
def _panel_label(axis,label): # 定义统一分面标签函数
    axis.text(-0.04,1.04,label,transform=axis.transAxes,ha="left",va="bottom",fontsize=8,fontweight="bold",color="#202020") # 在分面左上角放置小写粗体标签
def _save_formats(fig,stem): # 定义多格式出版输出函数
    stem=Path(stem) # 标准化输出文件前缀
    stem.parent.mkdir(parents=True,exist_ok=True) # 确保图件输出目录存在
    specifications=[(".svg",{}),(".pdf",{}),(".png",{"dpi":400}),(".tiff",{"dpi":600})] # 定义矢量与高分辨率出版格式
    for extension,options in specifications: # 逐格式执行带文件锁重试的保存
        for attempt in range(1,6): # 每种格式最多尝试五次
            try: fig.savefig(stem.with_suffix(extension),bbox_inches="tight",**options);break # 成功写入当前格式后继续下一格式
            except PermissionError: # 捕获Windows预览器或索引服务造成的短时文件锁
                if attempt==5: raise # 最后一次仍失败时保留真实异常
                time.sleep(attempt) # 递增等待后重试当前格式
    return [str(stem.with_suffix(extension)) for extension in [".svg",".pdf",".png",".tiff"]] # 返回全部图件路径
def make_figure_1(events,output_stem): # 定义全球分布与数据边界主图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出前缀
    root=output_stem.parents[2] # 定位代码项目根目录
    source_dir=root/"outputs/tables" # 定义逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    data=events.copy() # 复制事件数据避免修改输入
    data["event_date"]=pd.to_datetime(data["event_date"],errors="coerce") # 标准化事件日期
    data["event_year"]=pd.to_numeric(data["event_year"],errors="coerce") # 标准化事件年份
    data["latitude"]=pd.to_numeric(data["latitude"],errors="coerce") # 标准化纬度
    data["longitude"]=pd.to_numeric(data["longitude"],errors="coerce") # 标准化经度
    data["heatwave_score_0_100"]=pd.to_numeric(data.get("heatwave_score_0_100"),errors="coerce") # 标准化热暴露百分位
    data["population_count_2020_1km_cell"]=pd.to_numeric(data.get("population_count_2020_1km_cell"),errors="coerce") # 标准化一公里人口数量
    mapped=data.loc[data["latitude"].between(-90,90)&data["longitude"].between(-180,180)].copy() # 保留坐标有效事件
    mapped.to_csv(source_dir/"Figure_1a_event_map.csv",index=False,encoding="utf-8-sig") # 输出地图分面源数据
    fig=plt.figure(figsize=(7.2,5.75),constrained_layout=False) # 创建双栏宽度不对称复合图
    grid=fig.add_gridspec(2,3,height_ratios=[3.25,1.15],left=0.045,right=0.98,bottom=0.10,top=0.92,hspace=0.34,wspace=0.38) # 定义主地图与三项支持证据布局
    axis_map=fig.add_subplot(grid[0,:],projection=ccrs.Robinson()) # 创建跨三列全球主地图
    axis_map.set_global() # 设置完整全球范围
    axis_map.add_feature(cfeature.LAND.with_scale("110m"),facecolor="#F2F1EE",edgecolor="none",zorder=0) # 绘制克制陆地底色
    axis_map.add_feature(cfeature.OCEAN.with_scale("110m"),facecolor="white",edgecolor="none",zorder=0) # 绘制白色海洋
    population_path=root/"data/interim/gpw2020_population_count_global.png" # 指定旧GEE导出的人口显示层
    if population_path.exists(): axis_map.imshow(plt.imread(population_path),origin="upper",extent=[-180,180,-90,90],transform=ccrs.PlateCarree(),interpolation="bilinear",zorder=0.5,alpha=0.92) # 投影显示GPW约一公里原生人口像元的金字塔预览
    axis_map.add_feature(cfeature.COASTLINE.with_scale("110m"),edgecolor="#8D8B87",linewidth=0.32,zorder=1) # 叠加海岸线
    axis_map.add_feature(cfeature.BORDERS.with_scale("110m"),edgecolor="#C6C3BE",linewidth=0.16,zorder=1) # 弱化显示国界
    heat_cmap=LinearSegmentedColormap.from_list("heat_exposure",HEAT_COLORS) # 构造热暴露连续色带
    missing=mapped["heatwave_score_0_100"].isna() # 标记尚未完成当前GEE增强的事件
    axis_map.scatter(mapped.loc[missing,"longitude"],mapped.loc[missing,"latitude"],s=8,c="#9A9A9A",alpha=0.42,edgecolors="white",linewidths=0.25,transform=ccrs.PlateCarree(),zorder=2,label="Metric pending") # 以中性灰显示待补充指标事件
    scored=mapped.loc[~missing].copy() # 提取已有热暴露指标事件
    sizes=8+25*np.power(scored["heatwave_score_0_100"].clip(0,100).to_numpy()/100,0.8) # 使热暴露百分位越高的气泡越大
    points=axis_map.scatter(scored["longitude"],scored["latitude"],s=sizes,c=scored["heatwave_score_0_100"],cmap=heat_cmap,norm=Normalize(0,100),alpha=0.45+0.48*np.power(scored["heatwave_score_0_100"].clip(0,100).to_numpy()/100,0.8),edgecolors="white",linewidths=0.3,transform=ccrs.PlateCarree(),zorder=3) # 以渐变色、透明度和面积共同编码热暴露
    top=scored.nlargest(5,"heatwave_score_0_100").copy() # 选择热暴露百分位最高的五个事件城市
    offsets=[(8,8),(8,-10),(-8,9),(-8,-10),(10,0)] # 定义交替标签偏移以降低遮挡
    for offset,(_,row) in zip(offsets,top.iterrows()): axis_map.annotate(str(row["city_label_en"]),xy=(row["longitude"],row["latitude"]),xycoords=ccrs.PlateCarree()._as_mpl_transform(axis_map),xytext=offset,textcoords="offset points",ha="left" if offset[0]>0 else "right",va="center",fontsize=4.8,color="#222222",arrowprops={"arrowstyle":"-","color":"#777777","linewidth":0.35},zorder=5) # 使用黑色英文标注五个最高热暴露城市
    hong_kong=mapped.loc[mapped["city_label_en"].astype(str).str.contains("Hong Kong",case=False,na=False)] # 筛选香港事件记录
    if not hong_kong.empty: axis_map.annotate("Hong Kong",xy=(hong_kong["longitude"].median(),hong_kong["latitude"].median()),xycoords=ccrs.PlateCarree()._as_mpl_transform(axis_map),xytext=(18,-14),textcoords="offset points",ha="left",va="center",fontsize=4.8,color="#222222",arrowprops={"arrowstyle":"-","color":"#777777","linewidth":0.35},zorder=5) # 在数据存在时使用黑色英文标注香港
    axis_map.spines["geo"].set_edgecolor("#AAA7A1") # 设置地图外框颜色
    axis_map.spines["geo"].set_linewidth(0.45) # 设置地图外框线宽
    _panel_label(axis_map,"a") # 添加地图分面标签
    heat_axis=fig.add_axes([0.61,0.405,0.24,0.014]) # 在地图下方建立热暴露色条
    heat_bar=fig.colorbar(points,cax=heat_axis,orientation="horizontal") # 绘制热暴露连续图例
    heat_bar.set_ticks([0,25,50,75,100]) # 设置指定热暴露刻度
    heat_bar.set_label("7-day heat-exceedance score (0–100)",fontsize=5.6,labelpad=2) # 标注与旧增强表一致的描述性热暴露评分
    heat_bar.ax.tick_params(labelsize=5,length=1.5,width=0.4) # 设置紧凑色条刻度
    pop_axis=fig.add_axes([0.17,0.405,0.24,0.014]) # 在地图下方建立人口色条
    pop_scalar=mpl.cm.ScalarMappable(norm=Normalize(0,5),cmap=LinearSegmentedColormap.from_list("population",POP_COLORS)) # 构造一公里人口数量对数图例
    pop_bar=fig.colorbar(pop_scalar,cax=pop_axis,orientation="horizontal") # 绘制人口数量色条
    pop_bar.set_ticks([0,1,2,3,4,5]) # 设置人口数量对数刻度
    pop_bar.set_ticklabels(["1","10","100","1k","10k","100k"]) # 使用每像元人口数量标签
    pop_bar.set_label("Population count per ~1-km cell (GPW 2020)",fontsize=5.6,labelpad=2) # 标注人口栅格含义
    pop_bar.ax.tick_params(labelsize=5,length=1.5,width=0.4) # 设置紧凑人口色条刻度
    axis_trend=fig.add_subplot(grid[1,0]) # 创建年度记录趋势分面
    yearly=data.groupby("event_year").agg(all_events=("event_id","size"),core_events=("analysis_core","sum")).reset_index() # 汇总全量与核心队列年度记录数
    yearly.to_csv(source_dir/"Figure_1b_annual_records.csv",index=False,encoding="utf-8-sig") # 输出年度趋势源数据
    axis_trend.plot(yearly["event_year"],yearly["all_events"],color="#4F6072",linewidth=1.2,label="All documented") # 绘制全量记录年度趋势
    axis_trend.plot(yearly["event_year"],yearly["core_events"],color="#B84850",linewidth=1.2,label="Core cohort") # 绘制核心队列年度趋势
    axis_trend.axvspan(2025,2026.5,color="#D9D7D2",alpha=0.45,zorder=0) # 标记近期数据库扩展年份
    axis_trend.set_xlabel("Event year") # 标注年份横轴
    axis_trend.set_ylabel("Documented events") # 标注记录事件数量
    axis_trend.set_title("Recording intensity") # 设置年度记录分面标题
    axis_trend.legend(fontsize=5.2,loc="upper left") # 添加紧凑共享图例
    _panel_label(axis_trend,"b") # 添加年度趋势分面标签
    axis_heat=fig.add_subplot(grid[1,1]) # 创建热暴露分布分面
    heat_values=scored["heatwave_score_0_100"].dropna().clip(0,100) # 提取已有事件日热暴露百分位
    heat_source=pd.DataFrame({"heatwave_score_0_100":heat_values}) # 整理热暴露分面源数据
    heat_source.to_csv(source_dir/"Figure_1c_heat_exposure.csv",index=False,encoding="utf-8-sig") # 输出热暴露分布源数据
    bins=np.linspace(0,100,11) # 定义十个等宽热暴露百分位区间
    counts,edges=np.histogram(heat_values,bins=bins) # 计算事件热暴露频数
    centers=(edges[:-1]+edges[1:])/2 # 计算柱形中心位置
    axis_heat.bar(centers,counts,width=9,color=heat_cmap(centers/100),edgecolor="white",linewidth=0.35) # 使用同一暖色带显示热暴露分布
    axis_heat.set_xticks([0,25,50,75,100]) # 设置热暴露横轴刻度
    axis_heat.set_xlabel("7-day heat-exceedance score") # 标注热暴露横轴
    axis_heat.set_ylabel("Documented events") # 标注事件频数纵轴
    axis_heat.set_title("Heat-exposure profile") # 设置热暴露分面标题
    _panel_label(axis_heat,"c") # 添加热暴露分面标签
    axis_cohort=fig.add_subplot(grid[1,2]) # 创建事件队列分面
    cohort=pd.DataFrame({"stage":["All records","Geocoded","No external trigger","Core cohort"],"n":[len(data),int(data["valid_geocode"].sum()),int(data["analysis_extended"].sum()),int(data["analysis_core"].sum())]}) # 汇总队列筛选各阶段样本量
    cohort.to_csv(source_dir/"Figure_1d_cohort.csv",index=False,encoding="utf-8-sig") # 输出队列筛选源数据
    positions=np.arange(len(cohort))[::-1] # 定义自上而下队列位置
    colors=["#B9C5CC","#9CB2BE","#748F9E","#3D6579"] # 定义同一家族队列颜色
    axis_cohort.barh(positions,cohort["n"],color=colors,height=0.62) # 绘制队列样本量横向条形图
    axis_cohort.set_yticks(positions,cohort["stage"]) # 设置队列阶段标签
    axis_cohort.set_xlabel("Events") # 标注事件数量横轴
    axis_cohort.set_title("Analytical cohort") # 设置队列分面标题
    for y,value in zip(positions,cohort["n"]): axis_cohort.text(value+max(cohort["n"])*0.025,y,str(value),va="center",fontsize=5.8,color=NEUTRAL) # 在条形末端标注样本量
    axis_cohort.set_xlim(0,max(cohort["n"])*1.18) # 为样本量标签预留右侧空间
    _panel_label(axis_cohort,"d") # 添加队列分面标签
    fig.suptitle("Documented high-rise building fires across global population and heat gradients",x=0.51,y=0.975,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置主图标题
    fig.text(0.045,0.025,"Population uses native ~1-km GPW cells; event heat metrics combine 148 exact date-coordinate matches with 85 newly processed GEE records.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 透明说明人口显示与事件级指标来源
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回主图输出路径
def make_figure_2(case_control,primary_table,sensitivity_table,output_stem): # 定义病例交叉主效应与稳健性图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出前缀
    root=output_stem.parents[2] # 定位代码项目根目录
    source_dir=root/"outputs/tables" # 定义逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    data=case_control.dropna(subset=["case","tmax_anomaly_c"]).copy() # 保留病例对照与温度异常均完整的观测
    data["case_label"]=np.where(pd.to_numeric(data["case"],errors="coerce").eq(1),"Event day","Matched control day") # 生成人类可读的病例对照标签
    exposure_source=data[["event_id","stratum_id","date","case","case_label","tmax_anomaly_c","heatwave_indicator"]].copy() # 整理暴露分布分面源数据
    exposure_source.to_csv(source_dir/"Figure_2a_matched_exposure.csv",index=False,encoding="utf-8-sig") # 输出暴露分布分面源数据
    primary=primary_table.copy() # 复制主模型结果避免修改输入
    primary.to_csv(source_dir/"Figure_2b_primary_model.csv",index=False,encoding="utf-8-sig") # 输出主模型分面源数据
    sensitivity=sensitivity_table.copy() # 复制多定义稳健性结果
    sensitivity.to_csv(source_dir/"Figure_2c_heat_definitions.csv",index=False,encoding="utf-8-sig") # 输出敏感性分面源数据
    fig=plt.figure(figsize=(7.2,3.65),constrained_layout=False) # 创建Nature双栏宽度定量复合图
    grid=fig.add_gridspec(1,3,width_ratios=[1.18,1.0,1.18],left=0.08,right=0.98,bottom=0.20,top=0.84,wspace=0.55) # 定义暴露分布、主模型与稳健性布局
    axis_exposure=fig.add_subplot(grid[0,0]) # 创建事件日与对照日暴露分布分面
    bins=np.linspace(data["tmax_anomaly_c"].quantile(0.01),data["tmax_anomaly_c"].quantile(0.99),25) # 使用稳健范围定义共同直方图区间
    for label,color in [("Matched control day","#7894A3"),("Event day","#B84850")]: # 遍历对照日与事件日颜色体系
        values=data.loc[data["case_label"].eq(label),"tmax_anomaly_c"] # 提取当前组的温度异常
        axis_exposure.hist(values,bins=bins,density=True,histtype="step",linewidth=1.25,color=color,label=f"{label} (n={len(values)})") # 绘制可比较的概率密度轮廓
        axis_exposure.axvline(values.median(),color=color,linewidth=0.75,linestyle="--") # 标记当前组中位数
    axis_exposure.axvline(0,color="#B8B5B0",linewidth=0.7,zorder=0) # 标记局地第90百分位参考线
    axis_exposure.set_xlabel("Daily maximum-temperature anomaly (°C)") # 标注相对局地第90百分位的温度异常
    axis_exposure.set_ylabel("Probability density") # 标注归一化概率密度纵轴
    axis_exposure.set_title("Matched exposure contrast") # 设置暴露对比分面标题
    axis_exposure.legend(fontsize=5.3,loc="upper left") # 添加病例对照图例与观测数
    _panel_label(axis_exposure,"a") # 添加暴露分布分面标签
    axis_primary=fig.add_subplot(grid[0,1]) # 创建主条件Logit效应量分面
    label_map={"heatwave_indicator":"Heatwave","dewpoint_c":"Dew point","precipitation_mm":"Precipitation","wind_speed_ms":"Wind speed"} # 定义主模型变量显示名称
    primary["display_label"]=primary["variable"].map(label_map).fillna(primary["variable"]) # 生成人类可读的主模型标签
    primary=primary.iloc[::-1].reset_index(drop=True) # 反转结果顺序以自上而下显示主暴露
    positions=np.arange(len(primary)) # 定义主模型效应量纵向位置
    axis_primary.errorbar(primary["odds_ratio"],positions,xerr=[primary["odds_ratio"]-primary["ci_low"],primary["ci_high"]-primary["odds_ratio"]],fmt="o",color="#355F73",ecolor="#7894A3",elinewidth=0.9,capsize=2,markersize=4) # 绘制优势比与95%置信区间
    axis_primary.axvline(1,color="#B8B5B0",linewidth=0.7,zorder=0) # 标记无效应优势比参考线
    axis_primary.set_xscale("log") # 使用对数尺度保证比值效应对称显示
    axis_primary.set_xlim(0.2,2.4) # 固定涵盖主模型全部置信区间的紧凑范围
    axis_primary.set_xticks([0.25,0.5,1,2],labels=["0.25","0.5","1","2"]) # 设置不重叠的解释性优势比刻度
    axis_primary.minorticks_off() # 关闭密集对数次刻度避免标签拥挤
    axis_primary.set_yticks(positions,primary["display_label"]) # 设置主模型变量标签
    axis_primary.set_xlabel("Odds ratio (95% CI)") # 标注主模型效应量横轴
    axis_primary.set_title("Primary model") # 设置主模型分面标题
    _panel_label(axis_primary,"b") # 添加主模型分面标签
    axis_sensitivity=fig.add_subplot(grid[0,2]) # 创建热浪定义敏感性分面
    definition_labels={"heatwave_indicator":"P90, 3 d, 30 °C floor","hw_p85_3d":"P85, 3 d, 30 °C floor","hw_p90_2d":"P90, 2 d, 30 °C floor","hw_p90_4d":"P90, 4 d, 30 °C floor","hw_p95_3d":"P95, 3 d, 30 °C floor","hw_p90_3d_no_floor":"P90, 3 d, no floor"} # 定义热浪敏感性标签
    sensitivity["display_label"]=sensitivity["definition"].map(definition_labels).fillna(sensitivity["definition"]) # 生成人类可读的热浪定义标签
    sensitivity=sensitivity.iloc[::-1].reset_index(drop=True) # 反转定义顺序以突出顶部主定义
    sensitivity_positions=np.arange(len(sensitivity)) # 定义敏感性效应量纵向位置
    colors=np.where(sensitivity["definition"].eq("heatwave_indicator"),"#B84850","#7894A3") # 使用信号色突出预设主定义
    for index,row in sensitivity.iterrows(): axis_sensitivity.errorbar(row["odds_ratio"],sensitivity_positions[index],xerr=[[row["odds_ratio"]-row["ci_low"]],[row["ci_high"]-row["odds_ratio"]]],fmt="o",color=colors[index],ecolor=colors[index],elinewidth=0.9,capsize=2,markersize=4) # 绘制各热浪定义优势比与95%置信区间
    axis_sensitivity.axvline(1,color="#B8B5B0",linewidth=0.7,zorder=0) # 标记无效应优势比参考线
    axis_sensitivity.set_xscale("log") # 使用对数尺度显示比值效应
    axis_sensitivity.set_xlim(0.04,4.0) # 固定涵盖全部定义置信区间的显示范围
    axis_sensitivity.set_xticks([0.05,0.1,0.5,1,2,4],labels=["0.05","0.1","0.5","1","2","4"]) # 设置可解释的敏感性优势比刻度
    axis_sensitivity.minorticks_off() # 关闭对数次刻度保持面板简洁
    axis_sensitivity.set_yticks(sensitivity_positions,sensitivity["display_label"]) # 设置热浪定义标签
    axis_sensitivity.set_xlabel("Heatwave odds ratio (95% CI)") # 标注敏感性效应量横轴
    axis_sensitivity.set_title("Definition sensitivity") # 设置热浪定义敏感性标题
    _panel_label(axis_sensitivity,"c") # 添加敏感性分面标签
    fig.suptitle("Short-term heat exposure on documented high-rise fire event days",x=0.52,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置病例交叉图标题
    fig.text(0.08,0.055,"Time-stratified case-crossover design; controls share location, calendar month and weekday. Points are adjusted estimates and bars are 95% confidence intervals.",ha="left",va="bottom",fontsize=5.3,color=NEUTRAL) # 说明匹配设计、调整估计与不确定性
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回病例交叉图输出路径
def make_supplementary_figure_1(events,output_stem): # 定义记录结构与分析完整性补充图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出前缀
    root=output_stem.parents[2] # 定位代码项目根目录
    source_dir=root/"outputs/tables" # 定义逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    data=events.copy() # 复制事件数据避免修改输入
    fig=plt.figure(figsize=(7.2,3.45),constrained_layout=False) # 创建Nature双栏宽度补充图
    grid=fig.add_gridspec(1,3,width_ratios=[1.08,0.92,1.28],left=0.08,right=0.98,bottom=0.22,top=0.82,wspace=0.55) # 定义地区、来源与缺失性三分面布局
    axis_geo=fig.add_subplot(grid[0,0]) # 创建洲际记录结构分面
    continent_labels={"亚洲":"Asia","欧洲":"Europe","北美洲":"North America","南美洲":"South America","非洲":"Africa","大洋洲":"Oceania"} # 定义洲际英文投稿标签
    data["continent_display"]=data["continent"].map(continent_labels).fillna(data["continent"]) # 将中文洲际标签转换为英文并保留未知原值
    geography=data.groupby("continent_display",dropna=False).agg(all_events=("event_id","size"),core_events=("analysis_core","sum")).reset_index().rename(columns={"continent_display":"continent"}) # 汇总各洲全量与核心队列记录
    geography["other_events"]=geography["all_events"]-geography["core_events"] # 计算非核心记录数量
    geography=geography.sort_values("all_events",ascending=True).reset_index(drop=True) # 按总记录数量排序
    geography.to_csv(source_dir/"Figure_S1a_geographic_coverage.csv",index=False,encoding="utf-8-sig") # 输出洲际覆盖分面源数据
    geo_positions=np.arange(len(geography)) # 定义洲际条形位置
    axis_geo.barh(geo_positions,geography["core_events"],color="#355F73",height=0.65,label="Core cohort") # 绘制核心队列记录数量
    axis_geo.barh(geo_positions,geography["other_events"],left=geography["core_events"],color="#C9D2D6",height=0.65,label="Other records") # 堆叠绘制其余记录数量
    axis_geo.set_yticks(geo_positions,geography["continent"].fillna("Missing")) # 设置洲际标签
    axis_geo.set_xlabel("Documented events") # 标注记录事件数量横轴
    axis_geo.set_title("Geographic coverage") # 设置洲际覆盖标题
    axis_geo.legend(fontsize=5.2,loc="lower right") # 添加队列构成图例
    _panel_label(axis_geo,"a") # 添加洲际覆盖分面标签
    axis_source=fig.add_subplot(grid[0,1]) # 创建来源等级分面
    source=data.groupby("source_grade",dropna=False).agg(n_events=("event_id","size"),core_share=("analysis_core","mean")).reset_index() # 汇总来源等级数量与核心纳入比例
    source["source_grade"]=source["source_grade"].fillna("Missing").astype(str) # 显式显示缺失来源等级
    source=source.sort_values("n_events",ascending=True).reset_index(drop=True) # 按来源记录数量排序
    source.to_csv(source_dir/"Figure_S1b_source_grade.csv",index=False,encoding="utf-8-sig") # 输出来源等级分面源数据
    source_positions=np.arange(len(source)) # 定义来源等级条形位置
    source_colors=plt.get_cmap("Blues")(0.30+0.60*source["core_share"].fillna(0).to_numpy()) # 使用蓝色深浅编码核心队列纳入比例
    axis_source.barh(source_positions,source["n_events"],color=source_colors,height=0.65) # 绘制各来源等级记录数量
    axis_source.set_yticks(source_positions,source["source_grade"]) # 设置来源等级标签
    axis_source.set_xlabel("Documented events") # 标注来源记录数量横轴
    axis_source.set_title("Source structure") # 设置来源结构标题
    _panel_label(axis_source,"b") # 添加来源结构分面标签
    axis_missing=fig.add_subplot(grid[0,2]) # 创建关键变量缺失性分面
    missing_fields={"Deaths":"deaths","Injuries":"injuries","Evacuated":"evacuated","Population cell":"population_count_2020_1km_cell","7-day heat score":"heatwave_score_0_100","Built volume":"ghsl_built_volume_m3_1km","Country-year context":"context_year"} # 定义报告与外部增强关键字段
    missing=pd.DataFrame({"variable":list(missing_fields),"field":list(missing_fields.values())}) # 创建缺失性字段映射表
    missing["n_available"]=missing["field"].map(lambda column:int(pd.to_numeric(data[column],errors="coerce").notna().sum())) # 计算各字段有效观测数量
    missing["n_missing"]=len(data)-missing["n_available"] # 计算各字段缺失观测数量
    missing["percent_missing"]=missing["n_missing"].div(len(data)).mul(100) # 计算各字段缺失比例
    missing=missing.sort_values("percent_missing",ascending=True).reset_index(drop=True) # 按缺失比例排序
    missing.to_csv(source_dir/"Figure_S1c_missingness.csv",index=False,encoding="utf-8-sig") # 输出缺失性分面源数据
    missing_positions=np.arange(len(missing)) # 定义缺失性条形位置
    missing_colors=plt.get_cmap("OrRd")(0.20+0.65*missing["percent_missing"].div(100).to_numpy()) # 使用暖色深浅编码缺失比例
    axis_missing.barh(missing_positions,missing["percent_missing"],color=missing_colors,height=0.65) # 绘制关键字段缺失比例
    axis_missing.set_yticks(missing_positions,missing["variable"]) # 设置关键变量标签
    axis_missing.set_xlim(0,100) # 固定缺失比例横轴范围
    axis_missing.set_xticks([0,25,50,75,100]) # 设置统一百分比刻度
    axis_missing.set_xlabel("Missing observations (%)") # 标注缺失比例横轴
    axis_missing.set_title("Analytical completeness") # 设置分析完整性标题
    _panel_label(axis_missing,"c") # 添加缺失性分面标签
    fig.suptitle("Reporting structure and analytical completeness",x=0.52,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置补充图标题
    fig.text(0.08,0.055,"Missing means unavailable, not zero. GEE fields are complete for all 233 valid coordinates; five case-crossover strata use a documented 20-km coastal fallback.",ha="left",va="bottom",fontsize=5.3,color=NEUTRAL) # 说明缺失值语义与沿海采样边界
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回补充图输出路径
def make_supplementary_figure_2(sensitivity_table,output_stem): # 定义独立气象产品热浪敏感性森林图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    labels={"heatwave_indicator":"P90, 3 days + 30 °C floor (primary)","hw_p85_3d":"P85, 3 days + 30 °C floor","hw_p90_2d":"P90, 2 days + 30 °C floor","hw_p90_4d":"P90, 4 days + 30 °C floor","hw_p95_3d":"P95, 3 days + 30 °C floor","hw_p90_3d_no_floor":"P90, 3 days, no floor"} # 定义预设热浪方案显示标签
    order=list(labels) # 固定方案顺序以避免结果驱动排序
    data=sensitivity_table.loc[sensitivity_table["definition"].isin(order)].copy() # 保留预设独立产品敏感性结果
    data["definition_order"]=pd.Categorical(data["definition"],categories=order,ordered=True) # 写入预设方案顺序
    data=data.sort_values("definition_order").reset_index(drop=True) # 按预设顺序排列效应量
    data["definition_label"]=data["definition"].map(labels) # 生成人类可读方案标签
    data.to_csv(source_dir/"Figure_S2_weather_product_sensitivity.csv",index=False,encoding="utf-8-sig") # 输出森林图逐点源数据
    positions=np.arange(len(data))[::-1] # 定义自上而下的效应量位置
    information=pd.to_numeric(data["n_informative_strata"],errors="coerce").fillna(0) # 读取每个定义的有效分层数
    denominator=max(float(information.max()-information.min()),1.0) # 构造稳定的颜色归一化分母
    colors=LinearSegmentedColormap.from_list("heat_sensitivity",["#E9C9B2","#C96A58","#71324A"])((information-information.min())/denominator) # 使用低饱和暖色梯度编码有效分层数
    fig,axis=plt.subplots(figsize=(7.2,2.8),constrained_layout=False) # 创建Nature双栏宽度单面板森林图
    fig.subplots_adjust(left=0.36,right=0.94,bottom=0.24,top=0.80) # 为长标签、脚注和居中标题预留空间
    axis.axvline(1.0,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联参考线
    for index,row in data.iterrows(): # 逐方案绘制效应量及置信区间
        y=positions[index] # 读取当前方案纵向位置
        axis.plot([row["ci_low"],row["ci_high"]],[y,y],color=colors[index],linewidth=1.7,solid_capstyle="round",zorder=2) # 绘制95%置信区间
        marker="D" if row["definition"]=="heatwave_indicator" else "o" # 使用菱形突出主定义
        axis.scatter(row["odds_ratio"],y,s=32+1.2*row["n_informative_strata"],marker=marker,color=colors[index],edgecolor="white",linewidth=0.6,zorder=3) # 用气泡大小编码有效分层数
        axis.text(8.55,y,f"{int(row['n_informative_strata'])}",ha="center",va="center",fontsize=6,color="#333333") # 在右侧标注有效分层数
    axis.set_xscale("log") # 使用对数尺度保持优势比区间对称解释
    axis.set_xlim(0.2,10.0) # 固定能够容纳全部预设区间的横轴范围
    axis.set_xticks([0.25,0.5,1,2,4,8],labels=["0.25","0.5","1","2","4","8"]) # 设置便于阅读的优势比刻度
    axis.set_yticks(positions,data["definition_label"]) # 设置热浪定义纵轴标签
    axis.set_xlabel("Adjusted odds ratio for a documented event day (95% CI)") # 标注条件Logit效应量横轴
    axis.set_title("Independent weather-product sensitivity",loc="center",fontsize=9,fontweight="bold",pad=10,color="#202020") # 居中设置森林图标题
    axis.text(8.55,positions.max()+0.72,"Informative\nstrata",ha="center",va="bottom",fontsize=5.5,color=NEUTRAL) # 添加有效分层数列标题
    axis.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
    axis.tick_params(axis="y",length=0) # 去除标签附近多余刻度线
    fig.text(0.36,0.075,"NASA POWER MERRA-2/GEOS-IT, local solar time; conditional logistic models adjust for dewpoint, precipitation and wind. Points are estimates; bars are 95% Wald CIs.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 说明产品、设计、协变量与不确定性
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回补充森林图输出路径
def make_figure_3(events,injury_model,evacuation_model,output_stem): # 定义后果记录与观察过程主图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    data=events.copy() # 复制事件数据避免修改输入
    outcome_labels={"deaths":"Deaths","injuries":"Injuries","evacuated":"Evacuated"} # 定义后果字段显示标签
    state_rows=[] # 初始化后果可观察状态记录
    for field,label in outcome_labels.items(): # 遍历死亡、受伤与疏散字段
        values=pd.to_numeric(data[field],errors="coerce") # 将当前后果字段转换为数值
        state_rows.extend([{"outcome":label,"state":"Missing","n_events":int(values.isna().sum())},{"outcome":label,"state":"Reported zero","n_events":int(values.eq(0).sum())},{"outcome":label,"state":"Reported positive","n_events":int(values.gt(0).sum())}]) # 汇总缺失、零值和正值记录数
    states=pd.DataFrame(state_rows) # 创建后果可观察状态源数据表
    states.to_csv(source_dir/"Figure_3a_outcome_observability.csv",index=False,encoding="utf-8-sig") # 输出后果可观察状态源数据
    continent_labels={"亚洲":"Asia","欧洲":"Europe","北美洲":"North America","南美洲":"South America","非洲":"Africa","大洋洲":"Oceania"} # 定义洲际英文显示标签
    data["continent_display"]=data["continent"].map(continent_labels).fillna(data["continent"]) # 统一洲际英文标签
    geography_rows=[] # 初始化洲际报告完整性记录
    for continent,group in data.groupby("continent_display",dropna=False): # 遍历各洲记录
        for field,label in outcome_labels.items(): geography_rows.append({"continent":continent,"outcome":label,"n_events":len(group),"n_numeric":int(pd.to_numeric(group[field],errors="coerce").notna().sum()),"percent_numeric":float(pd.to_numeric(group[field],errors="coerce").notna().mean()*100)}) # 计算当前洲际后果字段数值报告比例
    geography=pd.DataFrame(geography_rows) # 创建洲际报告完整性源数据表
    geography.to_csv(source_dir/"Figure_3b_geographic_reporting.csv",index=False,encoding="utf-8-sig") # 输出洲际报告完整性源数据
    selected_terms={"event_year_scaled":"Event year\n(per 10 years)","log_gdp_scaled":"Log GDP per capita\n(per IQR)","C(source_grade)[T.B]":"Grade B vs A\nsource","C(source_grade)[T.C]":"Grade C vs A\nsource"} # 定义观察过程关键协变量标签
    model=pd.concat([injury_model.assign(outcome="Injuries"),evacuation_model.assign(outcome="Evacuated")],ignore_index=True) # 合并两个观察过程模型结果
    model=model.loc[model["term"].isin(selected_terms)].copy() # 保留预设时间、经济与来源等级项
    model["predictor"]=model["term"].map(selected_terms) # 生成人类可读协变量标签
    model.to_csv(source_dir/"Figure_3c_observation_process.csv",index=False,encoding="utf-8-sig") # 输出观察过程森林图源数据
    fig=plt.figure(figsize=(7.2,3.45),constrained_layout=False) # 创建Nature双栏宽度三分面主图
    grid=fig.add_gridspec(1,3,width_ratios=[0.95,1.05,1.55],left=0.07,right=0.985,bottom=0.27,top=0.80,wspace=0.62) # 抬高分面为横排状态图例和脚注预留独立空间
    axis_state=fig.add_subplot(grid[0,0]) # 创建后果可观察状态分面
    outcomes=list(outcome_labels.values()) # 固定后果显示顺序
    positions=np.arange(len(outcomes)) # 定义后果条形纵向位置
    left=np.zeros(len(outcomes)) # 初始化堆叠条形左边界
    state_colors={"Missing":"#D8D6D0","Reported zero":"#9CC2D1","Reported positive":"#D86A51"} # 定义缺失、零值与正值颜色
    for state in state_colors: # 按预设顺序绘制三类记录状态
        values=np.array([int(states.loc[states["outcome"].eq(outcome)&states["state"].eq(state),"n_events"].iloc[0]) for outcome in outcomes]) # 读取各后果当前状态数量
        axis_state.barh(positions,values,left=left,height=0.62,color=state_colors[state],label=state) # 绘制水平堆叠条形
        left+=values # 更新下一状态堆叠起点
    axis_state.set_yticks(positions,outcomes) # 设置后果名称标签
    axis_state.invert_yaxis() # 将死亡字段放置在顶部
    axis_state.set_xlim(0,len(data)) # 固定横轴为全部事件数
    axis_state.set_xlabel("Documented events") # 标注事件数量横轴
    axis_state.set_title("Outcome observability") # 设置后果可观察性标题
    axis_state.legend(fontsize=4.6,loc="upper center",bbox_to_anchor=(0.5,-0.26),ncol=3,columnspacing=0.8,handlelength=1.2) # 在横轴下方横排记录状态图例以避免遮挡柱体
    _panel_label(axis_state,"a") # 添加后果状态分面标签
    axis_geo=fig.add_subplot(grid[0,1]) # 创建洲际报告完整性热图分面
    continent_order=data["continent_display"].value_counts().index.tolist() # 按事件数量固定洲际顺序
    matrix=geography.pivot(index="continent",columns="outcome",values="percent_numeric").reindex(index=continent_order,columns=outcomes) # 构造洲际与后果字段报告率矩阵
    image=axis_geo.imshow(matrix.to_numpy(),cmap=LinearSegmentedColormap.from_list("reporting",["#F2EFEA","#9CC2D1","#315F73"]),vmin=0,vmax=100,aspect="auto") # 绘制低饱和报告完整性热图
    for row in range(matrix.shape[0]): # 遍历洲际热图行
        for column in range(matrix.shape[1]): axis_geo.text(column,row,f"{matrix.iloc[row,column]:.0f}",ha="center",va="center",fontsize=5.4,color="white" if matrix.iloc[row,column]>=62 else "#252525") # 在热图中标注百分比整数
    axis_geo.set_xticks(np.arange(len(outcomes)),outcomes,rotation=35,ha="right") # 设置后果字段横轴标签
    axis_geo.set_yticks(np.arange(len(continent_order)),continent_order) # 设置洲际纵轴标签
    axis_geo.set_title("Numeric reporting (%)") # 设置洲际报告完整性标题
    colorbar=fig.colorbar(image,ax=axis_geo,fraction=0.05,pad=0.03,ticks=[0,50,100]) # 添加统一报告率色标
    colorbar.ax.tick_params(labelsize=5,length=2) # 缩小色标刻度字号与长度
    _panel_label(axis_geo,"b") # 添加洲际报告完整性分面标签
    axis_model=fig.add_subplot(grid[0,2]) # 创建观察过程模型森林图分面
    predictors=list(selected_terms.values()) # 固定关键协变量显示顺序
    base=np.arange(len(predictors))[::-1] # 定义自上而下的协变量位置
    model_colors={"Injuries":"#315F73","Evacuated":"#C85B4B"} # 定义受伤与疏散模型颜色
    offsets={"Injuries":0.12,"Evacuated":-0.12} # 定义两类后果效应量错位距离
    for outcome in ["Injuries","Evacuated"]: # 遍历两个报告完整性模型
        current=model.loc[model["outcome"].eq(outcome)].set_index("predictor").reindex(predictors) # 按固定协变量顺序排列当前模型
        y=base+offsets[outcome] # 计算当前模型纵向位置
        axis_model.errorbar(current["odds_ratio"],y,xerr=[current["odds_ratio"]-current["ci_low"],current["ci_high"]-current["odds_ratio"]],fmt="o",markersize=4.3,color=model_colors[outcome],ecolor=model_colors[outcome],elinewidth=1.1,capsize=0,label=outcome,zorder=3) # 绘制调整优势比与95%置信区间
    axis_model.axvline(1,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联参考线
    axis_model.set_xscale("log") # 使用对数尺度展示优势比
    axis_model.set_xlim(0.01,20) # 固定涵盖全部关键区间的横轴范围
    axis_model.set_xticks([0.02,0.1,0.5,1,5,20],labels=["0.02","0.1","0.5","1","5","20"]) # 设置可解释的对数优势比刻度
    axis_model.set_yticks(base,predictors) # 设置关键协变量纵轴标签
    axis_model.set_xlabel("Odds of numeric reporting (95% CI)") # 标注观察过程效应量横轴
    axis_model.set_title("Adjusted observation process") # 设置观察过程模型标题
    axis_model.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
    axis_model.legend(fontsize=5.2,loc="lower right") # 添加两个报告字段图例
    _panel_label(axis_model,"c") # 添加观察过程森林图分面标签
    fig.suptitle("Human-consequence records are filtered by the observation process",x=0.52,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置主图结论式标题
    fig.text(0.07,0.015,"All 239 documented events are shown in a and b. Panel c uses 221 extended-cohort events with country-year context and adjusts simultaneously for continent, event year, GDP and source grade; missing does not mean zero.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 将样本和缺失值说明置于状态图例下方的独立脚注带
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回后果记录与观察过程主图路径
def make_supplementary_figure_3(case_control,events,output_stem): # 定义独立产品匹配天气诊断补充图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保源数据目录存在
    data=case_control.loc[case_control["weather_status"].eq("completed")].copy() # 保留接口成功的匹配天气记录
    data["case_label"]=np.where(pd.to_numeric(data["case"],errors="coerce").eq(1),"Event day","Matched control day") # 生成人类可读病例对照标签
    exposure=data.dropna(subset=["tmax_anomaly_c"])[["event_id","stratum_id","date","case","case_label","tmax_anomaly_c","heatwave_indicator"]].copy() # 整理温度异常分布源数据
    exposure.to_csv(source_dir/"Figure_S3a_temperature_anomaly.csv",index=False,encoding="utf-8-sig") # 输出温度异常分布源数据
    strata=data.groupby("stratum_id").apply(lambda group:pd.Series({"event_id":group["event_id"].iloc[0],"event_anomaly_c":pd.to_numeric(group.loc[pd.to_numeric(group["case"],errors="coerce").eq(1),"tmax_anomaly_c"],errors="coerce").mean(),"control_mean_anomaly_c":pd.to_numeric(group.loc[pd.to_numeric(group["case"],errors="coerce").eq(0),"tmax_anomaly_c"],errors="coerce").mean()}),include_groups=False).reset_index() # 计算每个分层事件日与平均对照日温度异常
    strata["event_minus_control_c"]=strata["event_anomaly_c"]-strata["control_mean_anomaly_c"] # 计算事件日相对平均对照日的温度异常差
    continent_labels={"亚洲":"Asia","欧洲":"Europe","北美洲":"North America","南美洲":"South America","非洲":"Africa","大洋洲":"Oceania"} # 定义洲际英文显示标签
    event_context=events[["event_id","continent"]].drop_duplicates("event_id").copy() # 提取事件与洲际唯一映射
    event_context["continent"]=event_context["continent"].map(continent_labels).fillna(event_context["continent"]) # 将洲际标签转换为英文
    strata=strata.merge(event_context,on="event_id",how="left",validate="one_to_one") # 为分层温度差附加洲际标签
    strata.to_csv(source_dir/"Figure_S3b_within_stratum_difference.csv",index=False,encoding="utf-8-sig") # 输出分层温度异常差源数据
    definitions={"heatwave_indicator":"P90, 3 days + floor","hw_p85_3d":"P85, 3 days + floor","hw_p90_2d":"P90, 2 days + floor","hw_p90_4d":"P90, 4 days + floor","hw_p95_3d":"P95, 3 days + floor","hw_p90_3d_no_floor":"P90, 3 days, no floor"} # 定义预设热浪方案显示标签
    definition_rows=[] # 初始化热浪方案诊断记录
    for field,label in definitions.items(): # 遍历全部预设热浪定义
        event_values=pd.to_numeric(data.loc[pd.to_numeric(data["case"],errors="coerce").eq(1),field],errors="coerce") # 提取事件日当前热浪定义状态
        control_by_stratum=data.loc[pd.to_numeric(data["case"],errors="coerce").eq(0)].groupby("stratum_id")[field].mean() # 计算每个分层对照日平均暴露比例
        definition_rows.append({"definition":field,"definition_label":label,"event_day_percent":float(event_values.mean()*100),"control_day_percent_equal_stratum_weight":float(control_by_stratum.mean()*100),"n_informative_strata":int(data.groupby("stratum_id")[field].nunique().gt(1).sum())}) # 保存事件日、等权对照日与有效分层诊断
    definitions_data=pd.DataFrame(definition_rows) # 创建热浪方案诊断源数据表
    definitions_data.to_csv(source_dir/"Figure_S3c_definition_diagnostics.csv",index=False,encoding="utf-8-sig") # 输出热浪方案诊断源数据
    fig=plt.figure(figsize=(7.2,3.45),constrained_layout=False) # 创建Nature双栏宽度三分面诊断图
    grid=fig.add_gridspec(1,3,width_ratios=[1.0,1.1,1.35],left=0.075,right=0.985,bottom=0.23,top=0.80,wspace=0.57) # 定义分布、洲际差异和定义诊断布局
    axis_distribution=fig.add_subplot(grid[0,0]) # 创建事件日与对照日温度异常分布分面
    limits=exposure["tmax_anomaly_c"].quantile([0.01,0.99]).to_numpy() # 读取温度异常稳健显示范围
    bins=np.linspace(limits[0],limits[1],24) # 定义共同直方图区间
    for label,color in [("Matched control day","#9CC2D1"),("Event day","#C85B4B")]: # 按固定顺序绘制对照日与事件日分布
        values=pd.to_numeric(exposure.loc[exposure["case_label"].eq(label),"tmax_anomaly_c"],errors="coerce").dropna() # 提取当前日期类型温度异常
        axis_distribution.hist(values,bins=bins,density=True,histtype="stepfilled",alpha=0.42,color=color,label=label) # 绘制透明重叠密度直方图
        axis_distribution.axvline(values.median(),color=color,linewidth=1.1) # 标记当前日期类型中位数
    axis_distribution.axvline(0,color="#777777",linewidth=0.7,linestyle="--") # 绘制本地P90异常零点参考线
    axis_distribution.set_xlabel("Daily maximum-temperature anomaly (°C)") # 标注温度异常横轴
    axis_distribution.set_ylabel("Density") # 标注概率密度纵轴
    axis_distribution.set_title("Matched-day exposure") # 设置温度异常分布标题
    axis_distribution.legend(fontsize=5.1,loc="upper left") # 添加事件日与对照日图例
    _panel_label(axis_distribution,"a") # 添加温度异常分布分面标签
    axis_difference=fig.add_subplot(grid[0,1]) # 创建洲际分层温度差分面
    continent_order=strata["continent"].value_counts().index.tolist()[::-1] # 按分层数量生成自下而上洲际顺序
    rng=np.random.default_rng(20260831) # 固定随机种子保证抖动位置可复现
    for index,continent in enumerate(continent_order): # 遍历洲际分层温度差
        values=pd.to_numeric(strata.loc[strata["continent"].eq(continent),"event_minus_control_c"],errors="coerce").dropna() # 提取当前洲际温度异常差
        jitter=rng.uniform(-0.15,0.15,len(values)) # 生成可复现的纵向抖动避免点重叠
        axis_difference.scatter(values,index+jitter,s=12,color="#567F91",alpha=0.55,edgecolor="none") # 绘制全部分层温度异常差散点
        axis_difference.plot([values.median()-0.12,values.median()+0.12],[index,index],color="#9A3F43",linewidth=2.2) # 标记当前洲际中位数
    axis_difference.axvline(0,color="#777777",linewidth=0.8,linestyle="--") # 绘制事件日等于平均对照日参考线
    axis_difference.set_yticks(np.arange(len(continent_order)),continent_order) # 设置洲际纵轴标签
    axis_difference.set_xlabel("Event minus mean control anomaly (°C)") # 标注分层温度差横轴
    axis_difference.set_title("Within-stratum contrast") # 设置分层温度差标题
    _panel_label(axis_difference,"b") # 添加分层温度差分面标签
    axis_definition=fig.add_subplot(grid[0,2]) # 创建热浪方案信息量诊断分面
    y=np.arange(len(definitions_data))[::-1] # 定义热浪方案纵向位置
    event_percent=definitions_data["event_day_percent"].to_numpy() # 读取事件日暴露百分比
    control_percent=definitions_data["control_day_percent_equal_stratum_weight"].to_numpy() # 读取等权对照日暴露百分比
    for index in range(len(definitions_data)): axis_definition.plot([control_percent[index],event_percent[index]],[y[index],y[index]],color="#CFCBC3",linewidth=1.4,zorder=1) # 绘制事件日与对照日暴露率连接线
    axis_definition.scatter(control_percent,y,s=24,color="#567F91",label="Matched controls",zorder=2) # 绘制等权对照日暴露率
    axis_definition.scatter(event_percent,y,s=24,color="#C85B4B",marker="D",label="Event days",zorder=3) # 绘制事件日暴露率
    for index,row in definitions_data.iterrows(): axis_definition.text(max(event_percent[index],control_percent[index])+0.35,y[index],f"n={int(row['n_informative_strata'])}",ha="left",va="center",fontsize=5.0,color=NEUTRAL) # 标注当前定义有效分层数
    axis_definition.set_yticks(y,definitions_data["definition_label"]) # 设置热浪定义纵轴标签
    axis_definition.set_xlim(0,max(float(max(event_percent.max(),control_percent.max()))+3,10)) # 动态设置暴露比例横轴范围并保留标签空间
    axis_definition.set_xlabel("Heatwave-exposed days (%)") # 标注热浪暴露比例横轴
    axis_definition.set_title("Definition information") # 设置热浪定义信息量标题
    axis_definition.legend(fontsize=5.0,loc="upper right") # 将事件日与对照日图例移至右上角以避免遮挡信息量标签
    _panel_label(axis_definition,"c") # 添加热浪定义信息量分面标签
    fig.suptitle("Matched-weather diagnostics for the independent product",x=0.52,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置独立产品诊断标题
    fig.text(0.075,0.055,"NASA POWER MERRA-2/GEOS-IT in local solar time. Controls are same-weekday dates in the same month and location; panel c weights each stratum equally. Diagnostics are descriptive, whereas inference uses conditional logistic regression.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 说明产品、匹配设计、等权规则和诊断边界
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回独立产品匹配天气诊断图路径
def make_figure_4(events,death_model,injury_model,output_stem): # 定义报告人员后果集中度与探索关联主图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保逐板源数据目录存在
    data=events.loc[events["analysis_extended"]].copy() # 使用排除外部触发事件的扩展队列
    outcome_colors={"Deaths":"#315F73","Injuries":"#C85B4B"} # 定义死亡与受伤后果颜色
    concentration_rows=[] # 初始化后果集中曲线源数据记录
    for field,label in [("deaths","Deaths"),("injuries","Injuries")]: # 遍历死亡与受伤数值后果
        values=pd.to_numeric(data[field],errors="coerce").dropna().clip(lower=0).sort_values().to_numpy() # 提取并排序非负数值后果
        cumulative=np.concatenate([[0],np.cumsum(values)/values.sum()]) if values.sum()>0 else np.zeros(len(values)+1) # 计算累计后果负担份额
        event_share=np.arange(len(values)+1)/len(values) # 计算累计数值记录份额
        gini=float(1-2*np.trapezoid(cumulative,event_share)) if values.sum()>0 else np.nan # 计算数值后果记录的基尼系数
        concentration_rows.extend({"outcome":label,"event_share":float(x),"consequence_share":float(y),"gini":gini,"n_numeric":len(values),"total_reported":float(values.sum())} for x,y in zip(event_share,cumulative)) # 保存完整集中曲线与样本说明
    concentration=pd.DataFrame(concentration_rows) # 创建后果集中曲线源数据表
    concentration.to_csv(source_dir/"Figure_4a_consequence_concentration.csv",index=False,encoding="utf-8-sig") # 输出后果集中曲线源数据
    height=pd.to_numeric(data["building_height_m_reported"],errors="coerce") # 读取明确报告的建筑高度
    storeys=pd.to_numeric(data["building_storeys_reported"],errors="coerce") # 读取明确报告的建筑层数
    data["building_scale_rank"]=pd.concat([height.rank(pct=True),storeys.rank(pct=True)],axis=1).mean(axis=1,skipna=True) # 构造高度与层数百分位平均的报告建筑规模
    data["building_scale_quartile"]=pd.qcut(data["building_scale_rank"],4,labels=["Q1, smaller","Q2","Q3","Q4, larger"]) # 将报告建筑规模划分为四分位组
    quartile_rows=[] # 初始化建筑规模分组后果记录
    for field,label in [("deaths","Deaths"),("injuries","Injuries")]: # 遍历死亡与受伤数值后果
        for quartile,group in data.groupby("building_scale_quartile",observed=True): # 遍历报告建筑规模四分位组
            values=pd.to_numeric(group[field],errors="coerce").dropna() # 提取当前分组数值后果
            n=len(values) # 计算当前分组数值后果样本量
            positive=int(values.gt(0).sum()) # 计算当前分组正后果记录数
            proportion=positive/n if n else np.nan # 计算当前分组正后果比例
            denominator=1+1.96**2/n if n else np.nan # 计算Wilson区间分母
            centre=(proportion+1.96**2/(2*n))/denominator if n else np.nan # 计算Wilson区间中心
            half=1.96*np.sqrt(proportion*(1-proportion)/n+1.96**2/(4*n**2))/denominator if n else np.nan # 计算Wilson区间半宽
            quartile_rows.append({"outcome":label,"building_scale_quartile":str(quartile),"n_numeric":n,"n_positive":positive,"positive_percent":proportion*100,"ci_low_percent":max(0,centre-half)*100,"ci_high_percent":min(1,centre+half)*100}) # 保存正后果比例与Wilson区间
    quartiles=pd.DataFrame(quartile_rows) # 创建建筑规模分组后果源数据表
    quartiles.to_csv(source_dir/"Figure_4b_building_scale_profile.csv",index=False,encoding="utf-8-sig") # 输出建筑规模分组后果源数据
    selected_terms={"building_scale_scaled":"Reported building size\n(per IQR)","event_year_10y":"Event year\n(per 10 years)","log_gdp_scaled":"Log GDP per capita\n(per IQR)","construction_related":"Construction-related","facade_fire":"Façade fire","arson_trigger":"Arson trigger"} # 定义探索模型关键协变量标签
    models=pd.concat([death_model.assign(outcome="Deaths"),injury_model.assign(outcome="Injuries")],ignore_index=True) # 合并死亡与受伤探索模型结果
    models=models.loc[models["term"].isin(selected_terms)].copy() # 保留预设建筑、时间、经济与事件类型协变量
    models["predictor"]=models["term"].map(selected_terms) # 生成人类可读协变量标签
    models.to_csv(source_dir/"Figure_4c_consequence_associations.csv",index=False,encoding="utf-8-sig") # 输出后果探索关联森林图源数据
    fig=plt.figure(figsize=(7.2,5.15),constrained_layout=False) # 创建适合论文整页展示的Nature双栏宽度主图
    grid=fig.add_gridspec(2,2,height_ratios=[1.05,1.0],left=0.10,right=0.98,bottom=0.18,top=0.86,wspace=0.42,hspace=0.64) # 采用上排双图与下排通栏森林图布局提升可读性
    axis_concentration=fig.add_subplot(grid[0,0]) # 创建左上后果集中曲线分面
    axis_concentration.plot([0,1],[0,1],color="#B8B5B0",linewidth=0.8,linestyle="--",zorder=0) # 绘制完全均等参考线
    for outcome,color in outcome_colors.items(): # 遍历死亡与受伤集中曲线
        current=concentration.loc[concentration["outcome"].eq(outcome)] # 提取当前后果集中曲线
        gini=float(current["gini"].iloc[0]) # 读取当前后果基尼系数
        axis_concentration.plot(current["event_share"]*100,current["consequence_share"]*100,color=color,linewidth=1.5,label=f"{outcome}, Gini={gini:.2f}") # 绘制累计事件与累计后果份额曲线
    axis_concentration.set_xlim(0,100) # 固定累计事件份额横轴范围
    axis_concentration.set_ylim(0,100) # 固定累计后果份额纵轴范围
    axis_concentration.set_xticks([0,25,50,75,100]) # 设置累计事件份额刻度
    axis_concentration.set_yticks([0,25,50,75,100]) # 设置累计后果份额刻度
    axis_concentration.set_xlabel("Numeric records, cumulative (%)") # 标注累计数值记录横轴
    axis_concentration.set_ylabel("Reported consequence, cumulative (%)") # 标注累计后果负担纵轴
    axis_concentration.set_title("Burden concentration") # 使用紧凑标题避免与分面标签相碰
    axis_concentration.legend(fontsize=4.9,loc="upper left") # 添加后果类型与基尼系数图例
    _panel_label(axis_concentration,"a") # 添加后果集中度分面标签
    axis_quartile=fig.add_subplot(grid[0,1]) # 创建右上建筑规模四分位后果分面
    quartile_order=["Q1, smaller","Q2","Q3","Q4, larger"] # 固定报告建筑规模四分位顺序
    x=np.arange(len(quartile_order)) # 定义建筑规模四分位横轴位置
    offsets={"Deaths":-0.09,"Injuries":0.09} # 定义死亡与受伤点位错开距离
    for outcome,color in outcome_colors.items(): # 遍历死亡与受伤正后果比例
        current=quartiles.loc[quartiles["outcome"].eq(outcome)].set_index("building_scale_quartile").reindex(quartile_order) # 按固定建筑规模顺序排列当前后果
        y=current["positive_percent"].to_numpy() # 读取正后果记录比例
        axis_quartile.errorbar(x+offsets[outcome],y,yerr=[y-current["ci_low_percent"].to_numpy(),current["ci_high_percent"].to_numpy()-y],fmt="o-",markersize=4,linewidth=1.0,capsize=2,color=color,label=outcome) # 绘制正后果比例与Wilson区间
        for index,row in enumerate(current.itertuples()): axis_quartile.text(x[index]+offsets[outcome],row.ci_high_percent+3,f"n={int(row.n_numeric)}",ha="center",va="bottom",fontsize=4.4,color=color) # 标注每个四分位数值后果样本量
    axis_quartile.set_xticks(x,["Q1","Q2","Q3","Q4"]) # 设置紧凑建筑规模四分位标签
    axis_quartile.set_ylim(0,100) # 固定正后果比例纵轴范围
    axis_quartile.set_yticks([0,25,50,75,100]) # 设置正后果比例刻度
    axis_quartile.set_xlabel("Reported building-size quartile") # 标注报告建筑规模四分位横轴
    axis_quartile.set_ylabel("Records with positive count (%)") # 标注正后果记录比例纵轴
    axis_quartile.set_title("Building-size profile") # 设置建筑规模后果标题
    axis_quartile.legend(fontsize=5.0,loc="lower left") # 添加死亡与受伤图例
    _panel_label(axis_quartile,"b") # 添加建筑规模后果分面标签
    axis_model=fig.add_subplot(grid[1,:]) # 创建横跨下排的报告后果探索关联森林图分面
    predictors=list(selected_terms.values()) # 固定探索模型协变量显示顺序
    base=np.arange(len(predictors))[::-1] # 定义自上而下的协变量位置
    for outcome in ["Deaths","Injuries"]: # 遍历死亡与受伤探索模型
        current=models.loc[models["outcome"].eq(outcome)].set_index("predictor").reindex(predictors) # 按固定协变量顺序排列当前模型
        y=base+offsets[outcome] # 计算当前模型纵向错位位置
        axis_model.errorbar(current["multiplicative_ratio"],y,xerr=[current["multiplicative_ratio"]-current["ci_low"],current["ci_high"]-current["multiplicative_ratio"]],fmt="o",markersize=4.2,color=outcome_colors[outcome],ecolor=outcome_colors[outcome],elinewidth=1.0,capsize=0,label=outcome,zorder=3) # 绘制几何均值比与95%稳健区间
    axis_model.axvline(1,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联比值参考线
    axis_model.set_xscale("log") # 使用对数尺度展示比值效应
    axis_model.set_xlim(0.05,5) # 固定涵盖全部关键区间的横轴范围
    axis_model.set_xticks([0.05,0.1,0.25,0.5,1,2,5],labels=["0.05","0.1","0.25","0.5","1","2","5"]) # 设置可解释的对数比值刻度
    axis_model.set_yticks(base,predictors) # 设置探索模型协变量纵轴标签
    axis_model.set_xlabel("Ratio of recorded outcome + 1 (95% CI)") # 标注对数线性模型效应量横轴
    axis_model.set_title("Adjusted recorded consequence") # 设置探索关联模型标题
    axis_model.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
    axis_model.legend(fontsize=5.1,loc="upper right") # 将死亡与受伤图例移至无数据的右上区域
    _panel_label(axis_model,"c") # 添加探索关联森林图分面标签
    death_n=int(death_model["n_observations"].iloc[0]) # 读取死亡探索模型样本量
    injury_n=int(injury_model["n_observations"].iloc[0]) # 读取受伤探索模型样本量
    fig.suptitle("Recorded human consequences are concentrated and structurally heterogeneous",x=0.54,y=0.965,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置结果导向主图标题
    fig.text(0.10,0.025,f"Panels a and b use available numeric outcomes. Panel c models log(count + 1) among records with reported building size and GDP (deaths n={death_n}; injuries n={injury_n}).\nInjury estimates use stabilized reporting weights, while death reporting exceeds 95%; associations are exploratory, conditional on documentation and not incidence effects.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL,linespacing=1.25) # 以两行说明样本变换权重与推断边界
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回报告后果集中度与探索关联主图路径
def make_supplementary_figure_4(events,capacity_results,output_stem): # 定义CTIF消防服务能力覆盖与敏感性补充图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保逐板源数据目录存在
    data=events.loc[events["analysis_extended"]].copy() # 使用扩展队列评估消防服务能力覆盖
    continent_labels={"亚洲":"Asia","欧洲":"Europe","北美洲":"North America","南美洲":"South America","非洲":"Africa","大洋洲":"Oceania"} # 定义洲际英文显示标签
    data["continent_display"]=data["continent"].map(continent_labels).fillna(data["continent"]) # 统一洲际英文显示标签
    data["ctif_capacity_available"]=pd.to_numeric(data["ctif_career_firefighters_per_100k"],errors="coerce").notna() # 标记CTIF职业消防员能力是否可匹配
    data["ctif_matched_iso3"]=data["iso3"].where(data["ctif_capacity_available"]) # 仅为能力匹配事件保留国家代码
    coverage=data.groupby("continent_display",dropna=False).agg(extended_events=("event_id","size"),capacity_matched_events=("ctif_capacity_available","sum"),matched_countries=("ctif_matched_iso3","nunique")).reset_index() # 按洲汇总扩展事件、能力匹配覆盖与国家数
    coverage["coverage_percent"]=coverage["capacity_matched_events"]/coverage["extended_events"]*100 # 计算各洲事件级能力覆盖比例
    coverage=coverage.sort_values("extended_events",ascending=False).reset_index(drop=True) # 按扩展事件数量固定洲际顺序
    coverage.to_csv(source_dir/"Figure_S4a_capacity_coverage.csv",index=False,encoding="utf-8-sig") # 输出消防服务能力覆盖源数据
    models=capacity_results.copy() # 复制消防服务能力敏感性结果避免修改输入
    metric_labels={"ctif_career_firefighters_per_100k":"Career firefighters","ctif_total_firefighters_per_100k":"All firefighters","ctif_fire_stations_per_100k":"Fire stations","ctif_fire_engines_per_100k":"Fire engines"} # 定义消防服务能力指标显示标签
    models["capacity_label"]=models["capacity_metric"].map(metric_labels) # 生成人类可读能力指标标签
    models["outcome"]=models["outcome_field"].map({"deaths":"Deaths","injuries":"Injuries"}) # 生成人类可读后果标签
    models.to_csv(source_dir/"Figure_S4b_capacity_sensitivity.csv",index=False,encoding="utf-8-sig") # 输出消防服务能力敏感性森林图源数据
    fig=plt.figure(figsize=(7.2,3.45),constrained_layout=False) # 创建Nature双栏宽度两分面补充图
    grid=fig.add_gridspec(1,2,width_ratios=[1.0,1.45],left=0.08,right=0.98,bottom=0.28,top=0.80,wspace=0.48) # 抬高分面为森林图图例和脚注预留独立空间
    axis_coverage=fig.add_subplot(grid[0,0]) # 创建消防服务能力覆盖分面
    positions=np.arange(len(coverage))[::-1] # 定义自上而下洲际位置
    axis_coverage.barh(positions,coverage["extended_events"],height=0.60,color="#D8D6D0",label="Extended cohort") # 绘制各洲扩展事件总数
    axis_coverage.barh(positions,coverage["capacity_matched_events"],height=0.60,color="#567F91",label="CTIF capacity matched") # 叠加各洲能力匹配事件数
    for y,row in zip(positions,coverage.itertuples()): axis_coverage.text(row.extended_events+2,y,f"{row.coverage_percent:.0f}%",ha="left",va="center",fontsize=5.2,color=NEUTRAL) # 标注各洲事件级能力覆盖比例
    axis_coverage.set_yticks(positions,coverage["continent_display"]) # 设置洲际纵轴标签
    axis_coverage.set_xlim(0,float(coverage["extended_events"].max())*1.28) # 为覆盖比例标签预留右侧空间
    axis_coverage.set_xlabel("Extended-cohort events") # 标注扩展队列事件数量横轴
    axis_coverage.set_title("Capacity-data coverage") # 设置消防服务能力覆盖标题
    axis_coverage.legend(fontsize=5.0,loc="lower right") # 添加扩展队列与能力匹配图例
    _panel_label(axis_coverage,"a") # 添加能力覆盖分面标签
    axis_model=fig.add_subplot(grid[0,1]) # 创建消防服务能力敏感性森林图分面
    labels=list(metric_labels.values()) # 固定四项消防服务能力指标顺序
    base=np.arange(len(labels))[::-1] # 定义自上而下指标位置
    colors={"Deaths":"#315F73","Injuries":"#C85B4B"} # 定义死亡与受伤后果颜色
    offsets={"Deaths":0.11,"Injuries":-0.11} # 定义两个后果模型错位距离
    for outcome in ["Deaths","Injuries"]: # 遍历死亡与受伤能力敏感性结果
        current=models.loc[models["outcome"].eq(outcome)].set_index("capacity_label").reindex(labels) # 按固定能力指标顺序排列当前后果
        y=base+offsets[outcome] # 计算当前后果点位纵向位置
        axis_model.errorbar(current["multiplicative_ratio"],y,xerr=[current["multiplicative_ratio"]-current["ci_low"],current["ci_high"]-current["multiplicative_ratio"]],fmt="o",markersize=4.2,color=colors[outcome],ecolor=colors[outcome],elinewidth=1.0,capsize=0,label=outcome,zorder=3) # 绘制能力效应比与95%稳健区间
    axis_model.axvline(1,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联比值参考线
    axis_model.set_xscale("log") # 使用对数尺度展示比值效应
    axis_model.set_xlim(0.25,4) # 固定涵盖全部消防能力敏感性区间的横轴范围
    axis_model.set_xticks([0.25,0.5,1,2,4],labels=["0.25","0.5","1","2","4"]) # 设置可解释的对数比值刻度
    axis_model.minorticks_off() # 关闭对数轴次刻度以避免科学计数标签干扰
    axis_model.set_yticks(base,labels) # 设置消防服务能力指标纵轴标签
    axis_model.set_xlabel("Ratio of recorded outcome + 1 per IQR (95% CI)") # 标注能力敏感性效应量横轴
    axis_model.set_title("National capacity sensitivity") # 设置消防服务能力敏感性标题
    axis_model.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
    axis_model.legend(fontsize=5.1,loc="upper center",bbox_to_anchor=(0.5,-0.25),ncol=2) # 将死亡与受伤图例置于横轴下方避免遮挡区间
    _panel_label(axis_model,"b") # 添加能力敏感性分面标签
    fig.suptitle("Fire-service capacity context is incomplete and estimates are imprecise",x=0.52,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 居中设置结果导向补充图标题
    fig.text(0.08,0.02,"CTIF Report No. 30 Table 1.13 provides each country's most recent reported value during 2010–2023, not a common-year series. Models add one log-scaled capacity metric at a time to the recorded-consequence specification; all intervals include one.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 将CTIF时间口径与不确定性说明置于图例下方的独立脚注带
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回CTIF消防服务能力覆盖与敏感性补充图路径
def make_supplementary_figure_5(sensitivity_results,output_stem): # 定义独立气象产品队列排除与逐洲留一补充图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保逐板源数据目录存在
    data=sensitivity_results.loc[sensitivity_results["status"].eq("completed")].sort_values("display_order").copy() # 保留成功模型并按预设顺序排列
    data.to_csv(source_dir/"Figure_S5_event_window_sensitivity.csv",index=False,encoding="utf-8-sig") # 输出队列与逐洲留一森林图源数据
    cmap=LinearSegmentedColormap.from_list("informative_strata",["#B7CDD5","#315F73"]) # 构造有效分层数量蓝色色带
    norm=Normalize(data["n_informative_strata"].min(),data["n_informative_strata"].max()) # 按全部模型有效分层范围统一着色
    fig=plt.figure(figsize=(7.2,3.55),constrained_layout=False) # 创建Nature双栏宽度两分面补充图
    grid=fig.add_gridspec(1,2,left=0.15,right=0.985,bottom=0.25,top=0.80,wspace=0.58) # 为较长队列标签和底部图例预留空间
    families=[("Cohort and event exclusions","Evidence and event restrictions"),("Leave-one-continent-out","Leave-one-continent-out")] # 定义两个可证伪性检验分面
    for index,(family,title) in enumerate(families): # 遍历证据排除与逐洲留一结果
        axis=fig.add_subplot(grid[0,index]) # 创建当前敏感性森林图分面
        current=data.loc[data["analysis_family"].eq(family)].iloc[::-1].reset_index(drop=True) # 反转当前结果使预设首项显示在顶部
        positions=np.arange(len(current)) # 定义当前模型纵向位置
        for y,row in zip(positions,current.itertuples()): # 逐行绘制不同有效分层颜色与面积的估计
            color=cmap(norm(row.n_informative_strata)) # 映射当前模型有效分层颜色
            axis.plot([row.ci_low,row.ci_high],[y,y],color=color,linewidth=1.05,zorder=2) # 绘制当前优势比95%置信区间
            axis.scatter(row.odds_ratio,y,s=14+row.n_informative_strata*0.55,marker="D" if row.restriction=="Extended cohort" else "o",color=color,edgecolor="white",linewidth=0.35,zorder=3) # 绘制按有效分层编码的效应点并以菱形标识主队列
        axis.axvline(1,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联优势比参考线
        axis.set_xscale("log") # 使用对数尺度对称展示优势比
        axis.set_xlim(0.1,8) # 固定涵盖全部队列敏感性置信区间的横轴范围
        axis.set_xticks([0.1,0.25,0.5,1,2,4,8],labels=["0.1","0.25","0.5","1","2","4","8"]) # 设置可解释的对数比值刻度
        axis.minorticks_off() # 关闭对数轴次刻度避免科学计数干扰
        axis.set_yticks(positions,current["restriction"]) # 设置队列排除或逐洲留一标签
        axis.set_xlabel("Heatwave odds ratio (95% CI)") # 标注独立产品病例交叉效应量横轴
        axis.set_title(title) # 设置当前敏感性分面标题
        axis.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
        _panel_label(axis,chr(ord("a")+index)) # 添加按顺序生成的补充分面标签
    color_axis=fig.add_axes([0.39,0.12,0.22,0.018]) # 创建全图共享有效分层水平色条
    color_bar=fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=color_axis,orientation="horizontal") # 绘制有效分层连续颜色图例
    color_bar.set_label("Informative strata",fontsize=5.5,labelpad=2) # 标注可识别热浪对比的事件分层数量
    color_bar.ax.tick_params(labelsize=5,length=1.5,width=0.4) # 设置紧凑色条刻度样式
    fig.suptitle("Coarse-product heat estimates remain imprecise across restrictions",x=0.53,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 使用结果边界导向标题概括所有区间均跨越一
    fig.text(0.15,0.02,"All models use the prespecified NASA POWER heatwave definition and adjust for dewpoint, precipitation and wind. The diamond is the 228-stratum extended-cohort estimate; all intervals include one.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 说明独立产品模型口径主队列与不精确性边界
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回队列排除与逐洲留一补充图路径
def make_supplementary_figure_6(era5_results,power_results,output_stem): # 定义双气象产品连续温度与滞后敏感性补充图
    set_nature_style() # 应用统一出版风格
    output_stem=Path(output_stem) # 标准化输出文件前缀
    source_dir=output_stem.parents[2]/"outputs/tables" # 定位逐图源数据目录
    source_dir.mkdir(parents=True,exist_ok=True) # 确保逐图源数据目录存在
    data=pd.concat([era5_results.copy(),power_results.copy()],ignore_index=True) # 合并两个独立气象产品结果
    data["product_label"]=data["weather_product"].map(lambda value:"ERA5-Land" if str(value).startswith("ERA5") else "NASA POWER") # 生成紧凑气象产品标签
    data.to_csv(source_dir/"Figure_S6_continuous_temperature_sensitivity.csv",index=False,encoding="utf-8-sig") # 输出连续温度森林图完整源数据
    labels=["Current day","Lag 1 day","Lag 2 days","Lag 3 days","Mean lag 0–3 days"] # 固定连续温度暴露规格显示顺序
    adjustments=[("Dewpoint + precipitation + wind","Weather-adjusted"),("Temperature only","Temperature only")] # 定义两个协变量规格分面
    products=[("ERA5-Land","o","#315F73",0.11),("NASA POWER","s","#C85B4B",-0.11)] # 定义产品形状颜色与纵向错位
    fig=plt.figure(figsize=(7.2,3.45),constrained_layout=False) # 创建Nature双栏宽度连续温度补充图
    grid=fig.add_gridspec(1,2,left=0.14,right=0.985,bottom=0.27,top=0.80,wspace=0.40) # 为标签图例与脚注预留独立空间
    for index,(adjustment,title) in enumerate(adjustments): # 遍历天气调整与仅温度规格
        axis=fig.add_subplot(grid[0,index]) # 创建当前模型规格分面
        base=np.arange(len(labels))[::-1] # 定义从当前日到四日均值的纵向位置
        for product,marker,color,offset in products: # 遍历两个独立气象产品
            current=data.loc[data["adjustment"].eq(adjustment)&data["product_label"].eq(product)].sort_values("display_order") # 筛选并排序当前产品模型
            y=base+offset # 计算产品错位后的纵向位置
            axis.errorbar(current["odds_ratio"],y,xerr=[current["odds_ratio"]-current["ci_low"],current["ci_high"]-current["odds_ratio"]],fmt=marker,markersize=4.3,color=color,ecolor=color,elinewidth=1.05,capsize=0,label=product,zorder=3) # 绘制每产品每四分位距优势比与95%区间
        axis.axvline(1,color="#8A8A8A",linewidth=0.8,linestyle="--",zorder=0) # 绘制无关联优势比参考线
        axis.set_xscale("log") # 使用对数尺度展示优势比
        axis.set_xlim(0.8,2.2) # 固定跨分面效应量横轴范围
        axis.set_xticks([0.8,1,1.25,1.5,2],labels=["0.8","1","1.25","1.5","2"]) # 设置共享可解释对数刻度
        axis.minorticks_off() # 关闭对数次刻度减少视觉干扰
        axis.set_yticks(base,labels if index==0 else []) # 仅左侧分面显示滞后规格标签
        axis.set_xlabel("Odds ratio per specification-specific IQR (95% CI)") # 标注连续温度条件优势比横轴
        axis.set_title(title) # 设置协变量规格分面标题
        axis.grid(axis="x",which="major",color="#ECE9E4",linewidth=0.6,zorder=0) # 添加克制的纵向参考网格
        _panel_label(axis,chr(ord("a")+index)) # 添加补充分面标签
    fig.axes[1].legend(fontsize=5.4,loc="upper center",bbox_to_anchor=(0.5,-0.25),ncol=2) # 将共享产品图例置于右分面横轴下方
    fig.suptitle("Continuous temperature associations depend on weather adjustment",x=0.53,y=0.96,ha="center",fontsize=10,fontweight="bold",color="#202020") # 以结论导向标题概括调整依赖性
    fig.text(0.14,0.02,"Conditional logistic models use 228 event strata. Product- and specification-specific IQRs span 4.3–5.2 °C. Holm-adjusted P values for each five-model family are provided in the source data; no estimate is interpreted as a causal heat effect.",ha="left",va="bottom",fontsize=5.2,color=NEUTRAL) # 说明尺度多重比较与因果边界
    paths=_save_formats(fig,output_stem) # 保存全部出版格式
    plt.close(fig) # 关闭图对象释放内存
    return paths # 返回连续温度敏感性补充图路径
