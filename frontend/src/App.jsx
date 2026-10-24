import { useEffect, useRef, useState } from "react";
import "./App.css";
import { API_URL, CUSTOMER_CARE_PHONE_NUMBER, getTelLink } from "./config";

function getSpeechRecognition() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export default function App() {
  // Authentication State
  const [token, setToken] = useState(() => localStorage.getItem("aura_token") || "");
  const [customer, setCustomer] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" | "register"
  const [authError, setAuthError] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Auth Form Fields
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authPasswordConfirm, setAuthPasswordConfirm] = useState("");

  // Customer Orders State
  const [orders, setOrders] = useState([]);
  const [ordersModalOpen, setOrdersModalOpen] = useState(false);

  // Interactive UI State
  const [wishlist, setWishlist] = useState({ 1: false, 2: true, 3: false, 4: false });
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [newsletterSubscribed, setNewsletterSubscribed] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [quickViewProduct, setQuickViewProduct] = useState(null);
  const [cartDrawerOpen, setCartDrawerOpen] = useState(false);

  // Quiz state
  const [quizSkinType, setQuizSkinType] = useState("Combination");
  const [quizGoal, setQuizGoal] = useState("Radiant Glow");

  // Shopping Cart items
  const [cartItems, setCartItems] = useState([
    {
      id: 1,
      name: "Hydra Glow Gel Cream",
      price: 34.0,
      qty: 1,
      img: "/images/product-hydra-cream.jpg",
    },
    {
      id: 2,
      name: "Radiance Boost Serum",
      price: 42.0,
      qty: 1,
      img: "/images/product-radiance-serum.jpg",
    },
  ]);

  // =========================================================================
  // BOT OPTION 1: NORMAL CONVERSATION BOT (Skincare Chat Assistant)
  // =========================================================================
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Namaste! Main Aura ki Skincare Chatbot hoon. Botanical ingredients, custom routines, ya product recommendations — kuch bhi poochho!",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatScrollRef = useRef(null);

  // =========================================================================
  // BOT OPTION 2: LIVE VOICE AGENT CALL (Spoken Call Studio & Support)
  // =========================================================================
  const [callModalOpen, setCallModalOpen] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [callId, setCallId] = useState(null);
  const [callStatus, setCallStatus] = useState("idle"); // idle | connecting | listening | thinking | speaking
  const [callTimer, setCallTimer] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [callMessages, setCallMessages] = useState([]);
  const [callSummary, setCallSummary] = useState(null);
  const [voiceError, setVoiceError] = useState("");
  const [voiceSupported, setVoiceSupported] = useState(true);
  const [backendLatency, setBackendLatency] = useState(null);
  const [isBargeInInterrupted, setIsBargeInInterrupted] = useState(false);
  const [highlightCustomerCare, setHighlightCustomerCare] = useState(false);
  const [userSpeakingTranscript, setUserSpeakingTranscript] = useState("");
  const [studioInput, setStudioInput] = useState("");
  const [speechLang, setSpeechLang] = useState("en-IN");
  const [isMicListening, setIsMicListening] = useState(false);
  const [micAudioLevel, setMicAudioLevel] = useState(0);

  const recognitionRef = useRef(null);
  const callActiveRef = useRef(false);
  const callIdRef = useRef(null);
  const callStatusRef = useRef("idle");
  const isMutedRef = useRef(false);
  const currentAudioRef = useRef(null);
  const toastTimeoutRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const callTranscriptScrollRef = useRef(null);
  const speechLangRef = useRef("en-IN");

  // Audio level monitoring refs
  const audioContextRef = useRef(null);
  const micStreamRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);

  // Barge-in & Speech Session Lifecycle Refs
  const speechSessionIdRef = useRef(0);
  const currentAriaSpeechTextRef = useRef("");
  const recentAriaTextsRef = useRef([]);
  const ariaSpeechStartTimeRef = useRef(0);
  const ariaSpeechEndTimeRef = useRef(0);
  const isRecognitionRunningRef = useRef(false);
  const isStartingRecognitionRef = useRef(false);
  const recognitionRestartTimerRef = useRef(null);
  const turnSilenceTimerRef = useRef(null);
  const pendingTurnSpeechRef = useRef("");
  const isProcessingTurnRef = useRef(false);
  const lastProcessedTurnRef = useRef({ text: "", timestamp: 0 });

  // Products Data
  const products = [
    {
      id: 1,
      name: "Hydra Glow Gel Cream",
      category: "MOISTURIZERS",
      badge: "BEST SELLER",
      badgeClass: "",
      price: 34.0,
      originalPrice: null,
      stars: 5,
      reviews: 245,
      img: "/images/product-hydra-cream.jpg",
      description: "Infused with botanical hyaluronic acid and jade mineral extract to deliver 72-hour dewy hydration.",
      keyIngredients: "Botanical Hyaluronic Acid, Jade Extract, Camellia Seed Oil",
      howToUse: "Apply a nickel-sized amount morning and evening after serum.",
    },
    {
      id: 2,
      name: "Radiance Boost Serum",
      category: "SERUMS",
      badge: "NEW",
      badgeClass: "",
      price: 42.0,
      originalPrice: null,
      stars: 5,
      reviews: 189,
      img: "/images/product-radiance-serum.jpg",
      description: "Concentrated 10% Vitamin C + Niacinamide elixir that brightens dark spots and restores youthful luminosity.",
      keyIngredients: "10% Pure Vitamin C, 5% Niacinamide, Ferulic Acid",
      howToUse: "Smooth 3–4 drops over freshly cleansed face and neck daily.",
    },
    {
      id: 3,
      name: "Nourishing Night Restorative Cream",
      category: "MOISTURIZERS",
      badge: "LIMITED",
      badgeClass: "",
      price: 38.0,
      originalPrice: null,
      stars: 5,
      reviews: 312,
      img: "/images/product-night-cream.jpg",
      description: "Deep nocturnal repair formulation with gentle plant retinoid and ceramides to renew skin elasticity.",
      keyIngredients: "Bakuchiol (Plant Retinol), Ceramide Complex, Evening Primrose",
      howToUse: "Massage gently into skin each night before resting.",
    },
    {
      id: 4,
      name: "Daily UV Defense Sunscreen SPF 50",
      category: "SUN CARE",
      badge: "SALE",
      badgeClass: "sale",
      price: 24.0,
      originalPrice: 30.0,
      stars: 5,
      reviews: 156,
      img: "/images/product-sunscreen.jpg",
      description: "Invisible broad-spectrum SPF 50+ shield with zero white cast, water-resistant for up to 40 minutes.",
      keyIngredients: "Zinc Oxide, Centella Asiatica, Green Tea Extract",
      howToUse: "Apply generously 15 minutes before sun exposure; reapply every 2 hours.",
    },
  ];

  function showToast(msg) {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToastMessage(msg);
    toastTimeoutRef.current = setTimeout(() => {
      setToastMessage("");
    }, 3200);
  }

  function handleCallCustomerCareClick(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    const telUri = getTelLink(CUSTOMER_CARE_PHONE_NUMBER);
    if (!telUri) {
      showToast("📞 Customer care calling will be available soon.");
      return;
    }

    // Open the customer device's phone dialer using a standard tel: URI
    window.location.href = telUri;
  }

  function stopAllSpeech(isInterruption = false) {
    speechSessionIdRef.current += 1;
    currentAriaSpeechTextRef.current = "";

    if (currentAudioRef.current) {
      const audio = currentAudioRef.current;
      audio.onplay = null;
      audio.onended = null;
      audio.onerror = null;
      try {
        audio.pause();
        audio.currentTime = 0;
        audio.removeAttribute("src");
        audio.load();
      } catch {
        // Ignored
      }
      currentAudioRef.current = null;
    }
    if ("speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // Ignored
      }
    }
  }

  function updateCallStatus(newStatus) {
    callStatusRef.current = newStatus;
    setCallStatus(newStatus);
  }

  function stopMicMonitor() {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      try {
        audioContextRef.current.close();
      } catch {}
      audioContextRef.current = null;
    }
    setMicAudioLevel(0);
  }

  useEffect(() => {
    speechLangRef.current = speechLang;
  }, [speechLang]);

  useEffect(() => {
    callStatusRef.current = callStatus;
  }, [callStatus]);

  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  useEffect(() => {
    callIdRef.current = callId;
  }, [callId]);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  useEffect(() => {
    if (callTranscriptScrollRef.current) {
      callTranscriptScrollRef.current.scrollTop = callTranscriptScrollRef.current.scrollHeight;
    }
  }, [callMessages]);

  // Active call duration timer
  useEffect(() => {
    if (callActive) {
      setCallTimer(0);
      timerIntervalRef.current = setInterval(() => {
        setCallTimer((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [callActive]);

  // Recognition liveness heartbeat: auto-restarts recognition if Chrome silently idled
  useEffect(() => {
    if (!callActive) return;

    const interval = setInterval(() => {
      if (
        callActiveRef.current &&
        !isMutedRef.current &&
        callStatusRef.current === "listening" &&
        !currentAudioRef.current &&
        !isRecognitionRunningRef.current &&
        !isStartingRecognitionRef.current
      ) {
        console.log("[Voice Heartbeat] Re-activating speech recognition...");
        safeStartRecognition();
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [callActive]);

  function formatCallDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  // Load customer profile on initial mount if token exists
  useEffect(() => {
    setVoiceSupported(Boolean(getSpeechRecognition()) && "speechSynthesis" in window);

    if (token) {
      fetchCustomerProfile(token);
    }

    return () => {
      callActiveRef.current = false;
      recognitionRef.current?.stop();
      stopAllSpeech();
      stopMicMonitor();
    };
  }, []);

  async function fetchCustomerProfile(jwtToken) {
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCustomer(data);
        fetchCustomerOrders(jwtToken);
      } else {
        handleLogout(false);
      }
    } catch {
      // Offline fallback
    } finally {
      setAuthLoading(false);
    }
  }

  async function fetchCustomerOrders(jwtToken) {
    try {
      const res = await fetch(`${API_URL}/api/orders`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOrders(data.orders || []);
      }
    } catch {
      // Ignore background order fetch failure
    }
  }

  function handleLogout(withToast = true) {
    localStorage.removeItem("aura_token");
    setToken("");
    setCustomer(null);
    setOrders([]);
    setUserMenuOpen(false);
    setOrdersModalOpen(false);
    if (withToast) {
      showToast("🚪 You have been safely logged out.");
    }
    if (callActiveRef.current) {
      endCall(false);
    }
  }

  function handleTrackOrderClick() {
    if (!token || !customer) {
      setAuthMode("login");
      setAuthError("Please log in to your account to view and track your orders.");
      setAuthModalOpen(true);
      return;
    }
    setOrdersModalOpen(true);
  }

  async function handleAuthSubmit(e) {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);

    const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
    const payload =
      authMode === "login"
        ? { email: authEmail, password: authPassword }
        : {
            full_name: authFullName,
            email: authEmail,
            password: authPassword,
            password_confirm: authPasswordConfirm,
          };

    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let data;
      try {
        data = await res.json();
      } catch {
        data = {};
      }

      if (!res.ok) {
        if (res.status === 404) {
          throw new Error(
            `Backend endpoint not found (404) at: ${API_URL}${endpoint}. Check your Vercel VITE_API_URL environment variable and ensure you redeployed.`
          );
        }
        throw new Error(data.detail || "Authentication failed. Please check your credentials.");
      }

      localStorage.setItem("aura_token", data.access_token);
      setToken(data.access_token);
      setCustomer(data.customer);
      setAuthModalOpen(false);
      setAuthPassword("");
      setAuthPasswordConfirm("");

      showToast(`✨ Welcome, ${data.customer.full_name}!`);
      fetchCustomerOrders(data.access_token);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  function fillDemoUser(email, name) {
    setAuthEmail(email);
    setAuthPassword("Password123!");
    setAuthFullName(name);
    setAuthPasswordConfirm("Password123!");
    setAuthError("");
  }

  // =========================================================================
  // BOT 1 LOGIC: NORMAL CONVERSATION BOT (Fast Text Chat)
  // =========================================================================
  async function sendNormalChatMessage(rawMessage) {
    const message = rawMessage.trim();
    if (!message) return;

    // Check if user is asking for order tracking while unauthenticated
    const isOrderQuery = /\b(order|track|tracking|ord-\d+|package|parcel|shipment|delivery status)\b/i.test(message);
    if (isOrderQuery && (!token || !customer)) {
      setChatMessages((prev) => [
        ...prev,
        { role: "user", text: message, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
        {
          role: "assistant",
          text: "Order tracking is securely restricted to authenticated customers. Please sign in to view and track your orders.",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
      setChatInput("");
      setAuthMode("login");
      setAuthError("Please log in to your Aura account to track your orders.");
      setAuthModalOpen(true);
      return;
    }

    setChatMessages((prev) => [
      ...prev,
      { role: "user", text: message, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
    ]);
    setChatInput("");
    setChatLoading(true);

    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const historyPayload = chatMessages.slice(-6).map((m) => ({
        role: m.role,
        content: m.text,
      }));

      const response = await fetch(`${API_URL}/api/chatbot`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message, call_id: null, history: historyPayload }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to reach chat assistant.");
      }

      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.reply || "I'm here to help with your skincare needs.",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `I'm having trouble connecting right now: ${err.message}`,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  // =========================================================================
  // BOT 2 LOGIC: LIVE AI VOICE AGENT CALL WITH REAL-TIME BARGE-IN
  // =========================================================================

  function isEchoOfAria(transcript) {
    if (!transcript) return false;
    const cleanUser = transcript
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (!cleanUser || cleanUser.length < 3) return false;

    // Check against active speech or within 350ms after Aria stopped talking (room reverb)
    const timeSinceSpeech = Date.now() - ariaSpeechEndTimeRef.current;
    const isActivelyOrJustSpoken =
      callStatusRef.current === "speaking" ||
      Boolean(currentAudioRef.current) ||
      timeSinceSpeech < 350;

    if (!isActivelyOrJustSpoken) {
      return false; // Once Aria finishes, customer speech is NEVER treated as echo!
    }

    const allRecentAria = [
      currentAriaSpeechTextRef.current,
      ...(recentAriaTextsRef.current || []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (!allRecentAria) return false;

    // Direct containment: only suppress if customer utterance is an exact long phrase (>= 15 chars) matching Aria's speech verbatim
    if (cleanUser.length >= 15 && allRecentAria.includes(cleanUser)) {
      return true;
    }

    // High word-overlap check (at least 3 words and >=75% overlap)
    const userWords = cleanUser.split(" ").filter((w) => w.length > 2);
    if (userWords.length >= 3) {
      const matchCount = userWords.filter((w) => allRecentAria.includes(w)).length;
      if (matchCount / userWords.length >= 0.75) {
        return true;
      }
    }

    return false;
  }

  function triggerBargeInInterruption() {
    if (!callActiveRef.current) return;
    if (callStatusRef.current !== "speaking" && !currentAudioRef.current) return;

    // Stop Aria's audio output and speech synthesis immediately
    stopAllSpeech(true);

    // Transition state to listening immediately
    updateCallStatus("listening");
    setIsBargeInInterrupted(true);
    setTimeout(() => {
      setIsBargeInInterrupted(false);
    }, 2800);

    // Safe restart recognition after brief settling time
    setTimeout(() => {
      if (callActiveRef.current && callStatusRef.current === "listening" && !currentAudioRef.current) {
        safeStartRecognition();
      }
    }, 200);

    showToast("⚡ Interrupted • Aria paused. Listening to your request...");
  }

  function safeStopRecognition() {
    clearTimeout(recognitionRestartTimerRef.current);
    clearTimeout(turnSilenceTimerRef.current);
    isStartingRecognitionRef.current = false;
    isRecognitionRunningRef.current = false;
    setIsMicListening(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch {
        // Ignored
      }
      recognitionRef.current = null;
    }
  }

  function safeStartRecognition() {
    if (!callActiveRef.current || isMutedRef.current) return;
    if (callStatusRef.current === "speaking" || currentAudioRef.current) return;
    if (isRecognitionRunningRef.current || isStartingRecognitionRef.current) return;

    const Recognition = getSpeechRecognition();
    if (!Recognition) return;

    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }

    const rec = createRecognition();
    if (!rec) return;
    recognitionRef.current = rec;

    isStartingRecognitionRef.current = true;
    try {
      rec.start();
    } catch (err) {
      isStartingRecognitionRef.current = false;
      isRecognitionRunningRef.current = false;
      setIsMicListening(false);
      console.warn("Speech recognition start warning:", err);
    }
  }

  function createRecognition() {
    const Recognition = getSpeechRecognition();
    if (!Recognition) return null;

    const recognition = new Recognition();
    recognition.lang = speechLangRef.current || speechLang || "en-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isStartingRecognitionRef.current = false;
      isRecognitionRunningRef.current = true;
      setIsMicListening(true);
      setVoiceError("");
      console.log(`[Voice] Recognition started (${recognition.lang})`);
      if (callActiveRef.current && callStatusRef.current !== "speaking" && callStatusRef.current !== "thinking") {
        updateCallStatus("listening");
      }
    };

    recognition.onresult = (event) => {
      // Barge-in check: If Aria is speaking and customer starts speaking
      if (callStatusRef.current === "speaking" || currentAudioRef.current) {
        let interimBarge = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          interimBarge += event.results[i][0]?.transcript || "";
        }
        interimBarge = interimBarge.trim();
        if (interimBarge.length >= 2 && !isEchoOfAria(interimBarge)) {
          triggerBargeInInterruption();
        }
        return;
      }

      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const item = event.results[i];
        const text = item[0]?.transcript || "";
        if (item.isFinal) {
          finalTranscript += text;
        } else {
          interimTranscript += text;
        }
      }

      const heardSpeech = (finalTranscript || interimTranscript).trim();
      if (!heardSpeech) return;

      if (isEchoOfAria(heardSpeech)) {
        return;
      }

      if (!callActiveRef.current || callStatusRef.current === "thinking") {
        return;
      }

      // Update live hearing transcript so user visibly sees their voice being tracked!
      setUserSpeakingTranscript(heardSpeech);

      // Final transcript turn submission
      if (finalTranscript.trim()) {
        const utteranceToSubmit = finalTranscript.trim();
        if (!isEchoOfAria(utteranceToSubmit)) {
          clearTimeout(turnSilenceTimerRef.current);
          setUserSpeakingTranscript("");
          pendingTurnSpeechRef.current = "";
          sendVoiceCallMessage(utteranceToSubmit);
          return;
        }
      }

      // Interim speech auto-submit after 1.2s silence
      pendingTurnSpeechRef.current = heardSpeech;
      clearTimeout(turnSilenceTimerRef.current);
      turnSilenceTimerRef.current = setTimeout(() => {
        if (
          callActiveRef.current &&
          callStatusRef.current !== "speaking" &&
          !currentAudioRef.current &&
          callStatusRef.current !== "thinking" &&
          pendingTurnSpeechRef.current
        ) {
          const utteranceToSubmit = pendingTurnSpeechRef.current.trim();
          if (utteranceToSubmit.length >= 2) {
            if (!isEchoOfAria(utteranceToSubmit)) {
              setUserSpeakingTranscript("");
              pendingTurnSpeechRef.current = "";
              sendVoiceCallMessage(utteranceToSubmit);
            }
          }
        }
      }, 1200);
    };

    recognition.onerror = (event) => {
      isStartingRecognitionRef.current = false;
      isRecognitionRunningRef.current = false;
      setIsMicListening(false);
      console.warn("[Voice] Recognition error:", event.error);

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        setVoiceError("Microphone access was denied. Please click the lock or camera/mic icon in your browser URL bar to allow microphone access.");
        showToast("⚠️ Microphone access denied. Please allow microphone in browser.");
      } else if (event.error === "network") {
        setVoiceError("Speech recognition network timeout. Ensure internet connection is active or use typed input.");
      } else if (event.error === "audio-capture") {
        setVoiceError("No microphone detected. Please check your system audio input device.");
      }
    };

    recognition.onend = () => {
      isStartingRecognitionRef.current = false;
      isRecognitionRunningRef.current = false;
      setIsMicListening(false);

      if (
        callActiveRef.current &&
        !isMutedRef.current &&
        callStatusRef.current === "listening" &&
        !currentAudioRef.current
      ) {
        clearTimeout(recognitionRestartTimerRef.current);
        recognitionRestartTimerRef.current = window.setTimeout(() => {
          if (
            callActiveRef.current &&
            !isMutedRef.current &&
            callStatusRef.current === "listening" &&
            !currentAudioRef.current
          ) {
            safeStartRecognition();
          }
        }, 150);
      }
    };

    return recognition;
  }

  async function sendVoiceCallMessage(rawMessage) {
    const message = rawMessage.trim();
    if (!message || !callActiveRef.current) return;

    // Suppress duplicate customer utterances within 2.5 seconds
    const now = Date.now();
    if (
      message.toLowerCase() === lastProcessedTurnRef.current.text.toLowerCase() &&
      now - lastProcessedTurnRef.current.timestamp < 2500
    ) {
      return;
    }

    // Suppress overlapping turn submissions
    if (isProcessingTurnRef.current) {
      return;
    }

    isProcessingTurnRef.current = true;
    lastProcessedTurnRef.current = { text: message, timestamp: now };

    // Highlight Call Customer Care if the customer asks for a human / live support agent
    const isHumanRequest = /\b(human|real person|agent|support team|customer care|call someone|talk to someone|representative|speak to someone)\b/i.test(message);
    if (isHumanRequest) {
      setHighlightCustomerCare(true);
    }

    // Stop recognition and clear hearing states while waiting for AI backend response
    clearTimeout(turnSilenceTimerRef.current);
    setUserSpeakingTranscript("");
    pendingTurnSpeechRef.current = "";
    safeStopRecognition();
    stopAllSpeech(false);

    setCallMessages((prev) => [
      ...prev,
      { role: "user", text: message, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
    ]);
    updateCallStatus("thinking");

    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const startTime = performance.now();

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message, call_id: callIdRef.current }),
      });

      const latencyMs = Math.round(performance.now() - startTime);
      setBackendLatency(latencyMs);

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to contact Aria.");
      }

      const reply = data.reply || "I am processing your inquiry.";
      setCallMessages((prev) => [
        ...prev,
        { role: "assistant", text: reply, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
      ]);

      if (callActiveRef.current) {
        speakCallReply(reply);
      }
    } catch (err) {
      const errReply = `Sorry, there was an issue: ${err.message}`;
      setCallMessages((prev) => [
        ...prev,
        { role: "assistant", text: errReply, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
      ]);
      if (callActiveRef.current) {
        speakCallReply(errReply);
      }
    } finally {
      isProcessingTurnRef.current = false;
    }
  }

  function handleSpeechFinished(speechId) {
    if (speechId !== speechSessionIdRef.current || !callActiveRef.current) {
      return;
    }
    ariaSpeechEndTimeRef.current = Date.now();
    currentAriaSpeechTextRef.current = "";
    setUserSpeakingTranscript("");
    pendingTurnSpeechRef.current = "";
    clearTimeout(turnSilenceTimerRef.current);
    if (callActiveRef.current) {
      updateCallStatus("listening");
      // Allow 200ms for speaker audio reverberation in the room to decay before opening microphone
      setTimeout(() => {
        if (callActiveRef.current && callStatusRef.current === "listening" && !currentAudioRef.current) {
          safeStartRecognition();
        }
      }, 200);
    } else {
      updateCallStatus("idle");
    }
  }

  function fallbackToBrowserTTS(text, speechId) {
    if (speechId !== speechSessionIdRef.current || !callActiveRef.current) {
      return;
    }
    if (!("speechSynthesis" in window)) {
      handleSpeechFinished(speechId);
      return;
    }
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.resume();
    } catch {
      // Ignored
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.volume = 1.0;
    utterance.rate = 1.15;
    utterance.pitch = 1.02;

    const voices = window.speechSynthesis.getVoices();
    const preferredVoice =
      voices.find((v) => v.lang.toLowerCase() === "en-in" && /google|natural|neural/i.test(v.name)) ||
      voices.find((v) => v.lang.toLowerCase() === "en-in") ||
      voices.find((v) => v.lang.toLowerCase().startsWith("en"));

    if (preferredVoice) utterance.voice = preferredVoice;

    let hasFinished = false;
    const finishUtterance = () => {
      if (hasFinished) return;
      hasFinished = true;
      if (speechId === speechSessionIdRef.current && callActiveRef.current) {
        handleSpeechFinished(speechId);
      }
    };

    utterance.onstart = () => {
      if (speechId !== speechSessionIdRef.current || !callActiveRef.current) {
        window.speechSynthesis.cancel();
        return;
      }
      updateCallStatus("speaking");
      safeStopRecognition();
    };

    utterance.onend = finishUtterance;
    utterance.onerror = finishUtterance;

    // Safety timeout in case browser speech synthesis hangs
    const estDuration = Math.max(3000, (text.split(" ").length * 350) + 2000);
    setTimeout(() => {
      if (!hasFinished && speechId === speechSessionIdRef.current && callActiveRef.current) {
        finishUtterance();
      }
    }, estDuration);

    window.speechSynthesis.speak(utterance);
  }

  async function speakCallReply(text) {
    stopAllSpeech(false);
    safeStopRecognition();

    const currentSpeechId = ++speechSessionIdRef.current;
    currentAriaSpeechTextRef.current = text;
    recentAriaTextsRef.current.push(text);
    if (recentAriaTextsRef.current.length > 5) {
      recentAriaTextsRef.current.shift();
    }
    ariaSpeechStartTimeRef.current = Date.now();

    try {
      updateCallStatus("speaking");
      const res = await fetch(`${API_URL}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: "en-IN-NeerjaNeural", rate: "+20%" }),
      });

      if (!res.ok) {
        throw new Error(`TTS server responded with ${res.status}`);
      }

      if (currentSpeechId !== speechSessionIdRef.current || !callActiveRef.current) {
        // Cancelled / interrupted while loading TTS
        return;
      }

      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      audio.onplay = () => {
        if (currentSpeechId !== speechSessionIdRef.current || !callActiveRef.current) {
          audio.pause();
          return;
        }
        updateCallStatus("speaking");
      };

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        if (currentSpeechId !== speechSessionIdRef.current || !callActiveRef.current) {
          return;
        }
        handleSpeechFinished(currentSpeechId);
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        currentAudioRef.current = null;
        if (currentSpeechId !== speechSessionIdRef.current || !callActiveRef.current) {
          return;
        }
        fallbackToBrowserTTS(text, currentSpeechId);
      };

      await audio.play();
    } catch (err) {
      if (currentSpeechId !== speechSessionIdRef.current || !callActiveRef.current) {
        return;
      }
      console.warn("Falling back to browser speech synthesis:", err);
      fallbackToBrowserTTS(text, currentSpeechId);
    }
  }

  async function startCall() {
    if (!token || !customer) {
      setAuthMode("login");
      setAuthError("Voice calls are personalized for registered customers. Please log in first.");
      setAuthModalOpen(true);
      return;
    }

    const Recognition = getSpeechRecognition();
    if (!Recognition) {
      setVoiceError("Voice recognition isn't supported by this browser. Try Chrome or Edge.");
      return;
    }

    // Prompt & connect microphone with real-time level analyzer
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        stopMicMonitor();
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        micStreamRef.current = micStream;

        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
          const audioCtx = new AudioContextClass();
          audioContextRef.current = audioCtx;
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 256;
          analyserRef.current = analyser;
          const source = audioCtx.createMediaStreamSource(micStream);
          source.connect(analyser);

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const checkVolume = () => {
            if (!callActiveRef.current) return;
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            const level = Math.min(100, Math.round((avg / 64) * 100));
            setMicAudioLevel(level);
            animFrameRef.current = requestAnimationFrame(checkVolume);
          };
          animFrameRef.current = requestAnimationFrame(checkVolume);
        }
      } catch (micErr) {
        setVoiceError("Microphone access was denied. Please click the lock or camera/mic icon in your browser URL bar to allow microphone access.");
        showToast("⚠️ Microphone access required to speak with Aria.");
        return;
      }
    }

    setCallModalOpen(true);
    stopAllSpeech(false);
    safeStopRecognition();
    setCallSummary(null);
    setVoiceError("");
    updateCallStatus("connecting");
    setIsBargeInInterrupted(false);
    setHighlightCustomerCare(false);
    setUserSpeakingTranscript("");
    setStudioInput("");
    pendingTurnSpeechRef.current = "";
    isProcessingTurnRef.current = false;
    lastProcessedTurnRef.current = { text: "", timestamp: 0 };

    try {
      const res = await fetch(`${API_URL}/api/calls/start`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error("Could not initialize call session.");
      }

      const callData = await res.json();
      setCallId(callData.call_id);
      callIdRef.current = callData.call_id;

      callActiveRef.current = true;
      setCallActive(true);

      setCallMessages([
        {
          role: "assistant",
          text: callData.greeting,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);

      speakCallReply(callData.greeting);
    } catch (err) {
      setVoiceError(err.message || "Failed to start call.");
      callActiveRef.current = false;
      setCallActive(false);
      updateCallStatus("idle");
    }
  }

  async function endCall(showSummary = true) {
    const currentCallId = callIdRef.current;
    callActiveRef.current = false;
    setCallActive(false);
    updateCallStatus("idle");
    setIsBargeInInterrupted(false);
    isProcessingTurnRef.current = false;
    clearTimeout(turnSilenceTimerRef.current);
    pendingTurnSpeechRef.current = "";
    setUserSpeakingTranscript("");

    // Safely stop recognition, speech, and mic monitor
    safeStopRecognition();
    stopAllSpeech(false);
    stopMicMonitor();

    if (currentCallId && token && showSummary) {
      try {
        const durationSeconds = callTimer;
        const res = await fetch(`${API_URL}/api/calls/${currentCallId}/end`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ duration_seconds: durationSeconds }),
        });
        if (res.ok) {
          const data = await res.json();
          setCallSummary(data.summary);
          if (data.summary?.email_scheduled) {
            showToast("📋 Call ended. Support email scheduled in 10s.");
          } else {
            showToast("📋 Call ended. Support summary generated.");
          }
        }
      } catch {
        // Fallback
      }
    }

    setCallId(null);
    callIdRef.current = null;
  }

  function toggleMute() {
    if (isMuted) {
      setIsMuted(false);
      isMutedRef.current = false;
      safeStartRecognition();
      if (callStatusRef.current !== "speaking" && callStatusRef.current !== "thinking") {
        updateCallStatus("listening");
      }
      showToast("🎙️ Microphone unmuted.");
    } else {
      setIsMuted(true);
      isMutedRef.current = true;
      safeStopRecognition();
      showToast("🔇 Microphone muted.");
    }
  }

  // =========================================================================
  // GENERAL HELPERS
  // =========================================================================
  function toggleWishlist(id) {
    setWishlist((prev) => {
      const next = !prev[id];
      showToast(next ? "♥ Added to your wishlist" : "Removed from wishlist");
      return { ...prev, [id]: next };
    });
  }

  function handleAddToCart(product) {
    setCartItems((prev) => {
      const existing = prev.find((i) => i.id === product.id);
      if (existing) {
        return prev.map((i) => (i.id === product.id ? { ...i, qty: i.qty + 1 } : i));
      }
      return [...prev, { id: product.id, name: product.name, price: product.price, qty: 1, img: product.img }];
    });
    showToast(`🛍️ ${product.name} added to your bag!`);
    setCartDrawerOpen(true);
  }

  function updateCartQty(id, delta) {
    setCartItems((prev) =>
      prev
        .map((item) => {
          if (item.id === id) {
            const newQty = item.qty + delta;
            return newQty > 0 ? { ...item, qty: newQty } : null;
          }
          return item;
        })
        .filter(Boolean)
    );
  }

  function handleNewsletterSubmit(e) {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    setNewsletterSubscribed(true);
    setNewsletterEmail("");
    showToast("🎉 Welcome to the Aura Club! 20% discount code: AURA20");
  }

  function handleQuizSubmit() {
    setQuizModalOpen(false);
    setChatDrawerOpen(true);
    sendNormalChatMessage(
      `I completed the skin diagnostic! My skin type is ${quizSkinType} and my primary goal is ${quizGoal}. What 3-step routine do you recommend?`
    );
  }

  // Filtered Products
  const filteredProducts =
    selectedCategory === "ALL"
      ? products
      : products.filter((p) => p.category.toUpperCase().includes(selectedCategory.toUpperCase()));

  const totalCartCount = cartItems.reduce((acc, item) => acc + item.qty, 0);
  const cartSubtotal = cartItems.reduce((acc, item) => acc + item.price * item.qty, 0);

  const callStatusLabel = {
    idle: "Call Ended / Idle",
    connecting: "Connecting to Aria...",
    listening: isBargeInInterrupted ? "Interrupted Aria • Listening to you..." : "Aria is listening to you...",
    thinking: "Aria is formulating response...",
    speaking: "Aria is speaking aloud...",
  }[callStatus];

  return (
    <div className="glow-app" onClick={() => userMenuOpen && setUserMenuOpen(false)}>
      {/* FLOATING INTERACTIVE TOAST */}
      {toastMessage && (
        <div className="toast-notification" role="status" aria-live="polite">
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. TOP ANNOUNCEMENT BAR */}
      <div className="top-notice-bar">
        <div className="top-notice-container">
          <div className="notice-left">
            <span className="notice-icon">🚚</span>
            <span>Free Shipping on Orders Over $50</span>
          </div>
          <div className="notice-right">
            {/* Direct links to both bots */}
            <button
              type="button"
              onClick={() => setChatDrawerOpen(true)}
              style={{ color: "#D6ECE5" }}
            >
              💬 Skincare Chat
            </button>
            <span className="notice-divider">|</span>
            <button
              type="button"
              onClick={startCall}
              style={{ color: "#55EFC4", fontWeight: 700 }}
            >
              🎙️ Live Voice Call
            </button>
            <span className="notice-divider">|</span>
            <button
              type="button"
              onClick={() => setQuizModalOpen(true)}
              style={{ color: "#F1C40F" }}
            >
              ✨ Skin Quiz
            </button>
            <span className="notice-divider">|</span>
            {customer ? (
              <>
                <span style={{ color: "#A8E6CF", fontSize: "0.78rem", fontWeight: 600 }}>
                  Hi, {customer.full_name.split(" ")[0]}
                </span>
                <span className="notice-divider">|</span>
                <button type="button" onClick={handleTrackOrderClick}>
                  My Orders ({orders.length})
                </button>
                <span className="notice-divider">|</span>
                <button
                  type="button"
                  onClick={() => handleLogout(true)}
                  style={{ color: "#FFAAA6", fontWeight: 700 }}
                  title="Log out of account"
                >
                  Log Out
                </button>
              </>
            ) : (
              <button type="button" onClick={handleTrackOrderClick}>
                Track Order
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. MAIN HEADER & NAVIGATION */}
      <header className="main-header">
        <div className="header-container">
          {/* Brand Logo */}
          <a href="#" className="brand-logo" aria-label="Aura Skincare">
            <div className="brand-emblem">❦</div>
            <div className="brand-text-block">
              <span className="brand-title">Aura</span>
              <span className="brand-subtitle">SKINCARE</span>
            </div>
          </a>

          {/* Nav Links */}
          <nav>
            <ul className="nav-links">
              <li><a href="#" className="nav-link active">HOME</a></li>
              <li><a href="#shop" className="nav-link">SHOP</a></li>
              <li><a href="#ai-experience" className="nav-link">AI ASSISTANTS</a></li>
              <li>
                <button
                  type="button"
                  onClick={() => setQuizModalOpen(true)}
                  className="nav-link"
                  style={{ background: "none", border: "none", cursor: "pointer" }}
                >
                  SKIN QUIZ
                </button>
              </li>
              <li><a href="#collections" className="nav-link">COLLECTIONS</a></li>
            </ul>
          </nav>

          {/* Header Action Icons */}
          <div className="header-actions">
            {/* SEPARATE BOT 1: Normal Skincare Chatbot Button */}
            <button
              className="bot-nav-btn chat-type"
              type="button"
              onClick={() => setChatDrawerOpen(true)}
              title="Open text-based Skincare Chat Assistant"
            >
              <span>💬</span>
              <span>Skincare Chat</span>
            </button>

            {/* SEPARATE BOT 2: Live AI Voice Agent Call Button */}
            <button
              className="bot-nav-btn call-type"
              type="button"
              onClick={startCall}
              title="Start spoken Voice Call with Aria AI Agent"
            >
              <span className="pulse-mic"></span>
              <span>Live Agent Call</span>
            </button>

            {/* Search Button */}
            <button
              className="icon-btn"
              type="button"
              title="Ask Skincare Chat about Products"
              onClick={() => {
                setChatDrawerOpen(true);
                sendNormalChatMessage("What products do you recommend for dry or sensitive skin?");
              }}
            >
              🔍
            </button>

            {/* User Account Controls & Logout Option */}
            {customer ? (
              <div className="user-menu-wrap" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="user-account-badge"
                  onClick={() => setUserMenuOpen((prev) => !prev)}
                  title="Account options"
                >
                  <span>👤</span>
                  <span>{customer.full_name.split(" ")[0]}</span>
                  <span style={{ fontSize: "0.62rem", opacity: 0.8 }}>▼</span>
                </button>

                {/* 1-Click Logout Button right in header */}
                <button
                  type="button"
                  className="header-logout-btn"
                  onClick={() => handleLogout(true)}
                  title="Log out of Aura"
                >
                  <span>🚪</span>
                  <span>Log Out</span>
                </button>

                {/* Dropdown Menu */}
                {userMenuOpen && (
                  <div className="user-dropdown-card">
                    <div className="user-dropdown-info">
                      <strong>{customer.full_name}</strong>
                      <span>{customer.email}</span>
                    </div>
                    <div className="user-dropdown-actions">
                      <button
                        type="button"
                        className="dropdown-item-btn"
                        onClick={() => {
                          setUserMenuOpen(false);
                          setOrdersModalOpen(true);
                        }}
                      >
                        <span>📦</span>
                        <span>My Orders ({orders.length})</span>
                      </button>
                      <button
                        type="button"
                        className="dropdown-item-btn"
                        onClick={() => {
                          setUserMenuOpen(false);
                          startCall();
                        }}
                      >
                        <span>🎙️</span>
                        <span>Start Voice Agent Call</span>
                      </button>
                      <button
                        type="button"
                        className="dropdown-item-btn dropdown-logout-btn"
                        onClick={() => handleLogout(true)}
                      >
                        <span>🚪</span>
                        <span>Log Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <button
                className="icon-btn"
                type="button"
                title="Account Login / Sign Up"
                onClick={() => {
                  setAuthMode("login");
                  setAuthModalOpen(true);
                }}
              >
                👤
              </button>
            )}

            {/* Shopping Cart Icon with Slide-over Drawer */}
            <button
              className="icon-btn"
              type="button"
              title="Open Shopping Bag"
              onClick={() => setCartDrawerOpen(true)}
            >
              🛍️
              <span className="cart-badge">{totalCartCount}</span>
            </button>
          </div>
        </div>
      </header>

      {/* 3. HERO BANNER SECTION */}
      <section className="hero-section">
        <div className="hero-grid">
          <div className="hero-content">
            <span className="hero-eyebrow">NATURALLY RADIANT</span>
            <h1 className="hero-headline">
              Skincare<br />
              that cares,<br />
              <span>beauty that<br />shines.</span>
            </h1>
            <div className="hero-flourish">❦</div>
            <p className="hero-subtitle">
              Discover the perfect blend of botanical science and dual AI assistance:
              instant text guidance or live voice customer support.
            </p>

            <div className="hero-cta-group">
              <a href="#shop" className="btn-pill-primary">
                <span>SHOP NOW</span>
                <span>→</span>
              </a>
              <button
                type="button"
                className="btn-pill-secondary"
                onClick={() => setChatDrawerOpen(true)}
              >
                <span>💬</span>
                <span>TEXT CHAT</span>
              </button>
              <button
                type="button"
                className="btn-pill-aria"
                onClick={startCall}
              >
                <span>🎙️</span>
                <span>LIVE VOICE CALL</span>
              </button>
            </div>
          </div>

          <div className="hero-image-wrap">
            <div className="hero-glow-backdrop"></div>
            <img
              src="/images/hero-model.jpg"
              alt="Radiant woman with glowing skin surrounded by botanical leaves and pure water droplets"
              className="hero-model-img"
            />
          </div>
        </div>
      </section>

      {/* 4. FLOATING FEATURE PILL BAR */}
      <div className="floating-features-bar">
        <div className="features-card">
          <div className="feature-col">
            <div className="feature-icon-circle">🌿</div>
            <div className="feature-texts">
              <h4>Natural Ingredients</h4>
              <p>Safe & Effective</p>
            </div>
          </div>
          <div className="feature-col">
            <div className="feature-icon-circle">💧</div>
            <div className="feature-texts">
              <h4>Dermatologist Tested</h4>
              <p>For All Skin Types</p>
            </div>
          </div>
          <div className="feature-col">
            <div className="feature-icon-circle">🧪</div>
            <div className="feature-texts">
              <h4>Paraben & Sulfate Free</h4>
              <p>Clean & Gentle</p>
            </div>
          </div>
          <div className="feature-col">
            <div className="feature-icon-circle">🐰</div>
            <div className="feature-texts">
              <h4>Cruelty Free</h4>
              <p>Never Tested on Animals</p>
            </div>
          </div>
        </div>
      </div>

      {/* =====================================================================
          5. DEDICATED SECTION: CHOOSE YOUR AI EXPERIENCE (SEPARATE BOTS)
          ===================================================================== */}
      <section className="ai-experience-section" id="ai-experience">
        <div className="ai-experience-heading">
          <h2>Two Ways to Experience Aura AI</h2>
          <p>
            Choose between our fast text chatbot for routine recommendations,
            or connect directly with our Voice Agent Call for spoken consultations and order support.
          </p>
        </div>

        <div className="ai-experience-grid">
          {/* Card 1: Normal Skincare Chatbot */}
          <div className="ai-bot-card chat-mode">
            <div className="bot-card-header">
              <div className="bot-icon-circle">💬</div>
              <span className="bot-badge">Option 1: Normal Chat</span>
            </div>
            <h3>Aura Skincare Chatbot</h3>
            <p>
              Ideal for quick product advice, ingredient questions, formula breakdowns,
              and building your personalized morning/evening skincare routine.
            </p>
            <ul className="bot-features-list">
              <li><span className="feature-check">✓</span> Instant text-based conversation</li>
              <li><span className="feature-check">✓</span> Skincare advice, skin types & ingredients</li>
              <li><span className="feature-check">✓</span> No microphone required (works on all devices)</li>
              <li><span className="feature-check">✓</span> Open to both guests and registered members</li>
            </ul>
            <button
              type="button"
              className="bot-card-btn"
              onClick={() => setChatDrawerOpen(true)}
            >
              <span>💬</span>
              <span>Open Skincare Chat</span>
            </button>
          </div>

          {/* Card 2: Live AI Voice Agent Call */}
          <div className="ai-bot-card call-mode">
            <div className="bot-card-header">
              <div className="bot-icon-circle">🎙️</div>
              <span className="bot-badge">Option 2: Live Agent Call</span>
            </div>
            <h3>Aria Voice Agent Call</h3>
            <p>
              A hands-free phone conversation with spoken voice output. Aria verifies your
              orders, resolves inquiries, and sends post-call support summaries via email.
            </p>
            <ul className="bot-features-list">
              <li><span className="feature-check">✓</span> Real-time speech recognition & Edge Neural voice</li>
              <li><span className="feature-check">✓</span> Secure order lookup & courier tracking (ORD-101–107)</li>
              <li><span className="feature-check">✓</span> Post-call summary & automated n8n support email</li>
              <li><span className="feature-check">✓</span> Dedicated call studio with live soundwave visualizer</li>
            </ul>
            <button
              type="button"
              className="bot-card-btn"
              onClick={startCall}
            >
              <span>🎙️</span>
              <span>Start Live Voice Call</span>
            </button>
          </div>
        </div>
      </section>

      {/* 6. SHOP BY CATEGORY SECTION */}
      <section className="category-section" id="collections">
        <div className="section-ribbon-heading">
          <div className="heading-line"></div>
          <span>—» SHOP BY CATEGORY «—</span>
          <div className="heading-line"></div>
        </div>

        <div className="categories-grid">
          {[
            { name: "SERUMS", icon: "🧪", action: "Explore" },
            { name: "MOISTURIZERS", icon: "🧴", action: "Explore" },
            { name: "CLEANSERS", icon: "🫧", action: "Explore" },
            { name: "TONERS", icon: "💦", action: "Explore" },
            { name: "EYE CARE", icon: "👁️", action: "Explore" },
            { name: "SUN CARE", icon: "☀️", action: "Explore" },
          ].map((cat, i) => (
            <div
              key={i}
              className="category-card"
              onClick={() => {
                setSelectedCategory(cat.name);
                showToast(`Filtered by ${cat.name}`);
                const el = document.getElementById("shop");
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
            >
              <div className="category-circle">
                <span className="category-circle-icon">{cat.icon}</span>
              </div>
              <span className="category-name">{cat.name}</span>
              <span className="category-action">{cat.action}</span>
            </div>
          ))}
        </div>
      </section>

      {/* 7. FEATURED PRODUCTS SECTION */}
      <section className="featured-section" id="shop">
        <div className="section-header-row">
          <div className="section-title-wrap">
            <h2>
              FEATURED PRODUCTS
              {selectedCategory !== "ALL" && (
                <span className="active-filter-badge">
                  Category: {selectedCategory}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCategory("ALL");
                    }}
                    style={{ background: "none", border: "none", cursor: "pointer", marginLeft: "4px" }}
                  >
                    ✕
                  </button>
                </span>
              )}
            </h2>
          </div>
          <button
            type="button"
            className="view-all-link"
            onClick={() => setSelectedCategory("ALL")}
          >
            {selectedCategory === "ALL" ? "VIEW ALL" : "SHOW ALL PRODUCTS"}
          </button>
        </div>

        <div className="products-grid">
          {filteredProducts.map((p) => (
            <div className="product-card" key={p.id}>
              <div
                className="product-img-container"
                onClick={() => setQuickViewProduct(p)}
                style={{ cursor: "pointer" }}
              >
                <span className={`product-badge ${p.badgeClass}`}>{p.badge}</span>
                <button
                  type="button"
                  className={`wishlist-btn ${wishlist[p.id] ? "active" : ""}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleWishlist(p.id);
                  }}
                  title="Toggle Wishlist"
                >
                  ♥
                </button>
                <img src={p.img} alt={p.name} className="product-img" />
              </div>
              <div className="product-info">
                <h3
                  className="product-name"
                  onClick={() => setQuickViewProduct(p)}
                  style={{ cursor: "pointer" }}
                >
                  {p.name}
                </h3>
                <div className="product-reviews">
                  <span className="stars">★★★★★</span>
                  <span>({p.reviews})</span>
                </div>
                <div className="product-price-row">
                  <span className="current-price">${p.price.toFixed(2)}</span>
                  {p.originalPrice && <span className="original-price">${p.originalPrice.toFixed(2)}</span>}
                </div>
                <div className="product-card-actions">
                  <button
                    type="button"
                    className="add-to-cart-btn"
                    onClick={() => handleAddToCart(p)}
                  >
                    ADD TO CART ›
                  </button>
                  <button
                    type="button"
                    className="ask-aria-quick-btn"
                    title={`Ask Skincare Chatbot about ${p.name}`}
                    onClick={() => {
                      setChatDrawerOpen(true);
                      sendNormalChatMessage(`Tell me about ${p.name}. What skin type is it best for?`);
                    }}
                  >
                    💬
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 8. SPECIAL OFFER PROMO BANNER */}
      <section className="promo-banner-section">
        <div className="promo-banner-card">
          <div className="promo-image-col">
            <img
              src="/images/promo-bottles.jpg"
              alt="Aura Skincare botanical bottles arranged on stone"
            />
          </div>
          <div className="promo-content-col">
            <span className="promo-tag">SPECIAL OFFER</span>
            <h3 className="promo-heading">Get 20% Off Your First Order</h3>
            <p className="promo-subtext">
              Join our Aura club & unlock exclusive botanical releases,
              skincare rituals, and priority consultations with Aria.
            </p>
          </div>
          <div className="promo-action-col">
            <div className="promo-mail-icon">✉</div>
            <h4>JOIN NOW</h4>
            <p>Be the first to know about new arrivals & exclusive deals.</p>
            {newsletterSubscribed ? (
              <span style={{ color: "#A8E6CF", fontWeight: 700, fontSize: "0.85rem" }}>
                ✓ You're in the Aura Club! (Code: AURA20)
              </span>
            ) : (
              <form onSubmit={handleNewsletterSubmit} style={{ display: "flex", gap: "6px", width: "100%" }}>
                <input
                  type="email"
                  required
                  placeholder="Your email address"
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                  style={{
                    flex: 1,
                    padding: "8px 12px",
                    borderRadius: "20px",
                    border: "none",
                    fontSize: "0.8rem",
                    outline: "none",
                  }}
                />
                <button type="submit" className="join-club-btn">Join</button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* 9. TRUST GUARANTEE FOOTER BAR */}
      <div className="trust-footer-bar">
        <div className="trust-container">
          <div className="trust-item">
            <div className="trust-item-icon">🚚</div>
            <div className="trust-texts">
              <strong>FREE SHIPPING</strong>
              <span>On orders over $50</span>
            </div>
          </div>
          <div className="trust-item">
            <div className="trust-item-icon">🛡️</div>
            <div className="trust-texts">
              <strong>SECURE PAYMENT</strong>
              <span>100% safe & secure</span>
            </div>
          </div>
          <div className="trust-item">
            <div className="trust-item-icon">🔄</div>
            <div className="trust-texts">
              <strong>EASY RETURNS</strong>
              <span>30 days return policy</span>
            </div>
          </div>
          <div className="trust-item">
            <div className="trust-item-icon">🎧</div>
            <div className="trust-texts">
              <strong>CUSTOMER SUPPORT</strong>
              <span>We're here to help</span>
            </div>
          </div>
        </div>
      </div>

      {/* 10. SITE FOOTER */}
      <footer className="site-footer">
        <div className="footer-container">
          <div className="footer-brand">
            <h3>Aura Skincare</h3>
            <p>
              Mindfully formulated botanical skincare backed by science.
              Offering dual AI assistance: 24/7 text advice & spoken voice calls.
            </p>
            <div className="aria-agent-status-badge">
              <span>●</span>
              <span>Aura AI Systems: Online & Active</span>
              {backendLatency && <span>({backendLatency}ms)</span>}
            </div>
          </div>

          <div className="footer-col">
            <h4>SHOP</h4>
            <ul>
              <li><a href="#collections">All Serums</a></li>
              <li><a href="#collections">Moisturizers & Gels</a></li>
              <li><a href="#collections">Gentle Cleansers</a></li>
              <li><a href="#collections">Sunscreen & UV Shield</a></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>AI ASSISTANCE</h4>
            <ul>
              <li>
                <button type="button" onClick={() => setChatDrawerOpen(true)}>
                  💬 Normal Skincare Chat
                </button>
              </li>
              <li>
                <button type="button" onClick={startCall}>
                  🎙️ Live Voice Agent Call
                </button>
              </li>
              <li>
                <button type="button" onClick={handleTrackOrderClick}>
                  Track My Order
                </button>
              </li>
              <li>
                <button type="button" onClick={() => setQuizModalOpen(true)}>
                  Diagnostic Skin Quiz
                </button>
              </li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>MY ACCOUNT</h4>
            <ul>
              {customer ? (
                <>
                  <li><span style={{ color: "#FFF" }}>Signed in: {customer.full_name}</span></li>
                  <li><button type="button" onClick={() => setOrdersModalOpen(true)}>My Orders ({orders.length})</button></li>
                  <li>
                    <button
                      type="button"
                      onClick={() => handleLogout(true)}
                      style={{ color: "#FFAAA6", fontWeight: 700 }}
                    >
                      🚪 Log Out
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li><button type="button" onClick={() => { setAuthMode("login"); setAuthModalOpen(true); }}>Log In</button></li>
                  <li><button type="button" onClick={() => { setAuthMode("register"); setAuthModalOpen(true); }}>Create Account</button></li>
                </>
              )}
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© 2026 Aura Skincare • AI Voice & Chat Assistant. All rights reserved.</span>
          <span>Powered by Google Gemini & Edge Cloud Neural Voice</span>
        </div>
      </footer>

      {/* =====================================================================
          11. DUAL FLOATING DOCK (SHOWS BOTH BOTS SEPARATELY AT BOTTOM-RIGHT)
          ===================================================================== */}
      <div className="dual-floating-dock">
        <button
          type="button"
          className="dock-btn chat-dock"
          onClick={() => setChatDrawerOpen(true)}
          title="Open Normal Skincare Chatbot"
        >
          <span>💬</span>
          <span>Chat</span>
        </button>
        <button
          type="button"
          className="dock-btn call-dock"
          onClick={startCall}
          title="Start Live Voice Agent Call"
        >
          <span>🎙️</span>
          <span>Voice Call</span>
        </button>
      </div>

      {/* =====================================================================
          12. BOT OPTION 1 MODAL/DRAWER: NORMAL SKINCARE CHATBOT
          ===================================================================== */}
      {chatDrawerOpen && (
        <div className="aria-drawer-backdrop" onClick={() => setChatDrawerOpen(false)}>
          <aside className="aria-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="aria-drawer-header">
              <div className="drawer-title-area">
                <div className="drawer-avatar" style={{ background: "#176B5A" }}>💬</div>
                <div className="drawer-titles">
                  <h3>Aura Chat Assistant</h3>
                  <p>
                    <span style={{ color: "#55EFC4" }}>●</span> Normal Conversation Bot • Instant Advice
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="drawer-close-btn"
                onClick={() => setChatDrawerOpen(false)}
                aria-label="Close Chat"
              >
                ✕
              </button>
            </div>

            {/* Quick banner to switch to voice call if desired */}
            <div style={{ background: "#EFF8F5", padding: "10px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #D6ECE5" }}>
              <span style={{ fontSize: "0.78rem", color: "#142E28" }}>Prefer speaking aloud?</span>
              <button
                type="button"
                onClick={() => {
                  setChatDrawerOpen(false);
                  startCall();
                }}
                style={{
                  background: "#176B5A",
                  color: "#FFF",
                  border: "none",
                  borderRadius: "20px",
                  padding: "4px 12px",
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                🎙️ Switch to Voice Call
              </button>
            </div>

            {/* Messages Area */}
            <div className="drawer-messages-area" ref={chatScrollRef}>
              {chatMessages.map((m, idx) => (
                <div key={idx} className={`drawer-msg ${m.role}`}>
                  {m.role === "assistant" && <div className="msg-avatar">❦</div>}
                  <div className="msg-bubble-wrap">
                    <div className="msg-bubble">{m.text}</div>
                    <span className="msg-time">{m.time}</span>
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="drawer-msg assistant">
                  <div className="msg-avatar">❦</div>
                  <div className="msg-bubble typing">Aura Chatbot is formulating advice...</div>
                </div>
              )}
            </div>

            {/* Quick suggestions */}
            <div className="drawer-chips">
              <button
                type="button"
                onClick={() => sendNormalChatMessage("Recommend a complete 3-step routine for radiant glass skin.")}
              >
                ✨ Glass Skin Routine
              </button>
              <button
                type="button"
                onClick={() => sendNormalChatMessage("What ingredients help fade acne scars and dark spots?")}
              >
                🌿 Dark Spots Advice
              </button>
              <button
                type="button"
                onClick={() => sendNormalChatMessage("Are all Aura Skincare formulas paraben and sulfate free?")}
              >
                🧪 Clean Formula Info
              </button>
              <button
                type="button"
                onClick={() => sendNormalChatMessage("What is your 30-day return policy?")}
              >
                🔄 Return Policy
              </button>
            </div>

            {/* Chat Input Bar */}
            <div className="drawer-input-bar">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!chatLoading && chatInput.trim()) sendNormalChatMessage(chatInput);
                }}
                className="drawer-input-form"
              >
                <input
                  type="text"
                  placeholder="Ask about ingredients, skin types, routines..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                />
                <button
                  type="submit"
                  className="drawer-send-btn"
                  disabled={chatLoading || !chatInput.trim()}
                  title="Send message"
                >
                  ➤
                </button>
              </form>
            </div>
          </aside>
        </div>
      )}

      {/* =====================================================================
          13. BOT OPTION 2 MODAL: LIVE AI VOICE AGENT CALL STUDIO
          ===================================================================== */}
      {callModalOpen && (
        <div className="voice-studio-backdrop" onClick={() => !callActive && setCallModalOpen(false)}>
          <div className="voice-studio-card" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="voice-studio-header">
              <div className="studio-title-area">
                <div className="studio-avatar-circle">🎙️</div>
                <div>
                  <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>Aria Voice Agent Call</h3>
                  <span style={{ fontSize: "0.75rem", color: "#A8E6CF" }}>
                    Live Spoken Customer Support & Orders
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                {/* Language Selector */}
                <div className="studio-lang-selector" title="Choose speech recognition language">
                  <span className="studio-lang-label">Lang:</span>
                  <select
                    value={speechLang}
                    onChange={(e) => {
                      const newL = e.target.value;
                      setSpeechLang(newL);
                      speechLangRef.current = newL;
                      if (callActiveRef.current && callStatusRef.current === "listening") {
                        safeStopRecognition();
                        setTimeout(() => safeStartRecognition(), 120);
                      }
                    }}
                    className="studio-lang-dropdown"
                    aria-label="Speech recognition language"
                  >
                    <option value="en-IN">🇮🇳 Hinglish / en-IN</option>
                    <option value="hi-IN">🇮🇳 Hindi / hi-IN</option>
                    <option value="en-US">🌐 English / en-US</option>
                  </select>
                </div>

                {callActive && (
                  <div className="call-timer-badge">
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#55EFC4" }}></span>
                    <span>{formatCallDuration(callTimer)}</span>
                  </div>
                )}
                {customer && (
                  <button
                    type="button"
                    className="header-logout-btn"
                    onClick={() => handleLogout(true)}
                  >
                    Log Out
                  </button>
                )}
                <button
                  type="button"
                  className="drawer-close-btn"
                  onClick={() => {
                    if (callActive) endCall(true);
                    setCallModalOpen(false);
                  }}
                  title="Close Studio"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Scrollable Center Body for perfect viewport fitting */}
            <div className="voice-studio-scroll-body">
              {/* Soundwave Center Area */}
              <div className="voice-studio-center">
                <div
                  className={`studio-soundwave-wrap ${callActive && callStatus !== "idle" ? `active ${userSpeakingTranscript ? "user-speaking" : callStatus}` : ""}`}
                  onClick={() => {
                    if (callActive && (callStatus === "speaking" || currentAudioRef.current)) {
                      triggerBargeInInterruption();
                    } else if (callActive && callStatus === "listening") {
                      safeStartRecognition();
                    }
                  }}
                  style={{ cursor: "pointer" }}
                  title={callActive && callStatus === "speaking" ? "Click to interrupt Aria" : "Click to speak / activate mic"}
                >
                  {[20, 50, 80, 100, 75, 45, 25].map((baseH, idx) => {
                    let barH = undefined;
                    if (callActive && (userSpeakingTranscript || micAudioLevel > 6)) {
                      const boost = userSpeakingTranscript ? 1.2 : 0.85;
                      barH = Math.max(8, Math.min(42, Math.round((baseH / 100) * Math.max(16, micAudioLevel * boost))));
                    }
                    return (
                      <div
                        key={idx}
                        className="studio-soundwave-bar"
                        style={barH ? { height: `${barH}px` } : {}}
                      />
                    );
                  })}
                </div>

                <div className="studio-status-text">
                  {callActive ? (userSpeakingTranscript ? "Tracking your voice..." : callStatusLabel) : "Voice Call Session Ended"}
                </div>

                {/* Live Mic Status & Real-time Volume Level Meter */}
                {callActive && (
                  <div className="studio-mic-status-row">
                    <div className={`mic-live-pill ${isMicListening ? "active" : "standby"}`}>
                      <span className="mic-dot"></span>
                      <span>{isMicListening ? "Microphone Live & Tracking" : "Mic Standby"}</span>
                    </div>

                    <div className="mic-level-container" title={`Microphone input volume: ${micAudioLevel}%`}>
                      <span style={{ fontSize: "0.68rem", fontWeight: 700 }}>Mic Vol:</span>
                      <div className="mic-level-track">
                        <div
                          className="mic-level-fill"
                          style={{
                            width: `${Math.max(4, micAudioLevel)}%`,
                            background: micAudioLevel > 15 ? "#55EFC4" : "#A8E6CF"
                          }}
                        />
                      </div>
                      <span style={{ fontSize: "0.68rem" }}>{micAudioLevel}%</span>
                    </div>

                    {!isMicListening && callStatus === "listening" && (
                      <button
                        type="button"
                        className="mic-reconnect-btn"
                        onClick={() => safeStartRecognition()}
                        title="Click to restart speech recognition"
                      >
                        <span>🎙️ Click to Speak</span>
                      </button>
                    )}
                  </div>
                )}

                {callActive && callStatus === "speaking" && (
                  <button
                    type="button"
                    className="studio-interrupt-btn"
                    onClick={triggerBargeInInterruption}
                    title="Interrupt Aria and speak now"
                  >
                    <span>✋ Tap to Interrupt Aria</span>
                  </button>
                )}

                {callActive && callStatus !== "speaking" && !userSpeakingTranscript && (
                  <div className={`studio-bargein-pill ${isBargeInInterrupted ? "interrupted" : ""}`}>
                    <span>{isBargeInInterrupted ? "⚡" : "🎙️"}</span>
                    <span>{isBargeInInterrupted ? "Aria Interrupted • Listening to You" : "Speak naturally in Hindi, English or Hinglish"}</span>
                  </div>
                )}

                {/* Real-time Voice Tracking Hearing Bubble */}
                {callActive && userSpeakingTranscript && (
                  <div className="studio-live-hearing-bubble">
                    <span className="live-hearing-icon">🎙️</span>
                    <span className="live-hearing-label">Hearing:</span>
                    <span className="live-hearing-text">"{userSpeakingTranscript}"</span>
                    <button
                      type="button"
                      className="live-send-now-btn"
                      onClick={() => {
                        clearTimeout(turnSilenceTimerRef.current);
                        const textToSend = userSpeakingTranscript.trim();
                        setUserSpeakingTranscript("");
                        pendingTurnSpeechRef.current = "";
                        sendVoiceCallMessage(textToSend);
                      }}
                      title="Send speech immediately to Aria"
                    >
                      Send ↵
                    </button>
                  </div>
                )}

                <p className="studio-status-sub">
                  {callActive
                    ? (userSpeakingTranscript ? "Aria is capturing your voice. Pause speaking to send, or tap Send." : "Speak directly into your microphone. Aria will answer as soon as you finish speaking.")
                    : "Click 'Start Voice Call' to reconnect or review your post-call summary below."}
                </p>
              </div>

              {voiceError && (
                <div style={{ background: "rgba(231, 76, 60, 0.25)", border: "1px solid #E74C3C", color: "#FFAAA6", padding: "8px 20px", fontSize: "0.8rem", margin: "0 20px 10px", borderRadius: "10px" }}>
                  {voiceError}
                </div>
              )}

              {/* Post-Call Summary Ticket */}
              {callSummary && (
                <div className="drawer-summary-card" style={{ margin: "0 20px 12px" }}>
                  <div className="drawer-summary-header">
                    <strong>Post-Call Support Ticket</strong>
                    <span className={`status-tag ${callSummary.resolution_status}`}>
                      {callSummary.resolution_status}
                    </span>
                  </div>
                  <p>{callSummary.call_summary}</p>
                  <div className="drawer-summary-meta">
                    <span>Intent: {callSummary.customer_intent}</span>
                    {callSummary.order_id && <span>Order: {callSummary.order_id}</span>}
                    <span>
                      Email Follow-up: {callSummary.email_status_message || (callSummary.email_scheduled ? "Scheduled in 10s via n8n" : "Triggered via n8n (10s delay)")}
                    </span>
                  </div>
                </div>
              )}

              {/* Transcript of the live spoken conversation */}
              <div className="studio-transcript-box" ref={callTranscriptScrollRef}>
                <strong style={{ fontSize: "0.74rem", textTransform: "uppercase", color: "#A8E6CF", letterSpacing: "0.08em" }}>
                  Live Call Transcript:
                </strong>
                {callMessages.length === 0 && !userSpeakingTranscript ? (
                  <span style={{ fontSize: "0.82rem", color: "#8CA6A0", fontStyle: "italic" }}>
                    Call transcript will appear here as you speak with Aria...
                  </span>
                ) : (
                  <>
                    {callMessages.map((msg, i) => (
                      <div key={i} className={`studio-transcript-msg ${msg.role}`}>
                        <strong>{msg.role === "assistant" ? "Aria:" : `${customer?.full_name?.split(" ")[0] || "You"}:`}</strong>
                        <span>{msg.text}</span>
                      </div>
                    ))}
                    {userSpeakingTranscript && (
                      <div className="studio-transcript-msg user live-interim">
                        <strong>{customer?.full_name?.split(" ")[0] || "You"} (speaking...):</strong>
                        <span>{userSpeakingTranscript}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Quick Spoken / Typed Turn Input Fallback */}
            {callActive && (
              <form
                className="studio-quick-input-bar"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!studioInput.trim() || !callActive || callStatus === "thinking") return;
                  const textToSend = studioInput.trim();
                  setStudioInput("");
                  setUserSpeakingTranscript("");
                  pendingTurnSpeechRef.current = "";
                  clearTimeout(turnSilenceTimerRef.current);
                  sendVoiceCallMessage(textToSend);
                }}
              >
                <input
                  type="text"
                  className="studio-quick-input-field"
                  placeholder="Or type here to speak with Aria (e.g. 'Track order ORD-1001')..."
                  value={studioInput}
                  onChange={(e) => setStudioInput(e.target.value)}
                  disabled={!callActive || callStatus === "thinking"}
                  aria-label="Direct question to Aria during voice call"
                />
                <button
                  type="submit"
                  className="studio-quick-input-submit"
                  disabled={!callActive || !studioInput.trim() || callStatus === "thinking"}
                  title="Submit message and Aria speaks aloud"
                >
                  Send ↵
                </button>
              </form>
            )}

            {/* Call Controls */}
            <div className="studio-call-controls">
              {callActive ? (
                <>
                  <button
                    type="button"
                    className={`studio-btn mic-btn ${isMuted ? "muted" : ""}`}
                    onClick={toggleMute}
                    aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}
                  >
                    <span>{isMuted ? "🔇" : "🎙️"}</span>
                    <span>{isMuted ? "Unmute" : "Mute Mic"}</span>
                  </button>
                  <button
                    type="button"
                    className="studio-btn end-call-btn"
                    onClick={() => endCall(true)}
                    aria-label="End call session and generate support ticket"
                  >
                    <span>🔴</span>
                    <span>End Call & Ticket</span>
                  </button>
                  <button
                    type="button"
                    className={`studio-btn customer-care-btn ${highlightCustomerCare ? "highlighted" : ""}`}
                    onClick={handleCallCustomerCareClick}
                    aria-label="Call Customer Care phone support"
                    title="Call Aura Skincare Customer Care Support"
                  >
                    <span>📞</span>
                    <span>Call Customer Care</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    className="studio-btn start-call-btn"
                    onClick={startCall}
                    aria-label="Start new AI voice call"
                  >
                    <span>📞</span>
                    <span>Start New Voice Call</span>
                  </button>
                  <button
                    type="button"
                    className={`studio-btn customer-care-btn ${highlightCustomerCare ? "highlighted" : ""}`}
                    onClick={handleCallCustomerCareClick}
                    aria-label="Call Customer Care phone support"
                    title="Call Aura Skincare Customer Care Support"
                  >
                    <span>📞</span>
                    <span>Call Customer Care</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 14. INTERACTIVE SHOPPING CART DRAWER */}
      {cartDrawerOpen && (
        <div className="cart-drawer-backdrop" onClick={() => setCartDrawerOpen(false)}>
          <aside className="cart-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="cart-header">
              <h3>Your Shopping Bag ({totalCartCount})</h3>
              <button
                type="button"
                className="drawer-close-btn"
                onClick={() => setCartDrawerOpen(false)}
              >
                ✕
              </button>
            </div>

            <div className="free-shipping-progress">
              {cartSubtotal >= 50 ? (
                <strong>🎉 You've unlocked FREE Shipping!</strong>
              ) : (
                <span>
                  Add <strong>${(50 - cartSubtotal).toFixed(2)}</strong> more for <strong>FREE Shipping</strong>!
                </span>
              )}
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min(100, (cartSubtotal / 50) * 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="cart-items-list">
              {cartItems.length === 0 ? (
                <div style={{ textAlign: "center", color: "#666", padding: "40px 0" }}>
                  <p>Your shopping bag is empty.</p>
                  <button
                    type="button"
                    className="btn-pill-primary"
                    style={{ marginTop: "16px" }}
                    onClick={() => setCartDrawerOpen(false)}
                  >
                    Start Exploring
                  </button>
                </div>
              ) : (
                cartItems.map((item) => (
                  <div key={item.id} className="cart-item-row">
                    <img src={item.img} alt={item.name} className="cart-item-img" />
                    <div className="cart-item-info">
                      <strong>{item.name}</strong>
                      <span>${item.price.toFixed(2)}</span>
                      <div className="cart-qty-controls">
                        <button
                          type="button"
                          className="qty-btn"
                          onClick={() => updateCartQty(item.id, -1)}
                        >
                          -
                        </button>
                        <span style={{ fontSize: "0.85rem", fontWeight: 700 }}>{item.qty}</span>
                        <button
                          type="button"
                          className="qty-btn"
                          onClick={() => updateCartQty(item.id, 1)}
                        >
                          +
                        </button>
                      </div>
                    </div>
                    <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>
                      ${(item.price * item.qty).toFixed(2)}
                    </span>
                  </div>
                ))
              )}
            </div>

            {cartItems.length > 0 && (
              <div className="cart-footer-area">
                <div className="cart-subtotal-row">
                  <span>Subtotal</span>
                  <span>${cartSubtotal.toFixed(2)}</span>
                </div>
                <button
                  type="button"
                  className="cart-checkout-btn"
                  onClick={() => {
                    showToast("🎉 Thank you! Order simulation completed.");
                    setCartDrawerOpen(false);
                  }}
                >
                  Proceed to Checkout ›
                </button>
              </div>
            )}
          </aside>
        </div>
      )}

      {/* 15. INTERACTIVE PRODUCT QUICK VIEW MODAL */}
      {quickViewProduct && (
        <div className="modal-backdrop" onClick={() => setQuickViewProduct(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "580px" }}>
            <div className="modal-header">
              <h3>{quickViewProduct.name}</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setQuickViewProduct(null)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div style={{ display: "flex", gap: "20px", marginBottom: "18px" }}>
                <img
                  src={quickViewProduct.img}
                  alt={quickViewProduct.name}
                  style={{ width: "140px", height: "140px", borderRadius: "14px", objectFit: "cover", border: "1px solid #D6ECE5" }}
                />
                <div>
                  <div style={{ display: "flex", gap: "8px", alignItems: "baseline" }}>
                    <span style={{ fontSize: "1.4rem", fontWeight: 700, color: "#0D332D" }}>
                      ${quickViewProduct.price.toFixed(2)}
                    </span>
                    {quickViewProduct.originalPrice && (
                      <span style={{ textDecoration: "line-through", color: "#888", fontSize: "0.95rem" }}>
                        ${quickViewProduct.originalPrice.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div style={{ color: "#F1C40F", margin: "6px 0 10px", fontSize: "0.85rem" }}>
                    ★★★★★ ({quickViewProduct.reviews} verified reviews)
                  </div>
                  <p style={{ fontSize: "0.86rem", color: "#3A5650", lineHeight: 1.5 }}>
                    {quickViewProduct.description}
                  </p>
                </div>
              </div>

              <div style={{ background: "#F4F8F6", padding: "14px", borderRadius: "12px", marginBottom: "16px" }}>
                <strong style={{ fontSize: "0.82rem", color: "#0D332D", display: "block", marginBottom: "4px" }}>
                  🌿 Key Ingredients:
                </strong>
                <span style={{ fontSize: "0.8rem", color: "#4EA388" }}>{quickViewProduct.keyIngredients}</span>
                <strong style={{ fontSize: "0.82rem", color: "#0D332D", display: "block", margin: "10px 0 4px" }}>
                  ✨ How to Use:
                </strong>
                <span style={{ fontSize: "0.8rem", color: "#555" }}>{quickViewProduct.howToUse}</span>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="button"
                  className="btn-pill-primary"
                  style={{ flex: 1, justifyContent: "center" }}
                  onClick={() => {
                    handleAddToCart(quickViewProduct);
                    setQuickViewProduct(null);
                  }}
                >
                  Add to Bag (${quickViewProduct.price.toFixed(2)})
                </button>
                <button
                  type="button"
                  className="btn-pill-secondary"
                  onClick={() => {
                    const pName = quickViewProduct.name;
                    setQuickViewProduct(null);
                    setChatDrawerOpen(true);
                    sendNormalChatMessage(`Tell me more about ${pName}.`);
                  }}
                >
                  Ask Chatbot 💬
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 16. INTERACTIVE VIDEO MODAL */}
      {videoModalOpen && (
        <div className="modal-backdrop" onClick={() => setVideoModalOpen(false)}>
          <div className="video-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="video-container">
              <img
                src="/images/promo-bottles.jpg"
                alt="Botanical ritual"
                className="video-botanical-bg"
              />
              <div className="video-overlay-content">
                <button
                  type="button"
                  className="video-play-big-btn"
                  onClick={() => {
                    showToast("🌿 Playing 'The Botanical Journey of Aura Skincare'");
                  }}
                >
                  ▶
                </button>
                <h3 style={{ fontFamily: "Playfair Display, serif", fontSize: "1.8rem" }}>
                  The Science of Pure Radiance
                </h3>
                <p style={{ maxWidth: "420px", fontSize: "0.88rem", color: "#D6ECE5" }}>
                  Watch how our sustainable harvest in the Himalayan foothills transforms into potent, living skincare.
                </p>
                <button
                  type="button"
                  className="btn-pill-aria"
                  style={{ marginTop: "10px" }}
                  onClick={() => {
                    setVideoModalOpen(false);
                    startCall();
                  }}
                >
                  <span>🎙️</span> Discuss Routine in Voice Call
                </button>
              </div>
            </div>
            <div style={{ padding: "16px 24px", display: "flex", justifyContent: "flex-end", background: "#061A16" }}>
              <button
                type="button"
                className="btn-pill-secondary"
                style={{ padding: "8px 18px", fontSize: "0.8rem" }}
                onClick={() => setVideoModalOpen(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 17. INTERACTIVE SKIN DIAGNOSTIC QUIZ MODAL */}
      {quizModalOpen && (
        <div className="modal-backdrop" onClick={() => setQuizModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>✨ 1-Minute Botanical Skin Diagnostic</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setQuizModalOpen(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: "0.86rem", color: "#5F7D76", marginBottom: "16px" }}>
                Select your skin profile and Aura's chatbot will instantly craft a tailored 3-step ritual.
              </p>

              <label style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0D332D" }}>
                1. What is your primary skin type?
              </label>
              <div className="quiz-options-grid">
                {["Dry & Dehydrated", "Oily & Acne-Prone", "Combination", "Sensitive & Reactive"].map((type) => (
                  <div
                    key={type}
                    className={`quiz-option-card ${quizSkinType === type ? "selected" : ""}`}
                    onClick={() => setQuizSkinType(type)}
                  >
                    <strong>{type}</strong>
                    <span>Tailored botanical extracts</span>
                  </div>
                ))}
              </div>

              <label style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0D332D" }}>
                2. What is your primary goal?
              </label>
              <div className="quiz-options-grid">
                {["Radiant Glass Skin", "Deep 72h Moisture", "Pore Minimizing", "Anti-Aging & Firming"].map((goal) => (
                  <div
                    key={goal}
                    className={`quiz-option-card ${quizGoal === goal ? "selected" : ""}`}
                    onClick={() => setQuizGoal(goal)}
                  >
                    <strong>{goal}</strong>
                    <span>Targeted active results</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                className="auth-submit-btn"
                onClick={handleQuizSubmit}
              >
                Generate My Custom Routine in Chat ›
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 18. CUSTOMER ORDERS MODAL */}
      {ordersModalOpen && (
        <div className="modal-backdrop" onClick={() => setOrdersModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>My Orders ({customer?.full_name})</h3>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <button
                  type="button"
                  className="header-logout-btn"
                  onClick={() => handleLogout(true)}
                  style={{ background: "#FEE2E2", color: "#991B1B", borderColor: "#FCA5A5" }}
                  title="Log out of account"
                >
                  🚪 Log Out
                </button>
                <button
                  type="button"
                  className="modal-close-btn"
                  onClick={() => setOrdersModalOpen(false)}
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="modal-body">
              <div className="orders-list-content">
                {orders.length === 0 ? (
                  <p style={{ textAlign: "center", color: "#666", padding: "20px 0" }}>
                    No orders linked to this account yet.
                  </p>
                ) : (
                  orders.map((ord) => (
                    <div key={ord.order_id} className="order-card-item">
                      <div className="order-top-row">
                        <strong>{ord.order_id}</strong>
                        <span className="order-status-pill">{ord.status}</span>
                      </div>
                      <p className="order-product-line">
                        {ord.product_name} • ₹{ord.amount}
                      </p>
                      <div className="order-detail-meta">
                        {ord.courier && <div>Courier: {ord.courier} ({ord.tracking_number})</div>}
                        {ord.expected_delivery && <div>Expected: {ord.expected_delivery}</div>}
                        {ord.delivered_days_ago && <div>Delivered {ord.delivered_days_ago} days ago</div>}
                      </div>
                      <button
                        type="button"
                        className="order-track-aria-btn"
                        onClick={() => {
                          setOrdersModalOpen(false);
                          startCall();
                        }}
                      >
                        Ask Voice Agent about this order 🎙️ ›
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 19. AUTHENTICATION MODAL (LOGIN / REGISTER) */}
      {authModalOpen && (
        <div className="modal-backdrop" onClick={() => setAuthModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{authMode === "login" ? "Welcome Back to Aura Skincare" : "Create Your Account"}</h3>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setAuthModalOpen(false)}
              >
                ✕
              </button>
            </div>

            <div className="auth-nav-tabs">
              <button
                type="button"
                className={`auth-nav-tab ${authMode === "login" ? "active" : ""}`}
                onClick={() => {
                  setAuthMode("login");
                  setAuthError("");
                }}
              >
                Log In
              </button>
              <button
                type="button"
                className={`auth-nav-tab ${authMode === "register" ? "active" : ""}`}
                onClick={() => {
                  setAuthMode("register");
                  setAuthError("");
                }}
              >
                Register
              </button>
            </div>

            <div className="modal-body">
              {authError && <div className="auth-error-banner">{authError}</div>}

              <form onSubmit={handleAuthSubmit}>
                {authMode === "register" && (
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Divesh Matkar"
                      value={authFullName}
                      onChange={(e) => setAuthFullName(e.target.value)}
                    />
                  </div>
                )}

                <div className="form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. matkardivesh26@gmail.com"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Password</label>
                  <input
                    type="password"
                    required
                    placeholder="At least 8 characters (1 letter, 1 number)"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                  />
                </div>

                {authMode === "register" && (
                  <div className="form-group">
                    <label>Confirm Password</label>
                    <input
                      type="password"
                      required
                      placeholder="Re-enter password"
                      value={authPasswordConfirm}
                      onChange={(e) => setAuthPasswordConfirm(e.target.value)}
                    />
                  </div>
                )}

                <button
                  type="submit"
                  className="auth-submit-btn"
                  disabled={authLoading}
                >
                  {authLoading
                    ? "Processing..."
                    : authMode === "login"
                    ? "Log In"
                    : "Create Account"}
                </button>
              </form>

              {/* Quick Demo Accounts Switcher */}
              <div className="demo-users-box">
                <span>⚡ Instant Demo Logins (Password: Password123!)</span>
                <div className="demo-buttons-grid">
                  <button
                    type="button"
                    onClick={() => fillDemoUser("matkardivesh26@gmail.com", "Divesh Matkar")}
                  >
                    Divesh (ORD-104)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoUser("priya@example.com", "Priya Sharma")}
                  >
                    Priya (ORD-101)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoUser("rahul@example.com", "Rahul Verma")}
                  >
                    Rahul (ORD-102)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoUser("ananya@example.com", "Ananya Patel")}
                  >
                    Ananya (ORD-103)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoUser("sneha@example.com", "Sneha Kapoor")}
                  >
                    Sneha (ORD-105)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoUser("rohan@example.com", "Rohan Mehta")}
                  >
                    Rohan (ORD-106)
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
