"use client"

import { useState } from "react"
import AdminLayout from "@/components/admin/layout"
import { Card } from "@/components/ui/card"
import {
    Users,
    MessageSquare,
    Zap,
    FileText,
    CheckCircle,
    ShieldAlert,
    BrainCircuit,
    ChevronRight,
    Maximize2,
    MoreVertical,
    Send,
    UserPlus
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

// Types
interface Personnel {
    id: string
    name: string
    role: string
    status: "idle" | "processing" | "offline"
    cognitiveLoad: number
    avatar: string
    department: "Growth" | "Intelligence" | "Operations"
}

const personnelData: Personnel[] = [
    { id: "1", name: "Aria", role: "Social Media Automation", status: "processing", cognitiveLoad: 82, avatar: "AR", department: "Growth" },
    { id: "2", name: "Joe", role: "Research & Data Analysis", status: "idle", cognitiveLoad: 0, avatar: "JO", department: "Intelligence" },
    { id: "3", name: "Eric", role: "Sales Optimization", status: "processing", cognitiveLoad: 45, avatar: "ER", department: "Growth" },
    { id: "4", name: "Clara", role: "Customer Support", status: "idle", cognitiveLoad: 0, avatar: "CL", department: "Operations" },
]

export default function StrategyRoomPage() {
    const [selectedPersonnel, setSelectedPersonnel] = useState<Personnel>(personnelData[0])
    const [stealthMode, setStealthMode] = useState(false)

    return (
        <AdminLayout>
            <div className="flex h-[calc(100vh-8rem)] gap-4 overflow-hidden">

                {/* Left Sidebar: Personnel Roster */}
                <div className="w-80 flex flex-col gap-4">
                    <Card className="flex-1 bg-gray-900/50 border-gray-800 backdrop-blur-sm overflow-hidden flex flex-col">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                            <h2 className="text-sm font-bold text-white uppercase tracking-widest">Team Roster</h2>
                            <button
                                onClick={() => setStealthMode(!stealthMode)}
                                className={cn(
                                    "px-2 py-1 rounded text-[10px] font-bold transition-all",
                                    stealthMode ? "bg-red-500/20 text-red-400 border border-red-500/50" : "bg-gray-800 text-gray-400 border border-gray-700"
                                )}
                            >
                                {stealthMode ? "STEALTH ACTIVE" : "STEALTH MODE"}
                            </button>
                        </div>

                        <ScrollArea className="flex-1">
                            <div className="p-2 space-y-1">
                                {personnelData.map((p) => (
                                    <button
                                        key={p.id}
                                        onClick={() => setSelectedPersonnel(p)}
                                        className={cn(
                                            "w-full p-3 rounded-xl flex items-center gap-3 transition-all text-left group",
                                            selectedPersonnel.id === p.id
                                                ? "bg-green-600/10 border border-green-500/30 text-white"
                                                : "text-gray-400 hover:bg-white/5 border border-transparent"
                                        )}
                                    >
                                        <div className="relative">
                                            <div className="w-10 h-10 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center font-bold text-xs ring-2 ring-transparent group-hover:ring-green-500/20">
                                                {p.avatar}
                                            </div>
                                            <div className={cn(
                                                "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-gray-900",
                                                p.status === "processing" ? "bg-green-500 animate-pulse" :
                                                    p.status === "idle" ? "bg-blue-500" : "bg-gray-500"
                                            )} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-center mb-0.5">
                                                <span className="text-sm font-bold truncate">{p.name}</span>
                                                <span className="text-[10px] opacity-60 uppercase">{p.department}</span>
                                            </div>
                                            <div className="text-[10px] flex items-center gap-1 opacity-70">
                                                {p.status === "processing" ? (
                                                    <span className="text-green-400 flex items-center animate-pulse">
                                                        <Zap size={10} className="mr-1" /> Working...
                                                    </span>
                                                ) : (
                                                    "At Duty"
                                                )}
                                            </div>
                                        </div>
                                        {selectedPersonnel.id === p.id && <ChevronRight size={14} className="text-green-500" />}
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>

                        <div className="p-4 border-t border-gray-800 bg-gray-950/50">
                            <div className="flex items-center gap-2 mb-2">
                                <BrainCircuit size={14} className="text-green-500" />
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Internal Comms Feed</span>
                            </div>
                            <div className="text-[10px] font-mono text-green-500/70 space-y-1">
                                <div className="flex gap-2">
                                    <span className="text-gray-600">18:24</span>
                                    <span>Aria requested data from Joe</span>
                                </div>
                                <div className="flex gap-2">
                                    <span className="text-gray-600">18:25</span>
                                    <span>Joe delivering lead analysis</span>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Center: Execution Floor */}
                <div className="flex-1 flex flex-col gap-4">
                    <Card className="flex-1 bg-gray-900/50 border-gray-800 overflow-hidden flex flex-col backdrop-blur-sm">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-white/5">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-green-600/20 flex items-center justify-center text-green-500">
                                    <FileText size={18} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-white uppercase tracking-tight">Active Workfloor</h3>
                                    <p className="text-[10px] text-gray-500">Drafting: {selectedPersonnel.name} — Phase 2 Optimization</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-[10px] border-green-500/20 text-green-500">DRAFTING</Badge>
                                <button className="p-2 hover:bg-white/5 rounded-lg text-gray-400"><Maximize2 size={16} /></button>
                                <button className="p-2 hover:bg-white/5 rounded-lg text-gray-400"><MoreVertical size={16} /></button>
                            </div>
                        </div>

                        <div className="flex-1 p-8 overflow-y-auto">
                            {/* Placeholder for real work content */}
                            <div className="max-w-2xl mx-auto space-y-6">
                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-4">
                                    <div className="h-4 w-1/3 bg-white/10 rounded animate-pulse" />
                                    <div className="space-y-2">
                                        <div className="h-3 w-full bg-white/5 rounded" />
                                        <div className="h-3 w-full bg-white/5 rounded" />
                                        <div className="h-3 w-4/5 bg-white/5 rounded" />
                                    </div>
                                </div>
                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-4 opacity-50">
                                    <div className="h-4 w-2/5 bg-white/10 rounded" />
                                    <div className="space-y-2">
                                        <div className="h-3 w-full bg-white/5 rounded" />
                                        <div className="h-3 w-full bg-white/5 rounded" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 border-t border-gray-800 bg-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Cognitive Utilization</div>
                                <div className="w-32 h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-green-500 transition-all duration-1000"
                                        style={{ width: `${selectedPersonnel.cognitiveLoad}%` }}
                                    />
                                </div>
                                <span className="text-[10px] font-mono text-green-500">{selectedPersonnel.cognitiveLoad}%</span>
                            </div>
                            <button className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-bold transition-all shadow-lg shadow-green-600/20">
                                <CheckCircle size={14} /> APPROVE FOR PRODUCTION
                            </button>
                        </div>
                    </Card>
                </div>

                {/* Right Sidebar: Strategic Command */}
                <div className="w-96 flex flex-col gap-4">
                    <Card className="flex-1 bg-gray-900 border-gray-800 overflow-hidden flex flex-col shadow-2xl relative">
                        <div className="p-4 border-b border-gray-800 bg-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-white">
                                <MessageSquare size={16} className="text-green-500" />
                                <span className="text-sm font-bold uppercase tracking-widest">Tactical Link</span>
                            </div>
                            <button className="p-1 hover:bg-white/5 rounded text-gray-500" title="Cross-Examine (Add Personnel)">
                                <UserPlus size={16} />
                            </button>
                        </div>

                        <ScrollArea className="flex-1 p-4">
                            <div className="space-y-4">
                                <div className="flex flex-col gap-1 max-w-[85%]">
                                    <span className="text-[10px] text-gray-500 ml-2">{selectedPersonnel.name}</span>
                                    <div className="p-3 bg-gray-800 rounded-2xl rounded-tl-none text-sm text-gray-200 border border-white/5">
                                        Strategic mission received. I am currently analyzing the current social trends to optimize your outreach.
                                    </div>
                                </div>
                            </div>
                        </ScrollArea>

                        <div className="p-4 bg-gray-950 border-t border-gray-800">
                            <div className="relative">
                                <textarea
                                    placeholder="Delegate command..."
                                    className="w-full bg-gray-900 border border-gray-800 rounded-xl p-3 pt-4 pr-12 text-sm text-gray-200 focus:outline-none focus:border-green-500/50 resize-none h-24 scrollbar-hide"
                                />
                                <button className="absolute bottom-3 right-3 p-2 bg-green-600 text-white rounded-lg hover:bg-green-500 transition-all">
                                    <Send size={16} />
                                </button>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                                <ShieldAlert size={12} className="text-yellow-500/50" />
                                <span className="text-[9px] text-gray-600 uppercase tracking-tighter">Authorized personnel interaction active</span>
                            </div>
                        </div>
                    </Card>
                </div>

            </div>
        </AdminLayout>
    )
}
