/**
 * WanderIQ — JavaScript Controller
 * Matching Reference UI Design with Leaflet OpenStreetMap & FastAPI Backend
 */

// AI Travel Planner backend runs on port 8001 (see start-backend.ps1)
const API_BASE = window.location.origin.includes(":8001")
    ? window.location.origin
    : "http://127.0.0.1:8001";

// Global State
let mapInstance = null;
let mapTileLayer = null;
let markersGroup = null;
let polylineLayer = null;
let placeMarkersMap = {};
let currentTravelPlan = null;
let currentSelectedDay = 1;

// DOM Elements
const travelForm = document.getElementById("travelForm");
const submitBtn = document.getElementById("submitBtn");
const destinationInput = document.getElementById("destination");
const daysInput = document.getElementById("days");
const travelersInput = document.getElementById("travelers");
const budgetInput = document.getElementById("budget");
const interestsInput = document.getElementById("interestsInput");

const loadingSection = document.getElementById("loadingSection");
const loadingBarFill = document.getElementById("loadingBarFill");
const resultsWorkspace = document.getElementById("resultsWorkspace");

const dashDestTitle = document.getElementById("dashDestTitle");
const dashDestStats = document.getElementById("dashDestStats");
const dashDestSummary = document.getElementById("dashDestSummary");
const dashDayPills = document.getElementById("dashDayPills");
const dashPlaceCardsList = document.getElementById("dashPlaceCardsList");
const dashTipsList = document.getElementById("dashTipsList");
const dashCopyBtn = document.getElementById("dashCopyBtn");

const btnMapLayer = document.getElementById("btnMapLayer");
const btnSatelliteLayer = document.getElementById("btnSatelliteLayer");

const navMyTripsBtn = document.getElementById("navMyTripsBtn");
const sbMyTrips = document.getElementById("sbMyTrips");
const historyModal = document.getElementById("historyModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const savedTripsList = document.getElementById("savedTripsList");
const quickPlanBtn = document.getElementById("quickPlanBtn");
const toastEl = document.getElementById("toast");

// --------------------------------------------------
// Initialization
// --------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    initMap();
    loadDefaultInitialView();
});

function initEvents() {
    travelForm.addEventListener("submit", handleFormSubmit);
    
    if (quickPlanBtn) {
        quickPlanBtn.addEventListener("click", () => {
            document.getElementById("heroSection").scrollIntoView({ behavior: "smooth" });
            destinationInput.focus();
        });
    }

    if (dashCopyBtn) {
        dashCopyBtn.addEventListener("click", handleCopyPlan);
    }

    // Modal Events
    if (navMyTripsBtn) navMyTripsBtn.addEventListener("click", openHistoryModal);
    if (sbMyTrips) sbMyTrips.addEventListener("click", openHistoryModal);
    if (closeModalBtn) closeModalBtn.addEventListener("click", closeHistoryModal);
    if (historyModal) {
        historyModal.addEventListener("click", (e) => {
            if (e.target === historyModal) closeHistoryModal();
        });
    }

    // Map Tile Switcher
    if (btnMapLayer && btnSatelliteLayer) {
        btnMapLayer.addEventListener("click", () => switchMapLayer("streets"));
        btnSatelliteLayer.addEventListener("click", () => switchMapLayer("satellite"));
    }
}

