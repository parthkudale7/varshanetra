/* =====================================================
   VARSHANETRA
   Pune Flood Risk MVP
   ===================================================== */


/* ================= PUNE LOCATION ================= */

const PUNE = {
    lat: 18.5204,
    lng: 73.8567
};


/* ================= PUNE ROADS ================= */

const puneRoads = [
    "Sinhagad Road",
    "Mundhwa Road",
    "Yerwada Low-Lying Area",
    "Kharadi Road",
    "Sangamwadi",
    "Pashan Road"
];


/* ================= SAFE ROUTES ================= */

const safeRoutes = {

    low:
        "Normal movement is recommended. Prefer major arterial roads and continue monitoring rainfall.",

    moderate:
        "Use major arterial roads and avoid low-lying areas near rivers, underpasses and drainage channels.",

    high:
        "Reroute through major elevated/arterial roads. Avoid Sinhagad Road, Mundhwa Road and other waterlogging-prone sections.",

    critical:
        "AVOID FLOODED ROADS. Use elevated arterial roads and follow emergency traffic instructions. Do not enter waterlogged underpasses."
};


/* ================= MAP ================= */

let map;
let riskCircle;
let puneMarker;


/* ================= INITIALIZE ================= */

document.addEventListener("DOMContentLoaded", function () {

    initializeMap();

    document
        .getElementById("runButton")
        .addEventListener("click", calculateRisk);

    document
        .getElementById("demoButton")
        .addEventListener("click", loadDemo);

    document
        .getElementById("resetButton")
        .addEventListener("click", resetDashboard);

});


/* ================= MAP INITIALIZATION ================= */

function initializeMap() {

    map = L.map("map").setView(
        [PUNE.lat, PUNE.lng],
        12
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);


    puneMarker = L.marker(
        [PUNE.lat, PUNE.lng]
    ).addTo(map);


    puneMarker.bindPopup(
        "<b>📍 Pune</b><br>VARSHANETRA Monitoring Area"
    );

}


/* =====================================================
   MAIN RISK CALCULATION
   ===================================================== */

