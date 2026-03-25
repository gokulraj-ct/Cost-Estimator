'use client';

import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [files, setFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const uploadedFiles = Array.from(e.target.files);
    const fileContents = await Promise.all(
      uploadedFiles.map(async (file) => ({
        name: file.name,
        content: await file.text()
      }))
    );
    setFiles(fileContents);
  };

  const handleEstimate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_URL}/api/v1/estimate`, {
        files: files,
        region: 'us-east-1'
      });
      setResult(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Kostructure
          </h1>
          <p className="text-gray-600">
            AWS Infrastructure Cost Estimator
          </p>
        </header>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Upload Terraform Files</h2>
          
          <input
            type="file"
            multiple
            accept=".tf"
            onChange={handleFileUpload}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-4"
          />

          {files.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                {files.length} file(s) selected
              </p>
            </div>
          )}

          <button
            onClick={handleEstimate}
            disabled={loading || files.length === 0}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Calculating...' : 'Estimate Cost'}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
              Error: {error}
            </div>
          )}
        </div>

        {result && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Cost Estimate</h2>
            
            <div className="bg-blue-50 p-6 rounded-lg mb-6">
              <div className="text-3xl font-bold text-blue-900">
                ${result.total_monthly_cost.toFixed(2)}
                <span className="text-lg font-normal text-gray-600">/month</span>
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Region: {result.region} | Resources: {result.resource_count}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Estimate ID: {result.estimate_id}
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-3">Cost Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Resource
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Monthly Cost
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.breakdown.map((item, idx) => (
                    <tr key={idx}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.resource}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        ${item.monthly_cost.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
