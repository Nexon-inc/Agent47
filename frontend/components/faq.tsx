"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, Minus, HelpCircle } from "lucide-react"

const faqs = [
    {
        question: "Wait, so these aren't real people?",
        answer: "Correct! Think of them as specialized software that works exactly like a high-performing employee would. Instead of hiring a social media manager for $3,500/month, you 'hire' Aria. She creates content, monitors engagement, and optimizes strategy 24/7 for a fraction of the cost. Not a human, but performs the work around the clock.",
    },
    {
        question: "Can AI really do these jobs well?",
        answer: "AI employees excel at speed, consistency, and scale. They offer instant responses and 24/7 availability while handling thousands of tasks simultaneously. While they don't handle high-level creative strategy or complex human negotiations yet, they are designed to handle 90% of the operational workload, freeing you to focus on the strategic decisions only you can make.",
    },
    {
        question: "Is $149/month expensive for software?",
        answer: "We reframe the cost: you're not just buying software; you're hiring a 7-person specialized team. A human team of a Sales Director, Marketing Manager, Content Creator, and Support Specialists would cost over $29,000/month. Agent47 delivers the same operational output for $149/month—a 99.5% savings on your overhead.",
    },
    {
        question: "How do I stay in control of my AI team?",
        answer: "You are the Boss. Our 'Human-in-the-Loop' system ensures that for critical tasks—like posting to social media or sending proposals—your AI employees will prepare the work and wait for your one-click approval. You get the autonomy of a team with the control of a founder.",
    },
    {
        question: "How long does it take to 'onboard' an employee?",
        answer: "Our onboarding process takes less than 5 minutes. You'll brief your team on your brand voice, business goals, and target audience. Once finished, your AI employees are ready to start working immediately—no training periods or long ramp-up times required.",
    },
    {
        question: "Can I fire or swap agents if my needs change?",
        answer: "Absolutely. Your AI workforce is fully flexible. You can scale your team up or down instantly based on your business needs. No messy offboarding or severance required. You're in complete control of your team's composition at all times.",
    },
]

export default function FAQ() {
    const [activeIndex, setActiveIndex] = useState<number | null>(null)

    return (
        <section className="py-24 bg-white relative overflow-hidden">
            <div className="container mx-auto px-4 max-w-4xl relative z-10">
                <motion.div
                    className="text-center mb-16"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5 }}
                >
                    <div className="inline-flex items-center justify-center p-2 bg-green-50 rounded-xl mb-4">
                        <HelpCircle className="w-5 h-5 text-green-600 mr-2" />
                        <span className="text-green-600 font-semibold text-sm">FAQ</span>
                    </div>
                    <h2 className="text-3xl md:text-5xl font-extrabold mb-6 text-slate-900">
                        Common Questions about <span className="gradient-text">AI Employees</span>
                    </h2>
                    <p className="text-xl text-gray-600">
                        Everything you need to know about hiring your 24/7 digital workforce.
                    </p>
                </motion.div>

                <div className="space-y-4">
                    {faqs.map((faq, index) => (
                        <motion.div
                            key={index}
                            className="border border-gray-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300"
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.3, delay: index * 0.1 }}
                        >
                            <button
                                className="w-full px-6 py-5 text-left flex items-center justify-between bg-white hover:bg-gray-50 transition-colors"
                                onClick={() => setActiveIndex(activeIndex === index ? null : index)}
                            >
                                <span className="text-lg font-bold text-slate-800 pr-8">{faq.question}</span>
                                <div className={`p-2 rounded-full transition-colors ${activeIndex === index ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-400"}`}>
                                    {activeIndex === index ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                                </div>
                            </button>
                            <AnimatePresence>
                                {activeIndex === index && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.3, ease: "easeInOut" }}
                                    >
                                        <div className="px-6 pb-6 text-gray-600 leading-relaxed border-t border-gray-50 pt-4">
                                            {faq.answer}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    ))}
                </div>

                <motion.div
                    className="mt-16 p-8 bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl text-center text-white"
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                >
                    <h3 className="text-2xl font-bold mb-4">Still have questions?</h3>
                    <p className="text-slate-300 mb-8 max-w-lg mx-auto">
                        Our team is here to help you build the perfect AI workforce for your specific business needs.
                    </p>
                    <div className="flex flex-wrap justify-center gap-4">
                        <button className="px-8 py-3 bg-green-500 hover:bg-green-400 text-white font-bold rounded-xl transition-all">
                            Contact Support
                        </button>
                        <button className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl transition-all">
                            Book a Demo
                        </button>
                    </div>
                </motion.div>
            </div>
        </section>
    )
}
