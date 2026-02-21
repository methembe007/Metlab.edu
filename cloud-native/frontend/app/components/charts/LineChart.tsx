interface DataPoint {
  date: string
  count: number
}

interface LineChartProps {
  data: DataPoint[]
  width?: number
  height?: number
  color?: string
}

export function LineChart({ 
  data, 
  width = 600, 
  height = 300,
  color = '#3b82f6'
}: LineChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No data available</p>
      </div>
    )
  }

  const padding = 40
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  const maxCount = Math.max(...data.map(d => d.count), 1)
  const minCount = 0

  const xStep = chartWidth / (data.length - 1 || 1)
  const yScale = chartHeight / (maxCount - minCount || 1)

  // Generate path for the line
  const linePath = data
    .map((point, index) => {
      const x = padding + index * xStep
      const y = padding + chartHeight - (point.count - minCount) * yScale
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  // Generate area path (filled area under the line)
  const areaPath = `${linePath} L ${padding + (data.length - 1) * xStep} ${padding + chartHeight} L ${padding} ${padding + chartHeight} Z`

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  // Show every nth label to avoid crowding
  const labelInterval = Math.ceil(data.length / 6)

  return (
    <div className="w-full">
      <svg width={width} height={height} className="w-full">
        {/* Grid lines */}
        {[0, 1, 2, 3, 4].map((i) => {
          const y = padding + (chartHeight / 4) * i
          return (
            <g key={i}>
              <line
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
              />
              <text
                x={padding - 10}
                y={y + 5}
                textAnchor="end"
                fontSize="12"
                fill="#6b7280"
              >
                {Math.round(maxCount - (maxCount / 4) * i)}
              </text>
            </g>
          )
        })}

        {/* Area under the line */}
        <path
          d={areaPath}
          fill={color}
          fillOpacity="0.1"
        />

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {data.map((point, index) => {
          const x = padding + index * xStep
          const y = padding + chartHeight - (point.count - minCount) * yScale
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="4"
              fill={color}
              stroke="white"
              strokeWidth="2"
            />
          )
        })}

        {/* X-axis labels */}
        {data.map((point, index) => {
          if (index % labelInterval !== 0 && index !== data.length - 1) return null
          const x = padding + index * xStep
          return (
            <text
              key={index}
              x={x}
              y={height - padding + 20}
              textAnchor="middle"
              fontSize="12"
              fill="#6b7280"
            >
              {formatDate(point.date)}
            </text>
          )
        })}
      </svg>
    </div>
  )
}
