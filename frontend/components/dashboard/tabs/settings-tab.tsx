"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { User as UserIcon, CreditCard, Bell, Upload, Download } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUserStore } from "@/lib/stores/user-store"
import { useBillingStore } from "@/lib/stores/billing-store"

// Types
type SettingsTab = "profile" | "billing" | "notifications"

export default function SettingsTab() {
  const { user, userPlan } = useUserStore()
  const {
    subscription,
    paymentHistory,
    usage,
    isLoading,
    error,
    fetchSubscription,
    fetchPaymentHistory,
    fetchUsage,
    cancelSubscription,
  } = useBillingStore()

  const [activeTab, setActiveTab] = useState<SettingsTab>("profile")
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    company: "",
    industry: "Marketing",
    timeZone: "UTC",
    avatar: null as string | null,
  })

  const [notificationSettings, setNotificationSettings] = useState({
    email: {
      taskCompleted: true,
      weeklyReport: true,
      newFeatures: false,
    },
    push: {
      taskCompleted: true,
      agentStatus: true,
      systemAlerts: true,
    },
    inApp: {
      taskCompleted: true,
      agentStatus: true,
      systemAlerts: true,
      newFeatures: true,
    },
  })

  // Mock invoices data
  const invoices = [
    { id: "INV-001", date: "2023-04-01", amount: "$59.00", status: "Paid", plan: "Pro" },
    { id: "INV-002", date: "2023-03-01", amount: "$59.00", status: "Paid", plan: "Pro" },
    { id: "INV-003", date: "2023-02-01", amount: "$59.00", status: "Paid", plan: "Pro" },
  ]

  // Handle form input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Handle notification toggle
  const handleNotificationToggle = (category: keyof typeof notificationSettings, setting: string) => {
    setNotificationSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        // @ts-ignore - dynamic key toggle
        [setting]: !prev[category as keyof typeof prev][setting as keyof typeof prev[typeof category]],
      },
    }))
  }

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // In a real app, this would call an API
    console.log("Form submitted:", formData)
  }

  // Fetch billing data when billing tab is active
  useEffect(() => {
    if (activeTab === "billing") {
      // suppressRedirect is handled inside the store calls where appropriate
      fetchSubscription?.(true).catch(() => {})
      fetchPaymentHistory?.().catch(() => {})
      fetchUsage?.().catch(() => {})
    }
  }, [activeTab, fetchSubscription, fetchPaymentHistory, fetchUsage])

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-[#4B0082]  mb-4">Settings</h1>
        <p className="text-gray-600  mb-6">Manage your account settings and preferences.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200  mb-8">
        <button
          onClick={() => setActiveTab("profile")}
          className={cn(
            "flex items-center px-4 py-2 font-medium text-sm border-b-2 -mb-px transition-colors",
            activeTab === "profile"
              ? "border-[#1E90FF] text-[#1E90FF]"
              : "border-transparent text-gray-500  hover:text-gray-700 :text-gray-300",
          )}
        >
          <UserIcon className="w-4 h-4 mr-2" />
          Profile
        </button>
        <button
          onClick={() => setActiveTab("billing")}
          className={cn(
            "flex items-center px-4 py-2 font-medium text-sm border-b-2 -mb-px transition-colors",
            activeTab === "billing"
              ? "border-[#1E90FF] text-[#1E90FF]"
              : "border-transparent text-gray-500  hover:text-gray-700 :text-gray-300",
          )}
        >
          <CreditCard className="w-4 h-4 mr-2" />
          Billing
        </button>
        <button
          onClick={() => setActiveTab("notifications")}
          className={cn(
            "flex items-center px-4 py-2 font-medium text-sm border-b-2 -mb-px transition-colors",
            activeTab === "notifications"
              ? "border-[#1E90FF] text-[#1E90FF]"
              : "border-transparent text-gray-500  hover:text-gray-700 :text-gray-300",
          )}
        >
          <Bell className="w-4 h-4 mr-2" />
          Notifications
        </button>
      </div>

      {/* Tab Content */}
      <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        {/* Profile Tab */}
        {activeTab === "profile" && (
          <div className="bg-white  rounded-xl shadow-sm border border-gray-200  overflow-hidden">
            <div className="p-6 border-b border-gray-200 ">
              <h2 className="text-lg font-semibold text-gray-900 ">Profile Information</h2>
              <p className="text-sm text-gray-500 ">Update your account details and preferences.</p>
            </div>
            <form onSubmit={handleSubmit} className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <div className="flex items-center">
                    <div className="w-20 h-20 rounded-full bg-[#1E90FF] flex items-center justify-center text-white text-2xl font-bold mr-4">
                      {formData.name ? formData.name.charAt(0) : "U"}
                    </div>
                    <div>
                      <button
                        type="button"
                        className="px-4 py-2 bg-gray-100  text-gray-700  rounded-lg hover:bg-gray-200 :bg-gray-600 transition-colors text-sm font-medium flex items-center"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Change Avatar
                      </button>
                      <p className="text-xs text-gray-500  mt-1">JPG, GIF or PNG. Max size 2MB.</p>
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700  mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700  mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
                  />
                </div>

                <div>
                  <label htmlFor="company" className="block text-sm font-medium text-gray-700  mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
                  />
                </div>

                <div>
                  <label htmlFor="industry" className="block text-sm font-medium text-gray-700  mb-1">
                    Industry
                  </label>
                  <select
                    id="industry"
                    name="industry"
                    value={formData.industry}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
                  >
                    <option value="Marketing">Marketing</option>
                    <option value="Sales">Sales</option>
                    <option value="Customer Support">Customer Support</option>
                    <option value="Content Creation">Content Creation</option>
                    <option value="E-commerce">E-commerce</option>
                    <option value="Education">Education</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="timeZone" className="block text-sm font-medium text-gray-700  mb-1">
                    Time Zone
                  </label>
                  <select
                    id="timeZone"
                    name="timeZone"
                    value={formData.timeZone}
                    onChange={handleChange}
                    className="w-full h-10 px-3 rounded-lg border border-gray-300  bg-white  text-gray-900  focus:outline-none focus:ring-2 focus:ring-[#1E90FF]"
                  >
                    <option value="UTC">UTC (Coordinated Universal Time)</option>
                    <option value="America/New_York">Eastern Time (ET)</option>
                    <option value="America/Chicago">Central Time (CT)</option>
                    <option value="America/Denver">Mountain Time (MT)</option>
                    <option value="America/Los_Angeles">Pacific Time (PT)</option>
                    <option value="Europe/London">Greenwich Mean Time (GMT)</option>
                    <option value="Europe/Paris">Central European Time (CET)</option>
                    <option value="Asia/Tokyo">Japan Standard Time (JST)</option>
                    <option value="Australia/Sydney">Australian Eastern Time (AET)</option>
                  </select>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200  flex justify-end">
                <button
                  type="submit"
                  className="px-6 py-2 bg-[#1E90FF] text-white rounded-lg text-sm font-medium hover:bg-[#1E90FF]/90 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Billing Tab */}
        {activeTab === "billing" && (
          <div className="bg-white  rounded-xl shadow-sm border border-gray-200  overflow-hidden">
            <div className="p-6 border-b border-gray-200 ">
              <h2 className="text-lg font-semibold text-gray-900 ">Billing Information</h2>
              <p className="text-sm text-gray-500 ">Manage your subscription and payment details.</p>
            </div>
            <div className="p-6">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900  mx-auto"></div>
                  <p className="mt-2 text-gray-500 ">Loading billing information...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-500">Error loading billing information: {error}</p>
                </div>
              ) : subscription ? (
                <>
                  <div className="mb-6">
                    <div className="bg-green-50 /20 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="font-medium text-gray-900  capitalize">{subscription.tier} Plan</h3>
                        <span
                          className={`text-sm px-2 py-1 rounded-full ${
                            subscription.status === "active"
                              ? "text-green-600 bg-green-100  /30"
                              : "text-yellow-600 bg-yellow-100  /30"
                          }`}
                        >
                          {subscription.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500  mb-2">
                        {'$'}{subscription.price_usd}/month • {subscription.plan_name}
                      </p>
                      <p className="text-sm text-gray-500  mb-4">
                        Started: {new Date(subscription.start_date).toLocaleDateString()} •
                        {subscription.auto_renew ? " Auto-renewal enabled" : " Auto-renewal disabled"}
                      </p>
                      <div className="flex space-x-2">
                        <a href="/pricing" className="text-sm text-blue-600 hover:text-blue-700  :text-blue-300">
                          Change Plan
                        </a>
                        <button
                          onClick={async () => {
                            if (confirm("Are you sure you want to cancel your subscription?")) {
                              try {
                                await cancelSubscription("User requested cancellation")
                              } catch (e) {
                                console.error("Failed to cancel subscription:", e)
                              }
                            }
                          }}
                          className="text-sm text-red-600 hover:text-red-700  :text-red-300"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Payment History */}
                  <div className="mb-6">
                    <h3 className="text-md font-medium text-gray-900  mb-3">Recent Payments</h3>
                    {paymentHistory && paymentHistory.length > 0 ? (
                      <div className="space-y-2">
                        {paymentHistory.slice(0, 5).map((payment: any) => (
                          <div key={payment.id} className="flex justify-between items-center p-3 bg-gray-50  rounded-lg">
                            <div>
                              <p className="text-sm font-medium text-gray-900 ">
                                {'$'}{Number(payment.amount_usd).toFixed(2)} {payment.currency}
                              </p>
                              <p className="text-xs text-gray-500 ">{new Date(payment.created_at).toLocaleDateString()}</p>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full ${payment.status === "successful" ? "text-green-600 bg-green-100  /30" : "text-red-600 bg-red-100  /30"}`}>
                              {payment.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 ">No payment history available.</p>
                    )}
                  </div>

                  {/* Usage Information */}
                  {usage && (
                    <div className="mb-6">
                      <h3 className="text-md font-medium text-gray-900  mb-3">Usage This Month</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-gray-50  rounded-lg">
                          <p className="text-sm text-gray-500 ">API Calls</p>
                          <p className="text-lg font-semibold text-gray-900 ">{usage.api_calls_count?.toLocaleString()}</p>
                        </div>
                        <div className="p-3 bg-gray-50  rounded-lg">
                          <p className="text-sm text-gray-500 ">Storage Used</p>
                          <p className="text-lg font-semibold text-gray-900 ">{usage.storage_used_mb?.toFixed(1)} MB</p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="mb-6">
                  <div className="bg-gray-50  rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="font-medium text-gray-900 ">No Active Subscription</h3>
                    </div>
                    <p className="text-sm text-gray-500  mb-4">You don't have an active subscription. Choose a plan to get started.</p>
                    <a href="/pricing" className="inline-flex items-center justify-center px-4 py-2 bg-[#00FF88] text-white font-medium rounded-lg hover:bg-[#00FF88]/90 transition-colors">Choose Plan</a>
                  </div>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-base font-medium text-gray-900  mb-3">Payment Method</h3>
                <div className="bg-gray-50  rounded-lg p-4 flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-10 h-6 bg-gray-200  rounded mr-3"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 ">•••• •••• •••• 4242</p>
                      <p className="text-xs text-gray-500 ">Expires 12/2025</p>
                    </div>
                  </div>
                  <button className="text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm">Update</button>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-base font-medium text-gray-900 ">Billing History</h3>
                  <button className="text-[#1E90FF] hover:text-[#00FF88] transition-colors text-sm flex items-center">
                    <Download className="w-4 h-4 mr-1" />
                    Download All
                  </button>
                </div>
                <div className="bg-gray-50  rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 ">
                    <thead className="bg-gray-100 ">
                      <tr>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">Invoice</th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">Date</th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">Amount</th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500  uppercase tracking-wider">Status</th>
                        <th scope="col" className="relative px-4 py-3"><span className="sr-only">Download</span></th>
                      </tr>
                    </thead>
                    <tbody className="bg-white  divide-y divide-gray-200 ">
                      {invoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td className="px-4 py-3 text-sm text-gray-900 ">{invoice.id}</td>
                          <td className="px-4 py-3 text-sm text-gray-500 ">{invoice.date}</td>
                          <td className="px-4 py-3 text-sm text-gray-900 ">{invoice.amount}</td>
                          <td className="px-4 py-3 text-sm"><span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800  ">{invoice.status}</span></td>
                          <td className="px-4 py-3 text-sm text-right"><button className="text-[#1E90FF] hover:text-[#00FF88] transition-colors"><Download className="w-4 h-4" /></button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === "notifications" && (
          <div className="bg-white  rounded-xl shadow-sm border border-gray-200  overflow-hidden">
            <div className="p-6 border-b border-gray-200 ">
              <h2 className="text-lg font-semibold text-gray-900 ">Notification Preferences</h2>
              <p className="text-sm text-gray-500 ">Manage how you receive notifications.</p>
            </div>
            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-base font-medium text-gray-900  mb-3">Email Notifications</h3>
                <div className="space-y-4">
                  {Object.entries(notificationSettings.email).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-700 ">
                          {key === "taskCompleted" ? "Task Completed" : key === "weeklyReport" ? "Weekly Report" : "New Features & Updates"}
                        </p>
                        <p className="text-xs text-gray-500 ">
                          {key === "taskCompleted" ? "Get notified when an agent completes a task" : key === "weeklyReport" ? "Receive a weekly summary of agent activity" : "Learn about new features and updates"}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" checked={Boolean(value)} onChange={() => handleNotificationToggle("email", key)} className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#1E90FF] :ring-[#1E90FF] rounded-full peer  peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all  peer-checked:bg-[#1E90FF]"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Other notification categories (push, inApp) omitted here for brevity but can be added similarly */}

              <div className="mt-6 pt-6 border-t border-gray-200  flex justify-end">
                <button type="button" className="px-6 py-2 bg-[#1E90FF] text-white rounded-lg text-sm font-medium hover:bg-[#1E90FF]/90 transition-colors">Save Preferences</button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}
