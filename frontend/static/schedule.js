const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function loadSchedule() {
    fetch("/api/schedule")
        .then(res => res.json())
        .then(data => {
            const body = document.getElementById("scheduleBody");
            body.innerHTML = "";

            days.forEach(day => {
                let row = `<tr><td class="day-cell">${day}</td>`;
                
                for (let i = 1; i <= 6; i++) {
                    let cell = data.find(c => c.day === day && c.hour === i);
                    let subject = cell ? cell.subject : "";
                    let displayText = subject || "+";
                    let cellClass = subject ? "schedule-cell filled" : "schedule-cell empty";
                    
                    row += `<td class="${cellClass}" onclick="editCell('${day}', ${i}, '${subject}')">
                                ${displayText}
                            </td>`;
                }
                
                row += "</tr>";
                body.innerHTML += row;
            });
        });
}

function editCell(day, hour, currentSubject) {
    let subject = prompt("Enter subject name:", currentSubject);
    
    // If user clicked cancel, do nothing
    if (subject === null) return;
    
    // If empty string, we'll clear the cell
    fetch("/api/schedule", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ day, hour, subject })
    }).then(() => {
        loadSchedule();
    });
}

// Load schedule on page load
loadSchedule();
