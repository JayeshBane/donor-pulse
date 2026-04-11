// donorpulse-frontend\src\components\donor\CSVImport.tsx 
'use client'

import { useState } from 'react'
import Papa from 'papaparse'
import { donorAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface ParseResult {
  data: any[]
  errors: any[]
  meta: any
}

export const CSVImport: React.FC = () => {
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState<{ success: number; failed: number; total: number } | null>(null)
  
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    Papa.parse(file, {
      header: true,
      complete: async (results: ParseResult) => {
        await importDonors(results.data)
      }
    })
  }
  
  const importDonors = async (donors: any[]) => {
    setUploading(true)
    let success = 0
    let failed = 0
    
    for (const donor of donors) {
      try {
        await donorAPI.register(donor)
        success++
      } catch (error) {
        failed++
        console.error('Failed to import donor:', donor, error)
      }
    }
    
    setResults({ success, failed, total: donors.length })
    setUploading(false)
  }
  
  return (
    <Card title="Bulk Import Donors (CSV)">
      <div className="space-y-4">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          disabled={uploading}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        
        {uploading && <div className="text-center">Importing donors...</div>}
        
        {results && (
          <div className="p-4 bg-gray-100 rounded">
            <p>✅ Success: {results.success}</p>
            <p>❌ Failed: {results.failed}</p>
            <p>📊 Total: {results.total}</p>
          </div>
        )}
      </div>
    </Card>
  )
}