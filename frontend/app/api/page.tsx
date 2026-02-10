"use client"

import DocsLayout from "@/components/docs-layout"
import { CodeBlock, Callout, Steps } from "@/components/docs-components"
import { Badge } from "@/components/ui/badge"
import { Terminal, Lock, Cpu, Globe } from "lucide-react"

export default function ApiPage() {
  return (
    <DocsLayout>
      <header className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <Badge className="bg-blue-100 text-blue-700 border-blue-200">
            API v1.0 (BETA)
          </Badge>
          <Badge className="bg-amber-100 text-amber-700 border-amber-200">
            Coming Soon
          </Badge>
        </div>
        <h1 id="introduction" className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight mb-6">
          API Reference
        </h1>
        <p className="text-xl text-gray-600 leading-relaxed">
          The Agent47 API provides a RESTful interface for interacting with your AI employees.
          <span className="block mt-2 font-semibold text-amber-600">Public API Access Launching Q4 2025.</span>
        </p>
      </header>

      <section id="auth" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Lock className="mr-2 text-green-500" size={24} />
          Authentication
        </h2>
        <p className="text-gray-600 mb-6">
          All API requests must be authenticated using a Bearer token. You can generate your API keys in the
          <strong> Developer Settings</strong> section of your dashboard.
        </p>

        <CodeBlock
          language="bash"
          code={`curl -X GET "https://api.agent47.ai/v1/personnel" \\
  -H "Authorization: Bearer YOUR_API_KEY"`}
        />

        <Callout type="warning">
          Never expose your API keys in client-side code (browsers, mobile apps). Always use a backend proxy to protect your credentials.
        </Callout>
      </section>

      <section id="personnel" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Cpu className="mr-2 text-green-500" size={24} />
          Personnel Chat API
        </h2>
        <p className="text-gray-600 mb-6">
          Send tasks or messages to specific AI employees. This endpoint supports streaming responses for real-time interactions.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Endpoint</h3>
            <div className="flex items-center space-x-2 font-mono text-sm bg-gray-100 px-3 py-2 rounded-lg w-fit">
              <span className="text-green-700 font-bold">POST</span>
              <span className="text-gray-600">/v1/chat/message</span>
            </div>

            <h3 className="text-lg font-bold text-gray-900 pt-4">Parameters</h3>
            <ul className="space-y-3">
              <li className="text-sm">
                <span className="font-mono text-green-600 font-bold">personnel_id</span>
                <span className="text-gray-400 mx-2">string</span>
                <p className="text-gray-600 mt-1 italic">Example: "aria", "eric", "clara"</p>
              </li>
              <li className="text-sm">
                <span className="font-mono text-green-600 font-bold">message</span>
                <span className="text-gray-400 mx-2">string</span>
                <p className="text-gray-600 mt-1 italic">The task or question for the employee.</p>
              </li>
              <li className="text-sm">
                <span className="font-mono text-green-600 font-bold">stream</span>
                <span className="text-gray-400 mx-2">boolean</span>
                <p className="text-gray-600 mt-1 italic">Whether to use Server-Sent Events (SSE).</p>
              </li>
            </ul>
          </div>

          <div className="bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl sticky top-24">
            <div className="flex items-center px-4 py-3 bg-slate-800 border-b border-slate-700">
              <div className="flex space-x-2">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
              </div>
              <span className="ml-4 text-[10px] font-mono text-slate-400 uppercase tracking-widest">Request Example</span>
            </div>
            <pre className="p-6 text-xs font-mono text-slate-300 leading-relaxed overflow-x-auto">
              <code>{`{
  "personnel_id": "aria",
  "message": "Analyze our twitter engagement for Q3",
  "options": {
    "include_charts": true,
    "tone": "analytical"
  },
  "stream": false
}`}</code>
            </pre>
          </div>
        </div>
      </section>

      <section id="limits" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <Globe className="mr-2 text-green-500" size={24} />
          Rate Limits
        </h2>
        <p className="text-gray-600 mb-6">
          To ensure system stability, we enforce rate limits on a per-API-key basis.
        </p>

        <div className="overflow-hidden border border-gray-100 rounded-2xl">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 font-bold uppercase text-[10px] tracking-widest">
              <tr>
                <th className="px-6 py-4">Tier</th>
                <th className="px-6 py-4">Request Limit</th>
                <th className="px-6 py-4">Burst Allowance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="px-6 py-4 font-bold">Standard</td>
                <td className="px-6 py-4 text-gray-600">60 req/min</td>
                <td className="px-6 py-4 text-gray-600">10 requests</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold">Enterprise</td>
                <td className="px-6 py-4 text-gray-600">1,200 req/min</td>
                <td className="px-6 py-4 text-gray-600">100 requests</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section id="errors" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Error Codes</h2>
        <div className="space-y-3">
          {[
            { code: "400", title: "Bad Request", desc: "The request was missing required parameters." },
            { code: "401", title: "Unauthorized", desc: "Invalid or expired API key." },
            { code: "429", title: "Too Many Requests", desc: "Daily or per-minute rate limit reached." },
            { code: "500", title: "Internal Server Error", desc: "A specialist encountered a temporary cognitive fault." }
          ].map((error, i) => (
            <div key={i} className="flex items-center p-4 bg-gray-50 rounded-xl border border-gray-100 group hover:border-red-100 transition-colors">
              <span className="w-12 font-mono font-bold text-red-500">{error.code}</span>
              <div className="ml-4">
                <h4 className="font-bold text-gray-900 text-sm">{error.title}</h4>
                <p className="text-xs text-gray-500">{error.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </DocsLayout>
  )
}
