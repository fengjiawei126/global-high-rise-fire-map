// GPWv4.11：2020年全球人口数量，30角秒（约1 km）
var gpw2020 = ee.Image(
  'CIESIN/GPWv411/GPW_Population_Count/' +
  'gpw_v4_population_count_rev11_2020_30_sec'
).select('population_count');

// 隐藏人口数量为0的网格
var population = gpw2020.updateMask(gpw2020.gt(0));

// 人口数量可视化参数
var populationVis = {
  min: 0,
  max: 5000,
  palette: [
    'ffffe5',
    'fee391',
    'fec44f',
    'fe9929',
    'ec7014',
    'cc4c02',
    '8c2d04'
  ]
};

// 显示2020年人口图层
Map.setOptions('ROADMAP');
Map.setCenter(105, 35, 4);
Map.addLayer(
  population,
  populationVis,
  'GPWv4.11 Population Count 2020'
);

// 在Console中查看数据属性
print('GPW 2020人口数据', gpw2020);
print('空间分辨率（米）', gpw2020.projection().nominalScale());
print('投影信息', gpw2020.projection());

// 如需导出研究区数据：
// 1. 在GEE地图上绘制矩形或多边形。
// 2. 将导入的Geometry名称修改为roi。
// 3. 取消以下代码的注释并运行。
// Export.image.toDrive({
//   image: gpw2020.clip(roi),
//   description: 'GPW2020_population_count',
//   folder: 'GEE_Output',
//   fileNamePrefix: 'GPW2020_population_count',
//   region: roi,
//   scale: 1000,
//   fileFormat: 'GeoTIFF',
//   maxPixels: 1e13
// });
