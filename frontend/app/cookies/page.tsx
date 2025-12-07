"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft, Cookie, Settings, BarChart3, Target, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Header from "@/components/header"
import Footer from "@/components/footer"

export default function CookiesPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <Header />

      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 2xl:px-12 3xl:px-16">
        <div className="max-w-7xl mx-auto 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
          {/* Back Button */}
          <Link
            href="/"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>

          {/* Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Badge className="mb-4 bg-gradient-to-r from-green-400 to-green-600 text-white">
              <Cookie className="w-3 h-3 mr-1" />
              Cookie Policy
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">Cookie Policy</h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Learn how Agent47 uses cookies to improve your experience and protect your privacy.
            </p>
            <p className="text-sm text-gray-500 mt-4">Last Updated: January 1, 2025</p>
          </motion.div>

          {/* What Are Cookies */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6">What Are Cookies?</h2>
            <p className="text-gray-700 mb-4">
              Cookies are small text files that are placed on your device when you visit our website. They help us
              provide you with a better experience by remembering your preferences, understanding how you use our
              service, and improving our platform.
            </p>
            <p className="text-gray-700">
              We use both session cookies (which expire when you close your browser) and persistent cookies (which stay
              on your device until they expire or you delete them).
            </p>
          </motion.div>

          {/* Types of Cookies */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-8">Types of Cookies We Use</h2>
            <div className="space-y-8">
              {[
                {
                  title: "Essential Cookies",
                  icon: Settings,
                  color: "from-blue-500 to-cyan-500",
                  required: true,
                  description:
                    "These cookies are necessary for the website to function properly. They enable core functionality such as security, authentication, and accessibility features.",
                  examples: [
                    { name: "session_id", purpose: "Maintains your login session", duration: "Session" },
                    { name: "csrf_token", purpose: "Protects against cross-site request forgery", duration: "Session" },
                    { name: "cookie_consent", purpose: "Remembers your cookie preferences", duration: "1 year" },
                  ],
                },
                {
                  title: "Functional Cookies",
                  icon: CheckCircle2,
                  color: "from-green-500 to-emerald-500",
                  required: false,
                  description:
                    "These cookies allow us to remember your choices and provide enhanced features and personalization.",
                  examples: [
                    { name: "theme_preference", purpose: "Remembers your dark/light mode choice", duration: "1 year" },
                    { name: "language", purpose: "Stores your preferred language", duration: "1 year" },
                    { name: "dashboard_layout", purpose: "Saves your dashboard customizations", duration: "6 months" },
                  ],
                },
                {
                  title: "Analytics Cookies",
                  icon: BarChart3,
                  color: "from-purple-500 to-pink-500",
                  required: false,
                  description:
                    "These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously.",
                  examples: [
                    { name: "_ga", purpose: "Google Analytics - distinguishes users", duration: "2 years" },
                    { name: "_gid", purpose: "Google Analytics - distinguishes sessions", duration: "24 hours" },
                    { name: "analytics_id", purpose: "Internal analytics tracking", duration: "1 year" },
                  ],
                },
                {
                  title: "Marketing Cookies",
                  icon: Target,
                  color: "from-orange-500 to-red-500",
                  required: false,
                  description:
                    "These cookies track your online activity to help advertisers deliver more relevant advertising or to limit how many times you see an ad.",
                  examples: [
                    { name: "_fbp", purpose: "Facebook Pixel tracking", duration: "3 months" },
                    { name: "ads_preference", purpose: "Ad personalization settings", duration: "1 year" },
                    { name: "campaign_id", purpose: "Tracks marketing campaign source", duration: "30 days" },
                  ],
                },
              ].map((category, index) => (
                <div key={index} className="border border-gray-200 rounded-xl p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <div
                        className={`w-12 h-12 rounded-xl bg-gradient-to-r ${category.color} flex items-center justify-center mr-4`}
                      >
                        <category.icon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">{category.title}</h3>
                        <Badge
                          className={
                            category.required
                              ? "bg-red-100 text-red-700"
                              : "bg-green-100 text-green-700"
                          }
                        >
                          {category.required ? "Required" : "Optional"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <p className="text-gray-700 mb-4">{category.description}</p>
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-900">Examples:</h4>
                    {category.examples.map((example, i) => (
                      <div key={i} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <code className="text-sm font-mono text-blue-600">{example.name}</code>
                          <span className="text-xs text-gray-500">{example.duration}</span>
                        </div>
                        <p className="text-sm text-gray-600">{example.purpose}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Managing Cookies */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6">How to Manage Cookies</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">In Your Dashboard</h3>
                <p className="text-gray-700 mb-4">
                  You can manage your cookie preferences directly in your Agent47 dashboard:
                </p>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Go to Settings → Privacy</li>
                  <li>Click "Cookie Preferences"</li>
                  <li>Toggle each cookie category on/off</li>
                  <li>Save your preferences</li>
                </ol>
                <Button asChild size="lg" className="mt-6 bg-green-600 hover:bg-green-700 text-white">
                  <Link href="/dashboard?tab=settings">Manage Cookie Settings</Link>
                </Button>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">In Your Browser</h3>
                <p className="text-gray-700 mb-4">
                  You can also control cookies through your browser settings:
                </p>
                <ul className="space-y-3">
                  {[
                    { browser: "Chrome", link: "chrome://settings/cookies" },
                    { browser: "Firefox", link: "about:preferences#privacy" },
                    { browser: "Safari", link: "Preferences → Privacy" },
                    { browser: "Edge", link: "edge://settings/privacy" },
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-semibold text-gray-900">{item.browser}:</span>
                        <code className="ml-2 text-sm text-blue-600">{item.link}</code>
                      </div>
                    </li>
                  ))}
                </ul>
                <p className="text-sm text-gray-600 mt-4">
                  Note: Disabling essential cookies may affect website functionality.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Third-Party Cookies */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Third-Party Cookies</h2>
            <p className="text-gray-700 mb-6">
              We use trusted third-party services that may set their own cookies. These services help us provide better
              functionality and analyze our service usage:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: "Google Analytics", purpose: "Website analytics", link: "https://policies.google.com/privacy" },
                { name: "Stripe", purpose: "Payment processing", link: "https://stripe.com/privacy" },
                { name: "Intercom", purpose: "Customer support chat", link: "https://www.intercom.com/legal/privacy" },
                { name: "Vercel", purpose: "Hosting and CDN", link: "https://vercel.com/legal/privacy-policy" },
                { name: "Sentry", purpose: "Error monitoring", link: "https://sentry.io/privacy" },
                { name: "Mixpanel", purpose: "Product analytics", link: "https://mixpanel.com/legal/privacy-policy" },
              ].map((service, i) => (
                <a
                  key={i}
                  href={service.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-4 bg-gray-50 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow"
                >
                  <h3 className="font-semibold text-gray-900 mb-1">{service.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{service.purpose}</p>
                  <span className="text-xs text-blue-600">View Privacy Policy →</span>
                </a>
              ))}
            </div>
          </motion.div>

          {/* Contact */}
          <motion.div
            className="bg-gradient-to-r from-green-400 to-green-600 rounded-2xl p-8 shadow-xl text-white text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <Cookie className="w-12 h-12 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-4">Questions About Our Cookie Policy?</h2>
            <p className="text-white/90 mb-6">
              If you have any questions about how we use cookies, please contact our privacy team.
            </p>
            <Button asChild size="lg" className="bg-white text-green-600 hover:bg-gray-100">
              <Link href="mailto:privacy@agent47.com">Contact Privacy Team</Link>
            </Button>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  )
}
