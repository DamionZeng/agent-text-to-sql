export const chartTypeNames = {
  bar: '柱状图',
  line: '折线图',
  pie: '饼图',
  doughnut: '环形图',
  scatter: '散点图',
  radar: '雷达图',
  funnel: '漏斗图',
  gauge: '仪表盘',
  number_card: '数字卡片',
  table: '数据表格',
  heatmap: '热力图',
  text: '文本',
  image: '图片',
  video: '视频',
  iframe: '网页',
  container: '容器/Tab',
}

export const chartTypeGroups = [
  {
    label: '指标类',
    types: ['number_card', 'gauge'],
  },
  {
    label: '折线 / 柱状',
    types: ['bar', 'line', 'scatter'],
  },
  {
    label: '饼图 / 环形',
    types: ['pie', 'doughnut'],
  },
  {
    label: '表格类',
    types: ['table', 'heatmap'],
  },
  {
    label: '其他组件',
    types: ['radar', 'funnel', 'text', 'image', 'video', 'iframe', 'container'],
  },
]

export const allChartTypes = Object.keys(chartTypeNames)

export function getChartTypeName(type) {
  return chartTypeNames[type] || type || '未知图表'
}

export function getResolvedChartType(panel, chartData) {
  return panel?._chartType || panel?.chart_type || chartData?.chart_type || 'bar'
}
