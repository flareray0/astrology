async function postJson(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(json));
  return json;
}

const natalForm = document.getElementById('natalForm');
if (natalForm) {
  natalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = new FormData(natalForm);
    const payload = {
      person_name: f.get('person_name'),
      birth: {
        date: f.get('date'), time: f.get('time'), timezone: Number(f.get('timezone')),
        lat: Number(f.get('lat')), lon: Number(f.get('lon')),
      },
    };
    const result = await postJson('/api/chart/natal', payload);
    document.getElementById('result').textContent = JSON.stringify(result, null, 2);
  });
}

const synastryForm = document.getElementById('synastryForm');
if (synastryForm) {
  synastryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = new FormData(synastryForm);
    const payload = {
      person1_name: f.get('person1_name'),
      person2_name: f.get('person2_name'),
      person1: {
        date: f.get('person1_date'), time: f.get('person1_time'), timezone: Number(f.get('person1_timezone')),
        lat: Number(f.get('person1_lat')), lon: Number(f.get('person1_lon')),
      },
      person2: {
        date: f.get('person2_date'), time: f.get('person2_time'), timezone: Number(f.get('person2_timezone')),
        lat: Number(f.get('person2_lat')), lon: Number(f.get('person2_lon')),
      },
    };
    const result = await postJson('/api/chart/synastry', payload);
    document.getElementById('result').textContent = JSON.stringify(result, null, 2);
  });
}
