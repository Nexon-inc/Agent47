import Link from "next/link"
import { Linkedin, Twitter, Instagram, ArrowRight } from "lucide-react"

export default function Footer() {
  return (
    <footer className="bg-[#0A0020] text-white pt-20 pb-8">
      <div className="container mx-auto px-4 max-w-7xl 2xl:max-w-[1400px] 3xl:max-w-[1600px]">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16 2xl:gap-16">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <Link href="/" className="inline-block mb-6">
              <span className="text-white font-extrabold text-3xl">
                Agent<span className="text-green-500">47</span>
              </span>
            </Link>
            <p className="text-white/70 text-lg mb-6 max-w-md">
              Automate smarter with specialized AI personnel designed to streamline your workflows and boost productivity.
            </p>
            <div className="flex space-x-4">
              <Link
                href="https://www.linkedin.com/in/nexonic-industries-936b47387/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-green-500/20 hover:text-green-500 transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin size={20} />
              </Link>
              <Link
                href="https://x.com/Nexon_ke"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-green-500/20 hover:text-green-500 transition-colors"
                aria-label="X (Twitter)"
              >
                <Twitter size={20} />
              </Link>
              <Link
                href="https://www.instagram.com/nexoninc/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-green-500/20 hover:text-green-500 transition-colors"
                aria-label="Instagram"
              >
                <Instagram size={20} />
              </Link>
            </div>
          </div>

          {/* Navigation Columns */}
          {[
            {
              title: "Product",
              links: [
                { name: "Features", path: "/features" },
                // Use landing page pricing section instead of onboarding pricing flow
                { name: "Pricing", path: "/#pricing" },
                { name: "Roadmap", path: "/roadmap" }, // Added roadmap link
              ],
            },
            {
              title: "Support",
              links: [
                { name: "Help Center", path: "/contact" }, // Linked to existing contact page
                { name: "Status", path: "/status" }, // Added status link
                { name: "Documentation", path: "/documentation" }, // Added documentation link
                { name: "API", path: "/api" }, // Added API link
              ],
            },
            {
              title: "Legal",
              links: [
                { name: "Privacy Policy", path: "/privacy-policy" },
                { name: "Terms of Service", path: "/terms" },
                { name: "Cookie Policy", path: "/cookies" },
                { name: "Security", path: "/security" },
                { name: "Compliance", path: "/compliance" },
              ],
            },
          ].map((column, i) => (
            <div key={i}>
              <h3 className="font-semibold text-xl mb-6">{column.title}</h3>
              <ul className="space-y-4">
                {column.links.map((link, j) => (
                  <li key={j}>
                    <Link
                      href={link.path}
                      className="text-white/70 hover:text-green-500 transition-colors inline-flex items-center"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Newsletter */}
        <div className="border-t border-white/10 pt-12 pb-8">
          <div className="max-w-3xl mx-auto">
            <div className="bg-green-500/10 rounded-2xl p-8 border border-green-500/20">
              <h3 className="text-2xl font-bold mb-2">Stay updated with Agent47 news</h3>
              <p className="text-white/70 mb-6">
                Get the latest updates, tips, and special offers delivered directly to your inbox.
              </p>
              <form className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-grow px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  aria-required="true"
                  required
                />
                <button
                  type="submit"
                  className="bg-gradient-to-r from-green-400 to-green-600 text-white font-semibold px-6 py-3 rounded-lg hover:shadow-lg hover:shadow-green-500/30 transition-all duration-300 flex items-center justify-center"
                >
                  Subscribe <ArrowRight size={16} className="ml-2" />
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-white/10 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-white/50 text-sm mb-4 md:mb-0">© 2025 Agent47. All rights reserved.</div>
            <div className="flex space-x-6">
              {[
                { name: "Privacy", path: "/privacy-policy" },
                { name: "Terms", path: "/terms" },
                { name: "Cookies", path: "/cookies" },
                { name: "FAQ", path: "/faq" },
              ].map((item, i) => (
                <Link key={i} href={item.path} className="text-white/50 hover:text-white text-sm transition-colors">
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
