"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronLeft, ChevronRight, Star, Quote } from "lucide-react"

const testimonials = [
  {
    quote: "Aria cut my social media workload in half! I can now focus on strategy instead of scheduling.",
    author: "Jane Doe",
    title: "Marketing Lead",
    company: "GrowEasy Inc.",
    rating: 5,
    agentUsed: "Aria",
    image: "/placeholder.svg?height=80&width=80",
    highlight: true,
  },
  {
    quote: "Jackie handles our customer inquiries 24/7, and our satisfaction scores have never been higher.",
    author: "Michael Chen",
    title: "Customer Success Manager",
    company: "TechFlow Solutions",
    rating: 5,
    agentUsed: "Jackie",
    image: "/placeholder.svg?height=80&width=80",
    highlight: false,
  },
  {
    quote: "Shakes helps us create content that ranks. Our organic traffic is up 200% since we started using it.",
    author: "Sarah Johnson",
    title: "Content Director",
    company: "MediaPulse",
    rating: 5,
    agentUsed: "Shakes",
    image: "/placeholder.svg?height=80&width=80",
    highlight: false,
  },
  {
    quote: "Clara's marketing insights helped us identify segments we were missing. Game changer for our campaigns.",
    author: "David Wilson",
    title: "CMO",
    company: "Nexus Brands",
    rating: 5,
    agentUsed: "Clara",
    image: "/placeholder.svg?height=80&width=80",
    highlight: false,
  },
  {
    quote: "Eric transformed our sales process. The lead scoring is scary accurate and our close rate is up 35%.",
    author: "Olivia Martinez",
    title: "Sales Director",
    company: "GrowthForce",
    rating: 5,
    agentUsed: "Eric",
    image: "/placeholder.svg?height=80&width=80",
    highlight: false,
  },
]

export default function Testimonials() {
  const [current, setCurrent] = useState(0)
  const [autoplay, setAutoplay] = useState(true)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const next = () => {
    setCurrent((current + 1) % testimonials.length)
  }

  const prev = () => {
    setCurrent((current - 1 + testimonials.length) % testimonials.length)
  }

  const goTo = (index: number) => {
    setCurrent(index)
  }

  useEffect(() => {
    if (autoplay) {
      timerRef.current = setInterval(() => {
        next()
      }, 5000)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [current, autoplay])

  const handleMouseEnter = () => {
    setAutoplay(false)
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
  }

  const handleMouseLeave = () => {
    setAutoplay(true)
  }

  return (
    <section className="py-24 bg-gradient-to-b from-[#FFF8F0] to-white relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute top-1/4 left-0 w-full h-1/2 bg-[#4B0082]/5 -skew-y-6 -z-10"></div>

      <div className="container mx-auto px-4">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl md:text-5xl font-extrabold mb-6">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">
              What Our Users Say
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-[800px] mx-auto">
            Join thousands automating their workflows with Agent47.
          </p>
        </motion.div>

        <div
          className="relative max-w-6xl mx-auto"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          role="carousel"
          aria-label="User testimonials"
        >
          <div className="overflow-hidden rounded-2xl">
            <AnimatePresence mode="wait">
              <motion.div
                key={current}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-white shadow-xl rounded-2xl overflow-hidden"
              >
                <div className="grid md:grid-cols-2">
                  <div
                    className={`${testimonials[current].highlight ? "bg-gradient-to-br from-green-400 to-green-600" : "bg-gradient-to-br from-green-500 to-green-700"} p-8 md:p-12 flex flex-col justify-between relative`}
                  >
                    <Quote className="w-16 h-16 text-white/10 absolute top-6 left-6" />
                    <div className="relative z-10">
                      <div className="inline-block px-3 py-1 rounded-full bg-white/20 text-white text-sm mb-6">
                        Using {testimonials[current].agentUsed}
                      </div>
                      <blockquote className="text-xl md:text-2xl font-medium text-white mb-8">
                        "{testimonials[current].quote}"
                      </blockquote>
                      <div className="flex mb-2">
                        {[...Array(testimonials[current].rating)].map((_, i) => (
                          <Star key={i} className="w-5 h-5 fill-[#FFD700] text-[#FFD700]" />
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center mt-8">
                      <img
                        src={testimonials[current].image || "/placeholder.svg"}
                        alt={testimonials[current].author}
                        className="w-14 h-14 rounded-full object-cover mr-4"
                      />
                      <div>
                        <h3 className="font-bold text-white">{testimonials[current].author}</h3>
                        <p className="text-white/80 text-sm">
                          {testimonials[current].title}, {testimonials[current].company}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-8 md:p-12 flex flex-col justify-center">
                    <h3 className="text-2xl font-bold text-slate-900 mb-6">
                      Results with {testimonials[current].agentUsed}
                    </h3>

                    <div className="space-y-6">
                      {[
                        { label: "Time Saved", value: "18+ hours/week" },
                        { label: "ROI", value: "347%" },
                        { label: "Team Satisfaction", value: "96%" },
                      ].map((stat, i) => (
                        <div key={i} className="flex justify-between items-center pb-4 border-b border-gray-100">
                          <span className="text-gray-600">{stat.label}</span>
                          <span className="text-xl font-bold text-green-600">{stat.value}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-8 pt-6 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <div className="text-sm text-gray-500">Industry Average</div>
                        <div className="text-sm text-gray-500">Agent47 Performance</div>
                      </div>
                      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-green-400 to-green-600 w-[75%]"></div>
                      </div>
                      <div className="mt-2 text-sm text-gray-500 text-right">75% better than industry average</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation Arrows */}
          <button
            className="absolute top-1/2 left-4 -translate-y-1/2 w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-green-600 hover:text-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 z-10"
            onClick={prev}
            aria-label="Previous testimonial"
          >
            <ChevronLeft size={24} />
          </button>
          <button
            className="absolute top-1/2 right-4 -translate-y-1/2 w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-green-600 hover:text-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 z-10"
            onClick={next}
            aria-label="Next testimonial"
          >
            <ChevronRight size={24} />
          </button>

          {/* Dots */}
          <div className="flex justify-center space-x-3 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                className={`w-3 h-3 rounded-full transition-colors ${
                  current === index ? "bg-gradient-to-r from-green-400 to-green-600" : "bg-gray-300 hover:bg-gray-400"
                }`}
                onClick={() => goTo(index)}
                aria-label={`Go to testimonial ${index + 1}`}
                aria-current={current === index ? "true" : "false"}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