// --------------------------------------------------
// Default Reference Initial Data
// --------------------------------------------------
function loadDefaultInitialView() {
    // Initial display matching Kanyakumari reference from image
    const demoPlan = {
        destination: "Kanyakumari, Tamil Nadu",
        days_count: 3,
        travelers: 2,
        budget: 10000,
        summary: "Explore the southern tip of India with stunning beaches, historic landmarks, and local flavors.",
        days: [
            {
                day: 1,
                places: [
                    {
                        name: "Vivekananda Rock Memorial",
                        type: "Historic Landmark",
                        best_time: "09:00 AM – 11:00 AM",
                        duration: "2 hrs",
                        location_verified: true,
                        latitude: 8.07832,
                        longitude: 77.554956,
                        image: "https://images.unsplash.com/photo-1596178065887-1198b6148b2b?auto=format&fit=crop&w=400&q=80"
                    },
                    {
                        name: "Thiruvalluvar Statue",
                        type: "Viewpoint & Monument",
                        best_time: "11:30 AM – 12:30 PM",
                        duration: "1 hr",
                        location_verified: true,
                        latitude: 8.077753,
                        longitude: 77.553995,
                        image: "https://images.unsplash.com/photo-1609137144827-024ef130f146?auto=format&fit=crop&w=400&q=80"
                    },
                    {
                        name: "Kanyakumari Beach",
                        type: "Beach & Triveni Sangam",
                        best_time: "04:00 PM – 06:00 PM",
                        duration: "2 hrs",
                        location_verified: true,
                        latitude: 8.077813,
                        longitude: 77.555798,
                        image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80"
                    },
                    {
                        name: "Sunset Point",
                        type: "Viewpoint",
                        best_time: "06:15 PM – 07:00 PM",
                        duration: "45 mins",
                        location_verified: true,
                        latitude: 8.0825,
                        longitude: 77.5385,
                        image: "https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=400&q=80"
                    }
                ]
            },
            {
                day: 2,
                places: [
                    {
                        name: "Padmanabhapuram Palace",
                        type: "Historic Palace",
                        best_time: "10:00 AM – 01:00 PM",
                        duration: "3 hrs",
                        location_verified: true,
                        latitude: 8.250661,
                        longitude: 77.327101,
                        image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=400&q=80"
                    },
                    {
                        name: "Suchindram Thanumalayan Temple",
                        type: "Spiritual Heritage",
                        best_time: "03:30 PM – 05:30 PM",
                        duration: "2 hrs",
                        location_verified: true,
                        latitude: 8.150974,
                        longitude: 77.471732,
                        image: "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=400&q=80"
                    }
                ]
            },
            {
                day: 3,
                places: [
                    {
                        name: "Gandhi Memorial Mandapam",
                        type: "Memorial & Architecture",
                        best_time: "09:30 AM – 11:00 AM",
                        duration: "1.5 hrs",
                        location_verified: true,
                        latitude: 8.078744,
                        longitude: 77.549953,
                        image: "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=400&q=80"
                    },
                    {
                        name: "Vattakottai Fort",
                        type: "Coastal Fort",
                        best_time: "03:00 PM – 05:30 PM",
                        duration: "2.5 hrs",
                        location_verified: true,
                        latitude: 8.1245,
                        longitude: 77.5645,
                        image: "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=400&q=80"
                    }
                ]
            }
        ],
        travel_tips: [
            "Carry light cotton clothes and stay hydrated.",
            "Best time to visit is October to March."
        ]
    };

    currentTravelPlan = demoPlan;
    renderDashboard(demoPlan);
}

// --------------------------------------------------
// Form Submission Flow
// --------------------------------------------------
async function handleFormSubmit(event) {
    event.preventDefault();

    const destination = destinationInput.value.trim();
    const days = parseInt(daysInput.value, 10);
    const budget = parseFloat(budgetInput.value);
    const travelers = parseInt(travelersInput.value, 10);
    const interests = interestsInput.value.split(",").map(s => s.trim()).filter(Boolean);

    if (!destination) {
        showToast("Please enter a destination city or region.", "error");
        return;
    }

    setLoadingState(true);
    const stepInterval = runStepAnimation();

    try {
        const response = await fetch(`${API_BASE}/api/travel/plan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                destination,
                days,
                budget,
                travelers,
                interests,
            }),
        });

        clearInterval(stepInterval);
        completeStepAnimation();

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error: ${response.status}`);
        }

        const resData = await response.json();
        if (!resData.success || !resData.data) {
            throw new Error("Failed to parse travel plan.");
        }

        currentTravelPlan = {
            ...resData.data,
            days_count: days,
            travelers: travelers,
            budget: budget,
        };

        setTimeout(() => {
            setLoadingState(false);
            renderDashboard(currentTravelPlan);
            resultsWorkspace.scrollIntoView({ behavior: "smooth" });
            showToast(`Generated verified itinerary for ${destination}! ✨`, "success");
        }, 500);

    } catch (error) {
        clearInterval(stepInterval);
        setLoadingState(false);
        showToast(error.message || "Could not generate plan. Please try again.", "error");
    }
}

