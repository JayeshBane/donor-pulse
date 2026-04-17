// donorpulse-frontend\src\app\hospital\machines\page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { 
  Plus, Settings, Activity, AlertCircle, CheckCircle, 
  Power, PowerOff, Edit, Trash2 
} from 'lucide-react'
import apiClient from '@/lib/api-client'

interface Machine {
  _id: string
  machine_id: string
  name: string
  machine_type: string
  status: string
  donation_types: string[]
  floor?: string
  room?: string
  is_active: boolean
  operating_start: string
  operating_end: string
}

export default function HospitalMachinesPage() {
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [hospital, setHospital] = useState<any>(null)
  const [newMachine, setNewMachine] = useState({
    machine_id: '',
    name: '',
    machine_type: 'whole_blood',
    donation_types: ['whole_blood'],
    floor: '',
    room: '',
    operating_start: '09:00',
    operating_end: '17:00',
    max_daily_donations: 15,
    slot_duration_minutes: 30,
    buffer_minutes: 15
  })

  useEffect(() => {
    const hospitalData = localStorage.getItem('hospital')
    if (hospitalData) {
      setHospital(JSON.parse(hospitalData))
    }
    fetchMachines()
  }, [])

  const fetchMachines = async () => {
    try {
      const hospitalData = JSON.parse(localStorage.getItem('hospital') || '{}')
      
      // Use apiClient instead of hardcoded URL with API_BASE_URL
      const response = await apiClient.get(`/machines/hospital/${hospitalData.id}`)
      setMachines(response.data)
    } catch (error) {
      console.error('Failed to fetch machines', error)
    } finally {
      setLoading(false)
    }
  }

  const addMachine = async () => {
    try {
      // Use apiClient instead of hardcoded URL with template literal bug
      await apiClient.post('/machines/add', newMachine)
      alert('Machine added successfully!')
      setShowAddForm(false)
      fetchMachines()
      setNewMachine({
        machine_id: '',
        name: '',
        machine_type: 'whole_blood',
        donation_types: ['whole_blood'],
        floor: '',
        room: '',
        operating_start: '09:00',
        operating_end: '17:00',
        max_daily_donations: 15,
        slot_duration_minutes: 30,
        buffer_minutes: 15
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add machine')
    }
  }

  const updateMachineStatus = async (machineId: string, status: string) => {
    try {
      // Use apiClient instead of hardcoded URL
      await apiClient.patch(`/machines/${machineId}/status`, { status })
      fetchMachines()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update status')
    }
  }

  const toggleMachineActive = async (machineId: string, currentActive: boolean) => {
    try {
      // Use apiClient instead of hardcoded URL
      await apiClient.patch(`/machines/${machineId}/toggle-active`, {})
      alert(`Machine ${currentActive ? 'deactivated' : 'activated'} successfully`)
      fetchMachines()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to toggle machine status')
    }
  }

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'available': return 'bg-green-100 text-green-800'
      case 'in_use': return 'bg-blue-100 text-blue-800'
      case 'maintenance': return 'bg-red-100 text-red-800'
      case 'cleaning': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'available': return <CheckCircle className="h-4 w-4" />
      case 'in_use': return <Activity className="h-4 w-4" />
      case 'maintenance': return <AlertCircle className="h-4 w-4" />
      default: return <Settings className="h-4 w-4" />
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Machine Management</h1>
        <Button onClick={() => setShowAddForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Machine
        </Button>
      </div>

      {/* Add Machine Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Add New Machine</h2>
            <div className="space-y-4">
              <Input
                label="Machine ID"
                value={newMachine.machine_id}
                onChange={(e) => setNewMachine({...newMachine, machine_id: e.target.value})}
                placeholder="e.g., M-001"
              />
              <Input
                label="Machine Name"
                value={newMachine.name}
                onChange={(e) => setNewMachine({...newMachine, name: e.target.value})}
                placeholder="e.g., Donation Station A"
              />
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Machine Type</label>
                <select
                  className="w-full px-3 py-2 border rounded-lg"
                  value={newMachine.machine_type}
                  onChange={(e) => setNewMachine({...newMachine, machine_type: e.target.value})}
                >
                  <option value="whole_blood">Whole Blood</option>
                  <option value="platelet">Platelet</option>
                  <option value="plasma">Plasma</option>
                  <option value="double_rbc">Double RBC</option>
                  <option value="multi_purpose">Multi Purpose</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Donation Types</label>
                <div className="space-y-2">
                  {['whole_blood', 'platelets', 'plasma', 'double_rbc'].map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newMachine.donation_types.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewMachine({
                              ...newMachine,
                              donation_types: [...newMachine.donation_types, type]
                            })
                          } else {
                            setNewMachine({
                              ...newMachine,
                              donation_types: newMachine.donation_types.filter(t => t !== type)
                            })
                          }
                        }}
                        className="mr-2"
                      />
                      {type.replace('_', ' ').toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>
              <Input
                label="Floor"
                value={newMachine.floor}
                onChange={(e) => setNewMachine({...newMachine, floor: e.target.value})}
                placeholder="e.g., Ground Floor"
              />
              <Input
                label="Room"
                value={newMachine.room}
                onChange={(e) => setNewMachine({...newMachine, room: e.target.value})}
                placeholder="e.g., Room 101"
              />
              <div className="grid grid-cols-2 gap-2">
                <Input
                  label="Start Time"
                  type="time"
                  value={newMachine.operating_start}
                  onChange={(e) => setNewMachine({...newMachine, operating_start: e.target.value})}
                />
                <Input
                  label="End Time"
                  type="time"
                  value={newMachine.operating_end}
                  onChange={(e) => setNewMachine({...newMachine, operating_end: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  label="Slot Duration (min)"
                  type="number"
                  value={newMachine.slot_duration_minutes}
                  onChange={(e) => setNewMachine({...newMachine, slot_duration_minutes: parseInt(e.target.value)})}
                />
                <Input
                  label="Buffer Time (min)"
                  type="number"
                  value={newMachine.buffer_minutes}
                  onChange={(e) => setNewMachine({...newMachine, buffer_minutes: parseInt(e.target.value)})}
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <Button onClick={addMachine}>Add</Button>
              <Button variant="secondary" onClick={() => setShowAddForm(false)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}

      {/* Machines Grid */}
      {loading ? (
        <div className="text-center py-8">Loading machines...</div>
      ) : machines.length === 0 ? (
        <Card>
          <div className="text-center py-8">
            <p className="text-gray-500">No machines added yet</p>
            <Button className="mt-4" onClick={() => setShowAddForm(true)}>
              Add Your First Machine
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {machines.map((machine) => (
            <Card key={machine._id} className={`hover:shadow-lg transition-shadow ${!machine.is_active ? 'opacity-60' : ''}`}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{machine.name}</h3>
                  <p className="text-sm text-gray-500">ID: {machine.machine_id}</p>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => toggleMachineActive(machine._id, machine.is_active)}
                    className={`p-1 rounded ${machine.is_active ? 'text-green-600 hover:text-green-800' : 'text-gray-400 hover:text-gray-600'}`}
                    title={machine.is_active ? 'Deactivate' : 'Activate'}
                  >
                    {machine.is_active ? <Power className="h-4 w-4" /> : <PowerOff className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              
              <div className="flex justify-between items-center mb-3">
                <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 ${getStatusColor(machine.status)}`}>
                  {getStatusIcon(machine.status)}
                  {machine.status.replace('_', ' ').toUpperCase()}
                </span>
                <span className={`text-xs ${machine.is_active ? 'text-green-600' : 'text-red-600'}`}>
                  {machine.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="space-y-2 mb-4 text-sm">
                <p>
                  <span className="font-medium">Type:</span> {machine.machine_type.replace('_', ' ').toUpperCase()}
                </p>
                <p>
                  <span className="font-medium">Donation Types:</span> {machine.donation_types.map(t => t.replace('_', ' ').toUpperCase()).join(', ')}
                </p>
                <p>
                  <span className="font-medium">Hours:</span> {machine.operating_start} - {machine.operating_end}
                </p>
                {machine.floor && (
                  <p>
                    <span className="font-medium">Location:</span> {machine.floor} {machine.room ? `- ${machine.room}` : ''}
                  </p>
                )}
              </div>
              
              {machine.is_active && (
                <div className="flex gap-2 flex-wrap">
                  {machine.status !== 'available' && (
                    <Button 
                      size="sm" 
                      variant="success"
                      onClick={() => updateMachineStatus(machine._id, 'available')}
                    >
                      Mark Available
                    </Button>
                  )}
                  {machine.status !== 'in_use' && (
                    <Button 
                      size="sm" 
                      variant="primary"
                      onClick={() => updateMachineStatus(machine._id, 'in_use')}
                    >
                      Start Donation
                    </Button>
                  )}
                  {machine.status !== 'maintenance' && (
                    <Button 
                      size="sm" 
                      variant="danger"
                      onClick={() => updateMachineStatus(machine._id, 'maintenance')}
                    >
                      Maintenance
                    </Button>
                  )}
                  {machine.status !== 'cleaning' && (
                    <Button 
                      size="sm" 
                      variant="secondary"
                      onClick={() => updateMachineStatus(machine._id, 'cleaning')}
                    >
                      Cleaning
                    </Button>
                  )}
                </div>
              )}
              
              {!machine.is_active && (
                <div className="text-center text-gray-500 text-sm mt-2">
                  Machine is deactivated. Click the power button to activate.
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}