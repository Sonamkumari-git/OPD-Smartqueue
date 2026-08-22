/** Clinical Flight Deck real-time hook: WebSocket change signals are followed by REST re-synchronization. */
import { API_BASE_URL } from "@/services/api";
import { useEffect, useRef, useState } from "react";

export function useQueueSocket(path: string | null, accessToken: string | null, onEvent: () => void) {
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "reconnecting">("idle");
  const retry = useRef<number | null>(null);

  useEffect(() => {
    if (!path || !accessToken) return;
    let socket: WebSocket | null = null;
    let cancelled = false;
    const connect = () => {
      setStatus(socket ? "reconnecting" : "connecting");
      const url = new URL(`${API_BASE_URL.replace(/^http/, "ws")}${path}`);
      url.searchParams.set("token", accessToken);
      socket = new WebSocket(url);
      socket.onopen = () => { if (!cancelled) setStatus("connected"); };
      socket.onmessage = () => { if (!cancelled) onEvent(); };
      socket.onclose = () => { if (!cancelled) { setStatus("reconnecting"); retry.current = window.setTimeout(connect, 1800); } };
    };
    connect();
    return () => { cancelled = true; if (retry.current) window.clearTimeout(retry.current); socket?.close(); };
  }, [path, accessToken, onEvent]);

  return status;
}
