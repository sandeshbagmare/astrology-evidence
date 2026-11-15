(function () {
  const cookieName = document.documentElement.dataset.csrfCookie || 'ae_csrf';
  function csrfToken() {
    const item = document.cookie.split('; ').find(value => value.startsWith(cookieName + '='));
    return item ? decodeURIComponent(item.slice(cookieName.length + 1)) : '';
  }
  document.querySelectorAll('form[data-api]').forEach(function (form) {
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form));
      const body = values.birth_date ? {alias:values.alias || '', storage_consent:values.storage_consent === 'true', notice_version:values.notice_version, birth_input:{birth_date:values.birth_date, local_time:values.local_time || null, time_precision:values.time_precision, latitude:Number(values.latitude), longitude:Number(values.longitude), timezone:values.timezone, timezone_history:values.timezone_history}} : {profile_revision_id:values.profile_revision_id,question:values.question};
      if (body.birth_input) {
        if (values.expected_version) body.expected_version = Number(values.expected_version);
        if (values.time_precision !== 'exact') body.birth_input.local_time = null;
        if (values.time_precision === 'approximate') {body.birth_input.earliest_local = values.earliest_local; body.birth_input.latest_local = values.latest_local;}
      }
      const headers = {'Content-Type':'application/json', Origin:location.origin, 'X-CSRF-Token':csrfToken()};
      if (form.dataset.api === '/api/readings') headers['Idempotency-Key'] = values.request_key;
      try {
      const response = await fetch(form.dataset.api, {method:form.dataset.method || 'POST', headers:headers, body:JSON.stringify(body)});
      if (response.ok) {const data = await response.json(); location.href = data.reading_id ? '/readings/' + data.reading_id : form.dataset.success || '/dashboard';}
      else { const alert = form.querySelector('[role=alert]'); const data = await response.json(); if (alert) alert.textContent = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Unable to submit. Check the entered values and try again.'; }
      } catch {form.querySelector('[role=alert]').textContent='Connection failed. Your inputs are preserved; please retry.';}
    });
  });
  const progress = document.querySelector('[data-export-job]');
  if (progress) {
    let attempts = 0;
    const timer = setInterval(async () => {
      try {
        const response = await fetch('/api/jobs/' + progress.dataset.exportJob);
        if (!response.ok || ++attempts > 60) {clearInterval(timer);return;}
        const job = await response.json();
        progress.textContent = 'Export status: ' + job.status;
        if (job.status === 'succeeded') {
          clearInterval(timer);
          const link = document.createElement('a');
          link.href = '/api/exports/' + progress.dataset.exportId;
          link.textContent = 'Download export';
          progress.replaceChildren(link);
        } else if (['failed','dead_letter','cancelled'].includes(job.status)) clearInterval(timer);
      } catch {clearInterval(timer);progress.textContent='Cannot refresh status. Use the refresh link below.';}
    }, 2000);
  }
}());
