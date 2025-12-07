"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft, Shield, Lock, Eye, Database, AlertTriangle, CheckCircle2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Header from "@/components/header"
import Footer from "@/components/footer"

export default function SecurityPage() {
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
              <Shield className="w-3 h-3 mr-1" />
              Enterprise-Grade Security
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">Security & Trust</h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Your data security is our top priority. We implement industry-leading security practices to protect your
              information and ensure compliance with global standards.
            </p>
          </motion.div>

          {/* Certifications */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-16">
            {[
              { name: "SOC 2 Type II", icon: Shield, color: "from-blue-500 to-cyan-500" },
              { name: "ISO 27001", icon: Lock, color: "from-purple-500 to-pink-500" },
              { name: "GDPR", icon: Eye, color: "from-green-500 to-emerald-500" },
              { name: "CCPA", icon: Database, color: "from-orange-500 to-red-500" },
              { name: "HIPAA", icon: FileText, color: "from-indigo-500 to-purple-500" },
            ].map((cert, index) => (
              <motion.div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200 text-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div
                  className={`w-16 h-16 mx-auto rounded-xl bg-gradient-to-r ${cert.color} flex items-center justify-center mb-4`}
                >
                  <cert.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">{cert.name}</h3>
                <p className="text-sm text-gray-600">Certified</p>
              </motion.div>
            ))}
          </div>

          {/* Data Handling */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center">
              <Database className="w-8 h-8 mr-3 text-green-600" />
              Data Handling Practices
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Data Collection</h3>
                <ul className="space-y-3">
                  {[
                    "We only collect data necessary for service functionality",
                    "All data collection is transparent and disclosed",
                    "You control what data you share with our AI agents",
                    "No selling or sharing of personal data with third parties",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Data Storage</h3>
                <ul className="space-y-3">
                  {[
                    "All data encrypted at rest using AES-256 encryption",
                    "Data stored in SOC 2 certified data centers",
                    "Geographic data residency options available",
                    "Regular security audits and penetration testing",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Data Access</h3>
                <ul className="space-y-3">
                  {[
                    "Strict role-based access control (RBAC)",
                    "Multi-factor authentication (MFA) required",
                    "All access logged and monitored 24/7",
                    "Zero-trust architecture implementation",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Data Retention</h3>
                <ul className="space-y-3">
                  {[
                    "Data retained only as long as necessary",
                    "Automatic deletion after account closure (30 days)",
                    "You can request data deletion at any time",
                    "Regular data purging per retention policies",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Security Features */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center">
              <Lock className="w-8 h-8 mr-3 text-purple-500" />
              Security Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  title: "End-to-End Encryption",
                  description: "All data transmitted between you and our servers is encrypted using TLS 1.3",
                  icon: Lock,
                },
                {
                  title: "Regular Security Audits",
                  description: "Third-party security audits conducted quarterly by certified professionals",
                  icon: Eye,
                },
                {
                  title: "Incident Response",
                  description: "24/7 security monitoring with < 15 minute incident response time",
                  icon: AlertTriangle,
                },
                {
                  title: "Secure API",
                  description: "API keys with granular permissions and automatic rotation",
                  icon: Database,
                },
                {
                  title: "DDoS Protection",
                  description: "Enterprise-grade protection against distributed denial-of-service attacks",
                  icon: Shield,
                },
                {
                  title: "Backup & Recovery",
                  description: "Daily automated backups with 99.99% data durability guarantee",
                  icon: Database,
                },
              ].map((feature, i) => (
                <div
                  key={i}
                  className="p-6 bg-gray-50 rounded-xl border border-gray-200"
                >
                  <feature.icon className="w-8 h-8 text-green-600 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Contact Security Team */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Questions About Security?</h2>
            <p className="text-gray-600 mb-6">
              Our security team is here to help. Contact us for security inquiries, compliance questions, or to report
              an issue.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button asChild size="lg" className="bg-green-600 hover:bg-green-700 text-white">
                <Link href="mailto:security@agent47.com">Email Security Team</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/contact">General Inquiries</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  )
}
