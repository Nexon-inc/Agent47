"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Calendar as CalendarIcon,
  Plus,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  Users,
  Bell,
  Edit,
  Trash2,
  Filter,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  Eye,
  EyeOff,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/stores/auth-store"

interface CalendarEvent {
  id: number
  title: string
  description?: string
  start_time: string
  end_time: string
  location?: string
  attendees?: string[]
  event_type: string
  status: string
  is_recurring: boolean
  recurrence_pattern?: string
  created_by: number
  created_at: string
  updated_at: string
}

interface CalendarStats {
  total_events: number
  upcoming_events: number
  completed_events: number
  cancelled_events: number
  this_week_events: number
  next_week_events: number
}

export default function CalendarTab() {
  const { user } = useAuthStore()
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [view, setView] = useState<"month" | "week" | "day">("month")
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [stats, setStats] = useState<CalendarStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [isCreatingEvent, setIsCreatingEvent] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [filterType, setFilterType] = useState<string>("all")
  const [filterStatus, setFilterStatus] = useState<string>("all")

  // Event form state
  const [eventForm, setEventForm] = useState({
    title: "",
    description: "",
    start_time: "",
    end_time: "",
    location: "",
    attendees: "",
    event_type: "meeting",
    is_recurring: false,
    recurrence_pattern: "none",
  })

  // Load calendar data
  useEffect(() => {
    loadCalendarData()
  }, [currentDate, view])

  // Subscribe to real-time calendar updates via WebSocket
  useEffect(() => {
    const { websocketService } = require('@/lib/websocket-service')
    
    if (!websocketService.getConnectionStatus()) {
      websocketService.connect()
    }

    // Reload calendar when events are created/updated
    const unsubscribe = websocketService.subscribe('notification', (message) => {
      if (message.data?.type === 'task_completed' || message.data?.type === 'system_update') {
        loadCalendarData()
      }
    })

    return () => unsubscribe()
  }, [currentDate, view])

  const loadCalendarData = async () => {
    try {
      setIsRefreshing(true)
      
      const startDate = new Date(currentDate)
      const endDate = new Date(currentDate)
      
      if (view === "month") {
        startDate.setDate(1)
        endDate.setMonth(endDate.getMonth() + 1)
        endDate.setDate(0)
      } else if (view === "week") {
        const day = startDate.getDay()
        startDate.setDate(startDate.getDate() - day)
        endDate.setDate(startDate.getDate() + 6)
      }
      // For day view, startDate and endDate are the same

      const [eventsResponse, statsResponse] = await Promise.all([
        apiClient.get(`/api/calendar/events?start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`),
        apiClient.get("/api/calendar/stats")
      ])
      
      setEvents(eventsResponse.data)
      setStats(statsResponse.data)
      setLastUpdated(new Date())
      
    } catch (error) {
      console.error("Failed to load calendar data:", error)
      generateFallbackData()
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  const generateFallbackData = () => {
    const mockEvents: CalendarEvent[] = [
      {
        id: 1,
        title: "Team Standup",
        description: "Daily team synchronization meeting",
        start_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() + 2.5 * 60 * 60 * 1000).toISOString(),
        location: "Conference Room A",
        attendees: ["john@example.com", "jane@example.com"],
        event_type: "meeting",
        status: "scheduled",
        is_recurring: true,
        recurrence_pattern: "daily",
        created_by: user?.id || 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        title: "Client Presentation",
        description: "Present quarterly results to key clients",
        start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() + 25 * 60 * 60 * 1000).toISOString(),
        location: "Virtual Meeting",
        attendees: ["client@example.com"],
        event_type: "presentation",
        status: "scheduled",
        is_recurring: false,
        created_by: user?.id || 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]

    const mockStats: CalendarStats = {
      total_events: 12,
      upcoming_events: 8,
      completed_events: 4,
      cancelled_events: 0,
      this_week_events: 5,
      next_week_events: 3,
    }

    setEvents(mockEvents)
    setStats(mockStats)
    setLastUpdated(new Date())
  }

  const handleCreateEvent = async () => {
    try {
      setIsCreatingEvent(true)
      
      const eventData = {
        ...eventForm,
        attendees: eventForm.attendees.split(",").map(email => email.trim()).filter(Boolean),
        start_time: new Date(eventForm.start_time).toISOString(),
        end_time: new Date(eventForm.end_time).toISOString(),
      }
      
      await apiClient.post("/api/calendar/events", eventData)
      await loadCalendarData()
      setIsCreatingEvent(false)
      setEventForm({
        title: "",
        description: "",
        start_time: "",
        end_time: "",
        location: "",
        attendees: "",
        event_type: "meeting",
        is_recurring: false,
        recurrence_pattern: "none",
      })
      
    } catch (error) {
      console.error("Failed to create event:", error)
    } finally {
      setIsCreatingEvent(false)
    }
  }

  const handleUpdateEvent = async (eventId: number, updates: Partial<CalendarEvent>) => {
    try {
      await apiClient.put(`/api/calendar/events/${eventId}`, updates)
      await loadCalendarData()
    } catch (error) {
      console.error("Failed to update event:", error)
    }
  }

  const handleDeleteEvent = async (eventId: number) => {
    try {
      await apiClient.delete(`/api/calendar/events/${eventId}`)
      await loadCalendarData()
    } catch (error) {
      console.error("Failed to delete event:", error)
    }
  }

  const handleRefresh = () => {
    loadCalendarData()
  }

  const navigateDate = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate)
    if (view === "month") {
      newDate.setMonth(newDate.getMonth() + (direction === "next" ? 1 : -1))
    } else if (view === "week") {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 7 : -7))
    } else {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 1 : -1))
    }
    setCurrentDate(newDate)
  }

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case "meeting": return "bg-blue-100 text-blue-800"
      case "presentation": return "bg-purple-100 text-purple-800"
      case "deadline": return "bg-red-100 text-red-800"
      case "reminder": return "bg-yellow-100 text-yellow-800"
      case "personal": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "scheduled": return "bg-green-100 text-green-800"
      case "in_progress": return "bg-blue-100 text-blue-800"
      case "completed": return "bg-gray-100 text-gray-800"
      case "cancelled": return "bg-red-100 text-red-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const filteredEvents = events.filter(event => {
    if (filterType !== "all" && event.event_type !== filterType) return false
    if (filterStatus !== "all" && event.status !== filterStatus) return false
    return true
  })

  const renderCalendarGrid = () => {
    if (view === "month") {
      return renderMonthView()
    } else if (view === "week") {
      return renderWeekView()
    } else {
      return renderDayView()
    }
  }

  const renderMonthView = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startDate = new Date(firstDay)
    startDate.setDate(startDate.getDate() - firstDay.getDay())
    
    const days = []
    const current = new Date(startDate)
    
    for (let i = 0; i < 42; i++) {
      const dayEvents = filteredEvents.filter(event => {
        const eventDate = new Date(event.start_time)
        return eventDate.toDateString() === current.toDateString()
      })
      
      days.push(
        <div
          key={i}
          className={`min-h-[120px] p-2 border border-gray-200  ${
            current.getMonth() !== month ? "bg-gray-50 " : ""
          } ${current.toDateString() === new Date().toDateString() ? "bg-blue-50 " : ""}`}
        >
          <div className="text-sm font-medium mb-1">{current.getDate()}</div>
          <div className="space-y-1">
            {dayEvents.slice(0, 3).map(event => (
              <div
                key={event.id}
                className={`text-xs p-1 rounded cursor-pointer ${getEventTypeColor(event.event_type)}`}
                onClick={() => setSelectedEvent(event)}
              >
                {event.title}
              </div>
            ))}
            {dayEvents.length > 3 && (
              <div className="text-xs text-gray-500">+{dayEvents.length - 3} more</div>
            )}
          </div>
        </div>
      )
      current.setDate(current.getDate() + 1)
    }
    
    return (
      <div className="grid grid-cols-7 gap-0 border border-gray-200  rounded-lg overflow-hidden">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(day => (
          <div key={day} className="p-3 bg-gray-100  font-medium text-center">
            {day}
          </div>
        ))}
        {days}
      </div>
    )
  }

  const renderWeekView = () => {
    const startDate = new Date(currentDate)
    const day = startDate.getDay()
    startDate.setDate(startDate.getDate() - day)
    
    const days = []
    for (let i = 0; i < 7; i++) {
      const current = new Date(startDate)
      current.setDate(startDate.getDate() + i)
      const dayEvents = filteredEvents.filter(event => {
        const eventDate = new Date(event.start_time)
        return eventDate.toDateString() === current.toDateString()
      })
      
      days.push(
        <div key={i} className="flex-1 border border-gray-200 ">
          <div className="p-3 bg-gray-100  font-medium text-center border-b">
            {current.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
          </div>
          <div className="p-2 space-y-1 min-h-[400px]">
            {dayEvents.map(event => (
              <div
                key={event.id}
                className={`text-xs p-2 rounded cursor-pointer ${getEventTypeColor(event.event_type)}`}
                onClick={() => setSelectedEvent(event)}
              >
                <div className="font-medium">{event.title}</div>
                <div className="text-xs opacity-75">
                  {new Date(event.start_time).toLocaleTimeString("en-US", { 
                    hour: "numeric", 
                    minute: "2-digit" 
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }
    
    return <div className="flex">{days}</div>
  }

  const renderDayView = () => {
    const dayEvents = filteredEvents.filter(event => {
      const eventDate = new Date(event.start_time)
      return eventDate.toDateString() === currentDate.toDateString()
    })
    
    return (
      <div className="space-y-4">
        <div className="text-lg font-medium mb-4">
          {currentDate.toLocaleDateString("en-US", { 
            weekday: "long", 
            year: "numeric", 
            month: "long", 
            day: "numeric" 
          })}
        </div>
        <div className="space-y-3">
          {dayEvents.map(event => (
            <Card key={event.id} className="cursor-pointer" onClick={() => setSelectedEvent(event)}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium">{event.title}</h3>
                    <p className="text-sm text-gray-600 ">{event.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(event.start_time).toLocaleTimeString("en-US", { 
                          hour: "numeric", 
                          minute: "2-digit" 
                        })} - {new Date(event.end_time).toLocaleTimeString("en-US", { 
                          hour: "numeric", 
                          minute: "2-digit" 
                        })}
                      </div>
                      {event.location && (
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {event.location}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getEventTypeColor(event.event_type)}>
                      {event.event_type}
                    </Badge>
                    <Badge className={getStatusColor(event.status)}>
                      {event.status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {dayEvents.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No events scheduled for this day
            </div>
          )}
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 ">Calendar</h1>
          <p className="text-gray-600  mt-1">
            Manage your events and schedule
            {lastUpdated && (
              <span className="text-xs text-gray-500 ml-2">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Event
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Event</DialogTitle>
                <DialogDescription>
                  Add a new event to your calendar
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Event Title</Label>
                    <Input
                      id="title"
                      value={eventForm.title}
                      onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                      placeholder="Enter event title"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="event_type">Event Type</Label>
                    <Select
                      value={eventForm.event_type}
                      onValueChange={(value) => setEventForm({ ...eventForm, event_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="meeting">Meeting</SelectItem>
                        <SelectItem value="presentation">Presentation</SelectItem>
                        <SelectItem value="deadline">Deadline</SelectItem>
                        <SelectItem value="reminder">Reminder</SelectItem>
                        <SelectItem value="personal">Personal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={eventForm.description}
                    onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                    placeholder="Enter event description"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start_time">Start Time</Label>
                    <Input
                      id="start_time"
                      type="datetime-local"
                      value={eventForm.start_time}
                      onChange={(e) => setEventForm({ ...eventForm, start_time: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end_time">End Time</Label>
                    <Input
                      id="end_time"
                      type="datetime-local"
                      value={eventForm.end_time}
                      onChange={(e) => setEventForm({ ...eventForm, end_time: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={eventForm.location}
                    onChange={(e) => setEventForm({ ...eventForm, location: e.target.value })}
                    placeholder="Enter location or meeting link"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="attendees">Attendees (comma-separated emails)</Label>
                  <Input
                    id="attendees"
                    value={eventForm.attendees}
                    onChange={(e) => setEventForm({ ...eventForm, attendees: e.target.value })}
                    placeholder="john@example.com, jane@example.com"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="recurring"
                    checked={eventForm.is_recurring}
                    onCheckedChange={(checked) => setEventForm({ ...eventForm, is_recurring: checked })}
                  />
                  <Label htmlFor="recurring">Recurring Event</Label>
                </div>
                {eventForm.is_recurring && (
                  <div className="space-y-2">
                    <Label htmlFor="recurrence_pattern">Recurrence Pattern</Label>
                    <Select
                      value={eventForm.recurrence_pattern}
                      onValueChange={(value) => setEventForm({ ...eventForm, recurrence_pattern: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEventForm({
                  title: "",
                  description: "",
                  start_time: "",
                  end_time: "",
                  location: "",
                  attendees: "",
                  event_type: "meeting",
                  is_recurring: false,
                  recurrence_pattern: "none",
                })}>
                  Cancel
                </Button>
                <Button onClick={handleCreateEvent} disabled={isCreatingEvent}>
                  {isCreatingEvent ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4 mr-2" />
                  )}
                  Create Event
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Events</CardTitle>
              <CalendarIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_events}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.upcoming_events}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">This Week</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.this_week_events}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Next Week</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.next_week_events}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Calendar Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={() => navigateDate("prev")}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={() => navigateDate("next")}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
              <h2 className="text-xl font-semibold">
                {currentDate.toLocaleDateString("en-US", { 
                  month: "long", 
                  year: "numeric" 
                })}
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <Select value={view} onValueChange={(value: "month" | "week" | "day") => setView(value)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="week">Week</SelectItem>
                  <SelectItem value="day">Day</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="meeting">Meeting</SelectItem>
                  <SelectItem value="presentation">Presentation</SelectItem>
                  <SelectItem value="deadline">Deadline</SelectItem>
                  <SelectItem value="reminder">Reminder</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {renderCalendarGrid()}
        </CardContent>
      </Card>

      {/* Event Details Modal */}
      {selectedEvent && (
        <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedEvent.title}</DialogTitle>
              <DialogDescription>
                Event details and management
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Start Time</Label>
                  <p className="text-sm text-gray-600 ">
                    {new Date(selectedEvent.start_time).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium">End Time</Label>
                  <p className="text-sm text-gray-600 ">
                    {new Date(selectedEvent.end_time).toLocaleString()}
                  </p>
                </div>
              </div>
              {selectedEvent.description && (
                <div>
                  <Label className="text-sm font-medium">Description</Label>
                  <p className="text-sm text-gray-600 ">
                    {selectedEvent.description}
                  </p>
                </div>
              )}
              {selectedEvent.location && (
                <div>
                  <Label className="text-sm font-medium">Location</Label>
                  <p className="text-sm text-gray-600 ">
                    {selectedEvent.location}
                  </p>
                </div>
              )}
              {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Attendees</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedEvent.attendees.map((attendee, index) => (
                      <Badge key={index} variant="outline">
                        {attendee}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex items-center gap-4">
                <Badge className={getEventTypeColor(selectedEvent.event_type)}>
                  {selectedEvent.event_type}
                </Badge>
                <Badge className={getStatusColor(selectedEvent.status)}>
                  {selectedEvent.status}
                </Badge>
                {selectedEvent.is_recurring && (
                  <Badge variant="outline">
                    Recurring: {selectedEvent.recurrence_pattern}
                  </Badge>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedEvent(null)}>
                Close
              </Button>
              <Button variant="outline">
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button 
                variant="destructive"
                onClick={() => {
                  handleDeleteEvent(selectedEvent.id)
                  setSelectedEvent(null)
                }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
