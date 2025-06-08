document.addEventListener("DOMContentLoaded", () => {
    fetch('/weather')
        .then(response => response.json())
        .then(data => {

            document.getElementById("temperature").textContent = `${data.temperature} °C`;
            document.getElementById("humidity").textContent = `${data.humidity}%`;
            document.getElementById("windspeed").textContent = `${data.windspeed} m/s`;
            document.getElementById("aqi").textContent = data.aqi;
            document.getElementById("aqi_status").textContent = data.aqi_status;
        })
        .catch(error => {
            console.error('Error fetching weather data:', error);
        });
});

function applyTheme(temperature) {
    const root = document.documentElement;
    root.classList.remove('theme-cool', 'theme-warm', 'theme-hot', 'theme-blazing');

    if (temperature <= 20) {
        root.classList.add('theme-cool');
    } else if (temperature <= 30) {
        root.classList.add('theme-warm');
    } else if (temperature <= 40) {
        root.classList.add('theme-hot');
    } else {
        root.classList.add('theme-blazing');
    }
}

// Fetch forecast data
fetch('/forecast')
    .then(response => {
        console.log('Response received:', response);
        return response.json();
    })
    .then(data => {
        console.log("Forecast data:", data);  // This will log the fetched data

        // Prepare data for the chart
        const labels = Object.keys(data);  // Days as the labels
        const avgTemps = labels.map(day => {
            let avgTemp = data[day].avg_temp;

            // Log avgTemp to debug
            console.log(`Day: ${day}, Avg Temp: ${avgTemp}`);

            // Exclude negative temperatures by setting them to 0
            if (avgTemp < 0) {
                avgTemp = 0;
            }
            return avgTemp;
        });

        // Log the avgTemps array to check if values are correctly mapped
        console.log("AvgTemps array:", avgTemps);

        // Update the text content for each day's forecast (with actual values)
        for (let i = 1; i <= 7; i++) {
            let avgTemp = data[i].avg_temp;
            if (avgTemp < 0) avgTemp = 0; // Exclude negative temperatures for display
            document.getElementById(`avg_temp_day${i}`).textContent = `Avg   : ${avgTemp} °C`;
            document.getElementById(`min_temp_day${i}`).textContent = `Min   : ${data[i].min_temp} °C`;
            document.getElementById(`max_temp_day${i}`).textContent = `Max   : ${data[i].max_temp} °C`;
            document.getElementById(`precip_day${i}`).textContent = `Prec: ${data[i].precip} mm`;
            document.getElementById(`wind_day${i}`).textContent = `Wind  : ${data[i].wind} m/s`;
        }

        // Create the line chart
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        const temperatureChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Temperature (°C)',
                    data: avgTemps,
                    borderColor: 'rgb(249, 255, 139)',
                    backgroundColor: 'rgba(148, 155, 155, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Day'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        }
                    }
                }
            }
        });
    })
    .catch(error => {
        console.error('Error fetching forecast data:', error);
    });


applyTheme(data.temperature);