"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { ChevronDown, ChevronUp, Download } from "lucide-react"

const sections = [
  {
    id: "acceptance-of-terms",
    title: "Acceptance of Terms",
    content: (
      <>
        <p className="mb-4">
          By accessing or using Agent47's platform, including our AI personnel (e.g., Aria, Jackie, Shakes, Clara, Eric)
          and services, you agree to be bound by these Terms and Conditions.
        </p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>These terms constitute a binding agreement between you and Agent47.</li>
          <li>You must be at least 16 years old to use our platform.</li>
        </ul>
        <p className="text-gray-700 italic">Note: If you don't agree with these terms, please don't use Agent47.</p>
      </>
    ),
  },
  {
    id: "services",
    title: "Services",
    content: (
      <>
        <p className="mb-4">Agent47 provides access to AI-powered personnel designed to automate various workflows:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Available Personnel:</strong> Aria (social media), Jackie (customer support), Shakes (content
            creation), Clara (marketing), Eric (sales), and others.
          </li>
          <li>
            <strong>Service Tiers:</strong> Features vary by plan (Free, Starter, Pro, Ecosystem).
          </li>
          <li>
            <strong>Beta Features:</strong> Some personnel or features may be in beta and have limited functionality.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: We may update personnel without notice to improve performance.</p>
      </>
    ),
  },
  {
    id: "user-accounts",
    title: "User Accounts",
    content: (
      <>
        <p className="mb-4">To use Agent47, you must create and maintain an account:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Account Information:</strong> You must provide accurate, complete, and updated information (name,
            email, etc.).
          </li>
          <li>
            <strong>Account Security:</strong> You are responsible for maintaining the confidentiality of your login
            credentials and for all activities under your account.
          </li>
          <li>
            <strong>Password Requirements:</strong> You must use secure passwords that meet our strength requirements.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Notify us at support@agent47.com if your account is compromised.</p>
      </>
    ),
  },
  {
    id: "payments",
    title: "Payments",
    content: (
      <>
        <p className="mb-4">Payment terms for using our platform:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Payment Processing:</strong> Payments are processed via Paystack (cards, bank transfers).
          </li>
          <li>
            <strong>Subscription Plans:</strong> Free (24-hour trial), Starter ($24.99/mo), Pro ($79/mo).
          </li>
          <li>
            <strong>Billing Cycle:</strong> Subscriptions auto-renew monthly/yearly unless canceled before the renewal
            date.
          </li>
          <li>
            <strong>Refunds:</strong> 14-day money-back guarantee for paid plans, no refunds for the Free tier.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Contact billing@agent47.com for payment disputes.</p>
      </>
    ),
  },
  {
    id: "user-responsibilities",
    title: "User Responsibilities",
    content: (
      <>
        <p className="mb-4">As a user of Agent47, you agree to:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Lawful Use:</strong> Not use our platform for any illegal or unauthorized purpose.
          </li>
          <li>
            <strong>Content Guidelines:</strong> Not upload or share content that is unlawful, harmful, threatening,
            abusive, or otherwise objectionable.
          </li>
          <li>
            <strong>API Usage:</strong> Respect integration limits (e.g., don't overload Zapier APIs).
          </li>
          <li>
            <strong>Data Accuracy:</strong> Provide accurate data for personnel (e.g., Clara's campaigns).
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Misuse may lead to account suspension.</p>
      </>
    ),
  },
  {
    id: "intellectual-property",
    title: "Intellectual Property",
    content: (
      <>
        <p className="mb-4">Ownership and rights regarding content and technology:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Platform Ownership:</strong> Agent47 owns the platform, personnel, and underlying code.
          </li>
          <li>
            <strong>User Content:</strong> You retain ownership of your data and content (e.g., Shakes' generated
            content).
          </li>
          <li>
            <strong>License to Us:</strong> You grant Agent47 a license to use your content solely to provide and
            improve our services.
          </li>
          <li>
            <strong>Restrictions:</strong> No reverse-engineering, copying, or creating derivative works of our personnel.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Contact us for licensing inquiries.</p>
      </>
    ),
  },
  {
    id: "integrations",
    title: "Integrations",
    content: (
      <>
        <p className="mb-4">Agent47 integrates with third-party services:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Third-Party Terms:</strong> When using integrations (Zapier, Salesforce, etc.), you're also subject
            to their terms.
          </li>
          <li>
            <strong>Integration Availability:</strong> We don't guarantee continuous availability of third-party
            integrations.
          </li>
          <li>
            <strong>Data Sharing:</strong> You control what data is shared with integrations.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Check integration status in your dashboard.</p>
      </>
    ),
  },
  {
    id: "termination",
    title: "Termination",
    content: (
      <>
        <p className="mb-4">Terms for ending your relationship with Agent47:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>User Termination:</strong> You can cancel your subscription anytime via account settings.
          </li>
          <li>
            <strong>Agent47 Termination:</strong> We may suspend or terminate accounts for violations (e.g.,
            non-payment, abuse).
          </li>
          <li>
            <strong>Data Retention:</strong> Upon termination, we may delete your data after a 30-day grace period.
          </li>
        </ul>
        <p className="text-gray-700 italic">
          Note: Email support@agent47.com to restore accounts within the grace period.
        </p>
      </>
    ),
  },
  {
    id: "limitation-of-liability",
    title: "Limitation of Liability",
    content: (
      <>
        <p className="mb-4">Limitations on Agent47's liability:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Service Accuracy:</strong> We don't guarantee 100% accuracy of personnel outputs (e.g., Eric's
            forecasts).
          </li>
          <li>
            <strong>Indirect Damages:</strong> We're not liable for indirect, incidental, special, or consequential
            damages.
          </li>
          <li>
            <strong>Liability Cap:</strong> Our maximum liability is limited to the amount you paid in the last 12
            months.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Use personnel at your own risk.</p>
      </>
    ),
  },
  {
    id: "governing-law",
    title: "Governing Law",
    content: (
      <>
        <p className="mb-4">Legal framework governing these terms:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Jurisdiction:</strong> These terms are governed by the laws of [Placeholder Country, e.g., Delaware,
            USA].
          </li>
          <li>
            <strong>Dispute Resolution:</strong> Disputes will be resolved via arbitration in a neutral venue.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Contact legal@agent47.com for disputes.</p>
      </>
    ),
  },
  {
    id: "changes-to-terms",
    title: "Changes to Terms",
    content: (
      <>
        <p className="mb-4">We may modify these Terms and Conditions from time to time:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Updates:</strong> Changes will be posted on this page with a new effective date.
          </li>
          <li>
            <strong>Notification:</strong> We'll notify you of significant changes via email.
          </li>
          <li>
            <strong>Continued Use:</strong> Your continued use after changes constitutes acceptance of the updated
            terms.
          </li>
        </ul>
        <p className="text-gray-700 italic">Note: Check back periodically for updates.</p>
      </>
    ),
  },
  {
    id: "contact-us",
    title: "Contact Us",
    content: (
      <>
        <p className="mb-4">If you have any questions about these Terms and Conditions, please contact us at:</p>
        <ul className="list-disc pl-5 mb-4 space-y-2">
          <li>
            <strong>Email:</strong> terms@agent47.com
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

export default function TermsPage() {
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
            <h1 className="text-4xl font-extrabold text-slate-900 mb-4">Terms and Conditions</h1>
            <p className="text-gray-600">Effective: April 14, 2025</p>
          </div>

          <div className="max-w-3xl mx-auto mb-8">
            <p className="text-gray-700 text-lg leading-relaxed">
              These Terms and Conditions govern your use of Agent47's platform, including our AI personnel (e.g., Aria,
              Jackie, Shakes, Clara, Eric) and services. By using Agent47, you agree to these terms.
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
                    className={`flex justify-between items-center w-full text-left text-xl font-semibold text-slate-900 mb-4 ${isMobile ? "cursor-pointer" : "cursor-default"
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
                              className={`text-left w-full ${activeSection === section.id
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
