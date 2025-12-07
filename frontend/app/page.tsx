import Header from "@/components/header"
import Hero from "@/components/hero"
import Features from "@/components/features"
import HowItWorks from "@/components/how-it-works"
import Pricing from "@/components/pricing"
import CtaBanner from "@/components/cta-banner"
import Footer from "@/components/footer"

export default function Home() {
  return (
    <main className="min-h-screen bg-white relative z-10">
      <Header />
      <Hero />
      <Features />
      {/* Testimonials component removed as requested */}
      <HowItWorks />
      <Pricing />
      <CtaBanner />
      <Footer />
    </main>
  )
}
