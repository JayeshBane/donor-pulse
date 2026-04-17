// frontend\src\app\admin\dashboard\page.tsx
"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  Shield,
  Users,
  CheckCircle,
  Check,
  Ban,
  Building2,
  Download,
  Mail,
  Clock,
  FileText,
} from "lucide-react";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import apiClient from '@/lib/api-client';

interface Hospital {
  id: string;
  name: string;
  type: string;
  email: string;
  phone: string;
  username: string;
  city: string;
  license_number: string;
  created_at: string;
  is_active?: boolean;
}

interface Donor {
  _id: string;
  name: string;
  medical?: {
    blood_type: string;
  };
  location?: {
    city: string;
    phone: string;
  };
  blood_type?: string;
  city?: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
}

export default function AdminDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [admin, setAdmin] = useState<any>(null);
  const [pendingHospitals, setPendingHospitals] = useState<Hospital[]>([]);
  const [verifiedHospitals, setVerifiedHospitals] = useState<Hospital[]>([]);
  const [donors, setDonors] = useState<Donor[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<
    "pending" | "verified" | "donors" | "analytics" | "logs"
  >("pending");
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [broadcastMessage, setBroadcastMessage] = useState("");
  const [broadcastType, setBroadcastType] = useState("donors");
  const [sending, setSending] = useState(false);

  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [hospitalLogs, setHospitalLogs] = useState<any[]>([]);
  const [donorLogs, setDonorLogs] = useState<any[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logFilter, setLogFilter] = useState("all");

  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    const adminData = localStorage.getItem("admin");

    if (!token) {
      router.push("/admin/login");
    } else {
      setAdmin(JSON.parse(adminData || "{}"));
      fetchData();
    }
  }, [router]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("admin_token");
      
      // Use apiClient for all requests - NO HARDCODED URLs
      const [pendingRes, verifiedRes, statsRes, donorsRes] = await Promise.all([
        apiClient.get("/admin/hospitals/pending"),
        apiClient.get("/admin/hospitals/verified"),
        apiClient.get("/admin/stats"),
        apiClient.get("/donors"),
      ]);

      setPendingHospitals(pendingRes.data.hospitals);
      setVerifiedHospitals(verifiedRes.data.hospitals);

      const mappedDonors = (donorsRes.data.donors || []).map((donor: any) => ({
        ...donor,
        medical: donor.medical || { blood_type: donor.blood_type },
        location: donor.location || { city: donor.city, phone: donor.phone },
      }));
      setDonors(mappedDonors);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Failed to fetch data", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    setLogsLoading(true);
    try {
      // Use apiClient for logs - NO HARDCODED URLs
      const [auditRes, hospitalRes, donorRes] = await Promise.all([
        apiClient.get("/admin/logs/audit"),
        apiClient.get("/admin/logs/hospitals"),
        apiClient.get("/admin/logs/donors"),
      ]);

      setAuditLogs(auditRes.data.logs || []);
      setHospitalLogs(hospitalRes.data.logs || []);
      setDonorLogs(donorRes.data.logs || []);
    } catch (error) {
      console.error("Failed to fetch logs", error);
    } finally {
      setLogsLoading(false);
    }
  };

  const verifyHospital = async (hospitalId: string) => {
    try {
      await apiClient.patch(`/admin/hospitals/${hospitalId}/verify`);
      alert("Hospital verified successfully!");
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to verify hospital");
    }
  };

  const rejectHospital = async (hospitalId: string) => {
    if (!confirm("Are you sure you want to reject this hospital registration?"))
      return;

    try {
      await apiClient.patch(`/admin/hospitals/${hospitalId}/reject`);
      alert("Hospital registration rejected");
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to reject hospital");
    }
  };

  const toggleHospitalActive = async (
    hospitalId: string,
    currentStatus: boolean,
  ) => {
    try {
      await apiClient.patch(`/admin/hospitals/${hospitalId}/toggle-active`);
      alert(
        `Hospital ${currentStatus ? "deactivated" : "activated"} successfully`,
      );
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to toggle status");
    }
  };

  const toggleDonorActive = async (donorId: string, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/donors/${donorId}/toggle-active`);
      alert(
        `Donor ${currentStatus ? "deactivated" : "activated"} successfully`,
      );
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to toggle donor status");
    }
  };

  const sendBroadcast = async () => {
    if (!broadcastMessage.trim()) {
      alert("Please enter a message");
      return;
    }

    setSending(true);
    try {
      const token = localStorage.getItem("admin_token");
      const endpoint =
        broadcastType === "donors"
          ? "/admin/broadcast/donors"
          : "/admin/broadcast/hospitals";

      const response = await apiClient.post(
        endpoint,
        { message: broadcastMessage },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      alert(
        `Broadcast sent! ${response.data.sent} received, ${response.data.failed} failed`,
      );
      setShowBroadcast(false);
      setBroadcastMessage("");

      if (activeTab === "logs") {
        fetchLogs();
      }
    } catch (error: any) {
      console.error("Broadcast error:", error);
      alert(error.response?.data?.detail || "Failed to send broadcast");
    } finally {
      setSending(false);
    }
  };

  const exportData = () => {
    const data = {
      hospitals: verifiedHospitals,
      donors: donors,
      statistics: stats,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `donorpulse_export_${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert("Data exported successfully!");
  };

  const bloodTypeDistribution = () => {
    const counts: Record<string, number> = {};
    donors.forEach((donor) => {
      const bloodType = donor.medical?.blood_type || donor.blood_type;
      if (bloodType) {
        counts[bloodType] = (counts[bloodType] || 0) + 1;
      }
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  };

  const hospitalTypeDistribution = () => {
    const counts: Record<string, number> = {};
    verifiedHospitals.forEach((h) => {
      counts[h.type] = (counts[h.type] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
    }));
  };

  const cityDistribution = () => {
    const counts: Record<string, number> = {};
    donors.forEach((donor) => {
      const city = donor.location?.city || donor.city;
      if (city) {
        counts[city] = (counts[city] || 0) + 1;
      }
    });
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  };

  const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#8884D8",
    "#82CA9D",
    "#FF6B6B",
    "#4ECDC4",
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Admin Dashboard
            </h1>
            <p className="text-gray-500 mt-1">
              Welcome back,{" "}
              <strong>{admin?.full_name || admin?.username}</strong>
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={exportData}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export Data
            </Button>
            <Button
              onClick={() => setShowBroadcast(true)}
              className="flex items-center gap-2"
            >
              <Mail className="h-4 w-4" />
              Broadcast
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">Total Hospitals</p>
                  <p className="text-3xl font-bold">{stats.hospitals.total}</p>
                </div>
                <Building2 className="h-10 w-10 text-blue-200" />
              </div>
            </Card>
            <Card className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-yellow-100 text-sm">
                    Pending Verification
                  </p>
                  <p className="text-3xl font-bold">
                    {stats.hospitals.pending}
                  </p>
                </div>
                <Clock className="h-10 w-10 text-yellow-200" />
              </div>
            </Card>
            <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm">Verified Hospitals</p>
                  <p className="text-3xl font-bold">
                    {stats.hospitals.verified}
                  </p>
                </div>
                <CheckCircle className="h-10 w-10 text-green-200" />
              </div>
            </Card>
            <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Total Donors</p>
                  <p className="text-3xl font-bold">{stats.donors.total}</p>
                </div>
                <Users className="h-10 w-10 text-purple-200" />
              </div>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8 overflow-x-auto">
            <button
              onClick={() => setActiveTab("pending")}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === "pending"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Pending ({pendingHospitals.length})
            </button>
            <button
              onClick={() => setActiveTab("verified")}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === "verified"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Hospitals ({verifiedHospitals.length})
            </button>
            <button
              onClick={() => setActiveTab("donors")}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === "donors"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Donors ({donors.length})
            </button>
            <button
              onClick={() => setActiveTab("analytics")}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === "analytics"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Analytics
            </button>
            <button
              onClick={() => {
                setActiveTab("logs");
                fetchLogs();
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-1 ${
                activeTab === "logs"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <FileText className="h-4 w-4" />
              Logs
            </button>
          </nav>
        </div>

        {/* Pending Hospitals Tab */}
        {activeTab === "pending" && (
          <Card title="Pending Hospital Verifications">
            {pendingHospitals.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
                <p className="text-gray-500">No pending verifications</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingHospitals.map((hospital) => (
                  <div
                    key={hospital.id}
                    className="border rounded-lg p-4 hover:shadow-md"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold">
                            {hospital.name}
                          </h3>
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                            Pending
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                          <p>
                            <span className="font-medium">Type:</span>{" "}
                            {hospital.type.toUpperCase()}
                          </p>
                          <p>
                            <span className="font-medium">License:</span>{" "}
                            {hospital.license_number}
                          </p>
                          <p>
                            <span className="font-medium">Email:</span>{" "}
                            {hospital.email}
                          </p>
                          <p>
                            <span className="font-medium">Phone:</span>{" "}
                            {hospital.phone}
                          </p>
                          <p>
                            <span className="font-medium">City:</span>{" "}
                            {hospital.city}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() => verifyHospital(hospital.id)}
                        >
                          <Check className="h-4 w-4 mr-1" /> Verify
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => rejectHospital(hospital.id)}
                        >
                          <Ban className="h-4 w-4 mr-1" /> Reject
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Verified Hospitals Tab */}
        {activeTab === "verified" && (
          <Card title="Verified Hospitals">
            {verifiedHospitals.length === 0 ? (
              <div className="text-center py-12">
                <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No verified hospitals yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Name</th>
                      <th className="px-4 py-2 text-left">Type</th>
                      <th className="px-4 py-2 text-left">City</th>
                      <th className="px-4 py-2 text-left">Status</th>
                      <th className="px-4 py-2 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {verifiedHospitals.map((hospital) => (
                      <tr
                        key={hospital.id}
                        className="border-t hover:bg-gray-50"
                      >
                        <td className="px-4 py-2 font-medium">
                          {hospital.name}
                        </td>
                        <td className="px-4 py-2">
                          {hospital.type.toUpperCase()}
                        </td>
                        <td className="px-4 py-2">{hospital.city}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs ${
                              hospital.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                            }`}
                          >
                            {hospital.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          <Button
                            size="sm"
                            variant={hospital.is_active ? "danger" : "success"}
                            onClick={() =>
                              toggleHospitalActive(
                                hospital.id,
                                hospital.is_active || false,
                              )
                            }
                          >
                            {hospital.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {/* Donors Tab */}
        {activeTab === "donors" && (
          <Card title="Donor Management">
            {donors.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No donors registered yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Name</th>
                      <th className="px-4 py-2 text-left">Blood Type</th>
                      <th className="px-4 py-2 text-left">City</th>
                      <th className="px-4 py-2 text-left">Phone</th>
                      <th className="px-4 py-2 text-left">Status</th>
                      <th className="px-4 py-2 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {donors.map((donor) => (
                      <tr key={donor._id} className="border-t hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{donor.name}</td>
                        <td className="px-4 py-2">
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {donor.medical?.blood_type ||
                              donor.blood_type ||
                              "N/A"}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          {donor.location?.city || donor.city || "—"}
                        </td>
                        <td className="px-4 py-2">
                          {donor.location?.phone || donor.phone || "—"}
                        </td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs ${
                              donor.is_active
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {donor.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          <Button
                            size="sm"
                            variant={donor.is_active ? "danger" : "success"}
                            onClick={() =>
                              toggleDonorActive(donor._id, donor.is_active)
                            }
                          >
                            {donor.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            <Card title="Blood Type Distribution">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={bloodTypeDistribution()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {bloodTypeDistribution().map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card title="Hospital Type Distribution">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hospitalTypeDistribution()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#8884d8" name="Hospitals" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card title="Top Cities by Donors">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={cityDistribution()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={100} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#82CA9D" name="Donors" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === "logs" && (
          <Card title="System Logs">
            <div className="border-b border-gray-200 mb-4">
              <nav className="-mb-px flex space-x-4">
                <button
                  onClick={() => setLogFilter("all")}
                  className={`py-2 px-3 text-sm font-medium ${
                    logFilter === "all"
                      ? "border-b-2 border-blue-500 text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  All (
                  {auditLogs.length + hospitalLogs.length + donorLogs.length})
                </button>
                <button
                  onClick={() => setLogFilter("audit")}
                  className={`py-2 px-3 text-sm font-medium ${
                    logFilter === "audit"
                      ? "border-b-2 border-blue-500 text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Admin Actions ({auditLogs.length})
                </button>
                <button
                  onClick={() => setLogFilter("hospitals")}
                  className={`py-2 px-3 text-sm font-medium ${
                    logFilter === "hospitals"
                      ? "border-b-2 border-blue-500 text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Hospitals ({hospitalLogs.length})
                </button>
                <button
                  onClick={() => setLogFilter("donors")}
                  className={`py-2 px-3 text-sm font-medium ${
                    logFilter === "donors"
                      ? "border-b-2 border-blue-500 text-blue-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  Donors ({donorLogs.length})
                </button>
              </nav>
            </div>

            {logsLoading ? (
              <div className="text-center py-8">Loading logs...</div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {(logFilter === "all" || logFilter === "audit") &&
                  auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="border-l-4 border-blue-500 bg-blue-50 p-3 rounded-r-lg"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-semibold text-blue-800">
                            {log.action}
                          </span>
                          <span className="text-xs text-gray-500 ml-2">
                            by {log.admin_name}
                          </span>
                          <p className="text-sm text-gray-600 mt-1">
                            {log.details?.hospital_name &&
                              `Hospital: ${log.details.hospital_name}`}
                            {log.details?.message_preview &&
                              `Message: ${log.details.message_preview}`}
                          </p>
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}

                {(logFilter === "all" || logFilter === "hospitals") &&
                  hospitalLogs.map((log) => (
                    <div
                      key={log.id}
                      className="border-l-4 border-green-500 bg-green-50 p-3 rounded-r-lg"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-semibold text-green-800">
                            Hospital Registration
                          </span>
                          <p className="font-medium">{log.name}</p>
                          <p className="text-sm text-gray-600">
                            {log.details?.email} • {log.details?.city}
                          </p>
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}

                {(logFilter === "all" || logFilter === "donors") &&
                  donorLogs.map((log) => (
                    <div
                      key={log.id}
                      className="border-l-4 border-purple-500 bg-purple-50 p-3 rounded-r-lg"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-semibold text-purple-800">
                            Donor Registration
                          </span>
                          <p className="font-medium">{log.name}</p>
                          <p className="text-sm text-gray-600">
                            Blood Type: {log.details?.blood_type} •{" "}
                            {log.details?.city}
                          </p>
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}

                {auditLogs.length === 0 &&
                  hospitalLogs.length === 0 &&
                  donorLogs.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No logs found
                    </div>
                  )}
              </div>
            )}
          </Card>
        )}
      </div>

      {/* Broadcast Modal */}
      {showBroadcast && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Send Broadcast Message</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Send to
              </label>
              <select
                className="w-full px-3 py-2 border rounded-lg"
                value={broadcastType}
                onChange={(e) => setBroadcastType(e.target.value)}
              >
                <option value="donors">All Donors</option>
                <option value="hospitals">All Hospitals</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <textarea
                className="w-full px-3 py-2 border rounded-lg"
                rows={4}
                value={broadcastMessage}
                onChange={(e) => setBroadcastMessage(e.target.value)}
                placeholder="Enter your message here..."
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={sendBroadcast} loading={sending}>
                Send Broadcast
              </Button>
              <Button
                variant="secondary"
                onClick={() => setShowBroadcast(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}