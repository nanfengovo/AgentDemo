'use client';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [reports, setReports] = useState<string[]>([]);
  const [content, setContent] = useState('');
  const [activeFile, setActiveFile] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/api/reports')
      .then(res => res.json())
      .then(data => setReports(data.reports));
  }, []);

  const handleSelect = async (filename: string) => {
    setActiveFile(filename);
    const res = await fetch(`http://localhost:8000/api/reports/${filename}`);
    const data = await res.json();
    setContent(data.content);
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <nav className="w-64 border-r bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold mb-8 text-gray-800">金融分析看板</h1>
        <div className="space-y-2">
          {reports.map((file) => (
            <button
              key={file}
              onClick={() => handleSelect(file)}
              className={`w-full text-left px-4 py-2 rounded-md transition duration-200 ${
                activeFile === file ? 'bg-blue-600 text-white' : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              {file.replace('.txt', '').replace('.md', '')}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 p-12">
        <div className="max-w-4xl mx-auto bg-white p-10 rounded-xl shadow-sm border border-gray-100">
          {content ? (
            <article className="prose prose-slate max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </article>
          ) : (
            <div className="text-gray-400 text-center py-20">请在左侧选择一份分析报告</div>
          )}
        </div>
      </main>
    </div>
  );
}