// --------------------------------------------------
// Step-by-step Loading Animation
// --------------------------------------------------
function runStepAnimation() {
    const steps = [
        document.getElementById("lStep-1"),
        document.getElementById("lStep-2"),
        document.getElementById("lStep-3"),
        document.getElementById("lStep-4"),
        document.getElementById("lStep-5"),
    ];

    steps.forEach(s => {
        s.className = "";
        s.querySelector("span").textContent = "○";
    });

    let current = 0;
    if (steps[0]) {
        steps[0].className = "active";
        steps[0].querySelector("span").textContent = "●";
    }

    loadingBarFill.style.width = "20%";

    return setInterval(() => {
        if (current < steps.length - 1) {
            steps[current].className = "completed";
            steps[current].querySelector("span").textContent = "✓";
            current++;
            steps[current].className = "active";
            steps[current].querySelector("span").textContent = "●";
            loadingBarFill.style.width = `${((current + 1) / steps.length) * 100}%`;
        }
    }, 1800);
}

function completeStepAnimation() {
    loadingBarFill.style.width = "100%";
    document.querySelectorAll(".loading-status-list li").forEach(li => {
        li.className = "completed";
        li.querySelector("span").textContent = "✓";
    });
}

function setLoadingState(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        loadingSection.classList.remove("hidden");
        loadingSection.scrollIntoView({ behavior: "smooth" });
    } else {
        submitBtn.disabled = false;
        loadingSection.classList.add("hidden");
    }
}

// --------------------------------------------------
// Render Dashboard Workspace
// --------------------------------------------------
function renderDashboard(plan) {
    // Header Meta
    dashDestTitle.innerHTML = `${escapeHtml(plan.destination)} <span class="dest-pin-icon">📍</span>`;
    
    const daysCount = plan.days_count || (plan.days ? plan.days.length : 3);
    const travelersCount = plan.travelers || 2;
    const budgetVal = plan.budget ? plan.budget.toLocaleString("en-IN") : "10,000";

    dashDestStats.innerHTML = `<span>${daysCount} Days Trip</span> • <span>${travelersCount} Travelers</span> • <span>₹${budgetVal} Budget</span>`;
    dashDestSummary.textContent = plan.summary || "Explore top verified sightseeing spots.";

    // Render Day Tabs
    renderDayPills(plan.days || []);

    // Select Day 1 by default
    currentSelectedDay = 1;
    renderDayPlaces(plan.days || [], 1);

    // Render Tips
    renderTips(plan.travel_tips || []);

    // Update Map with all verified locations
    updateMapLocations(plan.days || []);
}

