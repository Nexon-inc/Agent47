"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ArrowLeft, Shield, FileText, CheckCircle2, Globe, Lock, AlertCircle, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Header from "@/components/header"
import Footer from "@/components/footer"

export default function CompliancePage() {
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
              Global Compliance Standards
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              Compliance & Regulations
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Agent47 is committed to maintaining the highest standards of compliance with international data protection
              and privacy regulations to ensure your data is handled responsibly.
            </p>
          </motion.div>

          {/* Certifications Grid */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-16">
            {[
              {
                name: "SOC 2 Type II",
                description: "Service Organization Control",
                icon: Shield,
                color: "from-blue-500 to-cyan-500",
              },
              {
                name: "ISO 27001",
                description: "Information Security",
                icon: Lock,
                color: "from-purple-500 to-pink-500",
              },
              {
                name: "GDPR",
                description: "EU Data Protection",
                icon: Globe,
                color: "from-green-500 to-emerald-500",
              },
              {
                name: "CCPA",
                description: "California Privacy",
                icon: FileText,
                color: "from-orange-500 to-red-500",
              },
              {
                name: "HIPAA",
                description: "Healthcare Privacy",
                icon: Shield,
                color: "from-indigo-500 to-purple-500",
              },
            ].map((cert, index) => (
              <motion.div
                key={index}
                className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <div
                  className={`w-16 h-16 rounded-xl bg-gradient-to-r ${cert.color} flex items-center justify-center mb-4 mx-auto`}
                >
                  <cert.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 text-center mb-1">{cert.name}</h3>
                <p className="text-sm text-gray-600 text-center">{cert.description}</p>
              </motion.div>
            ))}
          </div>

          {/* Detailed Compliance */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-8">Our Compliance Standards</h2>
            <div className="space-y-8">
              {[
                {
                  title: "SOC 2 Type II Certification",
                  icon: Shield,
                  color: "from-blue-500 to-cyan-500",
                  description:
                    "We have completed SOC 2 Type II certification, demonstrating our commitment to security, availability, processing integrity, confidentiality, and privacy.",
                  requirements: [
                    "Annual third-party audits by certified auditors",
                    "Continuous monitoring of security controls",
                    "Documented policies and procedures",
                    "Regular security awareness training for all personnel",
                    "Incident response and disaster recovery plans",
                  ],
                },
                {
                  title: "ISO 27001 Information Security",
                  icon: Lock,
                  color: "from-purple-500 to-pink-500",
                  description:
                    "Our information security management system (ISMS) is certified to ISO 27001 standards, ensuring systematic management of sensitive information.",
                  requirements: [
                    "Risk assessment and treatment processes",
                    "Information security policies and controls",
                    "Regular internal and external audits",
                    "Continuous improvement of security measures",
                    "Asset management and access controls",
                  ],
                },
                {
                  title: "GDPR Compliance (EU)",
                  icon: Globe,
                  color: "from-green-500 to-emerald-500",
                  description:
                    "We comply with the General Data Protection Regulation, giving EU citizens full control over their personal data.",
                  requirements: [
                    "Lawful basis for data processing",
                    "Data minimization and purpose limitation",
                    "Right to access, rectify, and erase data",
                    "Data portability and processing restrictions",
                    "Data breach notifications within 72 hours",
                  ],
                },
                {
                  title: "CCPA Compliance (California)",
                  icon: FileText,
                  color: "from-orange-500 to-red-500",
                  description:
                    "We comply with the California Consumer Privacy Act, protecting the privacy rights of California residents.",
                  requirements: [
                    "Notice of data collection and usage",
                    "Right to know what data is collected",
                    "Right to delete personal information",
                    "Right to opt-out of data sales",
                    "Non-discrimination for exercising rights",
                  ],
                },
                {
                  title: "HIPAA Compliance (Healthcare)",
                  icon: Shield,
                  color: "from-indigo-500 to-purple-500",
                  description:
                    "For healthcare clients, we maintain HIPAA compliance to protect protected health information (PHI).",
                  requirements: [
                    "Business Associate Agreements (BAAs)",
                    "Encryption of PHI at rest and in transit",
                    "Access controls and audit logs",
                    "Employee HIPAA training",
                    "Breach notification procedures",
                  ],
                },
              ].map((standard, index) => (
                <div key={index} className="border border-gray-200 rounded-xl p-6">
                  <div className="flex items-start mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-r ${standard.color} flex items-center justify-center mr-4 flex-shrink-0`}
                    >
                      <standard.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2">{standard.title}</h3>
                      <p className="text-gray-700">{standard.description}</p>
                    </div>
                  </div>
                  <div className="ml-16">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">Key Requirements:</h4>
                    <ul className="space-y-2">
                      {standard.requirements.map((req, i) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* User Rights */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Your Data Rights</h2>
            <p className="text-gray-700 mb-6">
              Under GDPR, CCPA, and other privacy laws, you have the following rights regarding your personal data:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  title: "Right to Access",
                  description: "Request a copy of all personal data we hold about you",
                  icon: FileText,
                },
                {
                  title: "Right to Rectification",
                  description: "Correct any inaccurate or incomplete personal data",
                  icon: CheckCircle2,
                },
                {
                  title: "Right to Erasure",
                  description: "Request deletion of your personal data ('right to be forgotten')",
                  icon: AlertCircle,
                },
                {
                  title: "Right to Data Portability",
                  description: "Receive your data in a structured, commonly used format",
                  icon: Globe,
                },
                {
                  title: "Right to Restrict Processing",
                  description: "Limit how we process your personal data",
                  icon: Lock,
                },
                {
                  title: "Right to Object",
                  description: "Object to processing of your data for specific purposes",
                  icon: Shield,
                },
              ].map((right, i) => (
                <div key={i} className="flex items-start p-4 bg-gray-50 rounded-xl">
                  <right.icon className="w-6 h-6 text-green-600 mr-3 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">{right.title}</h3>
                    <p className="text-sm text-gray-600">{right.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 p-6 bg-green-50 rounded-xl border border-green-200">
              <h3 className="font-semibold text-gray-900 mb-2">How to Exercise Your Rights</h3>
              <p className="text-sm text-gray-700 mb-4">
                To exercise any of these rights, please contact our Data Protection Officer (DPO) at{" "}
                <a href="mailto:dpo@agent47.com" className="text-green-600 hover:underline">
                  dpo@agent47.com
                </a>
                . We will respond to your request within 30 days.
              </p>
              <Button asChild className="bg-green-600 hover:bg-green-700 text-white">
                <Link href="mailto:dpo@agent47.com">Contact DPO</Link>
              </Button>
            </div>
          </motion.div>

          {/* Data Breach Policy */}
          <motion.div
            className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200 mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center">
              <AlertCircle className="w-8 h-8 mr-3 text-orange-500" />
              Data Breach Notification Policy
            </h2>
            <p className="text-gray-700 mb-6">
              In the unlikely event of a data breach that affects your personal information, we will:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    1
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Immediate Detection</h3>
                    <p className="text-sm text-gray-600">
                      Our 24/7 security monitoring will detect the breach immediately
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    2
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Containment (less than 1 hour)</h3>
                    <p className="text-sm text-gray-600">
                      Contain the breach and prevent further unauthorized access
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-yellow-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    3
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      Assessment (less than 24 hours)
                    </h3>
                    <p className="text-sm text-gray-600">
                      Assess the scope and impact of the breach
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    4
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      User Notification (less than 72 hours)
                    </h3>
                    <p className="text-sm text-gray-600">
                      Notify affected users via email and in-app notification
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    5
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      Authority Notification (less than 72 hours)
                    </h3>
                    <p className="text-sm text-gray-600">
                      Report to relevant data protection authorities (GDPR requirement)
                    </p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                    6
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Remediation & Prevention</h3>
                    <p className="text-sm text-gray-600">
                      Fix vulnerabilities and implement additional security measures
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </section>

      <Footer />
    </main>
  )
}
