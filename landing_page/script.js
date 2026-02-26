// Scroll Reveal Animation
document.addEventListener("DOMContentLoaded", () => {
    const reveals = document.querySelectorAll(".reveal");

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("active");
                observer.unobserve(entry.target);
                
                // Trigger counter animation if it's the metrics section
                if(entry.target.classList.contains("metrics")) {
                    startCounters();
                }
            }
        });
    }, {
        threshold: 0.15
    });

    reveals.forEach(reveal => {
        revealObserver.observe(reveal);
    });

    // Setup Chart.js for Hero Dashboard
    initDashboardChart();
});

// Real-time Chart Animation
function initDashboardChart() {
    const ctx = document.getElementById('maturityChart').getContext('2d');
    
    // Initial data
    const initialData = [45, 52, 60, 68, 75, 84];
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Live'];

    const data = {
        labels: labels,
        datasets: [{
            label: 'AI Transformation Maturity',
            data: initialData,
            borderColor: '#E05A00', // Burnt Orange
            backgroundColor: 'rgba(224, 90, 0, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#fff',
            pointBorderColor: '#E05A00',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1A1A1A',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Inter', size: 14, weight: 'bold' },
                    padding: 10,
                    displayColors: false,
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter' } }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { borderDash: [5, 5], color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { family: 'Inter' } }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeOutQuart'
            }
        }
    };

    const chart = new Chart(ctx, config);

    // Simulate "Live" updates
    setInterval(() => {
        let lastVal = data.datasets[0].data[5];
        // Fluctuate between 82 and 88
        let newVal = lastVal + (Math.random() * 4 - 2); 
        newVal = Math.min(Math.max(newVal, 82), 88);
        
        data.datasets[0].data[5] = newVal;
        chart.update('none'); // Update without full animation for smooth live feel
        
        // Update score text
        document.getElementById('scoreVal').innerText = Math.round(newVal);
    }, 2500);
}

// Counter Animation
let countersStarted = false;
function startCounters() {
    if(countersStarted) return;
    countersStarted = true;
    
    const counters = document.querySelectorAll('.counter');
    const speed = 200; // The lower the slower

    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-target');
            const count = +counter.innerText;
            const inc = target / speed;

            if (count < target) {
                // Determine precision based on if target has decimals
                const isDecimal = target % 1 !== 0;
                let nextVal = count + inc;
                
                if(isDecimal) {
                    counter.innerText = nextVal.toFixed(1);
                } else {
                    counter.innerText = Math.ceil(nextVal);
                }
                setTimeout(updateCount, 15);
            } else {
                counter.innerText = target;
            }
        };
        updateCount();
    });
}
