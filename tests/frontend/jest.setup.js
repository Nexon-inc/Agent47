/**
 * Jest setup file for frontend tests
 */
import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock Next.js image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} />
  },
}))

// Mock Next.js link component
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...props }) => {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    )
  },
}))

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: 'div',
    span: 'span',
    button: 'button',
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    p: 'p',
    img: 'img',
    section: 'section',
    article: 'article',
    nav: 'nav',
    header: 'header',
    footer: 'footer',
    main: 'main',
    aside: 'aside',
    ul: 'ul',
    ol: 'ol',
    li: 'li',
    a: 'a',
    form: 'form',
    input: 'input',
    textarea: 'textarea',
    select: 'select',
    option: 'option',
    label: 'label',
    fieldset: 'fieldset',
    legend: 'legend',
    table: 'table',
    thead: 'thead',
    tbody: 'tbody',
    tr: 'tr',
    th: 'th',
    td: 'td',
    tfoot: 'tfoot',
    caption: 'caption',
    colgroup: 'colgroup',
    col: 'col',
    details: 'details',
    summary: 'summary',
    dialog: 'dialog',
    menu: 'menu',
    menuitem: 'menuitem',
    meter: 'meter',
    progress: 'progress',
    time: 'time',
  },
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({
    start: jest.fn(),
    stop: jest.fn(),
    set: jest.fn(),
  }),
  useInView: () => [jest.fn(), false],
  useMotionValue: () => ({
    get: jest.fn(),
    set: jest.fn(),
    onChange: jest.fn(),
  }),
  useTransform: () => jest.fn(),
  useSpring: () => jest.fn(),
  useScroll: () => ({
    scrollX: { get: jest.fn() },
    scrollY: { get: jest.fn() },
  }),
  useViewportScroll: () => ({
    scrollX: { get: jest.fn() },
    scrollY: { get: jest.fn() },
  }),
}))

// Mock zustand stores
jest.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: () => ({
    user: null,
    isAuthenticated: false,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
    updateProfile: jest.fn(),
  }),
}))

jest.mock('@/lib/stores/agent-store', () => ({
  useAgentStore: () => ({
    selectedAgent: null,
    setSelectedAgent: jest.fn(),
    agents: [],
    loadAgents: jest.fn(),
  }),
}))

// Mock API client
jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  },
}))

// Mock WebSocket client
jest.mock('@/lib/websocket-client', () => ({
  WebSocketClient: jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
  })),
}))

// Mock agent services
jest.mock('@/lib/agent-services', () => ({
  ariaService: {
    generateCaption: jest.fn(),
    suggestHashtags: jest.fn(),
    analyzeAccount: jest.fn(),
    generateImage: jest.fn(),
  },
  claraService: {
    processMessage: jest.fn(),
    getResponse: jest.fn(),
    escalateToHuman: jest.fn(),
  },
  ericService: {
    generateSalesPitch: jest.fn(),
    analyzeLead: jest.fn(),
    createFollowUp: jest.fn(),
  },
  jackieService: {
    generateCode: jest.fn(),
    reviewCode: jest.fn(),
    debugCode: jest.fn(),
  },
  joeService: {
    conductResearch: jest.fn(),
    analyzeData: jest.fn(),
    generateReport: jest.fn(),
  },
  purityService: {
    generateBusinessIdea: jest.fn(),
    conductMarketResearch: jest.fn(),
    createFinancialPlan: jest.fn(),
  },
  shakesService: {
    generateContent: jest.fn(),
    optimizeSEO: jest.fn(),
    createCampaign: jest.fn(),
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000/ws'

// Global test utilities
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.sessionStorage = sessionStorageMock

// Mock fetch
global.fetch = jest.fn()

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
}

// Setup test cleanup
afterEach(() => {
  jest.clearAllMocks()
  localStorageMock.clear()
  sessionStorageMock.clear()
})
