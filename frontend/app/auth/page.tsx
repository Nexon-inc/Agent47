"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, ArrowRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
// Select removed from minimal signup form
import { useAuthStore } from "@/lib/stores/auth-store"
import { SignupData, LoginData, PasswordResetData } from "@/lib/api-client"

export default function AuthPage() {
  const router = useRouter()
  const { signup, login, resetPassword, isLoading, error, clearError } = useAuthStore()
  
  const [activeTab, setActiveTab] = useState("signup")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [password, setPassword] = useState("")
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false)
  const [resetEmailSent, setResetEmailSent] = useState(false)

  // Form state
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [username, setUsername] = useState("")
  // optional business fields moved to account page
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")
  const [resetEmail, setResetEmail] = useState("")
  const [localError, setLocalError] = useState<string | null>(null)

  // Calculate password strength
  const calculatePasswordStrength = (pass: string) => {
    let strength = 0
    if (pass.length >= 8) strength++
    if (/[A-Z]/.test(pass)) strength++
    if (/[a-z]/.test(pass)) strength++
    if (/[0-9]/.test(pass)) strength++
    if (/[^A-Za-z0-9]/.test(pass)) strength++
    return strength
  }

  // Update password strength when password changes
  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value
    setPassword(newPassword)
    setPasswordStrength(calculatePasswordStrength(newPassword))
  }

  const getStrengthLabel = () => {
    if (passwordStrength <= 2) return { text: "Weak", color: "bg-red-500" }
    if (passwordStrength === 3) return { text: "Fair", color: "bg-orange-500" }
    if (passwordStrength === 4) return { text: "Strong", color: "bg-blue-500" }
    return { text: "Very Strong", color: "bg-green-500" }
  }

  const handleSignUp = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    clearError()
    setLocalError(null)

    // Validate passwords match
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match")
      return
    }

    // Create signup data
    const signupData: SignupData = {
      email,
      username,
      password,
      first_name: firstName,
      last_name: lastName
    }

    try {
      const success = await signup(signupData)
      if (success) {
        router.push("/onboarding")
      } else {
        // Get error from store
        const errorMessage = useAuthStore.getState().error
        if (errorMessage) {
          // Check if user already exists - suggest login instead
          if (errorMessage.toLowerCase().includes('already registered') || 
              errorMessage.toLowerCase().includes('already exists') ||
              errorMessage.toLowerCase().includes('already signed up')) {
            setLocalError("This email is already registered. Redirecting to login...")
            // Auto-switch to login tab after 2 seconds
            setTimeout(() => {
              setActiveTab("login")
              setLoginEmail(email) // Pre-fill email in login form
              setLocalError(null)
            }, 2000)
          } else {
            setLocalError(errorMessage)
          }
        } else {
          setLocalError("Signup failed. Please try again.")
        }
      }
    } catch (error) {
      console.error("Signup error:", error)
      const errorMessage = error instanceof Error ? error.message : "Signup failed. Please try again."
      setLocalError(errorMessage)
    }
  }

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    clearError()

    const loginData: LoginData = {
      email: loginEmail,
      password: loginPassword
    }

    const success = await login(loginData)
    if (success) {
      router.push("/dashboard")
    }
  }

  const handleForgotPassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    clearError()

    const resetData: PasswordResetData = {
      email: resetEmail
    }

    const success = await resetPassword(resetData)
    if (success) {
      setResetEmailSent(true)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 py-12 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="w-full max-w-md text-center mb-8">
        <Link href="/" className="inline-block mb-4">
          <span className="text-slate-900 font-extrabold text-3xl">
            Agent<span className="text-green-500">47</span>
          </span>
        </Link>
        <h2 className="text-gray-500 text-lg">Automate Your Business with AI Agents</h2>
      </div>

      {/* Main Card */}
      <Card className="w-full max-w-md bg-white shadow-xl">
        <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
          <CardHeader className="pb-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
              <TabsTrigger value="login">Login</TabsTrigger>
            </TabsList>
          </CardHeader>

          <CardContent>
            {/* Sign Up Form */}
            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    type="text"
                    placeholder="John"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    type="text"
                    placeholder="Doe"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                  />
                </div>
                {/* Nickname removed */}

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    placeholder="your.email@example.com" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required 
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input 
                    id="username" 
                    type="text" 
                    placeholder="Choose a username" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required 
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a password"
                      value={password}
                      onChange={handlePasswordChange}
                      required
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>

                  {/* Password strength meter */}
                  {password && (
                    <div className="mt-2">
                      <div className="flex justify-between items-center mb-1">
                        <div className="text-xs text-gray-500">Password strength:</div>
                        <div className="text-xs font-medium">{getStrengthLabel().text}</div>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getStrengthLabel().color} transition-all duration-300`}
                          style={{ width: `${(passwordStrength / 5) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm your password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    >
                      {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Optional business fields moved to account page */}

                {/* Extra demographic fields removed from signup */}

                {(localError || error) && (
                  <div className="text-red-500 text-sm py-2 px-3 bg-red-50 rounded-md">
                    {localError || error}
                  </div>
                )}

                <Button type="submit" className="w-full bg-[#3B82F6] hover:bg-blue-600" disabled={isLoading}>
                  {isLoading ? "Creating account..." : "Sign Up"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or sign up with</span>
                  </div>
                </div>

                  <div className="grid grid-cols-2 gap-3">
                    {["Google", "LinkedIn"].map((provider) => (
                    <Button
                      key={provider}
                      variant="outline"
                      type="button"
                      className="flex items-center justify-center bg-transparent"
                    >
                      <span className="sr-only">Sign up with {provider}</span>
                      {provider === "Google" && (
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12.545 10.239v3.821h5.445c-.712 2.315-2.647 3.972-5.445 3.972a6.033 6.033 0 110-12.064c1.498 0 2.866.549 3.921 1.453l2.814-2.814A9.969 9.969 0 0012.545 2C7.021 2 2.543 6.477 2.543 12s4.478 10 10.002 10c8.396 0 10.249-7.85 9.426-11.748l-9.426-.013z" />
                        </svg>
                      )}
                      {provider === "LinkedIn" && (
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.338 16.338H13.67V12.16c0-1-.02-2.285-1.39-2.285-1.39 0-1.6 1.087-1.6 2.21v4.253h-2.667V8.5h2.56v1.17h.036c.358-.674 1.228-1.387 2.534-1.387 2.712 0 3.216 1.785 3.216 4.106v3.95zM5.5 7.33a1.667 1.667 0 110-3.335 1.667 1.667 0 010 3.335zm1.334 9.008H4.166V8.5h2.668v7.838zM17.5 1H2.5a1.5 1.5 0 00-1.5 1.5v15A1.5 1.5 0 002.5 19h15a1.5 1.5 0 001.5-1.5v-15A1.5 1.5 0 0017.5 1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </Button>
                  ))}
                </div>
              </form>
            </TabsContent>

            {/* Login Form */}
            <TabsContent value="login">
              {forgotPasswordOpen ? (
                resetEmailSent ? (
                  <div className="text-center py-6">
                    <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                      <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Check your email</h3>
                    <p className="text-sm text-gray-500 mb-4">
                      We've sent a password reset link to your email address.
                    </p>
                    <Button type="button" variant="outline" onClick={() => setForgotPasswordOpen(false)}>
                      Back to login
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleForgotPassword} className="space-y-4">
                    <div className="space-y-2">
                      <h3 className="text-lg font-medium">Reset your password</h3>
                      <p className="text-sm text-gray-500">
                        Enter your email address and we'll send you a link to reset your password.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="resetEmail">Email</Label>
                      <Input 
                        id="resetEmail" 
                        type="email" 
                        placeholder="your.email@example.com" 
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        required 
                      />
                    </div>

                    <div className="flex space-x-2">
                      <Button type="submit" className="flex-1 bg-[#3B82F6] hover:bg-blue-600" disabled={isLoading}>
                        {isLoading ? "Sending..." : "Send reset link"}
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setForgotPasswordOpen(false)}>
                        Cancel
                      </Button>
                    </div>
                  </form>
                )
              ) : (
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="loginEmail">Email</Label>
                    <Input 
                      id="loginEmail" 
                      type="email" 
                      placeholder="your.email@example.com" 
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      required 
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="loginPassword">Password</Label>
                      <button
                        type="button"
                        className="text-sm font-medium text-blue-600 hover:text-blue-500"
                        onClick={() => setForgotPasswordOpen(true)}
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative">
                      <Input
                        id="loginPassword"
                        type={showPassword ? "text" : "password"}
                        placeholder="Enter your password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div className="text-red-500 text-sm py-2 px-3 bg-red-50 rounded-md border border-red-200">
                      <div className="font-medium">Login Failed</div>
                      <div>{error}</div>
                      {error.includes('Network error') && (
                        <div className="text-xs mt-1 text-red-400">
                          Please check if the backend server is running
                        </div>
                      )}
                    </div>
                  )}

                  <Button type="submit" className="w-full bg-[#3B82F6] hover:bg-blue-600" disabled={isLoading}>
                    {isLoading ? "Logging in..." : "Login"}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>

                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-white text-gray-500">Or login with</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    {["Google", "LinkedIn", "Instagram"].map((provider) => (
                      <Button
                        key={provider}
                        variant="outline"
                        type="button"
                        className="flex items-center justify-center bg-transparent"
                      >
                        <span className="sr-only">Login with {provider}</span>
                        {provider === "Google" && (
                          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12.545 10.239v3.821h5.445c-.712 2.315-2.647 3.972-5.445 3.972a6.033 6.033 0 110-12.064c1.498 0 2.866.549 3.921 1.453l2.814-2.814A9.969 9.969 0 0012.545 2C7.021 2 2.543 6.477 2.543 12s4.478 10 10.002 10c8.396 0 10.249-7.85 9.426-11.748l-9.426-.013z" />
                          </svg>
                        )}
                        {provider === "LinkedIn" && (
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.338 16.338H13.67V12.16c0-1-.02-2.285-1.39-2.285-1.39 0-1.6 1.087-1.6 2.21v4.253h-2.667V8.5h2.56v1.17h.036c.358-.674 1.228-1.387 2.534-1.387 2.712 0 3.216 1.785 3.216 4.106v3.95zM5.5 7.33a1.667 1.667 0 110-3.335 1.667 1.667 0 010 3.335zm1.334 9.008H4.166V8.5h2.668v7.838zM17.5 1H2.5a1.5 1.5 0 00-1.5 1.5v15A1.5 1.5 0 002.5 19h15a1.5 1.5 0 001.5-1.5v-15A1.5 1.5 0 0017.5 1z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                        {provider === "Instagram" && (
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-4.327 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                          </svg>
                        )}
                      </Button>
                    ))}
                  </div>
                </form>
              )}
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>

      {/* Footer */}
      <div className="w-full max-w-md mt-8 text-center">
        <p className="text-sm text-gray-500">
          Need help?{" "}
          <Link href="/contact" className="text-blue-600 hover:text-blue-500">
            Contact Support
          </Link>
        </p>
        <div className="mt-4 py-3 px-4 bg-gray-800 text-white text-sm rounded-md">Powered by Nexonic Industries</div>
      </div>
    </div>
  )
}
