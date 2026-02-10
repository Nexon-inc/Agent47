"use client"

import DocsLayout from "@/components/docs-layout"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, AlertCircle, Clock, Server, Globe, Database, Cpu } from "lucide-react"

export default function StatusPage() {
  const systems = [
    { name: "Core Automation Engine", status: "operational", icon: Cpu, latency: "42ms" },
    { name: "Personnel Intelligence Pool", status: "operational", icon: BrainIcon, latency: "128ms" },
    { name: "Global Workforce API", status: "operational", icon: Globe, latency: "12ms" },
    { name: "Real-time Intercommunication", status: "operational", icon: Server, latency: "8ms" },
    { name: "Employee Knowledge Base", status: "operational", icon: Database, latency: "3ms" },
  ]

  const incidents = [
    {
      date: "Oct 12, 2025",
      title: "Clara Service Interruption",
      status: "resolved",
      desc: "Our customer support specialist experienced a temporary delay in processing requests due to a localized high-traffic event. Service was restored inside 14 minutes."
    },
    {
      date: "Sep 28, 2025",
      title: "Scheduled Maintenance: Brain Core Update",
      status: "completed",
      desc: "System-wide update to improve reasoning capabilities for all AI employees."
    }
  ]

  return (
    <DocsLayout>
      <header className="mb-12">
        <div className="flex items-center space-x-3 mb-4">
          <div className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </div>
          <span className="text-sm font-bold text-green-600 uppercase tracking-widest">All Systems Operational</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight mb-6">
          System Status
        </h1>
        <p className="text-xl text-gray-600 leading-relaxed">
          Monitor the health and performance of the Agent47 AI workforce and underlying infrastructure in real-time.
        </p>
      </header>

      <section id="health" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4">Current Health</h2>
        <div className="space-y-4">
          {systems.map((system, i) => (
            <div key={i} className="p-6 bg-gray-50 rounded-2xl border border-gray-100 flex items-center justify-between group hover:border-green-200 transition-all">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-white rounded-xl shadow-sm border border-gray-100 group-hover:bg-green-50 group-hover:border-green-100 transition-colors">
                  <system.icon className="w-6 h-6 text-gray-600 group-hover:text-green-600" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 leading-none mb-1">{system.name}</h3>
                  <p className="text-xs text-gray-400 font-mono">Latency: {system.latency}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2 bg-green-100/50 text-green-700 px-3 py-1.5 rounded-full border border-green-200">
                <CheckCircle size={14} />
                <span className="text-xs font-bold uppercase tracking-widest">{system.status}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="history" className="mb-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4 flex items-center">
          <Clock className="mr-2 text-gray-400" size={24} />
          Incident History
        </h2>
        <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
          {incidents.map((incident, i) => (
            <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-200 group-[.is-active]:bg-green-500 text-slate-500 group-[.is-active]:text-emerald-50 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                {incident.status === "resolved" ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex items-center justify-between space-x-2 mb-1">
                  <div className="font-bold text-slate-900">{incident.title}</div>
                  <time className="font-mono text-xs font-medium text-green-500 uppercase">{incident.date}</time>
                </div>
                <div className="text-slate-500 text-sm leading-relaxed">{incident.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </DocsLayout>
  )
}

function BrainIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.105 4 4 0 0 0 8 0 4 4 0 0 0 8-0 4 4 0 0 0 .52-8.105 4 4 0 0 0-2.526-5.77A3 3 0 1 0 12 5" />
      <path d="M12 13v-4" />
      <path d="M12 5a8 8 0 0 1 8 8" />
      <path d="M4 13a8 8 0 0 1 8-8" />
    </svg>
  )
}
