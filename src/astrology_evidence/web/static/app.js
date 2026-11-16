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
        if (values.time_precision === 'exact' && values.fold !== '') body.birth_input.fold = Number(values.fold);
        if (values.time_precision === 'approximate') {body.birth_input.earliest_local = values.earliest_local; body.birth_input.latest_local = values.latest_local;}
      }
      const headers = {'Content-Type':'application/json', Origin:location.origin, 'X-CSRF-Token':csrfToken()};
      if (form.dataset.api === '/api/readings') headers['Idempotency-Key'] = values.request_key;
      try {
      if (body.birth_input && values.time_precision === 'exact' && values.fold === '') {
        const options = await fetch('/api/time-options', {method:'POST', headers:headers, body:JSON.stringify({birth_date:values.birth_date, local_time:values.local_time, timezone:values.timezone})});
        if (!options.ok) throw new Error('Birth time could not be resolved. Check the date, time and timezone.');
        const result = await options.json();
        if (result.ambiguous) throw new Error('Choose the first or second occurrence, including its UTC offset, before saving.');
      }
      const response = await fetch(form.dataset.api, {method:form.dataset.method || 'POST', headers:headers, body:JSON.stringify(body)});
      if (response.ok) {const data = await response.json(); location.href = data.reading_id ? '/readings/' + data.reading_id : form.dataset.success || '/dashboard';}
      else { const alert = form.querySelector('[role=alert]'); const data = await response.json(); if (alert) alert.textContent = typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Unable to submit. Check the entered values and try again.'; }
      } catch (error) {form.querySelector('[role=alert]').textContent=error.message || 'Connection failed. Your inputs are preserved; please retry.';}
    });
  });
  document.querySelectorAll('[data-profile-form]').forEach(function (form) {
    const status = form.querySelector('[data-time-status]');
    const fold = form.elements.namedItem('fold');
    let request = 0;
    async function updateTimeOptions(preserveSelection = false) {
      const selected = preserveSelection ? fold.value : '';
      const current = ++request;
      fold.value = '';
      fold.required = false;
      fold.replaceChildren(new Option('Not applicable / choose if asked', ''));
      if (form.elements.namedItem('time_precision').value !== 'exact') {
        status.textContent = '';
        return;
      }
      const birthDate = form.elements.namedItem('birth_date').value;
      const localTime = form.elements.namedItem('local_time').value;
      const timezone = form.elements.namedItem('timezone').value;
      if (!birthDate || !localTime || !timezone) return;
      status.textContent = 'Checking local-time offsets…';
      try {
        const response = await fetch('/api/time-options', {
          method: 'POST',
          headers: {'Content-Type':'application/json', Origin:location.origin, 'X-CSRF-Token':csrfToken()},
          body: JSON.stringify({birth_date:birthDate, local_time:localTime, timezone:timezone}),
        });
        if (current !== request) return;
        if (!response.ok) throw new Error('This local time does not exist in the selected timezone.');
        const result = await response.json();
        if (current !== request) return;
        if (result.ambiguous) {
          fold.replaceChildren(new Option('Choose a UTC offset', ''));
          for (const candidate of result.candidates) fold.add(new Option(candidate.label, String(candidate.fold)));
          fold.required = true;
          fold.value = selected;
          status.textContent = 'This local time occurs twice. Choose the correct UTC offset before saving.';
        } else {
          const offset = result.candidates[0]?.offset;
          fold.replaceChildren(new Option(offset ? `${offset} (only valid occurrence)` : 'Not applicable', ''));
          status.textContent = offset ? `This local time has one valid UTC offset: ${offset}.` : 'This local time has one valid UTC offset.';
        }
      } catch (error) {
        if (current === request) status.textContent = error.message || 'Unable to check the local-time offset.';
      }
    }
    for (const name of ['birth_date', 'local_time', 'timezone', 'time_precision']) {
      form.elements.namedItem(name).addEventListener('change', () => updateTimeOptions(false));
    }
    const existingProfile = form.elements.namedItem('profile_id');
    if (existingProfile && existingProfile.value && form.elements.namedItem('time_precision').value === 'exact') {
      updateTimeOptions(true);
    }
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
