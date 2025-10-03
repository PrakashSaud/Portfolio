document.addEventListener('DOMContentLoaded', () => {
  // Consent gate: disable submit until checked (assumes default id 'id_consent')
  const consent = document.getElementById('id_consent');
  const submitBtn = document.getElementById('contact-submit');
  if (consent && submitBtn) {
    const setState = () => { submitBtn.disabled = !consent.checked; };
    setState();
    consent.addEventListener('change', setState);
  }

  // Character counter for message (assumes default id 'id_message')
  const msg = document.getElementById('id_message');
  const counter = document.getElementById('message-counter');
  if (msg && counter) {
    const max = parseInt(counter.dataset.max || '1000', 10);
    const update = () => {
      const len = msg.value.length;
      counter.textContent = `${len}/${max}`;
      if (len > max) counter.classList.add('text-red-600'); else counter.classList.remove('text-red-600');
    };
    msg.addEventListener('input', update);
    update();
  }
});