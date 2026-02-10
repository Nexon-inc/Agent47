"use client"

import type React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import {
    ChevronRight,
    Book,
    Code,
    Activity,
    Zap,
    BarChart,
    Settings,
    Search,
    Menu,
    X,
    ArrowRight
} from "lucide-react"
import { useState, useEffect } from "react"
import Header from "./header"
import Footer from "./footer"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"

interface NavItem {
    title: string
    href: string
    items?: NavItem[]
}

const docsNav: NavItem[] = [
    {
        title: "Getting Started",
        href: "/documentation",
        items: [
            { title: "Introduction", href: "/documentation#introduction" },
            { title: "Quickstart", href: "/documentation#quickstart" },
            { title: "Core Concepts", href: "/documentation#concepts" },
        ],
    },
    {
        title: "API Reference",
        href: "/api",
        items: [
            { title: "Authentication", href: "/api#auth" },
            { title: "Personnel API", href: "/api#personnel" },
            { title: "Rate Limits", href: "/api#limits" },
            { title: "Error Codes", href: "/api#errors" },
        ],
    },
    {
        title: "Workforce",
        href: "/roadmap",
        items: [
            { title: "Roadmap", href: "/roadmap" },
            { title: "Specialists", href: "/features" },
        ],
    },
    {
        title: "System",
        href: "/status",
        items: [
            { title: "Real-time Status", href: "/status" },
            { title: "Incident History", href: "/status#history" },
        ],
    },
]

export default function DocsLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname()
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const [activeHeading, setActiveHeading] = useState("")

    // Simple scroll-spy logic for TOC
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setActiveHeading(entry.target.id)
                    }
                })
            },
            { rootMargin: "-20% 0% -35% 0%" }
        )

        const headings = document.querySelectorAll("h2, h3")
        headings.forEach((h) => observer.observe(h))

        return () => observer.disconnect()
    }, [children])

    return (
        <div className="min-h-screen bg-white">
            <Header />

            <div className="flex pt-20">
                {/* Mobile Sidebar Toggle */}
                <button
                    className="fixed bottom-4 right-4 z-50 p-3 bg-green-500 text-white rounded-full shadow-lg md:hidden"
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                >
                    {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
                </button>

                {/* Left Sidebar */}
                <aside
                    className={cn(
                        "fixed inset-y-0 left-0 z-40 w-64 bg-gray-50/50 backdrop-blur-xl border-r border-gray-200 transform md:translate-x-0 transition-transform duration-300 ease-in-out md:sticky md:top-20 md:h-[calc(100vh-5rem)]",
                        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
                    )}
                >
                    <ScrollArea className="h-full py-8 px-4">
                        <div className="space-y-6">
                            {docsNav.map((section, idx) => (
                                <div key={idx} className="space-y-2">
                                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest px-2">
                                        {section.title}
                                    </h4>
                                    <ul className="space-y-1">
                                        {section.items?.map((item, i) => (
                                            <li key={i}>
                                                <Link
                                                    href={item.href}
                                                    className={cn(
                                                        "flex items-center px-2 py-1.5 text-sm rounded-md transition-colors",
                                                        (pathname || "") + (item.href?.includes("#") ? item.href.split("#")[1] : "") === item.href
                                                            ? "bg-green-50 text-green-700 font-medium"
                                                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                                    )}
                                                    onClick={() => setIsSidebarOpen(false)}
                                                >
                                                    {item.title}
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 min-w-0 bg-white">
                    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                        {/* Breadcrumbs */}
                        <nav className="flex items-center space-x-2 text-xs text-gray-400 mb-8">
                            <Link href="/" className="hover:text-gray-600">Home</Link>
                            <ChevronRight size={12} />
                            <span className="text-gray-900 font-medium capitalize">
                                {(pathname || "").split("/").filter(Boolean).pop()?.replace("-", " ") || "Documentation"}
                            </span>
                        </nav>

                        <article className="prose prose-slate prose-green max-w-none">
                            {children}
                        </article>

                        {/* Pagination/Next Section */}
                        <div className="mt-16 pt-8 border-t border-gray-100 flex justify-between items-center text-sm">
                            <Link href="/" className="text-gray-500 hover:text-gray-900 flex items-center group">
                                <ChevronRight className="rotate-180 mr-2 group-hover:-translate-x-1 transition-transform" size={16} />
                                Previous Page
                            </Link>
                            <Link href="/api" className="text-green-600 font-semibold flex items-center group">
                                Next: API Reference
                                <ChevronRight className="ml-2 group-hover:translate-x-1 transition-transform" size={16} />
                            </Link>
                        </div>
                    </div>
                </main>

                {/* Right Sidebar (Table of Contents) */}
                <aside className="hidden xl:block w-64 sticky top-20 h-[calc(100vh-5rem)] border-l border-gray-100 px-6 py-10 overflow-y-auto">
                    <h5 className="text-xs font-bold text-gray-900 uppercase tracking-widest mb-4">
                        On this page
                    </h5>
                    <nav className="space-y-4">
                        {/* This would ideally be dynamic based on the page content */}
                        <ul className="text-sm space-y-3">
                            <li className="text-gray-500 hover:text-green-600 cursor-pointer transition-colors">Introduction</li>
                            <li className="text-gray-500 hover:text-green-600 cursor-pointer transition-colors">Prerequisites</li>
                            <li className="text-gray-500 hover:text-green-600 cursor-pointer transition-colors">Installation</li>
                            <li className="text-gray-500 hover:text-green-600 cursor-pointer transition-colors">Next Steps</li>
                        </ul>

                        <div className="mt-8 pt-8 border-t border-gray-100">
                            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                                <p className="text-xs text-green-800 font-medium mb-2 flex items-center">
                                    <Zap size={12} className="mr-1" /> Help & Support
                                </p>
                                <p className="text-[10px] text-green-700 leading-relaxed mb-3">
                                    Need specialized help with our API? Our personnel are here 24/7.
                                </p>
                                <Link href="/contact" className="text-[10px] font-bold text-green-800 hover:underline inline-flex items-center">
                                    Talk to Specialist <ArrowRight size={10} className="ml-1" />
                                </Link>
                            </div>
                        </div>
                    </nav>
                </aside>
            </div>

            <Footer />
        </div>
    )
}
