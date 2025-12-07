export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 py-4 px-6">
      <div className="flex flex-col md:flex-row justify-between items-center">
        <div className="text-sm text-gray-500">&copy; {new Date().getFullYear()} Agent47. All rights reserved.</div>
        <div className="flex space-x-4 mt-2 md:mt-0">
          <a href="/terms" className="text-sm text-gray-500 hover:text-gray-700">
            Terms
          </a>
          <a href="/privacy-policy" className="text-sm text-gray-500 hover:text-gray-700">
            Privacy
          </a>
          <a href="/contact" className="text-sm text-gray-500 hover:text-gray-700">
            Contact
          </a>
        </div>
      </div>
    </footer>
  )
}