function calculateRisk() {

    /* -------- GET INPUTS -------- */

    const rainfall =
        Number(
            document.getElementById("rainfall").value
        );

    const previousRain =
        Number(
            document.getElementById("previousRain").value
        );

    const humidity =
        Number(
            document.getElementById("humidity").value
        );

    const waterLevel =
        Number(
            document.getElementById("waterLevel").value
        );

    const drainage =
        document.getElementById("drainage").value;


    /* -------- VALIDATION -------- */

    if (
        rainfall === "" ||
        previousRain === "" ||
        humidity === "" ||
        waterLevel === ""
    ) {

        alert(
            "Please enter all weather and water values."
        );

        return;
    }


    if (
        humidity < 0 ||
        humidity > 100
    ) {

        alert(
            "Humidity must be between 0 and 100%."
        );

        return;
    }


    /* =================================================
       MVP RISK ENGINE

       Rainfall       = 40%
       Previous rain  = 20%
       Water level    = 30%
       Humidity       = 10%
       Drainage       = additional factor
       ================================================= */


    let score = 0;


    /* Current rainfall */

    score += Math.min(
        rainfall / 180 * 40,
        40
    );


    /* Previous rainfall */

    score += Math.min(
        previousRain / 150 * 20,
        20
    );


    /* Water level */

    score += Math.min(
        waterLevel / 5 * 30,
        30
    );


    /* Humidity */

    score += humidity / 100 * 10;


    /* Drainage */

    if (drainage === "blocked") {
        score += 5;
    }

    if (drainage === "severe") {
        score += 10;
    }


    /* Keep between 0 and 100 */

    let probability =
        Math.round(
            Math.min(
                Math.max(score, 0),
                100
            )
        );


    /* =================================================
       DETERMINE RISK
       ================================================= */

    let risk;

    if (probability >= 70) {

        risk = "critical";

    } else if (probability >= 50) {

        risk = "high";

    } else if (probability >= 30) {

        risk = "moderate";

    } else {

        risk = "low";

    }


    /* =================================================
       UPDATE DASHBOARD
       ================================================= */

    updateRisk(
        probability,
        risk
    );


    updateAlert(
        probability,
        risk
    );


    updateTraffic(
        risk
    );


    updateAI(
        rainfall,
        previousRain,
        humidity,
        waterLevel,
        probability
    );


    updateMap(
        probability,
        risk
    );


    updateRoads(
        risk
    );


    /* Map status */

    document.getElementById(
        "mapStatus"
    ).textContent =
        risk.toUpperCase();


    /* Scroll to result */

    document.getElementById(
        "riskCard"
    ).scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =====================================================
   UPDATE RISK CARD
   ===================================================== */

function updateRisk(
    probability,
    risk
) {

    const badge =
        document.getElementById("riskBadge");

    const title =
        document.getElementById("riskTitle");

    const message =
        document.getElementById("riskMessage");

    const probabilityText =
        document.getElementById("probability");

    const progress =
        document.getElementById("riskProgress");

    const circle =
        document.querySelector(".risk-circle");


    probabilityText.textContent =
        probability + "%";


    progress.style.width =
        probability + "%";


    /* Reset classes */

    badge.className =
        "badge";

    title.className = "";

    probabilityText.className = "";

    circle.style.background =
        "conic-gradient(#9ca8af 0deg, #e9edef 0deg)";


    /* LOW */

    if (risk === "low") {

        badge.textContent =
            "🟢 LOW";

        badge.style.background =
            "#e8f7ee";

        badge.style.color =
            "#208c54";

        title.textContent =
            "Low Flood Risk";

        title.className =
            "low";

        message.textContent =
            "Current conditions indicate a low probability of flooding. Continue monitoring rainfall.";

        progress.style.background =
            "#2aaa67";

        circle.style.background =
            "conic-gradient(#2aaa67 "
            + (probability * 3.6)
            + "deg, #e9edef 0deg)";
    }


    /* MODERATE */

    if (risk === "moderate") {

        badge.textContent =
            "🟡 MODERATE";

        badge.style.background =
            "#fff7d9";

        badge.style.color =
            "#967200";

        title.textContent =
            "Moderate Flood Risk";

        title.className =
            "moderate";

        message.textContent =
            "Rainfall and water conditions are increasing. Avoid low-lying areas and monitor the situation.";

        progress.style.background =
            "#d5ad20";

        circle.style.background =
            "conic-gradient(#d5ad20 "
            + (probability * 3.6)
            + "deg, #e9edef 0deg)";
    }


    /* HIGH */

    if (risk === "high") {

        badge.textContent =
            "🟠 HIGH";

        badge.style.background =
            "#fff0e6";

        badge.style.color =
            "#c85b22";

        title.textContent =
            "High Flood Risk";

        title.className =
            "high";

        message.textContent =
            "Heavy rainfall and elevated water levels indicate a high flood probability. Traffic rerouting is recommended.";

        progress.style.background =
            "#e27432";

        circle.style.background =
            "conic-gradient(#e27432 "
            + (probability * 3.6)
            + "deg, #e9edef 0deg)";
    }


    /* CRITICAL */

    if (risk === "critical") {

        badge.textContent =
            "🔴 CRITICAL";

        badge.style.background =
            "#ffe7e7";

        badge.style.color =
            "#c83232";

        title.textContent =
            "Critical Flood Risk";

        title.className =
            "critical";

        message.textContent =
            "Critical flood conditions detected. Avoid flooded roads and follow the recommended safe route.";

        progress.style.background =
            "#d83d3d";

        circle.style.background =
            "conic-gradient(#d83d3d "
            + (probability * 3.6)
            + "deg, #e9edef 0deg)";
    }

}


/* =====================================================
   ALERT SYSTEM
   ===================================================== */

function updateAlert(
    probability,
    risk
) {

    const status =
        document.getElementById("alertStatus");

    const icon =
        document.getElementById("alertIcon");

    const title =
        document.getElementById("alertTitle");

    const message =
        document.getElementById("alertMessage");

    const time =
        document.getElementById("alertTime");


    const now =
        new Date().toLocaleTimeString();


    time.textContent =
        "Updated at " + now;


    if (risk === "low") {

        status.textContent =
            "NO ALERT";

        status.style.background =
            "#e8f7ee";

        status.style.color =
            "#208c54";

        icon.textContent =
            "✓";

        title.textContent =
            "No Active Warning";

        message.textContent =
            "Pune currently has a low predicted flood risk.";

        return;
    }


    if (risk === "moderate") {

        status.textContent =
            "WATCH";

        status.style.background =
            "#fff7d9";

        status.style.color =
            "#967200";

        icon.textContent =
            "⚠️";

        title.textContent =
            "Flood Watch";

        message.textContent =
            "Moderate flood conditions detected. Residents should remain alert.";

        return;
    }


    if (risk === "high") {

        status.textContent =
            "WARNING";

        status.style.background =
            "#fff0e6";

        status.style.color =
            "#c85b22";

        icon.textContent =
            "⚠️";

        title.textContent =
            "Flood Warning";

        message.textContent =
            "High flood probability detected in Pune. Avoid vulnerable roads and prepare for rerouting.";

        return;
    }


    if (risk === "critical") {

        status.textContent =
            "CRITICAL";

        status.style.background =
            "#ffe7e7";

        status.style.color =
            "#c83232";

        icon.textContent =
            "🚨";

        title.textContent =
            "Critical Flood Alert";

        message.textContent =
            "Critical flood probability detected. Avoid flooded areas and follow safe-route instructions.";

    }

}


/* =====================================================
   TRAFFIC REROUTING
   ===================================================== */

function updateTraffic(risk) {

    const status =
        document.getElementById("trafficStatus");

    const icon =
        document.getElementById("trafficIcon");

    const title =
        document.getElementById("trafficTitle");

    const message =
        document.getElementById("trafficMessage");

    const safeRoute =
        document.getElementById("safeRoute");


    status.className =
        "badge";


    if (risk === "low") {

        status.textContent =
            "NORMAL";

        status.style.background =
            "#e8f7ee";

        status.style.color =
            "#208c54";

        icon.textContent =
            "🟢";

        title.textContent =
            "Traffic Conditions Normal";

        message.textContent =
            "No flood-based rerouting is currently required.";

        safeRoute.textContent =
            safeRoutes.low;

    }


    else if (risk === "moderate") {

        status.textContent =
            "CAUTION";

        status.style.background =
            "#fff7d9";

        status.style.color =
            "#967200";

        icon.textContent =
            "🟡";

        title.textContent =
            "Prepare for Alternate Route";

        message.textContent =
            "Some low-lying roads may experience waterlogging. Consider an alternate route.";

        safeRoute.textContent =
            safeRoutes.moderate;

    }


    else if (risk === "high") {

        status.textContent =
            "REROUTE";

        status.style.background =
            "#fff0e6";

        status.style.color =
            "#c85b22";

        icon.textContent =
            "🟠";

        title.textContent =
            "Traffic Rerouting Recommended";

        message.textContent =
            "High flood risk detected. Avoid vulnerable roads and use the recommended safer route.";

        safeRoute.textContent =
            safeRoutes.high;

    }


    else {

        status.textContent =
            "REROUTE REQUIRED";

        status.style.background =
            "#ffe7e7";

        status.style.color =
            "#c83232";

        icon.textContent =
            "🔴";

        title.textContent =
            "Emergency Traffic Rerouting";

        message.textContent =
            "Critical flooding detected. Do NOT enter flooded roads. Rerouting is required.";

        safeRoute.textContent =
            safeRoutes.critical;

    }

}


/* =====================================================
   HIGH-RISK ROADS
   ===================================================== */

/* =====================================================
   HIGH-RISK AND SAFE ROADS
   ===================================================== */

function updateRoads(risk) {

    const container =
        document.getElementById("roads");

    const safeContainer =
        document.getElementById("safeRoads");

    const safeSection =
        document.getElementById("safeRoadsSection");

    safeSection.style.display =
        risk === "moderate" ||
        risk === "high" ||
        risk === "critical"
            ? "block"
            : "none";


    /* Clear previous roads */

    container.innerHTML = "";

    safeContainer.innerHTML = "";


    /* =================================================
       SAFE ROAD DATA
       MVP REPRESENTATION
       ================================================= */

    const safeRoads = {

        low: [
            "University Road",
            "Senapati Bapat Road",
            "Baner Road",
            "JM Road"
        ],

        moderate: [
            "University Road",
            "Senapati Bapat Road",
            "Baner Road"
        ],

        high: [
            "University Road",
            "Senapati Bapat Road"
        ],

        critical: [
            "University Road",
            "Senapati Bapat Road"
        ]

    };


    /* =================================================
       HIGH-RISK / AVOID ROADS
       ================================================= */

    if (risk === "low") {

        container.innerHTML =
            '<span class="road-placeholder">' +
            'No high-risk roads detected.' +
            '</span>';

    }

    else {

        let count;

        if (risk === "moderate") {

            count = 2;

        } else if (risk === "high") {

            count = 4;

        } else {

            count = 6;

        }


        for (
            let i = 0;
            i < count;
            i++
        ) {

            const road =
                document.createElement("span");

            road.className =
                "road";

            road.textContent =
                "🚧 " + puneRoads[i];

            container.appendChild(
                road
            );

        }

    }


    /* =================================================
       RECOMMENDED SAFE ROADS
       ================================================= */

    const selectedSafeRoads =
        safeRoads[risk];


    if (
        !selectedSafeRoads ||
        selectedSafeRoads.length === 0
    ) {

        safeContainer.innerHTML =
            '<span class="safe-road-placeholder">' +
            'No safe roads available.' +
            '</span>';

        return;

    }


    selectedSafeRoads.forEach(
        function (roadName) {

            const road =
                document.createElement("span");

            road.className =
                "safe-road";

            road.textContent =
                "🛡️ " + roadName;

            safeContainer.appendChild(
                road
            );

        }
    );

}


/* =====================================================
   AI ANALYSIS
   ===================================================== */

function updateAI(
    rainfall,
    previousRain,
    humidity,
    waterLevel,
    probability
) {

    const rainImpact =
        document.getElementById("rainImpact");

    const waterImpact =
        document.getElementById("waterImpact");

    const overallImpact =
        document.getElementById("overallImpact");

    const rainText =
        document.getElementById("rainText");

    const waterText =
        document.getElementById("waterText");


    /* Rainfall */

    if (rainfall >= 120) {

        rainImpact.textContent =
            "HIGH";

        rainText.textContent =
            "Heavy rainfall is strongly contributing to flood risk.";

    }

    else if (rainfall >= 60) {

        rainImpact.textContent =
            "MEDIUM";

        rainText.textContent =
            "Rainfall is moderately contributing to flood risk.";

    }

    else {

        rainImpact.textContent =
            "LOW";

        rainText.textContent =
            "Rainfall contribution is currently low.";

    }


    /* Water */

    if (waterLevel >= 3.5) {

        waterImpact.textContent =
            "HIGH";

        waterText.textContent =
            "Elevated water level indicates increased inundation potential.";

    }

    else if (waterLevel >= 2) {

        waterImpact.textContent =
            "MEDIUM";

        waterText.textContent =
            "Water level is increasing and should be monitored.";

    }

    else {

        waterImpact.textContent =
            "LOW";

        waterText.textContent =
            "Water level contribution is currently low.";

    }


    /* Overall */

    if (probability >= 70) {

        overallImpact.textContent =
            "CRITICAL";

    }

    else if (probability >= 50) {

        overallImpact.textContent =
            "HIGH";

    }

    else if (probability >= 30) {

        overallImpact.textContent =
            "MODERATE";

    }

    else {

        overallImpact.textContent =
            "LOW";

    }

}


/* =====================================================
   MAP UPDATE
   ===================================================== */

function updateMap(
    probability,
    risk
) {

    /* Remove previous circle */

    if (riskCircle) {

        map.removeLayer(
            riskCircle
        );

    }


    let color;


    if (risk === "low") {

        color = "#2aaa67";

    }

    else if (risk === "moderate") {

        color = "#d5ad20";

    }

    else if (risk === "high") {

        color = "#e27432";

    }

    else {

        color = "#d83d3d";

    }


    let radius =
        3000 + probability * 80;


    riskCircle =
        L.circle(
            [PUNE.lat, PUNE.lng],
            {
                radius: radius,

                color: color,

                fillColor: color,

                fillOpacity: 0.25,

                weight: 3
            }
        )
        .addTo(map);


    riskCircle.bindPopup(

        "<b>VARSHANETRA Risk Zone</b><br>" +

        "Location: Pune<br>" +

        "Flood Probability: " +

        probability +

        "%<br>" +

        "Risk Level: " +

        risk.toUpperCase()

    );


    map.setView(
        [PUNE.lat, PUNE.lng],
        12
    );

}


/* =====================================================
   DEMO DATA
   ===================================================== */

function loadDemo() {

    document.getElementById(
        "rainfall"
    ).value = 145;


    document.getElementById(
        "previousRain"
    ).value = 95;


    document.getElementById(
        "humidity"
    ).value = 88;


    document.getElementById(
        "waterLevel"
    ).value = 3.8;


    document.getElementById(
        "drainage"
    ).value = "blocked";


    alert(
        "Demo data loaded for Pune. Now press RUN RISK CALCULATION."
    );

}


/* =====================================================
   RESET
   ===================================================== */

function resetDashboard() {

    document.getElementById(
        "rainfall"
    ).value = "";

    document.getElementById(
        "previousRain"
    ).value = "";

    document.getElementById(
        "humidity"
    ).value = "";

    document.getElementById(
        "waterLevel"
    ).value = "";

    document.getElementById(
        "drainage"
    ).value = "normal";


    document.getElementById(
        "probability"
    ).textContent = "--%";


    document.getElementById(
        "riskBadge"
    ).textContent = "WAITING";


    document.getElementById(
        "riskTitle"
    ).textContent =
        "Waiting for analysis";


    document.getElementById(
        "riskMessage"
    ).textContent =
        "Enter weather data and press RUN to calculate flood risk.";


    document.getElementById(
        "riskProgress"
    ).style.width = "0%";


    document.getElementById(
        "alertStatus"
    ).textContent =
        "NO ALERT";


    document.getElementById(
        "alertTitle"
    ).textContent =
        "No Active Warning";


    document.getElementById(
        "alertMessage"
    ).textContent =
        "Run the prediction to generate a location-specific alert.";


    document.getElementById(
        "trafficStatus"
    ).textContent =
        "WAITING";


    document.getElementById(
        "trafficTitle"
    ).textContent =
        "Waiting for risk calculation";


    document.getElementById(
        "trafficMessage"
    ).textContent =
        "Run the prediction to check traffic conditions.";


    document.getElementById(
        "safeRoute"
    ).textContent =
        "Run the prediction to generate a safe route.";


    document.getElementById(
        "roads"
    ).innerHTML =
        '<span class="road-placeholder">' +
        'No roads identified yet.' +
        '</span>';

    document.getElementById(
        "safeRoadsSection"
    ).style.display = "none";


    document.getElementById(
        "rainImpact"
    ).textContent = "--";


    document.getElementById(
        "waterImpact"
    ).textContent = "--";


    document.getElementById(
        "overallImpact"
    ).textContent = "--";


    document.getElementById(
        "rainText"
    ).textContent =
        "Waiting for calculation.";


    document.getElementById(
        "waterText"
    ).textContent =
        "Waiting for calculation.";


    document.getElementById(
        "mapStatus"
    ).textContent =
        "WAITING";


    if (riskCircle) {

        map.removeLayer(
            riskCircle
        );

        riskCircle = null;

    }


    map.setView(
        [PUNE.lat, PUNE.lng],
        12
    );

} 