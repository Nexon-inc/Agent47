import { toast as sonnerToast } from "sonner"
import { CheckCircle2, XCircle, AlertTriangle, Info, Loader2 } from "lucide-react"

export type ToastVariant = "success" | "error" | "warning" | "info" | "loading"

interface ToastOptions {
  title: string
  description?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

const toastIcons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  loading: Loader2,
}

const toastStyles = {
  success: {
    className: "bg-green-50 border-green-200 text-green-800",
    iconClassName: "text-green-600",
  },
  error: {
    className: "bg-red-50 border-red-200 text-red-800",
    iconClassName: "text-red-600",
  },
  warning: {
    className: "bg-yellow-50 border-yellow-200 text-yellow-800",
    iconClassName: "text-yellow-600",
  },
  info: {
    className: "bg-blue-50 border-blue-200 text-blue-800",
    iconClassName: "text-blue-600",
  },
  loading: {
    className: "bg-gray-50 border-gray-200 text-gray-800",
    iconClassName: "text-gray-600",
  },
}

export const toast = {
  success: (options: ToastOptions) => {
    const Icon = toastIcons.success
    return sonnerToast.success(options.title, {
      description: options.description,
      duration: options.duration || 5000,
      icon: <Icon className="h-5 w-5 text-green-600" />,
      action: options.action,
      className: toastStyles.success.className,
    })
  },

  error: (options: ToastOptions) => {
    const Icon = toastIcons.error
    return sonnerToast.error(options.title, {
      description: options.description,
      duration: options.duration || 7000,
      icon: <Icon className="h-5 w-5 text-red-600" />,
      action: options.action,
      className: toastStyles.error.className,
    })
  },

  warning: (options: ToastOptions) => {
    const Icon = toastIcons.warning
    return sonnerToast.warning(options.title, {
      description: options.description,
      duration: options.duration || 6000,
      icon: <Icon className="h-5 w-5 text-yellow-600" />,
      action: options.action,
      className: toastStyles.warning.className,
    })
  },

  info: (options: ToastOptions) => {
    const Icon = toastIcons.info
    return sonnerToast.info(options.title, {
      description: options.description,
      duration: options.duration || 5000,
      icon: <Icon className="h-5 w-5 text-blue-600" />,
      action: options.action,
      className: toastStyles.info.className,
    })
  },

  loading: (options: ToastOptions) => {
    const Icon = toastIcons.loading
    return sonnerToast.loading(options.title, {
      description: options.description,
      icon: <Icon className="h-5 w-5 text-gray-600 animate-spin" />,
      className: toastStyles.loading.className,
    })
  },

  // Helper for API errors
  apiError: (error: any, defaultMessage = "An error occurred") => {
    const message = error?.response?.data?.message || 
                   error?.message || 
                   defaultMessage
    
    return toast.error({
      title: "Error",
      description: message,
      duration: 7000,
    })
  },

  // Helper for API success
  apiSuccess: (message: string, description?: string) => {
    return toast.success({
      title: message,
      description,
      duration: 5000,
    })
  },
}

