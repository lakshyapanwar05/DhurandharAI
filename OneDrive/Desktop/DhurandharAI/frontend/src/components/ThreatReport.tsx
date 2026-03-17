import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import anime from 'animejs'

interface ThreatReportProps {
  isOpen: boolean
  onClose: () => void
}

export default function ThreatReport({ isOpen, onClose }: ThreatReportProps) {
  const [report, setReport] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const generateReport = async () => {
    setIsLoading(true)
    setReport('')
    
    try {
      const response = await fetch('http://localhost:8000/api/report/generate')
      const data = await response.json()
      setReport(data.report)
      
      // Animate content entrance
      anime({
        targets: '.report-content',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 500,
        easing: 'easeOutQuad'
      })
    } catch (error) {
      console.error('Error generating report:', error)
      setReport('# Error generating report\n\nUnable to connect to the backend. Please check if the server is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(report)
      setCopied(true)
      
      // Animate copy button
      anime({
        targets: '.copy-button',
        scale: [1, 0.9, 1],
        duration: 200,
        easing: 'easeInOutQuad'
      })
      
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Error copying to clipboard:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Dark overlay */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[80vh] bg-[#0d1117] border border-white/20 rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-2xl font-bold text-white">Threat Analysis Report</h2>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white transition-colors text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {!report && !isLoading && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-white mb-2">Generate Threat Report</h3>
              <p className="text-white/60 mb-6">
                Generate a comprehensive threat analysis report based on recent security incidents
              </p>
              <button
                onClick={generateReport}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded transition-colors"
              >
                Generate Report
              </button>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid border-blue-500 border-r-transparent mb-4"></div>
              <p className="text-white/80">Analyzing threats and generating report...</p>
            </div>
          )}

          {report && (
            <div className="report-content">
              {/* Actions */}
              <div className="flex gap-4 mb-6">
                <button
                  onClick={copyToClipboard}
                  className="copy-button px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors flex items-center gap-2"
                >
                  {copied ? '✓ Copied' : '📋 Copy Report'}
                </button>
                <button
                  onClick={generateReport}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
                >
                  🔄 Regenerate
                </button>
              </div>

              {/* Report content */}
              <div className="bg-[#0a0f0a] border border-white/10 rounded p-6 prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
