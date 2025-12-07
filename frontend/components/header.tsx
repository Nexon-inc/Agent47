"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Menu, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header
      className={cn(
        "fixed top-0 w-full z-50 transition-all duration-300",
        scrolled ? "bg-white/90 backdrop-blur-md shadow-sm" : "bg-transparent",
      )}
    >
      <div className="container mx-auto px-4 py-4 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px] flex items-center justify-between">
        <Link href="/" prefetch={true} className="group relative z-10">
          <div className="flex items-center transition-all duration-300">
            <span className="text-slate-900 font-extrabold text-2xl">
              Agent
              <span className="text-green-500 relative">
                47
                <span className="absolute -inset-1 rounded-full blur-sm bg-green-500/30 -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
              </span>
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-8">
          {[
            { name: "Home", href: "/" },
            { name: "Features", href: "/features" },
            { name: "Pricing", href: "/pricing" },
            // Removed "Explore Agents", "Blog", "Contact"
          ].map((item, index) => (
            <Link
              key={index}
              href={item.href}
              prefetch={true}
              className="text-slate-900 hover:text-green-600 transition-colors duration-300 font-normal text-base relative group"
            >
              {item.name}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-green-400 to-green-600 group-hover:w-full transition-all duration-300"></span>
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center space-x-4">
          <Link
            href="/auth"
            prefetch={true}
            className="text-[#4B0082] hover:text-[#1E90FF] transition-colors duration-300 font-normal text-base"
          >
            Sign In
          </Link>
          <Link
            href="/auth?tab=signup"
            prefetch={true}
            className="bg-gradient-to-r from-green-400 to-green-600 text-white font-semibold px-6 py-2 rounded-lg hover:shadow-lg hover:shadow-green-500/30 transition-all duration-300 relative overflow-hidden group"
          >
            <span className="relative z-10">Get Started</span>
            <span className="absolute inset-0 bg-gradient-to-r from-green-600 to-green-400 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></span>
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <div className="md:hidden flex items-center space-x-2 z-50">
          <button
            className="text-[#4B0082]"
            onClick={() => setIsOpen(!isOpen)}
            aria-expanded={isOpen}
            aria-label="Toggle menu"
          >
            {isOpen ? <X size={32} /> : <Menu size={32} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="md:hidden fixed inset-0 bg-white/80 backdrop-blur-md z-40 pt-20 px-4"
            initial={{ opacity: 0, x: "100%" }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: "100%" }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            <nav className="flex flex-col space-y-6 items-center mt-8">
              {[
                { name: "Home", href: "/" },
                { name: "Features", href: "/features" },
                { name: "Pricing", href: "/pricing" },
                // Removed "Explore Agents", "Blog", "Contact"
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link
                    href={item.href}
                    className="text-slate-900 text-xl font-normal"
                    onClick={() => setIsOpen(false)}
                  >
                    {item.name}
                  </Link>
                </motion.div>
              ))}
              <motion.div
                className="pt-6 flex flex-col space-y-4 w-full items-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <Link href="/auth" className="text-slate-900 text-xl font-normal" onClick={() => setIsOpen(false)}>
                  Sign In
                </Link>
                <Link
                  href="/auth?tab=signup"
                  className="bg-gradient-to-r from-green-400 to-green-600 text-white font-semibold px-6 py-3 rounded-lg w-full max-w-[300px] text-center"
                  onClick={() => setIsOpen(false)}
                >
                  Get Started
                </Link>
              </motion.div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
