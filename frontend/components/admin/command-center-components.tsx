"use client"

import { motion } from "framer-motion"
import { Users, Zap, TrendingUp, Brain, Shield, Target, Briefcase, Activity } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

// --- ROI Ticker Component ---
export function ExecutiveROITicker() {
    const metrics = [
        { label: "Man-Hours Saved", value: "14,208", sub: "+12% this week", icon: Zap, color: "text-yellow-500" },
        { label: "Automation ROI", value: "$412,850", sub: "Est. annual savings", icon: TrendingUp, color: "text-green-500" },
        { label: "Personnel Efficiency", value: "98.2%", sub: "Optimal utilization", icon: Activity, color: "text-blue-500" },
        { label: "Active Subsidies", value: "24", sub: "AI credit optimizations", icon: Briefcase, color: "text-purple-500" },
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.map((m, i) => (
                <Card key={i} className="bg-gray-900/40 border-gray-800 p-4 backdrop-blur-md hover:border-green-500/30 transition-all group">
                    <div className="flex items-center gap-3 mb-2">
                        <div className={cn("p-2 rounded-lg bg-gray-800 group-hover:bg-gray-700 transition-colors", m.color)}>
                            <m.icon size={18} />
                        </div>
                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{m.label}</span>
                    </div>
                    <div className="text-2xl font-black text-white">{m.value}</div>
                    <div className="text-[10px] text-gray-500 mt-1">{m.sub}</div>
                </Card>
            ))}
        </div>
    )
}

// --- Skill Matrix / Talent Card Component ---
export function PersonnelTalentCard({ name, role, stats, avatar, active }: any) {
    return (
        <Card className={cn(
            "bg-gray-900/60 border-gray-800 p-5 backdrop-blur-xl relative overflow-hidden transition-all group hover:shadow-2xl hover:shadow-green-500/10",
            active ? "ring-1 ring-green-500/50 border-green-500/20" : ""
        )}>
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gray-700 to-gray-900 border border-gray-700 flex items-center justify-center text-lg font-bold text-white shadow-lg">
                        {avatar}
                    </div>
                    <div>
                        <h4 className="text-sm font-black text-white leading-none mb-1">{name}</h4>
                        <p className="text-[10px] text-gray-500 font-medium uppercase tracking-tighter">{role}</p>
                    </div>
                </div>
                <Badge status={active ? "active" : "idle"} />
            </div>

            <div className="space-y-3">
                {stats.map((s: any, i: number) => (
                    <div key={i} className="space-y-1">
                        <div className="flex justify-between text-[10px] uppercase font-bold tracking-widest">
                            <span className="text-gray-500">{s.label}</span>
                            <span className="text-white">{s.value}</span>
                        </div>
                        <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${s.value}%` }}
                                className="h-full bg-green-500"
                            />
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    )
}

function Badge({ status }: { status: "active" | "idle" }) {
    return (
        <div className={cn(
            "px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest border",
            status === "active" ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-gray-800 text-gray-500 border-gray-700"
        )}>
            {status}
        </div>
    )
}

// --- Interactive Org Chart Component ---
export function InteractiveOrgChart() {
    const departments = [
        { name: "Growth", color: "from-orange-500 to-red-500", personnel: ["Aria", "Eric", "Jackie"] },
        { name: "Intelligence", color: "from-blue-500 to-cyan-500", personnel: ["Joe", "Shakes"] },
        { name: "Operations", color: "from-purple-500 to-indigo-500", personnel: ["Clara", "Purity"] },
    ]

    return (
        <Card className="bg-gray-900/40 border-gray-800 p-6 backdrop-blur-md">
            <div className="flex items-center gap-2 mb-6">
                <Target size={16} className="text-green-500" />
                <h3 className="text-xs font-bold text-white uppercase tracking-widest">Workforce Org Chart</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
                {/* Connector Lines (Abstract) */}
                <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-gray-800 to-transparent hidden md:block" />

                {departments.map((dept, i) => (
                    <div key={i} className="relative z-10 flex flex-col items-center">
                        <div className={cn("w-24 h-8 rounded-full bg-gradient-to-r p-px mb-4", dept.color)}>
                            <div className="w-full h-full bg-gray-950 rounded-full flex items-center justify-center">
                                <span className="text-[10px] font-black text-white uppercase">{dept.name}</span>
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 w-full">
                            {dept.personnel.map((p, j) => (
                                <div key={j} className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/50 text-center text-xs text-gray-400 font-medium hover:text-white hover:border-gray-600 transition-colors cursor-pointer">
                                    {p}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    )
}

// --- Company Brain Visual Component ---
export function CompanyBrainVisual() {
    return (
        <Card className="bg-gray-900/80 border-gray-800 p-8 flex flex-col items-center justify-center min-h-[300px] overflow-hidden relative">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-green-500/10 via-transparent to-transparent opacity-50" />

            <div className="relative">
                <motion.div
                    animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0.8, 0.5] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="w-48 h-48 rounded-full border border-green-500/20 blur-xl absolute -inset-4"
                />
                <div className="w-40 h-40 rounded-full border-2 border-green-500/30 flex items-center justify-center relative bg-black/40 backdrop-blur-2xl">
                    <Brain size={60} className="text-green-500 drop-shadow-[0_0_15px_rgba(34,197,94,0.5)]" />
                    {/* Abstract Data Nodes */}
                    {[...Array(6)].map((_, i) => (
                        <motion.div
                            key={i}
                            animate={{
                                rotate: 360,
                                translateY: [0, -10, 0]
                            }}
                            transition={{ duration: 10 + i * 2, repeat: Infinity, ease: "linear" }}
                            className="absolute w-2 h-2 rounded-full bg-green-500"
                            style={{
                                left: '50%',
                                top: '50%',
                                margin: '-4px',
                                transform: `rotate(${i * 60}deg) translateY(-60px)`
                            }}
                        />
                    ))}
                </div>
            </div>

            <div className="mt-8 text-center relative z-10">
                <h4 className="text-sm font-black text-white uppercase tracking-widest mb-2">Company Brain Active</h4>
                <p className="text-[10px] text-gray-500 max-w-[200px] leading-relaxed uppercase">
                    Neural synchronization at 99.4% — All authorized personnel connected.
                </p>
                <button className="mt-4 px-4 py-1.5 rounded-full border border-green-500/30 bg-green-500/5 text-[10px] font-bold text-green-400 hover:bg-green-500/10 transition-colors uppercase tracking-widest">
                    Neural Intercept
                </button>
            </div>
        </Card>
    )
}
