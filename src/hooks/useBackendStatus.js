import { useState, useEffect } from 'react';
import { apiUrl } from '../config';

const CHECK_INTERVAL_MS = 5000;
const REQUEST_TIMEOUT_MS = 3000;
const FAILURES_BEFORE_OFFLINE = 3;

// Surveille /api/health : "offline" apres plusieurs echecs consecutifs
// (un echec isole ne declenche pas l'alerte), et revient a "online" au premier succes.
export default function useBackendStatus() {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let failures = 0;
    let timer = null;

    const check = async () => {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
      try {
        const response = await fetch(apiUrl('/api/health'), { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        failures = 0;
        if (!cancelled) setOnline(true);
      } catch {
        failures += 1;
        if (!cancelled && failures >= FAILURES_BEFORE_OFFLINE) setOnline(false);
      } finally {
        clearTimeout(timeout);
        if (!cancelled) timer = setTimeout(check, CHECK_INTERVAL_MS);
      }
    };

    timer = setTimeout(check, CHECK_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  return online;
}
