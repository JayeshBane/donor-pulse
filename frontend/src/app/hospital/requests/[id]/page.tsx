// donorpulse-frontend\src\app\hospital\requests\[id]\page.tsx
"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useParams, useRouter } from "next/navigation";
import {
  Droplet,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  ArrowLeft,
  RefreshCw,
  Map,
} from "lucide-react";
import dynamic from "next/dynamic";
import apiClient from "@/lib/api-client";

const GoogleDonorsMap = dynamic(() => import("@/components/GoogleDonorsMap"), {
  ssr: false,
  loading: () => (
    <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p className="ml-2 text-gray-500">Loading map...</p>
    </div>
  ),
});

interface MatchedDonor {
  donor_id?: string;
  donor_name: string;
  donor_blood_type: string;
  distance_km?: number;
  status: string;
  eta_minutes?: number;
  live_lat?: number;
  live_lng?: number;
  profile_lat?: number;
  profile_lng?: number;
}

interface RequestDetails {
  id: string;
  blood_type: string;
  quantity_units: number;
  urgency: string;
  status: string;
  created_at: string;
  expires_at: string;
  hospital_id?: string;
  hospital_name?: string;
  statistics?: {
    donors_contacted: number;
    donors_accepted: number;
    donors_declined: number;
    donors_timeout: number;
  };
  matched_donors?: MatchedDonor[];
}

type UrgencyColorKey = "routine" | "urgent" | "critical" | "sos";

