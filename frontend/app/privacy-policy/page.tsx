"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { ChevronDown, ChevronUp, Download } from "lucide-react"

const sections = [
  {
    id: "information-we-collect",
    title: "Information We Collect",
    content: (
      <>
        <p className="mb-4">We collect several types of information from and about users of our platform, including:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Personal Data:</strong> Name, email address, payment information (via Paystack), profile settings,
            and preferences.
          </li>
          <li>
            <strong>Usage Data:</strong> IP address, browser type, pages visited, time spent on pages, agent
            interactions (e.g., Aria post schedules).
          </li>
          <li>
            <strong>Third-Party Data:</strong> Information from OAuth providers (Google/LinkedIn name, email) and CRM
            integrations (Salesforce, HubSpot).
          </li>
        </ul>
        <p className="text-gray-700 italic">
          Note: We don't collect unnecessary data. For example, we don't store your social media passwords.
        </p>
      </>
    ),
  },
  {
    id: "how-we-use-your-information",
    title: "How We Use Your Information",
    content: (
      <>
        <p className="mb-4">We use the information we collect for various purposes, including:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Provide Services:</strong> To operate our platform and deliver the services you request (e.g.,
            Jackie responding to tickets).
          </li>
          <li>
            <strong>Improve Platform:</strong> To understand how users interact with our agents (e.g., Clara's campaign
            analytics) and enhance our offerings.
          </li>
          <li>
            <strong>Communicate:</strong> To send you updates, newsletters, marketing communications, and respond to
            your inquiries.
          </li>
          <li>
            <strong>Comply with Laws:</strong> To fulfill our legal obligations (e.g., tax reporting via Paystack).
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: We never sell your data to third parties.</p>
      </>
    ),
  },
  {
    id: "how-we-share-your-information",
    title: "How We Share Your Information",
    content: (
      <>
        <p className="mb-4">We may share your information with:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Service Providers:</strong> Third parties that help us operate our business (Paystack for payments,
            AWS for hosting).
          </li>
          <li>
            <strong>Legal Requirements:</strong> When required by law, court order, or governmental authority.
          </li>
          <li>
            <strong>Integrations:</strong> With your consent, we may share data with third-party integrations (e.g.,
            Zapier for workflows).
          </li>
        </ul>
        <p className="text-gray-700 italic">
          Note: Data shared with agents (e.g., Eric's CRM access) stays within your control.
        </p>
      </>
    ),
  },
  {
    id: "data-security",
    title: "Data Security",
    content: (
      <>
        <p className="mb-4">We implement appropriate security measures to protect your personal information:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Encryption:</strong> AES-256 for data at rest, TLS 1.3 for data in transit.
          </li>
          <li>
            <strong>Access Controls:</strong> Role-based access for employees with strict need-to-know principles.
          </li>
          <li>
            <strong>Audits:</strong> Regular security assessments and annual third-party security reviews.
          </li>
        </ul>
        <p className="text-gray-700 italic">
          Note: We protect your data, but no system is 100% secure. Report security issues to security@agent47.com.
        </p>
      </>
    ),
  },
  {
    id: "your-rights",
    title: "Your Rights",
    content: (
      <>
        <p className="mb-4">
          Depending on your location, you may have certain rights regarding your personal information:
        </p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>Access, correct, or delete your personal data via dashboard settings.</li>
          <li>Opt-out of marketing emails using the unsubscribe link in our communications.</li>
          <li>Request data portability or erasure under GDPR/CCPA by contacting support@agent47.com.</li>
        </ul>
        <p className="text-gray-700 italic">Note: We respond to requests within 30 days for GDPR, 45 days for CCPA.</p>
      </>
    ),
  },
  {
    id: "cookies-and-tracking",
    title: "Cookies and Tracking",
    content: (
      <>
        <p className="mb-4">Our platform uses cookies and similar technologies:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Essential cookies:</strong> Required for platform functionality, session management, and
            authentication.
          </li>
          <li>
            <strong>Analytics cookies:</strong> Help us understand how users interact with our platform (Google
            Analytics with anonymized IPs).
          </li>
          <li>
            <strong>Preference cookies:</strong> Remember your settings and preferences for future visits.
          </li>
        </ul>
        <p className="mb-4">
          You can manage cookie preferences through your browser settings or our cookie consent banner (shown at first
          visit).
        </p>
        <p className="text-gray-700 italic">Note: We minimize tracking to respect your privacy.</p>
      </>
    ),
  },
  {
    id: "third-party-links",
    title: "Third-Party Links",
    content: (
      <>
        <p className="mb-4">
          Our platform may contain links to third-party websites and services (Paystack, Zapier, etc.) that are not
          owned or controlled by Agent47. These third parties have their own privacy policies and practices.
        </p>
        <p className="text-gray-700 italic">
          Note: We're not responsible for the privacy practices of third parties. We encourage you to review their
          policies before providing any personal information.
        </p>
      </>
    ),
  },
  {
    id: "childrens-privacy",
    title: "Children's Privacy",
    content: (
      <>
        <p className="mb-4">
          Our platform is designed for users 16 years of age and older. We do not knowingly collect personal information
          from children under 16. If we learn we have collected personal information from a child under 16, we will
          delete that information promptly.
        </p>
        <p className="text-gray-700 italic">
          Note: Contact us if you believe we've collected information from a user under 16.
        </p>
      </>
    ),
  },
  {
    id: "changes-to-this-policy",
    title: "Changes to This Policy",
    content: (
      <>
        <p className="mb-4">
          We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new
          Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this
          page with a new effective date. For significant changes, we will send email notifications to active users.
        </p>
        <p className="text-gray-700 italic">Note: Check back periodically for updates.</p>
      </>
    ),
  },
  {
    id: "contact-us",
    title: "Contact Us",
    content: (
      <>
        <p className="mb-4">If you have any questions about this Privacy Policy, please contact us at:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Email:</strong> privacy@agent47.com
          </li>
          <li>
            <strong>Address:</strong> Agent47 Inc., [Placeholder City, Country]
          </li>
        </ul>
        <p>
          <Link href="/contact" className="text-green-600 hover:text-green-700 transition-colors">
            Visit our help center
          </Link>{" "}
          for additional support options.
        </p>
      </>
    ),
  },
]

export default function PrivacyPolicyPage() {
  const [activeSection, setActiveSection] = useState("")
  const [openSections, setOpenSections] = useState<string[]>([])
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkMobile()
    window.addEventListener("resize", checkMobile)

    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  useEffect(() => {
    if (!isMobile) {
      setOpenSections(sections.map((section) => section.id))
    }
  }, [isMobile])

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100

      for (const section of sections) {
        const element = sectionRefs.current[section.id]
        if (element) {
          const { offsetTop, offsetHeight } = element

          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id)
            break
          }
        }
      }
    }

    window.addEventListener("scroll", handleScroll)
    handleScroll()

    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const toggleSection = (id: string) => {
    setOpenSections((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }

  const scrollToSection = (id: string) => {
    if (isMobile && !openSections.includes(id)) {
      toggleSection(id)
    }

    const element = sectionRefs.current[id]
    if (element) {
      const yOffset = -80
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset
      window.scrollTo({ top: y, behavior: "smooth" })
    }
  }

  return (
    <div className="bg-white min-h-screen">
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
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-slate-900 mb-4">Privacy Policy</h1>
            <p className="text-gray-600">Effective: April 14, 2025</p>
          </div>

          <div className="max-w-3xl mx-auto mb-8">
            <p className="text-gray-700 text-lg leading-relaxed">
              At Agent47, we value your privacy. This Privacy Policy explains how we collect, use, disclose, and protect
              your personal information when you use our platform, including our AI agents (e.g., Aria, Jackie, Shakes,
              Clara, Eric) and services.
            </p>
          </div>

          <div className="flex flex-col md:flex-row gap-8 max-w-6xl mx-auto">
            {/* Main content */}
            <div className="md:w-3/4">
              {sections.map((section) => (
                <div
                  key={section.id}
                  id={section.id}
                  ref={(el) => (sectionRefs.current[section.id] = el)}
                  className="mb-8 scroll-mt-24"
                >
                  <button
                    className={`flex justify-between items-center w-full text-left text-xl font-semibold text-slate-900 mb-4 ${
                      isMobile ? "cursor-pointer" : "cursor-default"
                    }`}
                    onClick={() => isMobile && toggleSection(section.id)}
                  >
                    <h2>{section.title}</h2>
                    {isMobile &&
                      (openSections.includes(section.id) ? (
                        <ChevronUp className="h-5 w-5 text-green-600" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-green-600" />
                      ))}
                  </button>

                  {(!isMobile || openSections.includes(section.id)) && (
                    <div className="text-gray-700 leading-relaxed">{section.content}</div>
                  )}

                  <div className="border-b border-gray-200 mt-6"></div>
                </div>
              ))}
            </div>

            {/* Table of contents sidebar */}
            <div className="md:w-1/4">
              <div className={`${isMobile ? "bg-white p-4 rounded-lg shadow-md mb-6" : "sticky top-24"}`}>
                {isMobile ? (
                  <div className="relative">
                    <select
                      className="w-full p-3 bg-white border border-gray-300 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-green-500 text-slate-900 font-medium"
                      onChange={(e) => scrollToSection(e.target.value)}
                      value={activeSection}
                    >
                      <option value="" disabled>
                        Jump to section
                      </option>
                      {sections.map((section) => (
                        <option key={section.id} value={section.id}>
                          {section.title}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-900 pointer-events-none" />
                  </div>
                ) : (
                  <>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">On this page</h3>
                    <nav>
                      <ul className="space-y-3">
                        {sections.map((section) => (
                          <li key={section.id}>
                            <button
                              onClick={() => scrollToSection(section.id)}
                              className={`text-left w-full ${
                                activeSection === section.id
                                  ? "text-green-600 font-semibold"
                                  : "text-green-600 hover:text-green-700"
                              } transition-colors`}
                            >
                              {section.title}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </nav>

                    <div className="mt-8">
                      <button className="flex items-center text-green-600 hover:text-green-700 transition-colors font-medium">
                        <Download className="h-4 w-4 mr-2" />
                        Download PDF
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
