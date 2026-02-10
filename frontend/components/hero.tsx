"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Shield, Clock, MessageCircle, Mic, Send, User, Bot, Globe, Megaphone, FileText, DollarSign, CheckCircle2, Calendar, TrendingUp, Zap } from "lucide-react"

export default function Hero() {
  const mockupRef = useRef<HTMLDivElement>(null)
  const chatMessagesRef = useRef<HTMLDivElement>(null)
  const [currentMessage, setCurrentMessage] = useState(0)
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [showIntercommunication, setShowIntercommunication] = useState(false)
  const [thinkingStepIndex, setThinkingStepIndex] = useState(0)

  const chatMessages = [
    {
      type: "user",
      message: "Help me automate my social media marketing",
      time: "2:34 PM",
      isVoice: false
    },
    {
      type: "thinking",
      agent: "Aria",
      message: "Analyzing your connected platforms...",
      time: "2:34 PM",
      color: "from-orange-400 to-orange-600",
      avatar: "AR",
      thinkingSteps: [
        "Checking connected social media platforms...",
        "Found: LinkedIn, Twitter, Instagram",
        "Analyzing posting history and engagement patterns...",
        "Reviewing your content preferences and brand voice..."
      ]
    },
    {
      type: "bot",
      agent: "Aria",
      message: "I've analyzed your connected platforms. Here's your 7-day automation plan:\n\n📅 Week Overview\n• LinkedIn: 3 posts/day (9 AM, 1 PM, 5 PM)\n• Twitter: 5 posts/day (8 AM, 12 PM, 3 PM, 6 PM, 9 PM)\n• Instagram: 2 posts/day (10 AM, 7 PM) + 3 stories/day\n\n📝 Content Strategy\n1. Monday-Wednesday: Educational content\n2. Thursday-Friday: Product highlights\n3. Weekend: Community engagement\n\n⚡ Automation Features\n• Auto-scheduling based on optimal engagement times\n• Content suggestions aligned with your brand\n• Hashtag optimization\n• Cross-platform repurposing\n\nShould I start implementing this plan?",
      time: "2:35 PM",
      color: "from-orange-400 to-orange-600",
      avatar: "AR",
    },
    {
      type: "user",
      message: "Yes, please start!",
      time: "2:36 PM",
      isVoice: false,
    },
    {
      type: "thinking",
      agent: "Aria",
      message: "Setting up automation workflows...",
      time: "2:36 PM",
      color: "from-orange-400 to-orange-600",
      avatar: "AR",
      thinkingSteps: [
        "Creating content calendar for next 7 days...",
        "Generating post ideas based on your brand...",
        "Scheduling posts at optimal times...",
        "Setting up cross-platform automation..."
      ]
    },
    {
      type: "bot",
      agent: "Aria",
      message: "✅ Automation Setup Complete!\n\n📊 Created\n• 21 LinkedIn posts scheduled\n• 35 Twitter posts scheduled\n• 14 Instagram posts + 21 stories scheduled\n\n📋 Next Steps\n1. Review scheduled content (I'll send you a preview)\n2. Adjust timing if needed\n3. Monitor engagement metrics\n\nYour social media is now fully automated! 🚀",
      time: "2:37 PM",
      color: "from-orange-400 to-orange-600",
      avatar: "AR",
    },
    {
      type: "system",
      message: "🤝 Aria is coordinating with other specialists for enhanced automation...",
      time: "2:37 PM",
    },
    {
      type: "thinking",
      agent: "Jackie",
      message: "Analyzing marketing opportunities...",
      time: "2:38 PM",
      color: "from-pink-400 to-pink-600",
      avatar: "JA",
      thinkingSteps: [
        "Reviewing social media performance data...",
        "Identifying target audience segments...",
        "Designing campaign strategy...",
        "Preparing marketing assets..."
      ]
    },
    {
      type: "bot",
      agent: "Jackie",
      message: "📈 Marketing Campaign Strategy\n\nI'll amplify your social reach with targeted campaigns:\n\n• 📧 Email sequences aligned with your social posts\n• 🎯 Ad campaigns to drive traffic to your content\n• 👥 Audience segmentation for better targeting\n• 📊 Performance tracking and optimization\n\nCampaigns will launch in sync with your automated posts.",
      time: "2:38 PM",
      color: "from-pink-400 to-pink-600",
      avatar: "JA",
    },
    {
      type: "thinking",
      agent: "Shakes",
      message: "Creating content variations...",
      time: "2:39 PM",
      color: "from-green-400 to-green-600",
      avatar: "SH",
      thinkingSteps: [
        "Analyzing content performance patterns...",
        "Generating SEO-optimized captions...",
        "Creating content variations...",
        "Optimizing for engagement..."
      ]
    },
    {
      type: "bot",
      agent: "Shakes",
      message: "✍️ Content Optimization Complete\n\nI've created compelling content variations:\n\n• 🔍 SEO-optimized captions for all platforms\n• 💡 Content ideas aligned with your brand\n• ⚡ Engagement-focused variations\n• 🔄 Cross-platform adaptations\n\nAll content is ready for Aria's automation schedule.",
      time: "2:39 PM",
      color: "from-green-400 to-green-600",
      avatar: "SH",
    },
  ]

  useEffect(() => {
    const messageTimer = setInterval(() => {
      setCurrentMessage((prev) => {
        if (prev < chatMessages.length - 1) {
          const nextMsg = chatMessages[prev + 1]
          // Reset thinking step index when moving to a new thinking message
          if (nextMsg?.type === "thinking") {
            setThinkingStepIndex(0)
          }
          // Show intercommunication when system message appears
          if (nextMsg?.type === "system") {
            setShowIntercommunication(true)
          }
          return prev + 1
        }
        // Reset after showing all messages
        setTimeout(() => {
          setCurrentMessage(0)
          setThinkingStepIndex(0)
          setShowIntercommunication(false)
        }, 5000)
        return prev
      })
    }, 3500) // Longer delay to show thinking states properly

    return () => {
      clearInterval(messageTimer)
    }
  }, [])

  // Animate thinking steps
  useEffect(() => {
    const currentMsg = chatMessages[currentMessage]
    if (currentMsg?.type === "thinking" && currentMsg.thinkingSteps) {
      const stepTimer = setInterval(() => {
        setThinkingStepIndex((prev) => {
          if (prev < currentMsg.thinkingSteps.length - 1) {
            return prev + 1
          }
          return prev
        })
      }, 800) // Show each step every 800ms

      return () => {
        clearInterval(stepTimer)
      }
    } else {
      setThinkingStepIndex(0)
    }
  }, [currentMessage])

  // Auto-scroll chat messages
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTo({
        top: chatMessagesRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }, [currentMessage, thinkingStepIndex])

  return (
    <section className="relative min-h-[90vh] w-full overflow-hidden pt-8 bg-white">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#FFF8F0] to-[#FFF1E5] -z-10"></div>
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute -top-[30%] -left-[10%] w-[70%] h-[70%] rounded-full bg-gradient-to-br from-green-400/5 to-green-600/5 blur-3xl"></div>
        <div className="absolute top-[20%] -right-[20%] w-[60%] h-[60%] rounded-full bg-gradient-to-bl from-green-400/5 to-green-600/5 blur-3xl"></div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 2xl:px-12 3xl:px-16 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px] h-full">
        <div className="grid md:grid-cols-2 gap-12 h-full items-center py-8 md:py-16">
          <motion.div
            className="flex flex-col space-y-8 text-center md:text-left"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div>
              <motion.div
                className="inline-block px-4 py-1 rounded-full bg-gradient-to-r from-green-400/10 to-green-600/10 text-green-600 font-medium text-sm mb-6"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                Introducing Agent47 — Meet Your 24/7 AI Personnel
              </motion.div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 leading-tight">
                Hire Your <span className="gradient-text">Digital Personnel</span>
              </h1>
            </div>
            <p className="text-lg md:text-xl text-gray-600 max-w-[500px] mx-auto md:mx-0">
              Stop overpaying for local operations. Hire specialized AI personnel that work 24/7 across marketing, sales, and support for 1/100th of the cost.
            </p>

            <div className="flex flex-wrap gap-4 justify-center md:justify-start">
              <Link
                href="/onboarding"
                className="group bg-gradient-to-r from-green-400 to-green-600 text-white font-semibold px-8 py-4 rounded-lg hover:shadow-lg hover:shadow-green-500/30 transition-all duration-300 flex items-center"
              >
                Hire Your Team
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
              <Link
                href="#features"
                className="bg-white text-green-600 border border-green-600/20 font-semibold px-8 py-4 rounded-lg hover:bg-green-50 transition-all duration-300"
              >
                Explore Specialists
              </Link>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-6">
              {[
                { icon: MessageCircle, text: "Chat & Voice Control" },
                { icon: Shield, text: "Enterprise Security" },
                { icon: Clock, text: "24/7 Automation" },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  className="flex flex-col items-center md:items-start"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.6 + i * 0.1 }}
                >
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center mb-2">
                    <item.icon className="w-5 h-5 text-green-600" />
                  </div>
                  <p className="text-sm text-gray-600">{item.text}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="relative"
            ref={mockupRef}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {/* Glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-green-400/20 to-green-600/20 rounded-3xl blur-3xl -z-10 opacity-60"></div>

            {/* Modern Chat Interface */}
            <div className="relative bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden">
              {/* Chat Header */}
              <div className="bg-gradient-to-r from-green-400 to-green-600 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center ring-2 ring-white/30">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">Personnel Tactical Link</h3>
                      <div className="text-sm text-white/90 flex items-center">
                        <motion.div
                          className="w-2 h-2 rounded-full bg-white mr-2"
                          animate={{ opacity: [1, 0.5, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                        />
                        {showIntercommunication ? "🤝 Personnel Collaborating" : "🟢 Online & Ready"}
                      </div>
                    </div>
                  </div>
                  <motion.button
                    className={`p-3 rounded-full transition-all duration-300 ${isVoiceActive
                      ? "bg-red-500 text-white shadow-lg shadow-red-500/50 ring-2 ring-red-300"
                      : "bg-white/20 backdrop-blur-sm text-white hover:bg-white/30"
                      }`}
                    animate={{
                      scale: isVoiceActive ? [1, 1.1, 1] : 1,
                    }}
                    transition={{ duration: 0.5, repeat: isVoiceActive ? Infinity : 0 }}
                  >
                    <Mic className="w-5 h-5" />
                  </motion.button>
                </div>
              </div>

              {/* Chat Messages Container */}
              <div
                ref={chatMessagesRef}
                className="bg-gray-50/50 px-4 py-4 h-[420px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
              >
                <div className="space-y-4">
                  {chatMessages.slice(0, currentMessage + 1).map((msg, i) => {
                    const isThinking = msg.type === "thinking"
                    const isCurrentThinking = isThinking && i === currentMessage

                    return (
                      <motion.div
                        key={i}
                        className={`flex ${msg.type === "user" ? "justify-end" : msg.type === "system" ? "justify-center" : "justify-start"}`}
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ duration: 0.4, delay: i * 0.05 }}
                      >
                        {msg.type === "system" ? (
                          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-2.5 text-sm text-green-700 max-w-[85%] text-center shadow-sm">
                            <span className="font-medium">{msg.message}</span>
                          </div>
                        ) : (
                          <div
                            className={`flex items-end gap-2 max-w-[80%] ${msg.type === "user" ? "flex-row-reverse" : ""}`}
                          >
                            {/* Avatar */}
                            {(msg.type === "bot" || msg.type === "thinking") && (
                              <div className={`w-9 h-9 rounded-full bg-gradient-to-r ${msg.color} flex items-center justify-center text-white text-xs font-bold shadow-md flex-shrink-0 ${isThinking ? "animate-pulse" : ""
                                }`}>
                                {msg.avatar || msg.agent?.slice(0, 2) || "AI"}
                              </div>
                            )}
                            {msg.type === "user" && (
                              <div className="w-9 h-9 rounded-full bg-gradient-to-r from-green-400 to-green-600 flex items-center justify-center text-white shadow-md flex-shrink-0">
                                <User className="w-4 h-4" />
                              </div>
                            )}

                            {/* Message Bubble */}
                            <div className="flex flex-col">
                              {(msg.type === "bot" || msg.type === "thinking") && msg.agent && (
                                <span className="text-xs font-semibold mb-1 px-1 text-gray-600">
                                  {msg.agent}
                                </span>
                              )}

                              {isThinking ? (
                                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                                  <div className="flex items-center gap-2 mb-2">
                                    <div className="flex space-x-1">
                                      {[0, 1, 2].map((dot) => (
                                        <motion.div
                                          key={dot}
                                          className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                                          animate={{
                                            opacity: [0.3, 1, 0.3],
                                            scale: [1, 1.2, 1]
                                          }}
                                          transition={{
                                            duration: 1.5,
                                            repeat: Infinity,
                                            delay: dot * 0.2,
                                          }}
                                        />
                                      ))}
                                    </div>
                                    <span className="text-xs text-gray-500 italic">{msg.message}</span>
                                  </div>

                                  {/* Thinking Steps */}
                                  {msg.thinkingSteps && (
                                    <div className="space-y-1.5 pt-2 border-t border-gray-100">
                                      {msg.thinkingSteps.map((step: string, stepIndex: number) => {
                                        const isStepActive = isCurrentThinking && stepIndex <= thinkingStepIndex

                                        return (
                                          <motion.div
                                            key={stepIndex}
                                            className="flex items-center gap-2 text-xs text-gray-600"
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{
                                              opacity: isStepActive ? 1 : 0.3,
                                              x: 0
                                            }}
                                            transition={{ duration: 0.3 }}
                                          >
                                            <motion.div
                                              className="w-1 h-1 rounded-full bg-green-500"
                                              animate={isStepActive ? {
                                                scale: [1, 1.3, 1],
                                                opacity: [0.5, 1, 0.5]
                                              } : {
                                                scale: 1,
                                                opacity: 0.3
                                              }}
                                              transition={{ duration: 1, repeat: isStepActive ? Infinity : 0 }}
                                            />
                                            <span>{step}</span>
                                          </motion.div>
                                        )
                                      })}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div
                                  className={`rounded-2xl px-4 py-3 shadow-sm ${msg.type === "user"
                                    ? "bg-gradient-to-br from-green-400 to-green-600 text-white"
                                    : "bg-white border border-gray-200 text-gray-800"
                                    }`}
                                >
                                  {msg.isVoice && (
                                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/20">
                                      <Mic className="w-3.5 h-3.5" />
                                      <span className="text-xs font-medium opacity-90">Voice Message</span>
                                    </div>
                                  )}
                                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                                    {msg.message.split('\n').map((line, idx) => {
                                      // Format lines with emojis/icons
                                      if (line.trim().startsWith('📅') || line.trim().startsWith('📊') || line.trim().startsWith('📝') || line.trim().startsWith('⚡') || line.trim().startsWith('✅') || line.trim().startsWith('📋')) {
                                        return (
                                          <div key={idx} className="mt-2 first:mt-0">
                                            <span className="font-semibold text-gray-900">{line}</span>
                                          </div>
                                        )
                                      } else if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
                                        return (
                                          <div key={idx} className="flex items-start gap-2 mt-1.5">
                                            <span className="text-green-600 mt-1">•</span>
                                            <span>{line.replace(/^[•-]\s*/, '')}</span>
                                          </div>
                                        )
                                      } else if (line.trim().match(/^\d+\./)) {
                                        return (
                                          <div key={idx} className="flex items-start gap-2 mt-1.5">
                                            <span className="text-green-600 font-semibold mt-0.5">{line.match(/^\d+\./)?.[0]}</span>
                                            <span>{line.replace(/^\d+\.\s*/, '')}</span>
                                          </div>
                                        )
                                      } else if (line.trim() === '') {
                                        return <div key={idx} className="h-2" />
                                      } else {
                                        return <div key={idx} className={idx === 0 ? '' : 'mt-1.5'}>{line}</div>
                                      }
                                    })}
                                  </div>
                                  <p className={`text-xs mt-2 ${msg.type === "user"
                                    ? "text-white/70"
                                    : "text-gray-500"
                                    }`}>
                                    {msg.time}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    )
                  })}

                  {/* Typing Indicator - Only show when not thinking, use next agent's avatar */}
                  {currentMessage < chatMessages.length - 1 && chatMessages[currentMessage + 1]?.type !== "thinking" && (
                    (() => {
                      const nextMsg = chatMessages[currentMessage + 1]
                      const agentColor = nextMsg?.color || "from-green-400 to-green-600"
                      const agentAvatar = nextMsg?.avatar || "AI"

                      return (
                        <motion.div
                          className="flex justify-start items-center gap-2"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.3 }}
                        >
                          <div className={`w-9 h-9 rounded-full bg-gradient-to-r ${agentColor} flex items-center justify-center text-white text-xs font-bold shadow-md`}>
                            {agentAvatar}
                          </div>
                          <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                            <div className="flex space-x-1.5">
                              {[0, 1, 2].map((i) => (
                                <motion.div
                                  key={i}
                                  className="w-2 h-2 bg-green-500 rounded-full"
                                  animate={{
                                    y: [0, -6, 0],
                                    opacity: [0.5, 1, 0.5]
                                  }}
                                  transition={{
                                    duration: 1.2,
                                    repeat: Infinity,
                                    delay: i * 0.15,
                                  }}
                                />
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )
                    })()
                  )}
                </div>
              </div>

              {/* Chat Input Area */}
              <div className="bg-white border-t border-gray-200 px-4 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      placeholder={isVoiceActive ? "Listening..." : "Type a message or use voice..."}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                      readOnly
                    />
                    {isVoiceActive && (
                      <motion.div
                        className="absolute right-3 top-1/2 -translate-y-1/2"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      </motion.div>
                    )}
                  </div>
                  <motion.button
                    className={`p-3 rounded-xl transition-all duration-300 ${isVoiceActive
                      ? "bg-red-500 text-white shadow-lg shadow-red-500/50"
                      : "bg-gradient-to-r from-green-400 to-green-600 text-white hover:shadow-lg hover:shadow-green-500/30"
                      }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isVoiceActive ? (
                      <Mic className="w-5 h-5" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </motion.button>
                </div>

                {/* Voice Status Indicator */}
                {isVoiceActive && (
                  <motion.div
                    className="mt-3 flex items-center justify-center gap-2 text-red-600 text-xs font-medium"
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                  >
                    <motion.div
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      <Mic className="w-4 h-4" />
                    </motion.div>
                    <span>Recording voice message...</span>
                  </motion.div>
                )}
              </div>
            </div>

          </motion.div>
        </div>
      </div>

    </section>
  )
}

