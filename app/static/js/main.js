// AI Smart Prediction Dashboard Controller

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map
    let map = null;
    let markers = {};
    const mapElement = document.getElementById('map');

    if (mapElement && typeof L !== 'undefined') {
        // Centered on Feng Chia University (逢甲大學)
        map = L.map('map', {
            center: [24.1794, 120.6482],
            zoom: 17,
            zoomControl: true,
            attributionControl: false
        });

        // Add Dark Matter Tile Layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19
        }).addTo(map);

        // Populate markers from locationsData
        initMapMarkers();
    }

    function getMarkerColor(crowdLevel) {
        if (crowdLevel >= 70) return 'red';
        if (crowdLevel >= 40) return 'yellow';
        return 'green';
    }

    function initMapMarkers() {
        if (!map || !locationsData) return;

        locationsData.forEach(loc => {
            const color = getMarkerColor(loc.current_crowd || 30);
            
            // Custom HTML Marker Icon
            const customIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `
                    <div class="custom-marker" id="marker-wrapper-${loc.id}">
                        <div class="marker-pin marker-pin-${color}"></div>
                        <div class="marker-pulse marker-pulse-${color}"></div>
                    </div>
                `,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            const marker = L.marker([loc.latitude, loc.longitude], { icon: customIcon })
                .addTo(map)
                .bindPopup(`<strong class="text-white">${loc.name}</strong><br><span class="text-muted">當前人潮: ${Math.round(loc.current_crowd)}%</span>`);

            marker.on('click', () => {
                selectLocation(loc.id);
            });

            markers[loc.id] = {
                markerObj: marker,
                location: loc
            };
        });
    }

    function updateMarkerStyle(locationId, crowdLevel) {
        const wrapper = document.getElementById(`marker-wrapper-${locationId}`);
        if (!wrapper) return;

        const color = getMarkerColor(crowdLevel);
        
        // Update pin class
        const pin = wrapper.querySelector('.marker-pin');
        pin.className = `marker-pin marker-pin-${color}`;

        // Update pulse class
        const pulse = wrapper.querySelector('.marker-pulse');
        pulse.className = `marker-pulse marker-pulse-${color}`;
    }

    // 2. Geolocation / IP Positioning
    function getDistance(lat1, lon1, lat2, lon2) {
        const dx = lat1 - lat2;
        const dy = lon1 - lon2;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function locateAndSelect(simulate = false) {
        const geoStatus = document.getElementById('geo-status');
        if (geoStatus) {
            geoStatus.innerHTML = `<i class="bi bi-arrow-repeat animate-spin text-info me-1"></i> 正在獲取地理定位...`;
        }

        fetch(`/api/geoip?simulate=${simulate}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const uLat = data.lat;
                    const uLon = data.lon;
                    
                    // Find closest location
                    let closestLoc = null;
                    let minDist = Infinity;
                    
                    locationsData.forEach(loc => {
                        const dist = getDistance(uLat, uLon, loc.latitude, loc.longitude);
                        if (dist < minDist) {
                            minDist = dist;
                            closestLoc = loc;
                        }
                    });

                    // Check if user is reasonably close to campus (simulate is always close)
                    if (closestLoc && (minDist < 0.015 || simulate)) {
                        selectLocation(closestLoc.id);
                        if (geoStatus) {
                            if (simulate) {
                                geoStatus.innerHTML = `<span class="text-success"><i class="bi bi-geo-alt-fill me-1"></i> 定位模擬成功：已切換至最接近的「${closestLoc.name}」</span>`;
                            } else {
                                geoStatus.innerHTML = `<span class="text-success"><i class="bi bi-geo-alt-fill me-1"></i> 已根據 IP 自動定位至最接近的「${closestLoc.name}」</span>`;
                            }
                        }
                    } else {
                        if (geoStatus) {
                            geoStatus.innerHTML = `<span class="text-muted"><i class="bi bi-info-circle me-1"></i> 偵測到您不在校園內，已切換為手動選擇模式。</span>`;
                        }
                        // Default select first
                        if (initialLocationId) selectLocation(initialLocationId);
                    }
                } else {
                    if (geoStatus) {
                        geoStatus.innerHTML = `<span class="text-muted"><i class="bi bi-exclamation-triangle-fill text-warning me-1"></i> 定位失敗，已切換為手動選擇模式。</span>`;
                    }
                    if (initialLocationId) selectLocation(initialLocationId);
                }
            })
            .catch(err => {
                console.error("定位失敗", err);
                if (geoStatus) {
                    geoStatus.innerHTML = `<span class="text-muted"><i class="bi bi-exclamation-triangle-fill text-warning me-1"></i> 定位失敗，切換為手動模式。</span>`;
                }
                if (initialLocationId) selectLocation(initialLocationId);
            });
    }

    const simulateBtn = document.getElementById('btn-simulate-gps');
    if (simulateBtn) {
        simulateBtn.addEventListener('click', () => {
            locateAndSelect(true);
        });
    }

    // Auto locate on start
    locateAndSelect(false);

    // 3. UI Selection & Fetch Predictions
    let predictionChart = null;

    function selectLocation(locationId) {
        const loc = locationsData.find(l => l.id === locationId);
        if (!loc) return;

        // Update selected location UI header
        document.getElementById('selected-loc-name').innerText = loc.name;
        document.getElementById('report-location-id').value = locationId;

        // Enable Submit button (if values selected)
        checkSubmitStatus();

        // Focus map on location
        if (map) {
            map.panTo([loc.latitude, loc.longitude]);
        }

        // Fetch prediction metrics and graph
        fetch(`/api/predictions/${locationId}`)
            .then(res => res.json())
            .then(data => {
                // Update stats gauge
                const crowdVal = Math.round(data.current_crowd);
                const tempVal = data.current_temp;

                // Update crowd text & bar
                document.getElementById('stat-crowd-num').innerText = crowdVal;
                const crowdBar = document.getElementById('stat-crowd-bar');
                crowdBar.style.width = crowdVal + '%';
                
                // Color gauges
                let crowdLbl = "空曠";
                let crowdColorClass = "bg-success";
                let crowdTextClass = "text-success";
                if (crowdVal >= 70) {
                    crowdLbl = "擁擠";
                    crowdColorClass = "bg-danger";
                    crowdTextClass = "text-danger";
                } else if (crowdVal >= 40) {
                    crowdLbl = "適中";
                    crowdColorClass = "bg-warning";
                    crowdTextClass = "text-warning";
                }
                crowdBar.className = `progress-bar ${crowdColorClass}`;
                const crowdBadge = document.getElementById('stat-crowd-lbl');
                crowdBadge.innerText = crowdLbl;
                crowdBadge.className = `badge bg-opacity-25 mt-2 d-inline-block fs-8 ${crowdTextClass} ${crowdColorClass}`;

                // Update temp text & bar
                document.getElementById('stat-temp-num').innerText = tempVal.toFixed(1);
                const tempBar = document.getElementById('stat-temp-bar');
                // Maps 15-35°C to 0-100%
                const tempPercentage = Math.max(0, Math.min(100, ((tempVal - 15) / 20) * 100));
                tempBar.style.width = tempPercentage + '%';

                let tempLbl = "舒適";
                let tempColorClass = "bg-success";
                let tempTextClass = "text-success";
                if (tempVal >= 28) {
                    tempLbl = "悶熱";
                    tempColorClass = "bg-danger";
                    tempTextClass = "text-danger";
                } else if (tempVal <= 21) {
                    tempLbl = "偏冷";
                    tempColorClass = "bg-info";
                    tempTextClass = "text-info";
                }
                tempBar.className = `progress-bar ${tempColorClass}`;
                const tempBadge = document.getElementById('stat-temp-lbl');
                tempBadge.innerText = tempLbl;
                tempBadge.className = `badge bg-opacity-25 mt-2 d-inline-block fs-8 ${tempTextClass} ${tempColorClass}`;

                // Update Marker dynamically
                updateMarkerStyle(locationId, crowdVal);

                // Render Chart
                renderChart(data);
            });
    }

    // Chart.js render function
    function renderChart(data) {
        const ctx = document.getElementById('predictionChart').getContext('2d');

        // Prepare continuous timeline labels
        const labels = [];
        const pastCrowd = [];
        const pastTemp = [];
        const predCrowd = [];
        const predTemp = [];

        // 1. Add historical records (past 3 hours)
        data.history.forEach(item => {
            labels.push(item.time_str);
            pastCrowd.push(item.crowd_level);
            pastTemp.push(item.temperature);
            predCrowd.push(null); // No prediction values for past
            predTemp.push(null);
        });

        // 2. Add transition point (current value fits at index end of past / start of prediction)
        const transitionIndex = labels.length;
        if (labels.length > 0) {
            // Overlay current adjusted stats to connect the line segments
            predCrowd[transitionIndex - 1] = data.current_crowd;
            predTemp[transitionIndex - 1] = data.current_temp;
        }

        // 3. Add prediction records (future 1 hour)
        data.predictions.forEach(item => {
            labels.push(item.time_str + " (預測)");
            predCrowd.push(item.crowd_level);
            predTemp.push(item.temperature);
            pastCrowd.push(null); // No historical values for future
            pastTemp.push(null);
        });

        if (predictionChart) {
            predictionChart.destroy();
        }

        predictionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '人潮 - 歷史紀錄',
                        data: pastCrowd,
                        borderColor: '#00d2ff',
                        backgroundColor: 'rgba(0, 210, 255, 0.05)',
                        borderWidth: 2,
                        tension: 0.3,
                        spanGaps: true,
                        fill: true
                    },
                    {
                        label: '人潮 - AI預測',
                        data: predCrowd,
                        borderColor: '#00d2ff',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3,
                        spanGaps: true
                    },
                    {
                        label: '溫度 - 歷史紀錄',
                        data: pastTemp,
                        borderColor: '#ffc107',
                        borderWidth: 2,
                        tension: 0.3,
                        spanGaps: true
                    },
                    {
                        label: '溫度 - AI預測',
                        data: predTemp,
                        borderColor: '#ffc107',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3,
                        spanGaps: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // Hide default legend
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(13, 10, 37, 0.95)',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.04)'
                        },
                        ticks: {
                            color: '#8b949e',
                            font: { size: 9 }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255,255,255,0.04)'
                        },
                        ticks: {
                            color: '#8b949e',
                            font: { size: 9 }
                        }
                    }
                }
            }
        });
    }

    // 4. Quick Report Form Interaction
    let selectedCrowd = null;
    let selectedTemp = null;

    const reportButtons = document.querySelectorAll('.btn-report-val');
    reportButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const field = btn.getAttribute('data-field');
            const val = btn.getAttribute('data-val');

            // Reset peers
            const peers = document.querySelectorAll(`.btn-report-val[data-field="${field}"]`);
            peers.forEach(p => {
                p.classList.remove('active', 'btn-active-success', 'btn-active-warning', 'btn-active-danger', 'btn-active-info');
            });

            // Set active class
            btn.classList.add('active');
            
            // Assign specific colored themes
            if (val === 'low' || val === 'comfort') {
                btn.classList.add('btn-active-success');
            } else if (val === 'medium') {
                btn.classList.add('btn-active-warning');
            } else if (val === 'high' || val === 'hot') {
                btn.classList.add('btn-active-danger');
            } else if (val === 'cold') {
                btn.classList.add('btn-active-info');
            }

            if (field === 'crowd_level') {
                selectedCrowd = val;
            } else {
                selectedTemp = val;
            }

            checkSubmitStatus();
        });
    });

    function checkSubmitStatus() {
        const activeLocId = document.getElementById('report-location-id').value;
        const submitBtn = document.getElementById('btn-submit-report');
        if (activeLocId && (selectedCrowd || selectedTemp)) {
            submitBtn.removeAttribute('disabled');
        } else {
            submitBtn.setAttribute('disabled', 'true');
        }
    }

    // Handle Submit Report Form
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
        reportForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const locationId = document.getElementById('report-location-id').value;
            const submitBtn = document.getElementById('btn-submit-report');
            const resultMsg = document.getElementById('report-result-msg');

            submitBtn.setAttribute('disabled', 'true');
            resultMsg.innerHTML = `<span class="text-info"><i class="bi bi-hourglass-split animate-spin me-1"></i> 傳送回報中...</span>`;

            fetch('/api/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location_id: parseInt(locationId),
                    crowd_level: selectedCrowd,
                    temperature_felt: selectedTemp
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    resultMsg.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-check-circle-fill me-1"></i> ${data.message}</span>`;
                    
                    // Reset selected states
                    selectedCrowd = null;
                    selectedTemp = null;
                    reportButtons.forEach(btn => {
                        btn.classList.remove('active', 'btn-active-success', 'btn-active-warning', 'btn-active-danger', 'btn-active-info');
                    });
                    
                    // Reload predictions after delay
                    setTimeout(() => {
                        resultMsg.innerHTML = "";
                        selectLocation(parseInt(locationId));
                    }, 1500);
                } else {
                    resultMsg.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i> ${data.message}</span>`;
                    submitBtn.removeAttribute('disabled');
                }
            })
            .catch(err => {
                console.error("回報發生錯誤", err);
                resultMsg.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i> 網路連線錯誤，請稍後重試。</span>`;
                submitBtn.removeAttribute('disabled');
            });
        });
    }

    // 5. Open-Meteo Real-time Weather Fetch
    function fetchLiveWeather() {
        // Taichung coordinates
        const lat = 24.179;
        const lon = 120.647;
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,weather_code`;

        fetch(weatherUrl)
            .then(res => res.json())
            .then(data => {
                if (data && data.current) {
                    const temp = data.current.temperature_2m;
                    const hum = data.current.relative_humidity_2m;
                    const code = data.current.weather_code;

                    // Update values
                    const tempElem = document.getElementById('weather-temp');
                    if (tempElem) tempElem.innerText = `${temp.toFixed(1)}°C`;

                    const humElem = document.getElementById('weather-humidity');
                    if (humElem) humElem.innerText = `相對濕度: ${hum}%`;

                    // Parse weather code to icon and description
                    let iconHtml = '<i class="bi bi-cloud-sun-fill animate-float"></i>';
                    let desc = '多雲時晴';

                    if (code === 0) {
                        iconHtml = '<i class="bi bi-sun-fill animate-float text-warning"></i>';
                        desc = '晴朗';
                    } else if ([1, 2, 3].includes(code)) {
                        iconHtml = '<i class="bi bi-cloud-sun-fill animate-float text-info"></i>';
                        desc = '多雲時晴';
                    } else if ([45, 48].includes(code)) {
                        iconHtml = '<i class="bi bi-cloud-fog2-fill text-muted"></i>';
                        desc = '有霧';
                    } else if ([51, 53, 55].includes(code)) {
                        iconHtml = '<i class="bi bi-cloud-drizzle-fill text-info"></i>';
                        desc = '毛毛細雨';
                    } else if ([61, 63, 65, 80, 81, 82].includes(code)) {
                        iconHtml = '<i class="bi bi-cloud-rain-heavy-fill text-primary"></i>';
                        desc = '局部陣雨';
                    } else if ([95, 96, 99].includes(code)) {
                        iconHtml = '<i class="bi bi-cloud-lightning-rain-fill text-warning"></i>';
                        desc = '雷陣雨';
                    }

                    const iconContainer = document.getElementById('weather-icon-container');
                    if (iconContainer) iconContainer.innerHTML = iconHtml;

                    const descElem = document.getElementById('weather-desc');
                    if (descElem) descElem.innerText = desc;
                }
            })
            .catch(err => {
                console.error("天氣獲取失敗", err);
                const descElem = document.getElementById('weather-desc');
                if (descElem) descElem.innerText = "無法載入即時天氣";
            });
    }

    // Fetch weather immediately
    fetchLiveWeather();
});
