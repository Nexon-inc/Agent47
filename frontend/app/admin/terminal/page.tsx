"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Terminal, 
  Play,
  Square,
  RefreshCw,
  Settings,
  AlertTriangle,
  History,
  Trash2,
  Badge
} from "lucide-react"
import { useAdminStore } from "@/lib/stores/admin-store"
import AdminLayout from "@/components/admin/layout"
import { adminAPI } from "@/lib/services/admin-api"

interface CommandHistory {
  command: string
  output: string
  timestamp: string
  status: 'success' | 'error' | 'running'
}

export default function AdminTerminalPage() {
  const [command, setCommand] = useState("")
  const [output, setOutput] = useState<string[]>([])
  const [commandHistory, setCommandHistory] = useState<CommandHistory[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [sessionId, setSessionId] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const terminalRef = useRef<HTMLDivElement>(null)
  const { currentAdmin } = useAdminStore()

  const hasAccess = currentAdmin?.permissions?.includes("super_admin")

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [output])

  useEffect(() => {
    const initializeSession = async () => {
      if (hasAccess) {
        try {
          const session = await adminAPI.createTerminalSession()
          setSessionId(session.session_id || session.id)
        } catch (err: any) {
          setError(err.message || "Failed to initialize terminal session")
        }
      }
    }
    initializeSession()
  }, [hasAccess])

  const executeCommand = async () => {
    if (!command.trim() || !sessionId) return
    
    const newOutput = [...output, `$ ${command}`]
    setOutput(newOutput)
    setIsRunning(true)
    setError(null)
    
    // Add to command history
    const historyEntry: CommandHistory = {
      command: command,
      output: '',
      timestamp: new Date().toISOString(),
      status: 'running'
    }
    setCommandHistory(prev => [...prev, historyEntry])
    
    try {
      const result = await adminAPI.executeTerminalCommand(sessionId, command)
      const response = result.output || result.stdout || result.stderr || 'Command executed successfully'
      
      setOutput([...newOutput, response])
      
      // Update command history
      setCommandHistory(prev => prev.map((entry, index) => 
        index === prev.length - 1 
          ? { ...entry, output: response, status: result.exit_code === 0 ? 'success' : 'error' }
          : entry
      ))
    } catch (error: any) {
      const errorResponse = `Error: ${error.message || 'Command failed'}`
      setOutput([...newOutput, errorResponse])
      setError(errorResponse)
      
      // Update command history with error
      setCommandHistory(prev => prev.map((entry, index) => 
        index === prev.length - 1 
          ? { ...entry, output: errorResponse, status: 'error' }
          : entry
      ))
    } finally {
      setIsRunning(false)
      setCommand("")
    }
  }

  const loadHistory = async () => {
    if (!sessionId) return
    try {
      const history = await adminAPI.getTerminalHistory(sessionId)
      if (history.commands) {
        setCommandHistory(history.commands.map((cmd: any) => ({
          command: cmd.command,
          output: cmd.output || cmd.stdout || '',
          timestamp: cmd.timestamp || cmd.created_at,
          status: cmd.exit_code === 0 ? 'success' : 'error'
        })))
      }
    } catch (err: any) {
      console.error("Failed to load history:", err)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeCommand()
    }
  }

  const clearTerminal = () => {
    setOutput([])
  }

  const clearHistory = () => {
    setCommandHistory([])
  }

  const runFromHistory = (historyCommand: string) => {
    setCommand(historyCommand)
    setShowHistory(false)
  }

  if (!hasAccess) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Terminal className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              Super admin access required.
            </p>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (!sessionId) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Web Terminal</h1>
            <p className="text-gray-600 dark:text-gray-400">Secure command execution interface</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => {
              setShowHistory(!showHistory)
              if (!showHistory) loadHistory()
            }}>
              <History className="h-4 w-4 mr-2" />
              History
            </Button>
            <Button variant="outline" onClick={clearTerminal}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Clear
            </Button>
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Command History Panel */}
        {showHistory && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Command History</span>
                <Button variant="outline" size="sm" onClick={clearHistory}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear History
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {commandHistory.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No command history</p>
                ) : (
                  commandHistory.map((entry, index) => (
                    <div key={index} className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <div className="flex items-center justify-between mb-2">
                        <code className="text-sm font-mono text-gray-900 dark:text-white">
                          {entry.command}
                        </code>
                        <Badge className={
                          entry.status === 'success' ? 'bg-green-100 text-green-800' :
                          entry.status === 'error' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }>
                          {entry.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">
                        {new Date(entry.timestamp).toLocaleString()}
                      </p>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => runFromHistory(entry.command)}
                      >
                        Run Again
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Terminal */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Terminal Session
              {sessionId && (
                <span className="text-sm text-gray-500">({sessionId})</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Terminal Output */}
              <div 
                ref={terminalRef}
                className="bg-black text-green-400 p-4 rounded-lg h-96 overflow-y-auto font-mono text-sm"
              >
                <div className="mb-2 text-gray-400">
                  Agent47 Web Terminal v1.0.0
                </div>
                <div className="mb-2 text-gray-400">
                  Type 'help' for available commands
                </div>
                {output.map((line, index) => (
                  <div key={index} className="mb-1">
                    {line}
                  </div>
                ))}
                {isRunning && (
                  <div className="text-yellow-400">Executing command...</div>
                )}
              </div>

              {/* Command Input */}
              <div className="flex gap-2">
                <Input
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter command..."
                  className="font-mono dark:bg-gray-800 dark:border-gray-600"
                  disabled={isRunning}
                />
                <Button 
                  onClick={executeCommand}
                  disabled={!command.trim() || isRunning}
                >
                  {isRunning ? (
                    <Square className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {/* Quick Commands */}
              <div className="flex flex-wrap gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("ls -la")}
                  disabled={isRunning}
                >
                  ls -la
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("ps aux")}
                  disabled={isRunning}
                >
                  ps aux
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("df -h")}
                  disabled={isRunning}
                >
                  df -h
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("top")}
                  disabled={isRunning}
                >
                  top
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("whoami")}
                  disabled={isRunning}
                >
                  whoami
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setCommand("pwd")}
                  disabled={isRunning}
                >
                  pwd
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Notice */}
        <Card className="border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800 dark:text-yellow-200">Security Notice</h3>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  This terminal provides direct access to the server. All commands are logged and monitored. 
                  Use with caution and only execute commands you understand. Session ID: {sessionId}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  )
}
