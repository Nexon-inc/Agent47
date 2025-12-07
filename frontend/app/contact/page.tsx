"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { Mail, Phone, MapPin, Send, Clock, CheckCircle, ChevronDown, ChevronUp } from "lucide-react"

type FAQItem = {
  question: string
  answer: string
  isOpen?: boolean
}

export default function ContactPage() {
  const [formStatus, setFormStatus] = useState<"idle" | "submitting" | "success" | "error">("idle")
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  })
  const [faqs, setFaqs] = useState<FAQItem[]>([
    {
      question: "How do I get started with Agent47?",
      answer:
        "Getting started is easy! Simply sign up for a free account, choose your AI agents based on your workflow needs, and follow our guided setup process. You'll be automating tasks in minutes.",
      isOpen: true,
    },
    {
      question: "Can I switch between different agents?",
      answer:
        "Yes! Depending on your plan, you can swap agents monthly. The Starter plan allows 3 agents, Pro allows 6, and Ecosystem gives you access to all available agents.",
      isOpen: false,
    },
    {
      question: "How does billing work?",
      answer:
        "We offer monthly and annual billing options. Annual plans save you 10%. You can upgrade, downgrade, or cancel your subscription at any time through your account settings.",
      isOpen: false,
    },
    {
      question: "Is my data secure with Agent47?",
      answer:
        "Absolutely. We use enterprise-grade security measures including AES-256 encryption for data at rest and TLS 1.3 for data in transit. We never sell your data to third parties and comply with GDPR and CCPA regulations.",
      isOpen: false,
    },
    {
      question: "What integrations do you support?",
      answer:
        "Agent47 integrates with popular tools like Slack, Gmail, Zapier, Salesforce, HubSpot, and Notion. Each agent has specific integration capabilities tailored to its function.",
      isOpen: false,
    },
  ])

  const toggleFAQ = (index: number) => {
    setFaqs(
      faqs.map((faq, i) => {
        if (i === index) {
          return { ...faq, isOpen: !faq.isOpen }
        }
        return faq
      }),
    )
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormStatus("submitting")

    // Simulate API call
    setTimeout(() => {
      setFormStatus("success")
      // Reset form after success
      setFormData({
        name: "",
        email: "",
        subject: "",
        message: "",
      })
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header with navigation */}
      <header className="h-20 bg-white shadow-sm fixed top-0 left-0 right-0 z-50">
        <div className="container mx-auto px-4 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center">
            <span className="text-slate-900 font-extrabold text-2xl">
              Agent<span className="text-green-500">47</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center space-x-6">
            <Link href="/" className="text-gray-600 hover:text-green-600 transition-colors">
              Home
            </Link>
            <Link href="/#features" className="text-gray-600 hover:text-green-600 transition-colors">
              Features
            </Link>
            <Link href="/#pricing" className="text-gray-600 hover:text-green-600 transition-colors">
              Pricing
            </Link>
            <Link href="/auth" className="text-gray-600 hover:text-green-600 transition-colors">
              Sign In
            </Link>
            <Link
              href="/auth?tab=signup"
              className="bg-gradient-to-r from-green-400 to-green-600 text-white px-4 py-2 rounded-lg hover:shadow-md transition-all duration-300"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="pt-32 pb-20">
        <div className="container mx-auto px-4 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          <div className="text-center mb-16">
            <h1 className="text-4xl font-extrabold text-slate-900 mb-4">Contact Us</h1>
            <p className="text-xl text-gray-600 max-w-[800px] mx-auto">
              Have questions about Agent47? Our team is here to help you automate your workflows.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 max-w-6xl mx-auto">
            {/* Contact Form */}
            <div>
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                <div className="bg-gradient-to-r from-[#4B0082] to-[#1E90FF] px-8 py-6 text-white">
                  <h2 className="text-2xl font-bold">Send Us a Message</h2>
                  <p className="text-white/80">We'll get back to you within 24 hours</p>
                </div>

                <div className="p-8">
                  {formStatus === "success" ? (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center py-8"
                    >
                      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <CheckCircle className="w-8 h-8 text-green-500" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">Message Sent!</h3>
                      <p className="text-gray-600 mb-6">
                        Thank you for reaching out. We'll get back to you as soon as possible.
                      </p>
                      <button
                        onClick={() => setFormStatus("idle")}
                        className="text-green-600 hover:text-green-700 transition-colors font-medium"
                      >
                        Send another message
                      </button>
                    </motion.div>
                  ) : (
                    <form onSubmit={handleSubmit}>
                      <div className="grid grid-cols-1 gap-6">
                        <div>
                          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                            Your Name
                          </label>
                          <input
                            type="text"
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            required
                            className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                            placeholder="John Doe"
                          />
                        </div>

                        <div>
                          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                            Email Address
                          </label>
                          <input
                            type="email"
                            id="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                            placeholder="your.email@example.com"
                          />
                        </div>

                        <div>
                          <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
                            Subject
                          </label>
                          <select
                            id="subject"
                            name="subject"
                            value={formData.subject}
                            onChange={handleChange}
                            required
                            className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                          >
                            <option value="">Select a topic</option>
                            <option value="Sales Inquiry">Sales Inquiry</option>
                            <option value="Technical Support">Technical Support</option>
                            <option value="Billing Question">Billing Question</option>
                            <option value="Feature Request">Feature Request</option>
                            <option value="Partnership">Partnership</option>
                            <option value="Other">Other</option>
                          </select>
                        </div>

                        <div>
                          <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                            Message
                          </label>
                          <textarea
                            id="message"
                            name="message"
                            value={formData.message}
                            onChange={handleChange}
                            required
                            rows={5}
                            className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                            placeholder="How can we help you?"
                          ></textarea>
                        </div>

                        <div>
                          <button
                            type="submit"
                            disabled={formStatus === "submitting"}
                            className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-white bg-gradient-to-r from-green-400 to-green-600 hover:shadow-lg hover:shadow-green-500/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 font-semibold transition-all duration-300 ${
                              formStatus === "submitting" ? "opacity-70 cursor-not-allowed" : ""
                            }`}
                          >
                            {formStatus === "submitting" ? (
                              <>
                                <svg
                                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                >
                                  <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                  ></circle>
                                  <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                  ></path>
                                </svg>
                                Sending...
                              </>
                            ) : (
                              <>
                                Send Message <Send className="ml-2 h-5 w-5" />
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            {/* Contact Info & FAQs */}
            <div className="space-y-8">
              {/* Contact Info */}
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                <div className="bg-gradient-to-r from-green-400 to-green-600 px-8 py-6 text-white">
                  <h2 className="text-2xl font-bold">Contact Information</h2>
                  <p className="text-white/80">Reach out to us directly</p>
                </div>

                <div className="p-8">
                  <div className="space-y-6">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                          <Mail className="h-5 w-5 text-green-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-medium text-gray-900">Email</h3>
                        <p className="mt-1 text-gray-600">agent47assist@gmail.com</p>
                      </div>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                          <Phone className="h-5 w-5 text-green-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-medium text-gray-900">Phone</h3>
                        <p className="mt-1 text-gray-600">+1 (555) 123-4567</p>
                        <p className="mt-1 text-gray-600">Mon-Fri, 9AM-6PM EST</p>
                      </div>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                          <MapPin className="h-5 w-5 text-green-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-medium text-gray-900">Office</h3>
                        <p className="mt-1 text-gray-600">123 Innovation Drive</p>
                        <p className="mt-1 text-gray-600">Tech City, TC 10101</p>
                      </div>
                    </div>

                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                          <Clock className="h-5 w-5 text-green-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-medium text-gray-900">Hours</h3>
                        <p className="mt-1 text-gray-600">Monday - Friday: 9AM - 6PM EST</p>
                        <p className="mt-1 text-gray-600">Saturday - Sunday: Closed</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* FAQs */}
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                <div className="bg-gradient-to-r from-green-400 to-green-600 px-8 py-6 text-white">
                  <h2 className="text-2xl font-bold">Frequently Asked Questions</h2>
                  <p className="text-white/80">Quick answers to common questions</p>
                </div>

                <div className="p-8">
                  <div className="space-y-4">
                    {faqs.map((faq, index) => (
                      <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
                        <button
                          className="flex justify-between items-center w-full text-left py-2 focus:outline-none"
                          onClick={() => toggleFAQ(index)}
                        >
                          <h3 className="text-lg font-medium text-gray-900">{faq.question}</h3>
                          {faq.isOpen ? (
                            <ChevronUp className="h-5 w-5 text-green-600" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-green-600" />
                          )}
                        </button>
                        {faq.isOpen && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="mt-2 text-gray-600"
                          >
                            <p>{faq.answer}</p>
                          </motion.div>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-200">
                    <p className="text-gray-600">
                      Can't find what you're looking for?{" "}
                      <button
                        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
                        className="text-green-600 hover:text-green-700 transition-colors font-medium"
                      >
                        Contact us directly
                      </button>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
