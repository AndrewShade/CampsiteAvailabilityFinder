export interface CampgroundResult {
  facility_id: string
  facility_name: string
  parent_name: string
  city: string
  state: string
  latitude: number
  longitude: number
  reservable: boolean
  description: string
}

export interface AvailabilityResult {
  id: number
  campsite_id: string
  campsite_name: string
  site_type: string
  loop: string
  available_dates: string // JSON-encoded string[]
  found_at: string
  notification_sent: boolean
}

export interface WatchlistEntry {
  id: number
  campground_id: string
  campground_name: string
  park_name: string
  start_date: string
  end_date: string
  min_nights: number
  site_types: string
  status: 'watching' | 'found' | 'paused'
  last_checked: string | null
  created_at: string
  results: AvailabilityResult[]
}

export interface Webhook {
  id: number
  name: string
  webhook_type: 'slack' | 'discord' | 'generic'
  url: string
  enabled: boolean
  created_at: string
}

export interface AppSettings {
  check_interval_minutes: number
  ridb_api_key_configured: boolean
}