function renderDayPills(days) {
    dashDayPills.innerHTML = "";
    
    days.forEach((d, idx) => {
        const pill = document.createElement("button");
        pill.type = "button";
        pill.className = `day-pill ${d.day === currentSelectedDay ? "active" : ""}`;
        pill.textContent = `Day ${d.day}`;
        pill.addEventListener("click", () => {
            document.querySelectorAll(".day-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentSelectedDay = d.day;
            renderDayPlaces(days, d.day);
        });
        dashDayPills.appendChild(pill);
    });
}

function renderDayPlaces(days, selectedDay) {
    dashPlaceCardsList.innerHTML = "";
    const dayObj = days.find(d => d.day === selectedDay) || days[0];

    if (!dayObj || !dayObj.places || dayObj.places.length === 0) {
        dashPlaceCardsList.innerHTML = `<p class="empty-msg">No scheduled places for this day.</p>`;
        return;
    }

    dayObj.places.forEach((p, idx) => {
        const card = document.createElement("div");
        card.className = "place-item-card";

        const isVerified = p.location_verified && p.latitude && p.longitude;
        const verifiedTagHtml = isVerified 
            ? `<span class="tag-verified">Verified</span>` 
            : `<span class="tag-verified" style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; border-color: #64748b;">Unverified</span>`;

        const timeStr = p.best_time || "09:00 AM – 11:00 AM";
        const durationStr = p.duration || (p.estimated_duration_hours ? `${p.estimated_duration_hours} hrs` : "2 hrs");
        const categoryStr = p.type || p.activity || "Sightseeing Landmark";
        const imgSrc = p.image || "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80";

        card.innerHTML = `
            <div class="place-card-left">
                <img src="${escapeAttr(imgSrc)}" alt="${escapeAttr(p.name)}" class="place-thumbnail" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=400&q=80'">
                <div class="place-text-info">
                    <div class="place-name-row">
                        <h4 class="place-title">${escapeHtml(p.name)}</h4>
                        ${verifiedTagHtml}
                    </div>
                    <span class="place-category">${escapeHtml(categoryStr)}</span>
                    <span class="place-time-duration">${escapeHtml(timeStr)} • ${escapeHtml(durationStr)}</span>
                </div>
            </div>
            <span class="place-card-chevron">›</span>
        `;

        // Clicking card flies to map location
        card.addEventListener("click", () => {
            if (isVerified && mapInstance) {
                mapInstance.flyTo([p.latitude, p.longitude], 15, { animate: true, duration: 1.2 });
                const marker = placeMarkersMap[p.name];
                if (marker) {
                    setTimeout(() => marker.openPopup(), 1200);
                }
            }
        });

        dashPlaceCardsList.appendChild(card);
    });
}

function renderTips(tips) {
    dashTipsList.innerHTML = "";
    if (tips.length === 0) {
        tips = [
            "Carry light cotton clothes and stay hydrated.",
            "Best time to visit is October to March."
        ];
    }
    tips.forEach(t => {
        const li = document.createElement("li");
        li.textContent = t;
        dashTipsList.appendChild(li);
    });
}

// --------------------------------------------------
// Leaflet OpenStreetMap Controller
// --------------------------------------------------
function initMap() {
    if (mapInstance) return;

    mapInstance = L.map("dashboardMap", {
        scrollWheelZoom: false,
    }).setView([8.0781, 77.5553], 13); // Kanyakumari default

    mapTileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(mapInstance);

    markersGroup = L.featureGroup().addTo(mapInstance);
    polylineLayer = L.layerGroup().addTo(mapInstance);
}

function switchMapLayer(type) {
    if (!mapInstance) return;
    
    if (type === "satellite") {
        btnSatelliteLayer.classList.add("active");
        btnMapLayer.classList.remove("active");
        mapTileLayer.setUrl("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}");
    } else {
        btnMapLayer.classList.add("active");
        btnSatelliteLayer.classList.remove("active");
        mapTileLayer.setUrl("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");
    }
}

function updateMapLocations(days) {
    if (!mapInstance || !markersGroup) return;

    markersGroup.clearLayers();
    polylineLayer.clearLayers();
    placeMarkersMap = {};

    const allVerified = [];

    days.forEach(d => {
        (d.places || []).forEach(p => {
            if (p.location_verified && p.latitude && p.longitude) {
                allVerified.push({
                    name: p.name,
                    lat: p.latitude,
                    lon: p.longitude,
                    type: p.type || "Attraction",
                    day: d.day,
                });
            }
        });
    });

    if (allVerified.length === 0) return;

    const latlngs = [];

    allVerified.forEach((place) => {
        const latlng = [place.lat, place.lon];
        latlngs.push(latlng);

        // Custom Emerald Marker Icon
        const customIcon = L.divIcon({
            className: "custom-map-pin",
            html: `
                <div style="
                    background: #10B981;
                    width: 28px;
                    height: 28px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    border: 2.5px solid #ffffff;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <span style="transform: rotate(45deg); color: white; font-size: 11px; font-weight: 800;">📍</span>
                </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 28],
            popupAnchor: [0, -28],
        });

        const marker = L.marker(latlng, { icon: customIcon });

        const popupContent = `
            <div style="font-family: 'Poppins', sans-serif; padding: 4px;">
                <span style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase;">Day ${place.day} • Verified</span>
                <h4 style="margin: 2px 0 4px; font-size: 13px; font-weight: 600; color: #f8fafc;">${escapeHtml(place.name)}</h4>
                <p style="margin: 0; font-size: 11px; color: #94a3b8;">${escapeHtml(place.type)}</p>
            </div>
        `;

        marker.bindPopup(popupContent);
        markersGroup.addLayer(marker);
        placeMarkersMap[place.name] = marker;
    });

    // Draw connecting route line
    if (latlngs.length > 1) {
        const polyline = L.polyline(latlngs, {
            color: "#2563EB",
            weight: 3,
            opacity: 0.8,
            dashArray: "5, 8",
        });
        polylineLayer.addLayer(polyline);
    }

    // Auto-fit bounds
    mapInstance.fitBounds(markersGroup.getBounds(), {
        padding: [40, 40],
        maxZoom: 14,
    });

    setTimeout(() => mapInstance.invalidateSize(), 300);
}

// --------------------------------------------------
// My Trips (History Modal)
// --------------------------------------------------
async function openHistoryModal() {
    historyModal.classList.remove("hidden");
    savedTripsList.innerHTML = `<p class="empty-msg">Loading saved itineraries...</p>`;

    try {
        const response = await fetch(`${API_BASE}/api/travel/history`);
        if (!response.ok) throw new Error("Could not load history.");

        const resData = await response.json();
        const trips = resData.data || [];

        if (trips.length === 0) {
            savedTripsList.innerHTML = `<p class="empty-msg">No saved trips found yet. Start by generating a plan!</p>`;
            return;
        }

        savedTripsList.innerHTML = trips.map(t => {
            const dateStr = t.created_at ? new Date(t.created_at).toLocaleDateString() : "";
            return `
                <div class="saved-trip-card" id="saved-trip-${t.id}">
                    <div>
                        <div class="trip-card-dest">📍 ${escapeHtml(t.destination)}</div>
                        <div class="trip-card-meta">${t.days} Days • ${t.travelers} Travelers • ₹${(t.budget || 0).toLocaleString("en-IN")} ${dateStr ? `• ${dateStr}` : ""}</div>
                    </div>
                    <div class="trip-card-btns">
                        <button class="btn-trip-view" onclick="loadSavedTripById(${t.id})">Open</button>
                        <button class="btn-trip-del" onclick="deleteSavedTripById(${t.id})">Delete</button>
                    </div>
                </div>
            `;
        }).join("");

    } catch (error) {
        savedTripsList.innerHTML = `<p class="empty-msg" style="color: #ef4444;">${escapeHtml(error.message)}</p>`;
    }
}

function closeHistoryModal() {
    historyModal.classList.add("hidden");
}

window.loadSavedTripById = async function(id) {
    try {
        const response = await fetch(`${API_BASE}/api/travel/${id}`);
        if (!response.ok) throw new Error("Failed to load plan.");

        const resData = await response.json();
        const trip = resData.data;

        closeHistoryModal();

        currentTravelPlan = {
            id: trip.id,
            destination: trip.destination,
            summary: trip.summary,
            days: trip.days_plan || [],
            travel_tips: trip.travel_tips || [],
            budget: trip.budget,
            travelers: trip.travelers,
            days_count: trip.days,
        };

        renderDashboard(currentTravelPlan);
        resultsWorkspace.scrollIntoView({ behavior: "smooth" });
        showToast(`Loaded ${trip.destination}! ✨`, "success");
    } catch (e) {
        showToast(e.message, "error");
    }
};

window.deleteSavedTripById = async function(id) {
    if (!confirm("Delete this saved travel plan?")) return;
    try {
        const res = await fetch(`${API_BASE}/api/travel/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Delete failed.");
        const el = document.getElementById(`saved-trip-${id}`);
        if (el) el.remove();
        showToast("Trip removed.", "info");
    } catch (e) {
        showToast(e.message, "error");
    }
};

// --------------------------------------------------
// Utility Functions
// --------------------------------------------------
function handleCopyPlan() {
    if (!currentTravelPlan) return;
    let text = `✈️ WanderIQ Itinerary: ${currentTravelPlan.destination}\n`;
    text += `Summary: ${currentTravelPlan.summary}\n\n`;

    (currentTravelPlan.days || []).forEach(d => {
        text += `🗓️ Day ${d.day}:\n`;
        (d.places || []).forEach(p => {
            text += `  • ${p.name} (${p.best_time || ""}) - ${p.activity || p.type || ""}\n`;
        });
        text += `\n`;
    });

    navigator.clipboard.writeText(text).then(() => {
        showToast("📋 Itinerary copied to clipboard!", "success");
    }).catch(() => {
        showToast("Failed to copy text.", "error");
    });
}

function showToast(msg, type = "info") {
    toastEl.textContent = msg;
    toastEl.className = `toast-notification ${type}`;
    toastEl.classList.remove("hidden");
    setTimeout(() => toastEl.classList.add("hidden"), 4000);
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function escapeAttr(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}