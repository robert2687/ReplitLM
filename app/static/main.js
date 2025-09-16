async function submitForm(e) {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  const resp = await fetch("/api/jobs", { method: "POST", body: data });
  if (!resp.ok) {
    alert("Failed to queue job");
    return;
  }
  const { job_id } = await resp.json();
  poll(job_id);
}

async function poll(jobId) {
  const statusEl = document.getElementById("status");
  const dlEl = document.getElementById("download");
  statusEl.textContent = "Queued…";
  dlEl.style.display = "none";

  const timer = setInterval(async () => {
    const r = await fetch(`/api/jobs/${jobId}`);
    if (!r.ok) return;
    const j = await r.json();
    statusEl.textContent = `${j.status} ${Math.round((j.progress || 0) * 100)}% ${j.message || ""}`;

    if (j.status === "succeeded") {
      dlEl.href = `/api/jobs/${jobId}/download`;
      dlEl.style.display = "inline-block";
      clearInterval(timer);
    } else if (j.status === "failed") {
      alert("Job failed: " + (j.message || ""));
      clearInterval(timer);
    }
  }, 1000);
}

window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("builder-form");
  if (form) form.addEventListener("submit", submitForm);
});