export default function RequestDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = params.id as string;
  const [request, setRequest] = useState<RequestDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hospitalLocation, setHospitalLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [mapDonors, setMapDonors] = useState<any[]>([]);

  useEffect(() => {
    if (requestId) {
      fetchRequest();
      fetchHospitalLocation();
    }
  }, [requestId]);

  const fetchRequest = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use apiClient instead of axios with API_BASE_URL
      const response = await apiClient.get(`/requests/${requestId}`);
      setRequest(response.data);

      // Process donors for map
      await processDonorsForMap(response.data.matched_donors || []);
    } catch (error: any) {
      console.error("Failed to fetch request", error);
      if (error.response?.status === 404) {
        setError("Request not found. It may have been deleted or expired.");
      } else {
        setError(
          error.response?.data?.detail || "Failed to load request details",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const processDonorsForMap = async (donors: MatchedDonor[]) => {
    const mapDonorsList = [];

    for (const donor of donors) {
      let lat = donor.live_lat || donor.profile_lat;
      let lng = donor.live_lng || donor.profile_lng;
      let distance = donor.distance_km;
      let eta = donor.eta_minutes;

      // If no location in matched_donor, fetch from donor profile
      if (!lat || !lng) {
        try {
          // Use apiClient instead of axios with API_BASE_URL
          const donorsRes = await apiClient.get(`/donors/`, {
            params: { search: donor.donor_name }
          });

          if (donorsRes.data.donors && donorsRes.data.donors.length > 0) {
            const donorData = donorsRes.data.donors[0];
            lat = donorData.location?.lat;
            lng = donorData.location?.lng;

            // Calculate route using backend API for accepted donors only
            if (lat && lng && hospitalLocation && donor.status === "accepted") {
              try {
                // Use apiClient instead of axios with API_BASE_URL
                const routeRes = await apiClient.get(`/location/route/${donorData._id}/${requestId}`);
                distance = routeRes.data.distance_km;
                eta = routeRes.data.eta_minutes;
              } catch (err) {
                console.error(
                  `Failed to get route for ${donor.donor_name}`,
                  err,
                );
              }
            }
          }
        } catch (err) {
          console.error(
            `Failed to fetch location for ${donor.donor_name}`,
            err,
          );
        }
      }

      if (lat && lng) {
        mapDonorsList.push({
          id: donor.donor_id || donor.donor_name,
          name: donor.donor_name,
          lat: lat,
          lng: lng,
          distance: distance,
          eta: eta,
          status: donor.status,
        });
      }
    }

    setMapDonors(mapDonorsList);
  };

  const fetchHospitalLocation = async () => {
    try {
      const hospitalData = localStorage.getItem("hospital");

      if (hospitalData) {
        const hospital = JSON.parse(hospitalData);
        // Use apiClient instead of axios with API_BASE_URL
        const response = await apiClient.get(`/hospitals/${hospital.id}`);

        // Check nested location object
        const hospitalLat = response.data.location?.lat || response.data.lat;
        const hospitalLng = response.data.location?.lng || response.data.lng;

        if (hospitalLat && hospitalLng) {
          setHospitalLocation({ lat: hospitalLat, lng: hospitalLng });
          console.log("Hospital location loaded:", hospitalLat, hospitalLng);
        } else {
          console.log("No hospital location found, using default");
          // Default to Philadelphia for testing
          setHospitalLocation({ lat: 39.9526, lng: -75.1652 });
        }
      }
    } catch (error) {
      console.error("Failed to fetch hospital location", error);
      // Default location
      setHospitalLocation({ lat: 39.9526, lng: -75.1652 });
    }
  };

  const cancelRequest = async () => {
    if (!confirm("Are you sure you want to cancel this request?")) return;

    try {
      // Use apiClient instead of axios with API_BASE_URL
      await apiClient.patch(`/requests/${requestId}/cancel`, {});
      alert("Request cancelled");
      router.push("/hospital/dashboard");
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to cancel request");
    }
  };

  const getUrgencyColor = (urgency: string): string => {
    const colors: Record<UrgencyColorKey, string> = {
      routine: "bg-blue-100 text-blue-800",
      urgent: "bg-yellow-100 text-yellow-800",
      critical: "bg-orange-100 text-orange-800",
      sos: "bg-red-100 text-red-800",
    };
    return colors[urgency as UrgencyColorKey] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading request details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <div className="text-center py-12">
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Unable to Load Request
            </h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => router.push("/hospital/dashboard")}>
                Go to Dashboard
              </Button>
              <Button variant="secondary" onClick={fetchRequest}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">Request not found</p>
            <Button onClick={() => router.push("/hospital/dashboard")}>
              Go to Dashboard
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const hasMapDonors = mapDonors.length > 0 && hospitalLocation;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - Request Details */}
        <div className="lg:col-span-2">
          <Card>
            <div className="mb-6">
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-2xl font-bold">Blood Request Details</h1>
                  <p className="text-gray-500 mt-1">ID: {request.id}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${getUrgencyColor(request.urgency)}`}
                >
                  {request.urgency}
                </span>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Droplet className="h-5 w-5 text-red-500" />
                  <div>
                    <p className="text-sm text-gray-500">Blood Type Needed</p>
                    <p className="text-2xl font-bold">{request.blood_type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="text-sm text-gray-500">Quantity Needed</p>
                    <p className="text-2xl font-bold">
                      {request.quantity_units} unit(s)
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-yellow-500" />
                  <div>
                    <p className="text-sm text-gray-500">Created</p>
                    <p>{new Date(request.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-red-500" />
                  <div>
                    <p className="text-sm text-gray-500">Expires</p>
                    <p>{new Date(request.expires_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t pt-6 mb-6">
              <h2 className="text-lg font-semibold mb-4">Statistics</h2>
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">
                    {request.statistics?.donors_contacted || 0}
                  </p>
                  <p className="text-sm text-gray-500">Contacted</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">
                    {request.statistics?.donors_accepted || 0}
                  </p>
                  <p className="text-sm text-gray-500">Accepted</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">
                    {request.statistics?.donors_declined || 0}
                  </p>
                  <p className="text-sm text-gray-500">Declined</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-600">
                    {request.statistics?.donors_timeout || 0}
                  </p>
                  <p className="text-sm text-gray-500">Timeout</p>
                </div>
              </div>
            </div>

            {request.matched_donors && request.matched_donors.length > 0 && (
              <div className="border-t pt-6">
                <h2 className="text-lg font-semibold mb-4">
                  Responding Donors ({request.matched_donors.length})
                </h2>
                <div className="space-y-3">
                  {request.matched_donors.map((donor, index) => (
                    <div
                      key={index}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{donor.donor_name}</p>
                        <p className="text-sm text-gray-500">
                          Blood Type: {donor.donor_blood_type}
                        </p>
                        {donor.distance_km && (
                          <p className="text-xs text-gray-400">
                            {donor.distance_km} km away
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <span
                          className={`px-2 py-1 rounded-full text-xs ${
                            donor.status === "accepted"
                              ? "bg-green-100 text-green-800"
                              : donor.status === "declined"
                                ? "bg-red-100 text-red-800"
                                : donor.status === "arrived"
                                  ? "bg-purple-100 text-purple-800"
                                  : donor.status === "donated"
                                    ? "bg-blue-100 text-blue-800"
                                    : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {donor.status}
                        </span>
                        {donor.eta_minutes && (
                          <p className="text-xs text-gray-500 mt-1">
                            ETA: {donor.eta_minutes} min
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {request.status !== "fulfilled" &&
              request.status !== "cancelled" &&
              request.status !== "expired" && (
                <div className="border-t pt-6 mt-6">
                  <Button
                    variant="danger"
                    onClick={cancelRequest}
                    className="w-full"
                  >
                    Cancel Request
                  </Button>
                </div>
              )}

            {request.status === "fulfilled" && (
              <div className="mt-6 p-4 bg-green-50 rounded-lg text-center">
                <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <p className="text-green-800 font-semibold">
                  Request Fulfilled!
                </p>
                <p className="text-green-600 text-sm">
                  All required donors have been confirmed.
                </p>
              </div>
            )}

            {request.status === "expired" && (
              <div className="mt-6 p-4 bg-red-50 rounded-lg text-center">
                <XCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                <p className="text-red-800 font-semibold">Request Expired</p>
                <p className="text-red-600 text-sm">
                  This request has expired.
                </p>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column - Map */}
        <div className="lg:col-span-1">
          <Card title="Live Donor Tracking">
            {!hospitalLocation ? (
              <div className="text-center py-12">
                <Map className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">Loading hospital location...</p>
              </div>
            ) : !hasMapDonors ? (
              <div className="text-center py-12">
                <Map className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">
                  No accepted donors with location
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {request.matched_donors?.some((d) => d.status === "accepted")
                    ? "Accepted donors need to have location in their profile"
                    : "Waiting for donors to accept the request"}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Showing</p>
                    <p className="font-semibold">
                      {mapDonors.length} donor(s) on map
                    </p>
                  </div>
                  <Map className="h-5 w-5 text-blue-500" />
                </div>

                <GoogleDonorsMap
                  donors={mapDonors}
                  hospitalLat={hospitalLocation.lat}
                  hospitalLng={hospitalLocation.lng}
                  hospitalName={request.hospital_name || "Hospital"}
                  googleMapsApiKey={
                    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ""
                  }
                />

                <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-800">
                  <p className="font-semibold">📍 Map Legend</p>
                  <p>🔵 Blue marker: Donor location</p>
                  <p>🔴 Red marker: Hospital location</p>
                  <p>🟢 Green line: Light traffic</p>
                  <p>🟠 Orange line: Moderate traffic</p>
                  <p>🔴 Red line: Heavy traffic</p>
                  <p>Click on markers for route details & weather</p>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}