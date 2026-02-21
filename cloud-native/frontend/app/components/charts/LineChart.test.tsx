import { describe, it, expect } from 'vitest'
import { LineChart } from './LineChart'

describe('LineChart', () => {
  it('should render empty state when no data provided', () => {
    const { container } = { container: document.createElement('div') }
    // Basic smoke test - component should handle empty data
    expect(() => {
      const chart = LineChart({ data: [] })
      expect(chart).toBeDefined()
    }).not.toThrow()
  })

  it('should render with valid data', () => {
    const data = [
      { date: '2024-01-01', count: 5 },
      { date: '2024-01-02', count: 10 },
      { date: '2024-01-03', count: 7 },
    ]
    
    expect(() => {
      const chart = LineChart({ data })
      expect(chart).toBeDefined()
    }).not.toThrow()
  })

  it('should handle single data point', () => {
    const data = [{ date: '2024-01-01', count: 5 }]
    
    expect(() => {
      const chart = LineChart({ data })
      expect(chart).toBeDefined()
    }).not.toThrow()
  })
})
